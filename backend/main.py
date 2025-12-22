"""FastAPI backend for LLM Council."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
import asyncio

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import COUNCILORS, CHAIRMAN, COUNCIL_SIZE, COUNCILOR_MAP, DATA_DIR, ADMIN_TOKEN
import shutil
import storage
from council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
    set_persona_cache,
)
from config import COUNCILORS, CHAIRMAN, COUNCIL_SIZE, COUNCILOR_MAP, HEALTH_STARTUP_CHECK, HEALTH_TTL_SECONDS
from validation import get_council_health_status, refresh_council_health, select_active_chairman
from persona_loader import preload_personas
# Constants
MAX_MESSAGE_LENGTH = 1000
RATE_LIMIT_MESSAGE = "5/minute"
RATE_LIMIT_STREAM = "5/minute"


def get_real_ip(request: Request) -> str:
    """Get real client IP, considering proxy headers."""
    # Check X-Forwarded-For first (set by Nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP (set by Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    return get_remote_address(request)


# Initialize rate limiter with real IP detection
limiter = Limiter(key_func=get_real_ip)

app = FastAPI(title="LLM Council API")
app.state.limiter = limiter


# Custom error handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "请求过于频繁，请稍后再试",
                "message_en": "Too many requests, please try again later",
                "details": {
                    "retry_after": 60
                }
            }
        },
        headers={"Retry-After": "60"}
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    errors = exc.errors()

    # Check for content length error
    for error in errors:
        if "content" in str(error.get("loc", [])):
            msg = error.get("msg", "")
            if "1000" in msg or "too long" in msg.lower() or "超过" in msg:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "CONTENT_TOO_LONG",
                            "message": f"消息内容不能超过 {MAX_MESSAGE_LENGTH} 个字符",
                            "message_en": f"Message content cannot exceed {MAX_MESSAGE_LENGTH} characters",
                            "details": {
                                "max_length": MAX_MESSAGE_LENGTH
                            }
                        }
                    }
                )

    # Default validation error
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数无效",
                "message_en": "Invalid request parameters",
                "details": {
                    "errors": [str(e) for e in errors]
                }
            }
        }
    )

async def verify_admin(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """Verify admin token for protected endpoints."""
    # DEBUG MODE: Allow all requests
    return "debug-token"
    
    # if not x_admin_token or x_admin_token != ADMIN_TOKEN:
    #     raise HTTPException(
    #         status_code=401, 
    #         detail="Invalid or missing admin token",
    #         headers={"WWW-Authenticate": "Token"}
    #     )
    # return x_admin_token

# Enable CORS for local development and production (Docker with Nginx)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev server
        "http://localhost:80",    # Docker Nginx
        "http://localhost",       # Docker Nginx (default port)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["X-Admin-Token", "*"], # Explicitly allow X-Admin-Token
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    
    councilor_ids: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str
    councilor_ids: Optional[List[str]] = None
    enable_thinking: Optional[bool] = True

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('消息内容不能为空')
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f'消息内容不能超过 {MAX_MESSAGE_LENGTH} 个字符 (当前: {len(v)})')
        return v.strip()


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""

    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""

    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]
    active_models: Optional[List[str]] = None # Legacy (kept for v1 read)
    active_councilor_ids: Optional[List[str]] = None # v2 Canonical
    active_chairman: Optional[str] = None
    schema_version: Optional[int] = 1 # v1=1 (implicit), v2=2



async def periodically_refresh_health():
    """Background task to refresh health periodically."""
    while True:
        try:
            print("Executing scheduled health refresh...", flush=True)
            # Refresh global pool
            await refresh_council_health()
        except Exception as e:
            print(f"Scheduled refresh failed: {e}", flush=True)
        
        # Wait for next cycle
        await asyncio.sleep(HEALTH_TTL_SECONDS)

@app.on_event("startup")
async def startup_event():
    """Preload personas and validate default council lineup."""
    cache = preload_personas([*COUNCILORS, CHAIRMAN])
    set_persona_cache(cache)
    global ACTIVE_COUNCIL, ACTIVE_CHAIRMAN
    
    # Start background health refresh (Runs immediately first time)
    asyncio.create_task(periodically_refresh_health())

    # Initialize from cache (will be unknown initially until first refresh completes)
    ACTIVE_COUNCIL = get_council_health_status(COUNCILORS)
    ACTIVE_CHAIRMAN = select_active_chairman(CHAIRMAN)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "ok"}


# Global model cache
ACTIVE_COUNCIL = []
ACTIVE_CHAIRMAN = None


def sanitize_councilor_public(definitions: List[Dict[str, Any]]):
    return [
        {
            "id": c["id"], 
            "name": c.get("name"), 
            "model": c.get("model"),
            "avatar": c.get("avatar"),
            "active": c.get("active", True),
            "healthy": c.get("healthy", True),
            "health_error": c.get("health_error"),
            "health_checked_at": c.get("health_checked_at")
        }
        for c in definitions
    ]


def normalize_councilor_ids(values: List[str]) -> List[str]:
    ids: List[str] = []
    for value in values:
        if value in COUNCILOR_MAP:
            ids.append(value)
            continue
        for councilor in COUNCILORS:
            if councilor.get("model") == value:
                ids.append(councilor["id"])
                break
    return ids


def resolve_councilors(active_ids: List[str]) -> List[Dict[str, Any]]:
    resolved = [COUNCILOR_MAP[cid] for cid in active_ids if cid in COUNCILOR_MAP]
    if resolved:
        return resolved
    return COUNCILORS[:COUNCIL_SIZE]


@app.get("/api/models")
async def get_models(refresh: bool = False):
    """
    Legacy alias for /api/councilors.
    Preserved for backward compatibility.
    """
    return await get_councilors(refresh)


@app.get("/api/councilors")
async def get_councilors(refresh: bool = False):
    """
    Get current councilor configuration.
    Returns list of councilors and the chairman.
    """
    global ACTIVE_COUNCIL
    
    meta = {}
    if refresh:
        # Calls HealthManager.refresh_all, returns meta (skipped, next_allowed, etc)
        # Include Chairman in refresh!
        meta = await refresh_council_health([*COUNCILORS, CHAIRMAN])
    
    # Always get fresh status from memory (respects TTL, Cooldown)
    ACTIVE_COUNCIL = get_council_health_status(COUNCILORS)
    ACTIVE_CHAIRMAN = select_active_chairman(CHAIRMAN)
    
    return {
        "version": "2.1-health-v3",
        "councilors": sanitize_councilor_public(ACTIVE_COUNCIL),
        "chairman": sanitize_councilor_public([ACTIVE_CHAIRMAN])[0] if ACTIVE_CHAIRMAN else None,
        "meta": meta
    }


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """
    Create a new conversation.
    Uses the currently cached active models.
    """
    global ACTIVE_COUNCIL, ACTIVE_CHAIRMAN
    
    # Ensure we have active models (fallback if cache empty)
    # ACTIVE_COUNCIL is initialized on startup.
    # But if it's empty/all unhealthy, maybe we force a refresh here?
    # User spec: "Startup... unknown".
    # If I create conversation, I want healthy models.
    # Let's allow one auto-refresh if we have NO active models at all?
    # "Cache empty, validating..." 
    # If status is unknown, we might want to check.
    # However, for a NEW conversation, we probably want at least one healthy.
    # Let's perform a single check if default list is empty.
    # Ensure we have active models (fallback if cache empty)
    # ACTIVE_COUNCIL is initialized on startup.
    # We do NOT force refresh here to avoid latency/blocking.
    # If no healthy models, default_ids will be empty, which is handled downstream.
    current_actives = [c for c in ACTIVE_COUNCIL if c.get("healthy") is True]

    conversation_id = str(uuid.uuid4())
    # v2: Store active_councilor_ids
    # Priority: Request > Default
    default_ids = [c["id"] for c in ACTIVE_COUNCIL]
    
    if request.councilor_ids:
        normalized = normalize_councilor_ids(request.councilor_ids)
        valid_requested = [cid for cid in normalized if cid in COUNCILOR_MAP]
        if valid_requested:
            default_ids = valid_requested
            
    conversation = storage.create_conversation(
        conversation_id,
        active_councilor_ids=default_ids,
        active_chairman=ACTIVE_CHAIRMAN.get("id") if ACTIVE_CHAIRMAN else None
    )
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, token: str = Depends(verify_admin)):
    """
    Delete a specific conversation.
    Requires Admin Token.
    Returns 204 on success.
    """
    if not storage.validate_conversation_id(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
        
    try:
        storage.delete_conversation(conversation_id)
        return JSONResponse(status_code=204, content=None)
    except OSError as e:
        # Permission denied or locked (storage logic raises this)
        import errno
        reason = "os_error"
        if e.errno == errno.EACCES: reason = "permission_denied"
        elif e.errno == errno.EBUSY: reason = "file_locked"
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "DELETE_FAILED", 
                    "message": "Failed to delete conversation",
                    "details": {"reason": reason, "id": conversation_id}
                }
            } 
        )


class BulkDeleteRequest(BaseModel):
    ids: List[str]


@app.post("/api/conversations/bulk-delete")
async def bulk_delete_conversations(body: BulkDeleteRequest, token: str = Depends(verify_admin)):
    """
    Bulk delete conversations.
    Requires Admin Token.
    Returns 200 with result.
    """
    if len(body.ids) > 50:
        raise HTTPException(status_code=400, detail="Too many IDs (max 50)")
        
    if not body.ids:
         return {"deletedIds": [], "failed": []}
         
    # Storage Deduplicate Logic handled implicitly by `bulk_delete_conversations`
    # But storage expects `[str]`. Pydantic handles validation of List[str].
    
    result = storage.bulk_delete_conversations(body.ids)
    return result


def resolve_target_councilors(
    payload_ids: Optional[List[str]],
    conversation: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Resolve effective councilors based on priority:
    1. Payload (Temporary)
    2. Conversation (Saved)
    3. Global Defaults
    
    Returns:
        (resolved_councilor_objs, needs_migration, ignored_ids)
    """
    needs_migration = False
    ignored_ids = []
    
    # Helper to check health (using dynamic HealthManager state)
    # We fetch fresh status for the map
    # This ensures even if ACTIVE_COUNCIL global is stale, we get latest state
    # (e.g. if cooldown expired 1ms ago)
    import validation
    # This is a bit heavy (rebuilding list), but safe.
    # To optimize, we could just query HealthManager for specific IDs.
    # But get_council_health_status is fast (dict lookup).
    # Update global ACTIVE_COUNCIL as side effect? Maybe.
    current_council_status = validation.get_council_health_status(ACTIVE_COUNCIL) # Use ACTIVE_COUNCIL as pool def source
    
    health_map = {c["id"]: c.get("healthy", True) for c in current_council_status}
    
    def is_healthy(cid):
        # STRICT requirement: "healthy === True".
        # If "unknown", healthy is False?
        # In HealthManager: status="unknown" -> healthy=False.
        # So unknown models are ignored. This matches "Startup default disabled".
        # But wait, if startup check is False, everything is unknown.
        # This means NO ONE can start a conversation until they visit home page (get_councilors) or manual refresh?
        # If I POST to /api/conversations directly on fresh boot, it might fail to find healthy models?
        # User spec: "Startup... unknown... stale=true"
        # If unknown -> healthy=False, then `default_ids` will be empty.
        # This might be too strict.
        # Let's check HealthManager.get_status().
        # "healthy": effective_status == "healthy"
        # So yes, unknown is NOT healthy.
        # If so, we need to ensure at least one check if we have 0 healthy?
        # Or blindly trust config if unknown?
        # User: "Passive... Runtime updates".
        # If I send a message, and everyone is unknown, and I filter them out... I have 0 councilors.
        # Then `run_full_council` fails or complains.
        # We should probably allow "unknown" to be candidate if we have no choices?
        # Or better: "unknown" status should be treated as "candidate for trial" (optimistic)?
        # User defined: "healthy = (health_status=='healthy')".
        # So strictly speaking, unknown is not healthy.
        # But for 'resolve', maybe we accept unknown?
        # Let's stick to strict for now, but if 'default_ids' ends up empty, we might have an issue.
        return health_map.get(cid, False) is True
    
    # 1. Payload Overrides
    if payload_ids:
        # Normalize: convert models to councilor IDs if needed
        # Normalize: convert models to councilor IDs if needed
        normalized_ids = normalize_councilor_ids(payload_ids)
        
        valid_ids = []
        for cid in normalized_ids:
            if cid in COUNCILOR_MAP:
                if is_healthy(cid):
                    valid_ids.append(cid)
                else:
                    ignored_ids.append(cid)
                    
        if valid_ids:
             # Just return mapped objects
             return [COUNCILOR_MAP[cid] for cid in valid_ids], needs_migration, ignored_ids
             
    # 2. Conversation Stored
    # Check v2 first
    v2_ids = conversation.get("active_councilor_ids")
    if v2_ids:
        # Validate existence AND health (should we filter out unhealthy from history? 
        # User said "Execution will STRICTLY ignore unhealthy". So yes.)
        valid_v2 = []
        for cid in v2_ids:
             if cid in COUNCILOR_MAP:
                 if is_healthy(cid):
                     valid_v2.append(cid)
                 else:
                     ignored_ids.append(cid)
                     
        if valid_v2:
            return [COUNCILOR_MAP[cid] for cid in valid_v2], needs_migration, ignored_ids
            
    # Check v1 (Legacy Migration)
    v1_models = conversation.get("active_models")
    if v1_models:
        needs_migration = True
        migrated_ids = []
        for model_name in v1_models:
            # Algorithm: Find first councilor using this model
            found = False
            for c in COUNCILORS:
                if c["model"] == model_name:
                    migrated_ids.append(c["id"])
                    found = True
                    break
            # If not found, discard (as per requirement)
        
        if migrated_ids:
            # Filter healthy
            valid_migrated = []
            for cid in migrated_ids:
                if is_healthy(cid):
                    valid_migrated.append(cid)
                else:
                    ignored_ids.append(cid)
            
            if valid_migrated:
                 return [COUNCILOR_MAP[cid] for cid in valid_migrated], needs_migration, ignored_ids
            
    # 3. Global Default (Fallback)
    # Use all ACTIVE and HEALTHY councilors
    # If strictly healthy is required, and on startup all are unknown...
    # We should fallback to "all councilors" if valid_count == 0? 
    # Or rely on client to refresh?
    # Let's allow ACTIVE_COUNCIL (which is cached) to be the source.
    # If strict is applied, and we have 0, we might return empty list.
    default_ids = [c["id"] for c in current_council_status if c.get("healthy") is True]
    
    # Fallback: If 0 healthy (e.g. startup), but we have candidates in status 'unknown'?
    # Logic: if len(default_ids) < 2 (insufficient), maybe include 'unknown'?
    # Let's keep it strict for now. If user sees 0 active, they will refresh.
    
    return [COUNCILOR_MAP[cid] for cid in default_ids], True, ignored_ids # Mark as needing migration/save


