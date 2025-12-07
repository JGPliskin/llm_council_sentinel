"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
from typing import List, Dict, Any
import uuid
import json
import asyncio

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import storage
from council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
)
from config import COUNCIL_MODEL_POOL, CHAIRMAN_MODEL_POOL, COUNCIL_SIZE
from validation import select_active_council, select_active_chairman
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
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str

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


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "ok"}


# Global model cache
ACTIVE_COUNCIL: List[str] = []
ACTIVE_CHAIRMAN: Optional[str] = None


@app.get("/api/models")
async def get_models(refresh: bool = False):
    """
    Get model configuration.
    
    Args:
        refresh: If True, force re-validation of models.
                 If False, return cached valid models if available.
    """
    global ACTIVE_COUNCIL, ACTIVE_CHAIRMAN
    
    # If refresh requested or cache empty, run validation
    if refresh or not ACTIVE_COUNCIL:
        print("Validating models...", flush=True)
        ACTIVE_COUNCIL = await select_active_council(COUNCIL_MODEL_POOL, COUNCIL_SIZE)
        ACTIVE_CHAIRMAN = await select_active_chairman(CHAIRMAN_MODEL_POOL)
    
    return {
        "council_models": ACTIVE_COUNCIL,
        "chairman_model": ACTIVE_CHAIRMAN
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
    if not ACTIVE_COUNCIL:
        print("Cache empty, validating models for new conversation...", flush=True)
        ACTIVE_COUNCIL = await select_active_council(COUNCIL_MODEL_POOL, COUNCIL_SIZE)
        ACTIVE_CHAIRMAN = await select_active_chairman(CHAIRMAN_MODEL_POOL)
    
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(
        conversation_id, 
        active_models=ACTIVE_COUNCIL, 
        active_chairman=ACTIVE_CHAIRMAN
    )
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


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

    # Retrieve active models from conversation, or fall back to defaults (for old conversations)
    # Important: In a real migration we'd backfill, but here we fallback to current valid ones or pool
    active_models = conversation.get("active_models")
    if not active_models:
        # Fallback for old conversations
        active_models = COUNCIL_MODEL_POOL[:COUNCIL_SIZE]
        
    active_chairman = conversation.get("active_chairman")
    if not active_chairman:
        active_chairman = CHAIRMAN_MODEL_POOL[0]

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        body.content, active_models, active_chairman
    )

    # Add assistant message with all stages and metadata
    storage.add_assistant_message(
        conversation_id, stage1_results, stage2_results, stage3_result, metadata
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata,
    }


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
        try:
            # Add user message
            storage.add_user_message(conversation_id, body.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(
                    generate_conversation_title(body.content)
                )

            # Retrieve active models from conversation, or fall back to defaults
            active_models = conversation.get("active_models")
            if not active_models:
                active_models = COUNCIL_MODEL_POOL[:COUNCIL_SIZE]
                
            active_chairman = conversation.get("active_chairman")
            if not active_chairman:
                active_chairman = CHAIRMAN_MODEL_POOL[0]

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(body.content, active_models)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(
                body.content, stage1_results, active_models
            )
            aggregate_rankings = calculate_aggregate_rankings(
                stage2_results, label_to_model
            )
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(
                body.content, stage1_results, stage2_results, active_chairman
            )
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message with metadata
            metadata = {
                "label_to_model": label_to_model,
                "aggregate_rankings": aggregate_rankings,
            }
            storage.add_assistant_message(
                conversation_id, stage1_results, stage2_results, stage3_result, metadata
            )

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

    uvicorn.run(app, host="0.0.0.0", port=8009)
