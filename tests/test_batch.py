import json
import urllib.error

import pytest

from uma_tally_tool import batch


def test_load_club_specs_uses_single_club_fallback():
    env = {
        "CIRCLE_ID": "123",
        "DISCORD_WEBHOOK": "https://discord.example/webhook",
    }

    assert batch.load_club_specs(env) == [
        {
            "name": "default",
            "circle_id": "123",
            "discord_webhook": "https://discord.example/webhook",
        }
    ]


def test_load_club_specs_accepts_array_and_wrapped_object():
    clubs = [{"name": "A", "circle_id": "1", "discord_webhook": "hook"}]

    assert batch.load_club_specs({"CLUBS_JSON": json.dumps(clubs)}) == clubs
    assert batch.load_club_specs({"CLUBS_JSON": json.dumps({"clubs": clubs})}) == clubs


def test_load_club_specs_reports_malformed_json_cleanly():
    with pytest.raises(SystemExit, match="CLUBS_JSON is not valid JSON"):
        batch.load_club_specs({"CLUBS_JSON": '[{"circle_id": "123\n456"}]'})


def test_environment_for_club_merges_defaults_and_overrides():
    base = {
        "UMA_API_KEY": "shared-key",
        "MONTHLY_QUOTA": "60000000",
    }
    club = {
        "circle_id": "456",
        "discord_webhook": "https://discord.example/club",
        "pin leader": "true",
        "highlight_leader": "true",
    }

    env = batch.environment_for_club(club, base)

    assert env["UMA_API_KEY"] == "shared-key"
    assert env["CIRCLE_ID"] == "456"
    assert env["DISCORD_WEBHOOK"] == "https://discord.example/club"
    assert env["MONTHLY_QUOTA"] == "60000000"
    assert env["PIN_LEADER"] == "true"
    assert env["HIGHLIGHT_LEADER"] == "true"


def test_environment_for_club_requires_api_key_circle_and_webhook():
    with pytest.raises(SystemExit, match="missing required"):
        batch.environment_for_club({}, {})


def test_post_clubs_continues_when_logo_download_fails(monkeypatch, tmp_path):
    calls = []

    def fail_download(_url, _path):
        raise urllib.error.HTTPError(_url, 403, "Forbidden", {}, None)

    def fake_run(args, env, check):
        calls.append((args, env, check))

    monkeypatch.setattr(batch.urllib.request, "urlretrieve", fail_download)
    monkeypatch.setattr(batch.subprocess, "run", fake_run)
    monkeypatch.setattr(batch.tempfile, "TemporaryDirectory", lambda prefix: _TempDir(tmp_path))

    batch.post_clubs(
        [{
            "circle_id": "123",
            "discord_webhook": "https://discord.example/webhook",
            "logo_url": "https://example.invalid/logo.png",
        }],
        {"UMA_API_KEY": "key"},
    )

    assert len(calls) == 1
    assert "LOGO_URL" not in calls[0][1]
    assert "CLUB_LOGO" not in calls[0][1]


class _TempDir:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        return str(self.path)

    def __exit__(self, *_args):
        return False
