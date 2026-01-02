import urllib.request
import urllib.error

PORTS = [8000, 8010, 8011, 8080]

def probe():
    for port in PORTS:
        url = f"http://localhost:{port}/health"
        print(f"Probing {url}...")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                print(f"  [SUCCESS] Port {port} is OPEN. Status: {response.status}")
                return port
        except urllib.error.URLError as e:
            print(f"  [FAILED] Port {port}: {e}")
        except Exception as e:
            print(f"  [ERROR] Port {port}: {e}")
    return None

if __name__ == "__main__":
    found = probe()
    if found:
        print(f"\nBackend found on port {found}")
    else:
        print("\nBackend NOT FOUND on common ports.")
