import os
from transcriber.config import load_config


def test_add_random_personal_message_default_true(monkeypatch):
    # Ensure var not set -> defaults to True
    monkeypatch.delenv("ADD_RANDOM_PERSONAL_MESSAGE", raising=False)
    cfg = load_config()
    assert cfg.add_random_personal_message is True


def test_add_random_personal_message_false_variants(monkeypatch):
    for val in ["0", "false", "no", "off", "FALSE"]:
        monkeypatch.setenv("ADD_RANDOM_PERSONAL_MESSAGE", val)
        cfg = load_config()
        assert cfg.add_random_personal_message is False
    # A truthy override
    monkeypatch.setenv("ADD_RANDOM_PERSONAL_MESSAGE", "yes")
    cfg = load_config()
    assert cfg.add_random_personal_message is True

