import os
from pathlib import Path
from dotenv import dotenv_values

ROOT_PATH = Path(__file__).resolve().parents[2]

def load_config() -> dict[str, str]:
    shared = dotenv_values(ROOT_PATH / ".env.shared")
    local = dotenv_values(ROOT_PATH / ".env")
    return {**shared, **local, **os.environ}
    