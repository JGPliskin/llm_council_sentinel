
import sys
import os
import traceback
import asyncio

LOG_FILE = "debug_log.txt"

def log(msg):
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(str(msg) + "\n")

# Clear log file
with open(LOG_FILE, "w", encoding='utf-8') as f:
    f.write("Starting debug script...\n")

try:
    from dotenv import load_dotenv
    log("dotenv imported")
    load_dotenv()
except ImportError as e:
    log(f"Failed to import dotenv: {e}")

# Ensure we can import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
log(f"Python path: {sys.path}")

try:
    from backend.openrouter import query_model
    from backend.config import COUNCIL_MODELS, CHAIRMAN_MODEL
    log("Backend modules imported")
except ImportError as e:
    log(f"Failed to import backend modules: {e}")
    log(traceback.format_exc())
    sys.exit(1)

async def test_model(model_name):
    log(f"Testing model: {model_name}...")
    messages = [{"role": "user", "content": "Hi"}]
    try:
        response = await query_model(model_name, messages, timeout=20.0)
        if response:
            log(f"SUCCESS: {model_name}")
            return True
        else:
            log(f"FAILED (None response): {model_name}")
            return False
    except Exception as e:
        log(f"ERROR: {model_name} - {e}")
        return False

async def main():
    log("Starting Model Availability Check...")
    log("-" * 40)
    
    all_passed = True
    
    log("Checking Council Models:")
    for model in COUNCIL_MODELS:
        if not await test_model(model):
            all_passed = False
            
    log("\nChecking Chairman Model:")
    if not await test_model(CHAIRMAN_MODEL):
        all_passed = False
        
    log("-" * 40)
    if all_passed:
        log("All models are responding correctly.")
    else:
        log("Some models failed to respond.")

if __name__ == "__main__":
    try:
        if 'win32' in sys.platform:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except Exception as e:
        log(f"Fatal error: {e}")
        log(traceback.format_exc())
