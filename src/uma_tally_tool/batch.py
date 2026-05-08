import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from collections.abc import Iterable, Mapping
from pathlib import Path


DEFAULTED_ENV_KEYS = (
    "UMA_API_KEY",
    "MONTHLY_QUOTA",
    "LOW_DAY_THRESHOLD",
    "FONT",
    "JOINER_QUOTA",
    "TALLY",
    "EXPECTED_FANS_STYLE",
    "SHOW_DAILY_AVG",
    "SHOW_ON_PACE",
    "SHOW_NEEDED_PER_DAY",
    "SHOW_DAYS_BELOW_THRESHOLD",
    "SHOW_LATEST_DAY",
    "PIN_LEADER",
    "HIGHLIGHT_LEADER",
    "SAVE_OUTPUT",
    "OUTPUT_DIR",
    "CLUB_LOGO",
    "LOGO_URL",
)

CLUB_JSON_KEYS = {
    "circle_id": "CIRCLE_ID",
    "discord_webhook": "DISCORD_WEBHOOK",
    "monthly_quota": "MONTHLY_QUOTA",
    "low_day_threshold": "LOW_DAY_THRESHOLD",
    "font": "FONT",
    "joiner_quota": "JOINER_QUOTA",
    "tally": "TALLY",
    "expected_fans_style": "EXPECTED_FANS_STYLE",
    "show_daily_avg": "SHOW_DAILY_AVG",
    "show_on_pace": "SHOW_ON_PACE",
    "show_needed_per_day": "SHOW_NEEDED_PER_DAY",
    "show_days_below_threshold": "SHOW_DAYS_BELOW_THRESHOLD",
    "show_latest_day": "SHOW_LATEST_DAY",
    "pin_leader": "PIN_LEADER",
    "pin leader": "PIN_LEADER",
    "highlight_leader": "HIGHLIGHT_LEADER",
    "save_output": "SAVE_OUTPUT",
    "output_dir": "OUTPUT_DIR",
    "club_logo": "CLUB_LOGO",
    "logo_url": "LOGO_URL",
    "uma_api_key": "UMA_API_KEY",
}


def load_club_specs(env: Mapping[str, str] = os.environ) -> list[dict[str, object]]:
    raw = env.get("CLUBS_JSON", "").strip()
    if not raw:
        return [
            {
                "name": "default",
                "circle_id": env.get("CIRCLE_ID", ""),
                "discord_webhook": env.get("DISCORD_WEBHOOK", ""),
            }
        ]

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(
            "CLUBS_JSON is not valid JSON. "
            f"JSON parser stopped at line {e.lineno}, column {e.colno}: {e.msg}. "
            "Common causes are missing quotes, trailing commas, or a pasted line break inside a string value."
        ) from e
    if isinstance(decoded, dict):
        decoded = decoded.get("clubs", [])
    if not isinstance(decoded, list) or not decoded:
        raise SystemExit("CLUBS_JSON must be a non-empty JSON array, or an object with a non-empty clubs array.")
    if any(not isinstance(item, dict) for item in decoded):
        raise SystemExit("Every CLUBS_JSON item must be an object.")
    return decoded


def _json_value(club: Mapping[str, object], key: str, env_name: str) -> str | None:
    for candidate in (key, env_name, env_name.lower()):
        value = club.get(candidate)
        if value is not None:
            return str(value)
    return None


def environment_for_club(
    club: Mapping[str, object],
    base_env: Mapping[str, str] = os.environ,
) -> dict[str, str]:
    run_env = dict(base_env)
    for env_name in DEFAULTED_ENV_KEYS:
        value = base_env.get(env_name)
        if value is not None:
            run_env[env_name] = value

    for key, env_name in CLUB_JSON_KEYS.items():
        value = _json_value(club, key, env_name)
        if value is not None:
            run_env[env_name] = value

    label = str(club.get("name") or club.get("circle_id") or "club")
    missing = [name for name in ("UMA_API_KEY", "CIRCLE_ID", "DISCORD_WEBHOOK") if not run_env.get(name)]
    if missing:
        raise SystemExit(f"{label}: missing required setting(s): {', '.join(missing)}")
    return run_env


def _with_downloaded_logo(run_env: dict[str, str], temp_dir: Path) -> dict[str, str]:
    logo_url = run_env.get("LOGO_URL", "").strip()
    if not logo_url:
        return run_env
    logo_path = temp_dir / "club_logo.png"
    try:
        urllib.request.urlretrieve(logo_url, logo_path)
    except (OSError, urllib.error.URLError) as e:
        print(f"Warning: couldn't download LOGO_URL ({e}); continuing without that logo.", file=sys.stderr)
        merged = dict(run_env)
        merged.pop("LOGO_URL", None)
        merged.pop("CLUB_LOGO", None)
        return merged
    merged = dict(run_env)
    merged["CLUB_LOGO"] = str(logo_path)
    return merged


def post_clubs(clubs: Iterable[Mapping[str, object]], base_env: Mapping[str, str] = os.environ) -> None:
    for index, club in enumerate(clubs, start=1):
        label = str(club.get("name") or club.get("circle_id") or f"club {index}")
        run_env = environment_for_club(club, base_env)
        with tempfile.TemporaryDirectory(prefix=f"uma-report-{index}-") as tmp:
            run_env = _with_downloaded_logo(run_env, Path(tmp))
            print(f"::group::Posting {label}")
            try:
                subprocess.run([sys.executable, "-m", "uma_tally_tool"], env=run_env, check=True)
            finally:
                print("::endgroup::")


def main() -> int:
    post_clubs(load_club_specs())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
