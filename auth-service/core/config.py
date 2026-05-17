import os
from pathlib import Path
from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_config() -> dict[str, str]:
    shared = dotenv_values(REPO_ROOT / ".env.shared")
    local = dotenv_values(REPO_ROOT / ".env")
    return {**shared, **local, **os.environ}