import pytest
from core.config import load_config

class TestConfig:
    def test_config_return_type(self):
        config = load_config()
        assert isinstance(config, dict)