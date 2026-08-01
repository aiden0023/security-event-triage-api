import pytest

from app import create_app
from app.config import TestConfig


def test_create_app():
    app = create_app("test")
    assert app.config["TESTING"] is True
    assert app.config["DEFAULT_PAGE_SIZE"] == 25


def test_create_app_rejects_an_unknown_config_name():
    with pytest.raises(RuntimeError, match="Unknown config name"):
        create_app("unknown")


def test_create_app_refuses_start_without_secret_key(monkeypatch):
    monkeypatch.setattr(TestConfig, "SECRET_KEY", None)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("test")