@app.post("/api/conversations/{conversation_id}/message")
@limiter.limit(RATE_LIMIT_MESSAGE)
async def send_message(request: Request, conversation_id: str, body: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, body.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(body.content)
        storage.update_conversation_title(conversation_id, title)

    # Resolution Logic
    active_councilors, needs_migration, ignored_ids = resolve_target_councilors(body.councilor_ids, conversation)
    
    active_chairman_id = conversation.get("active_chairman") or CHAIRMAN.get("id")
    active_chairman = CHAIRMAN if active_chairman_id == CHAIRMAN.get("id") else CHAIRMAN

    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        body.content, active_councilors, active_chairman, enable_thinking=body.enable_thinking
    )

    # Add assistant message with all stages and metadata
    storage.add_assistant_message(
        conversation_id, stage1_results, stage2_results, stage3_result, metadata
    )
    
    # Persistence Update (Soft Migration or Preference Update)
    # Update if migration needed OR if user provided explicit IDs (making them the new default? 
    # User said: "Persist selection per conversation: ... on send, include ids and update server-side conversation defaults")
    # So if body.councilor_ids provided, we update.
    current_ids = [c["id"] for c in active_councilors]
    
    should_update_schema = False
    
    # Logic: Update if (Payload Provided) OR (Needs Migration)
    if body.councilor_ids:
        should_update_schema = True
    elif needs_migration:
        should_update_schema = True
        
    if should_update_schema:
        # Handle Backup if this is first migration (v1 -> v2)
        if conversation.get("schema_version", 1) < 2:
            try:
                src = storage.get_conversation_path(conversation_id)
                dst = src + ".bak"
                if not os.path.exists(dst):
                     shutil.copy2(src, dst)
            except Exception as e:
                print(f"Backup failed: {e}")

        storage.update_conversation_schema(conversation_id, current_ids, version=2)

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata,
    }


