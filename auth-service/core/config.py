import os

from dotenv import dotenv_values


def load_config() -> dict[str, str]:
    shared = dotenv_values("../.env.shared")
    local = dotenv_values("../.env")
    return {**shared, **local, **os.environ}