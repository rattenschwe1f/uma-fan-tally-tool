from pathlib import Path

import pytest

from uma_tally_tool import __main__ as cli
from uma_tally_tool.__main__ import _load_config, _parse_args
from uma_tally_tool.config import Config


@pytest.fixture(autouse=True)
def _isolate_bootstrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect starter .env writes and stub out editor opening."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setattr(cli, "binary_dir", lambda: sandbox)
    monkeypatch.setattr(cli, "open_in_editor", lambda _path: False)
    return sandbox


@pytest.fixture
def env_config(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "CIRCLE_ID=333\n"
        "MONTHLY_QUOTA=60000000\n"
        "LOW_DAY_THRESHOLD=250000\n"
        "FONT=mplus\n"
        "JOINER_QUOTA=prorated\n"
        "TALLY=live\n"
        "EXPECTED_FANS_STYLE=bar\n"
        "SHOW_DAILY_AVG=false\n"
        "SHOW_ON_PACE=off\n"
        "SHOW_NEEDED_PER_DAY=no\n"
        "SHOW_DAYS_BELOW_500K=hide\n"
        "SHOW_DAY_X=0\n"
        "PIN_LEADER=true\n"
        "HIGHLIGHT_LEADER=true\n"
        "ON_PACE_COLOR=#112233\n"
        "FINISHED_COLOR=68,85,102\n"
        "OFF_PACE_COLOR=778899\n"
        "OUTPUT_DIR=from_env\n"
        "SAVE_OUTPUT=true\n"
        "CLUB_LOGO=logo-env.png\n"
        "DISCORD_WEBHOOK=https://wh.example/from-env\n"
        "UMA_API_KEY=key-from-env\n"
    )
    return p


def test_loads_defaults_from_env(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config)]))
    assert cfg.circle_id == 333
    assert cfg.monthly_quota == 60_000_000
    assert cfg.low_day_threshold == 250_000
    assert cfg.font == "mplus"
    assert cfg.joiner_quota == "prorated"
    assert cfg.tally == "live"
    assert cfg.expected_fans_style == "bar"
    assert cfg.show_daily_avg is False
    assert cfg.show_on_pace is False
    assert cfg.show_needed_per_day is False
    assert cfg.show_days_below_threshold is False
    assert cfg.show_latest_day is False
    assert cfg.pin_leader is True
    assert cfg.highlight_leader is True
    assert cfg.on_pace_color == (17, 34, 51)
    assert cfg.finished_color == (68, 85, 102)
    assert cfg.off_pace_color == (119, 136, 153)
    assert cfg.output_dir == Path("from_env")
    assert cfg.save_output is True
    assert cfg.club_logo == Path("logo-env.png")
    assert cfg.discord_webhook == "https://wh.example/from-env"
    assert cfg.uma_moe_api_key == "key-from-env"


def test_env_parser_allows_export_and_quotes(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "export CIRCLE_ID=\"444\" # inline comments are okay\n"
        "OUTPUT_DIR='quoted out'\n"
    )
    cfg = Config.from_env(env)
    assert cfg.circle_id == 444
    assert cfg.output_dir == Path("quoted out")


def test_blank_optional_env_values_are_treated_as_unset(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "CIRCLE_ID=444\n"
        "CLUB_LOGO=\n"
        "DISCORD_WEBHOOK=\n"
        "UMA_API_KEY=\n"
    )
    cfg = Config.from_env(env)
    assert cfg.club_logo is None
    assert cfg.discord_webhook is None
    assert cfg.uma_moe_api_key is None


