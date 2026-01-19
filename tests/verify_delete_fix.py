import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8010"

def test_delete_flow():
    # 1. Create a conversation
    print("Creating conversation...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/conversations", 
            data=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            conv_id = data['id']
            print(f"Created conversation: {conv_id}")
    except Exception as e:
        print(f"Failed to create conversation: {e}")
        return False

    # 2. Delete the conversation
    print(f"Deleting conversation {conv_id}...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/conversations/{conv_id}", 
            headers={"X-Admin-Token": "secret"},
            method="DELETE"
        )
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("Delete successful (204 No Content).")
                # Verify body is empty
                content = response.read()
                if content:
                    print(f"WARNING: Response content is not empty: {content}")
                    return False
                return True
            else:
                print(f"Delete failed with status {response.status}")
                return False
            
    except urllib.error.HTTPError as e:
        print(f"HTTPError during delete: {e.code} {e.reason}")
        print(e.read())
        return False
    except Exception as e:
        print(f"Exception during delete: {e}")
        return False

if __name__ == "__main__":
    time.sleep(2)
    success = test_delete_flow()
    if success:
        print("VERIFICATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED")
        sys.exit(1)
