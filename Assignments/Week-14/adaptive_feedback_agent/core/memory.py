import json
from pathlib import Path

MEMORY_FILE = Path("data/feedback_history.json")

def load_memory():
    if MEMORY_FILE.exists():
        try:
            data = json.loads(MEMORY_FILE.read_text())
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
    return []

def save_memory(memory):
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))
