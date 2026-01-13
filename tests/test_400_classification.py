
import sys
import os
import pytest
from typing import Dict, Any

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.council import classify_400_error
from backend.config import REQUEST_ERROR_CODES, REQUEST_ERROR_KEYWORDS, MODEL_ERROR_KEYWORDS

def test_classify_400_not_400():
    """非 400 错误应返回 other"""
    response = {"status_code": 500, "content": "Internal Server Error"}
    result = classify_400_error(response)
    assert result == ("other", True, True)

def test_classify_400_context_length_code():
    """Context Length Exceeded by Code -> request_error (no retry)"""
    response = {
        "status_code": 400, 
        "error_payload": {
            "error": {"code": "context_length_exceeded", "message": "Too long"}
        }
    }
    result = classify_400_error(response)
    assert result == ("request_error", False, False)

def test_classify_400_invalid_request_keyword():
    """Invalid Request by Keyword -> request_error (no retry)"""
    response = {
        "status_code": 400,
        "error_payload": {
            "error": {"message": "Invalid JSON format in tool call"}
        }
    }
    result = classify_400_error(response)
    assert result == ("request_error", False, False)

def test_classify_400_model_unavailable():
    """Model Unavailable -> model_error (retry)"""
    response = {
        "status_code": 400,
        "error_payload": {
            "error": {"message": "Model not found or unavailable"}
        }
    }
    result = classify_400_error(response)
    assert result == ("model_error", True, True)

def test_classify_400_provider_error():
    """Provider Error -> model_error (retry)"""
    response = {
        "status_code": 400, 
        "content": "Provider disabled for this model"
    }
    result = classify_400_error(response)
    assert result == ("model_error", True, True)
    
def test_classify_400_unknown():
    """Unknown 400 -> unknown_400 (retry)"""
    response = {
        "status_code": 400,
        "content": "Something weird happened"
    }
    result = classify_400_error(response)
    assert result == ("unknown_400", True, True)

def test_classify_400_no_response():
    """Empty response -> other"""
    result = classify_400_error(None)
    assert result == ("other", True, True)

def test_classify_provider_rate_limited():
    """Provider rate limit should be retryable and not update health."""
    response = {
        "status_code": 429,
        "error_code": "provider_rate_limited",
        "content": "NIM API keys exhausted"
    }
    result = classify_400_error(response)
    assert result == ("provider_rate_limited", True, False)
