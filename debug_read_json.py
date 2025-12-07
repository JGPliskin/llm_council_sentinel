import json
import os

filepath = r"f:\OneDrive\PY\ZYZ\project\llm_council_sentinel\backend\data\conversations\4ac11bb6-da92-4b9b-99c7-96506e5a4aa0.json"

try:
    with open(filepath, 'r') as f:
        data = json.load(f)
        with open("debug_json_output.txt", "w") as out:
            out.write(f"Active Models: {data.get('active_models')}\n")
            out.write(f"Active Chairman: {data.get('active_chairman')}\n")
except Exception as e:
    with open("debug_json_output.txt", "w") as out:
        out.write(f"Error: {e}\n")
