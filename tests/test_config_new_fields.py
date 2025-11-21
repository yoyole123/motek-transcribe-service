import os
from transcriber.config import load_config

def test_max_segment_retries_default(monkeypatch):
    monkeypatch.delenv("MAX_SEGMENT_RETRIES", raising=False)
    cfg = load_config()
    assert cfg.max_segment_retries == 2

def test_max_segment_retries_override(monkeypatch):
    monkeypatch.setenv("MAX_SEGMENT_RETRIES", "5")
    cfg = load_config()
    assert cfg.max_segment_retries == 5


def test_balance_alert_value_default(monkeypatch):
    monkeypatch.delenv("BALANCE_ALERT_VALUE", raising=False)
    cfg = load_config()
    assert abs(cfg.balance_alert_value - 2.0) < 1e-9


def test_balance_alert_value_override(monkeypatch):
    monkeypatch.setenv("BALANCE_ALERT_VALUE", "3.5")
    cfg = load_config()
    assert abs(cfg.balance_alert_value - 3.5) < 1e-9

