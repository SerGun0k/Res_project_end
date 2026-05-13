from datetime import datetime, timedelta

from data_pipeline.import_open_prices import _is_url_allowed, _parse_date


def test_is_url_allowed_with_empty_allowlist():
    assert _is_url_allowed("https://any-domain.example/prices.csv", []) is True


def test_is_url_allowed_with_exact_and_subdomain():
    allowed = ["example.com"]
    assert _is_url_allowed("https://example.com/a.csv", allowed) is True
    assert _is_url_allowed("https://data.example.com/a.csv", allowed) is True
    assert _is_url_allowed("https://evil.com/a.csv", allowed) is False


def test_parse_date_with_valid_iso():
    parsed = _parse_date("2026-05-13T12:00:00")
    assert parsed.year == 2026
    assert parsed.month == 5
    assert parsed.day == 13


def test_parse_date_with_invalid_value_returns_recent_time():
    before = datetime.utcnow() - timedelta(seconds=2)
    parsed = _parse_date("not-a-date")
    after = datetime.utcnow() + timedelta(seconds=2)
    assert before <= parsed <= after
