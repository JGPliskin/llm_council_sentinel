
import sys
import os
sys.path.append("backend")

# Need to mock httpx before importing council
from unittest.mock import MagicMock
sys.modules["httpx"] = MagicMock()

import council

def check(name, resp, expected):
    res = council.is_retryable_error(resp)
    print(f"{name}: Expected {expected}, Got {res} -> {'PASS' if res == expected else 'FAIL'}")

print("Testing is_retryable_error...")

# 401 Fatal
check("401", {"error": True, "status_code": 401, "content": "Unauth"}, False)

# 429 Retry
check("429", {"error": True, "status_code": 429, "content": "Rate Limit"}, True)

# None
check("None", None, True)

# Missing status code
check("Missing Status", {"error": True, "content": "Unknown"}, True)

# Success dict (not error) - function shouldn't strictly be called on success but if so?
# The function logic: if not response_dict -> True. if response_dict.get('error') -> check. 
# If success (no 'error'), it returns False (defaults to False at end of function).
check("Success", {"content": "ok", "status_code": 200}, False)

print("\nTesting get_retry_after...")
h1 = {"headers": {"retry-after": "10.5"}}
print(f"Lower header: {council.get_retry_after(h1)}")

h2 = {"headers": {"Retry-After": "20"}}
print(f"Cap header: {council.get_retry_after(h2)}")