def test_loads_from_environment_variables(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    missing_env = tmp_path / "no.env"
    monkeypatch.setenv("CIRCLE_ID", "555")
    monkeypatch.setenv("MONTHLY_QUOTA", "45000000")
    monkeypatch.setenv("DISCORD_WEBHOOK", "https://wh.example/from-process-env")
    monkeypatch.setenv("UMA_API_KEY", "key-from-process-env")
    cfg = _load_config(_parse_args(["--env", str(missing_env)]))
    assert cfg.circle_id == 555
    assert cfg.monthly_quota == 45_000_000
    assert cfg.discord_webhook == "https://wh.example/from-process-env"
    assert cfg.uma_moe_api_key == "key-from-process-env"


def test_cli_overrides_circle_id(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config), "--circle-id", "222"]))
    assert cfg.circle_id == 222


def test_cli_overrides_threshold(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config), "--threshold", "999"]))
    assert cfg.low_day_threshold == 999


def test_cli_overrides_expected_fans_style_and_column_toggles(env_config: Path):
    cfg = _load_config(_parse_args([
        "--env", str(env_config),
        "--expected-fans-style", "numbers",
        "--show-daily-avg",
        "--show-on-pace",
        "--show-needed-per-day",
        "--show-days-below-threshold",
        "--show-latest-day",
        "--no-pin-leader",
        "--no-highlight-leader",
    ]))
    assert cfg.expected_fans_style == "numbers"
    assert cfg.show_daily_avg is True
    assert cfg.show_on_pace is True
    assert cfg.show_needed_per_day is True
    assert cfg.show_days_below_threshold is True
    assert cfg.show_latest_day is True
    assert cfg.pin_leader is False
    assert cfg.highlight_leader is False


def test_cli_overrides_output_dir(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config), "--out", "elsewhere"]))
    assert cfg.output_dir == Path("elsewhere")


def test_cli_overrides_save_output(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config), "--no-save-output"]))
    assert cfg.save_output is False


def test_cli_overrides_logo(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config), "--logo", "x.png"]))
    assert cfg.club_logo == Path("x.png")


def test_cli_overrides_discord_webhook(env_config: Path):
    cfg = _load_config(_parse_args(
        ["--env", str(env_config), "--discord-webhook", "https://wh.example/cli"]
    ))
    assert cfg.discord_webhook == "https://wh.example/cli"


def test_cli_overrides_uma_api_key(env_config: Path):
    cfg = _load_config(_parse_args(
        ["--env", str(env_config), "--uma-api-key", "key-from-cli"]
    ))
    assert cfg.uma_moe_api_key == "key-from-cli"


def test_cli_overrides_status_colors(env_config: Path):
    cfg = _load_config(_parse_args([
        "--env", str(env_config),
        "--on-pace-color", "#010203",
        "--finished-color", "4,5,6",
        "--off-pace-color", "070809",
    ]))
    assert cfg.on_pace_color == (1, 2, 3)
    assert cfg.finished_color == (4, 5, 6)
    assert cfg.off_pace_color == (7, 8, 9)


def test_cli_monthly_quota_override(env_config: Path):
    cfg = _load_config(_parse_args(["--env", str(env_config), "--monthly-quota", "65000000"]))
    assert cfg.monthly_quota == 65_000_000


def test_circle_id_required_when_no_env(tmp_path: Path):
    missing_env = tmp_path / "no.env"
    with pytest.raises(SystemExit):
        _load_config(_parse_args(["--env", str(missing_env)]))


def test_load_config_writes_starter_env_when_none_exists(tmp_path: Path, _isolate_bootstrap: Path):
    missing_env = tmp_path / "no.env"
    with pytest.raises(SystemExit) as exc:
        _load_config(_parse_args(["--env", str(missing_env)]))
    assert exc.value.code == 2
    starter = _isolate_bootstrap / ".env"
    assert starter.exists()
    assert "CIRCLE_ID" in starter.read_text()


def test_circle_id_via_cli_only_works_when_no_env(tmp_path: Path):
    missing_env = tmp_path / "no.env"
    cfg = _load_config(_parse_args(["--env", str(missing_env), "--circle-id", "777"]))
    assert cfg.circle_id == 777