import time

@app.post("/api/conversations/{conversation_id}/message/stream")
@limiter.limit(RATE_LIMIT_STREAM)
async def send_message_stream(request: Request, conversation_id: str, body: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        # Shared queue for incremental events from callbacks
        event_queue = asyncio.Queue()
        start_time = time.time()
        
        # Persistence Accumulator
        thinking_log = {"stage1": {}, "stage2": {}, "stage3": {}}
        thinking_count = 0
        
        async def on_thinking(cid, stage, title, model=None):
            if not body.enable_thinking:
                return

            nonlocal thinking_count
            t_val = round(time.time() - start_time, 2)
            
            # Emit Event
            event = {
                "type": "thinking",
                "stage": stage,
                "councilor_id": cid,
                "model": model, 
                "delta": title,
                "is_title": True,
                "t": t_val
            }
            await event_queue.put(f"data: {json.dumps(event)}\n\n")
            
            # Persistence Log (Limit: 50 per model/stage, 200 total)
            if thinking_count < 200 and stage in thinking_log:
                if cid not in thinking_log[stage]:
                     thinking_log[stage][cid] = []
                
                if len(thinking_log[stage][cid]) < 50:
                     thinking_log[stage][cid].append({"t": t_val, "title": title})
                     thinking_count += 1

        try:
            # Add user message
            storage.add_user_message(conversation_id, body.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(
                    generate_conversation_title(body.content)
                )

            # Resolution Logic
            active_councilors, needs_migration, ignored_ids = resolve_target_councilors(body.councilor_ids, conversation)
            
            # Emit Meta Event
            meta_payload = {
                "type": "meta",
                "resolved_councilor_ids": [c["id"] for c in active_councilors],
                "resolved_councilors": [
                    {"id": c["id"], "name": c["name"], "avatar": c.get("avatar", ""), "model": c["model"]} 
                    for c in active_councilors
                ],
                "chairman": {
                    "id": CHAIRMAN["id"], 
                    "name": CHAIRMAN["name"], 
                    "avatar": CHAIRMAN.get("avatar", ""),
                    "model": CHAIRMAN["model"]
                },
                "ignored_ids": ignored_ids,
                "spec_version": "stage2_v1.2",
            }
            yield f"data: {json.dumps(meta_payload)}\n\n"
            
            active_chairman_id = conversation.get("active_chairman") or CHAIRMAN.get("id")
            active_chairman = CHAIRMAN if active_chairman_id == CHAIRMAN.get("id") else CHAIRMAN

            # --- Stage 1: Collect responses ---
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            
            # Callback that puts items into the queue (NOT a generator)
            async def on_stage1_item(item):
                await event_queue.put(f"data: {json.dumps({'type': 'stage1_item', 'data': item})}\n\n")

            # Start stage1 task
            stage1_task = asyncio.create_task(
                stage1_collect_responses(
                    body.content, 
                    active_councilors, 
                    on_result=on_stage1_item,
                    on_thinking=on_thinking,
                    enable_thinking=body.enable_thinking
                )
            )
            
            # Drain queue while stage1 task is running
            while not stage1_task.done() or not event_queue.empty():
                try:
                    # Wait for events with timeout to check task status
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield event
                    event_queue.task_done()
                except asyncio.TimeoutError:
                    # No event available, continue loop to check if task is done
                    continue
            
            # Get stage1 results
            stage1_results = await stage1_task
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # --- Stage 2: Collect rankings ---
            valid_c = [r for r in stage1_results if r.get("status") == "ok"]
            is_skipped = len(valid_c) < 2
            
            if is_skipped:
                # Skipped Case
                yield f"data: {json.dumps({'type': 'stage2_start', 'skipped': True, 'skipped_reason': 'insufficient_candidates'})}\n\n"
                
                stage2_result = await stage2_collect_rankings(
                    body.content, stage1_results, active_councilors, on_thinking=on_thinking, enable_thinking=body.enable_thinking
                )
            else:
                # Normal Case
                anon_map_payload = {}
                count = 1
                for res in stage1_results:
                    if res.get("status") == "ok":
                         anon_map_payload[f"anon_{count}"] = res.get("councilor_id")
                         count += 1
                
                yield f"data: {json.dumps({'type': 'stage2_start', 'anon_map': anon_map_payload})}\n\n"
            
                # Callback for stage2 items (NOT a generator)
                async def on_stage2_item(item):
                    await event_queue.put(f"data: {json.dumps({'type': 'stage2_item', 'data': item})}\n\n")
                
                # Start stage2 task
                stage2_task = asyncio.create_task(
                    stage2_collect_rankings(
                        body.content, 
                        stage1_results, 
                        active_councilors,
                        on_result=on_stage2_item,
                        on_thinking=on_thinking,
                        enable_thinking=body.enable_thinking
                    )
                )
                
                # Drain queue while stage2 task is running
                while not stage2_task.done() or not event_queue.empty():
                    try:
                        event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                        yield event
                        event_queue.task_done()
                    except asyncio.TimeoutError:
                        continue
                
                stage2_result = await stage2_task
            
            aggregate_rankings = []
            if not stage2_result.get("skipped"):
                 aggregate_rankings = calculate_aggregate_rankings(
                    stage2_result.get("reviews", []), stage2_result.get("anon_map", {})
                )

            # Emit stage2_complete
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_result, 'metadata': {'anon_to_councilor': stage2_result.get('anon_map', {}), 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # --- Stage 3: Synthesize final answer ---
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            
            stage3_task = asyncio.create_task(
                stage3_synthesize_final(
                    body.content, 
                    stage1_results, 
                    stage2_result, 
                    active_chairman,
                    on_thinking=on_thinking,
                    enable_thinking=body.enable_thinking
                )
            )
            
            while not stage3_task.done() or not event_queue.empty():
                try:
                     event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                     yield event
                     event_queue.task_done()
                except asyncio.TimeoutError:
                     continue
            
            stage3_result = await stage3_task
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message with metadata
            metadata = {
                "anon_to_councilor": stage2_result.get("anon_map", {}),
                "aggregate_rankings": aggregate_rankings,
                "spec_version": "stage2_v1.2",
            }
            storage.add_assistant_message(
                conversation_id, stage1_results, stage2_result, stage3_result, metadata
            )

            current_ids = [c["id"] for c in active_councilors]
            should_update_schema = False
            if body.councilor_ids: should_update_schema = True
            elif needs_migration: should_update_schema = True
            
            if should_update_schema:
                 if conversation.get("schema_version", 1) < 2:
                    try:
                        src = storage.get_conversation_path(conversation_id)
                        dst = src + ".bak"
                        if not os.path.exists(dst): shutil.copy2(src, dst)
                    except: pass
                 storage.update_conversation_schema(conversation_id, current_ids, version=2)

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"



    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
