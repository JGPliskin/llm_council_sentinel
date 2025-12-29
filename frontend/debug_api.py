import requests
import json

BASE_URL = "http://localhost:8010"

def debug_api():
    print(f"Fetching list from {BASE_URL}/api/conversations...")
    try:
        r = requests.get(f"{BASE_URL}/api/conversations")
        r.raise_for_status()
        convs = r.json()
        print(f"Found {len(convs)} conversations.")
    except Exception as e:
        print(f"List failed: {e}")
        return

    if not convs:
        print("No conversations to inspect.")
        return

    # Pick the most recent one (usually first or check created_at?)
    # Assuming list is sorted desc or we pick index 0
    target_id = convs[0]['id']
    print(f"Inspecting Conversation ID: {target_id}")

    try:
        r = requests.get(f"{BASE_URL}/api/conversations/{target_id}")
        r.raise_for_status()
        data = r.json()
        
        print("\n=== DATA KEYS ===")
        print(data.keys())
        
        msgs = data.get('messages', [])
        print(f"\nMessage Count: {len(msgs)}")
        
        if msgs:
            last = msgs[-1]
            print("\n=== LAST MESSAGE ===")
            print(f"Role: {last.get('role')}")
            print(f"Has Stage1: {bool(last.get('stage1'))}")
            print(f"Has Stage2: {bool(last.get('stage2'))}")
            print(f"Has Stage3: {bool(last.get('stage3'))}")
        else:
            print("WARNING: Messages array is empty!")
            
    except Exception as e:
        print(f"Detail fetch failed: {e}")

if __name__ == "__main__":
    debug_api()
