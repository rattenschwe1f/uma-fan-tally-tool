import os

import httpx
import pytest

from uma_tally_tool import client
from uma_tally_tool.client import CircleNotFound, FetchError, fetch_circle


@pytest.mark.network
def test_fetch_circle_returns_well_formed_response():
    circle_id = os.environ.get("UMA_TEST_CIRCLE_ID")
    api_key = os.environ.get("UMA_API_KEY")
    if not circle_id or not api_key:
        pytest.skip("Set UMA_TEST_CIRCLE_ID and UMA_API_KEY to run the live uma.moe smoke test")
    resp = fetch_circle(int(circle_id), api_key=api_key)
    assert len(resp.members) > 0
    assert all(len(m.daily_fans) == 32 for m in resp.members)


def test_fetch_circle_raises_circle_not_found_on_404(monkeypatch):
    class FakeResp:
        status_code = 404
        is_success = False

    monkeypatch.setattr(client.httpx, "get", lambda *a, **kw: FakeResp())
    with pytest.raises(CircleNotFound):
        fetch_circle(1234, api_key="secret-key")


def test_fetch_circle_raises_fetch_error_on_network_failure(monkeypatch):
    def boom(*a, **kw):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(client.httpx, "get", boom)
    with pytest.raises(FetchError):
        fetch_circle(1234, api_key="secret-key", sleep=lambda _s: None)


def test_fetch_circle_raises_fetch_error_on_5xx(monkeypatch):
    class FakeResp:
        status_code = 503
        is_success = False

    monkeypatch.setattr(client.httpx, "get", lambda *a, **kw: FakeResp())
    with pytest.raises(FetchError):
        fetch_circle(1234, api_key="secret-key", sleep=lambda _s: None)


def test_fetch_circle_retries_after_transient_5xx(monkeypatch):
    class GoodResp:
        status_code = 200
        is_success = True

        @staticmethod
        def json():
            return {
                "circle": {"circle_id": 1, "name": "X", "member_count": 0},
                "members": [],
            }

    class BadResp:
        status_code = 503
        is_success = False

    calls = {"n": 0}

    def flaky(*a, **kw):
        calls["n"] += 1
        return BadResp() if calls["n"] == 1 else GoodResp()

    monkeypatch.setattr(client.httpx, "get", flaky)
    resp = fetch_circle(1234, api_key="secret-key", sleep=lambda _s: None)
    assert resp.circle.name == "X"
    assert calls["n"] == 2


def test_fetch_circle_sends_api_key_header(monkeypatch):
    class GoodResp:
        status_code = 200
        is_success = True

        @staticmethod
        def json():
            return {
                "circle": {"circle_id": 1, "name": "X", "member_count": 0},
                "members": [],
            }

    seen = {}

    def fake_get(*_args, **kwargs):
        seen.update(kwargs)
        return GoodResp()

    monkeypatch.setattr(client.httpx, "get", fake_get)
    fetch_circle(1234, api_key="secret-key")
    assert seen["headers"] == {"X-API-Key": "secret-key"}


def test_fetch_circle_requires_api_key():
    with pytest.raises(ValueError, match="API key is required"):
        fetch_circle(1234, api_key="")


def test_fetch_circle_does_not_retry_on_4xx_other_than_404(monkeypatch):
    class FakeResp:
        status_code = 400
        is_success = False

    calls = {"n": 0}

    def fake_get(*a, **kw):
        calls["n"] += 1
        return FakeResp()

    monkeypatch.setattr(client.httpx, "get", fake_get)
    with pytest.raises(FetchError):
        fetch_circle(1234, api_key="secret-key", sleep=lambda _s: None)
    assert calls["n"] == 1
