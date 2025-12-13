"""JSON-based storage for conversations."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR


def ensure_data_dir():
    """Ensure the data directory exists."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def get_conversation_path(conversation_id: str) -> str:
    """Get the file path for a conversation."""
    return os.path.join(DATA_DIR, f"{conversation_id}.json")


def create_conversation(
    conversation_id: str, 
    active_models: Optional[List[str]] = None,
    active_councilor_ids: Optional[List[str]] = None,
    active_chairman: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation
        active_models: Legacy (optional)
        active_councilor_ids: List of active councilor IDs (v2)
        active_chairman: Active chairman model for this conversation

    Returns:
        New conversation dict
    """
    ensure_data_dir()

    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": [],
        "active_models": active_models,
        "active_councilor_ids": active_councilor_ids,
        "active_chairman": active_chairman,
        "schema_version": 2
    }

    # Save to file
    path = get_conversation_path(conversation_id)
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    path = get_conversation_path(conversation_id)

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        return json.load(f)


def save_conversation(conversation: Dict[str, Any]):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
    """
    ensure_data_dir()

    path = get_conversation_path(conversation['id'])
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)


def list_conversations() -> List[Dict[str, Any]]:
    """
    List all conversations (metadata only).

    Returns:
        List of conversation metadata dicts
    """
    ensure_data_dir()

    conversations = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            with open(path, 'r') as f:
                data = json.load(f)
                # Return metadata only
                conversations.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "title": data.get("title", "New Conversation"),
                    "message_count": len(data["messages"])
                })

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


def add_user_message(conversation_id: str, content: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "user",
        "content": content
    })

    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: Dict[str, Any],
    stage3: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
        metadata: Optional metadata including anon_to_councilor and aggregate_rankings
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    message = {
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    }

    # Add metadata if provided
    if metadata is not None:
        message["metadata"] = metadata

    conversation["messages"].append(message)

    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title
    save_conversation(conversation)


def update_conversation_schema(conversation_id: str, active_councilor_ids: List[str], version: int = 2):
    """
    Update conversation text with new schema/active IDs.
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        return
        
    conversation["active_councilor_ids"] = active_councilor_ids
    conversation["schema_version"] = version
    save_conversation(conversation)



def validate_conversation_id(conversation_id: str) -> bool:
    """
    Validate conversation ID format to prevent path traversal/injection.
    Allowlist: alphanumeric, underscore, hyphen. Length: 1-64.
    """
    if not conversation_id or not isinstance(conversation_id, str):
        return False
    # Use config.DATA_DIR safe joining logic implicitly by ensuring ID is safe
    import re
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', conversation_id):
        return False
    return True


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation by ID.
    Idempotent: Returns True if file is deleted or already gone.
    Returns False only if validation fails.
    Raises OSError if deletion fails for other reasons (permission, lock).
    """
    if not validate_conversation_id(conversation_id):
        # We generally return False or raise ValueError. 
        # Given the plan says "Validate ID format", let's raise ValueError to be specific,
        # but the plan also says "Return 204 always (unless 400)".
        # For this internal function, let's return False for invalid ID so caller handles it.
        return False

    path = get_conversation_path(conversation_id)
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return True
    except OSError as e:
        # Permission denied or locked
        raise e


def bulk_delete_conversations(conversation_ids: List[str]) -> Dict[str, Any]:
    """
    Bulk delete conversations.
    Returns:
        {
            "deletedIds": [...],
            "failed": [{ "id": "...", "reason": "..." }]
        }
    """
    # Dedupe and validate string type
    unique_ids = list(set([str(i) for i in conversation_ids if i and isinstance(i, str)]))
    
    result = {
        "deletedIds": [],
        "failed": []
    }
    
    for cid in unique_ids:
        if not validate_conversation_id(cid):
            result["failed"].append({"id": cid, "reason": "invalid_id"})
            continue
            
        try:
            delete_conversation(cid)
            result["deletedIds"].append(cid)
        except OSError as e:
            # Check strictly for permission/lock issues
            # We treat FileNotFoundError as success (in delete_conversation), so it won't raise here.
            import errno
            reason = "os_error"
            if e.errno == errno.EACCES: # Permission denied
                reason = "permission_denied"
            elif e.errno == errno.EBUSY: # Resource busy
                reason = "file_locked"
            
            result["failed"].append({"id": cid, "reason": reason})
        except Exception as e:
            result["failed"].append({"id": cid, "reason": "unknown_error"})
            
    return result


def update_conversation_schema(conversation_id: str, active_councilor_ids: List[str], version: int = 2):
    """
    Update conversation text with new schema/active IDs.
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        return
        
    conversation["active_councilor_ids"] = active_councilor_ids
    conversation["schema_version"] = version
    save_conversation(conversation)
