from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from os import environ
from pathlib import Path


JOINER_QUOTA_MODES = ("strict", "prorated")
TALLY_MODES = ("live", "complete")
EXPECTED_FANS_STYLES = ("numbers", "bar")
Color = tuple[int, int, int]


def _as_bool(value: object, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "show"}:
        return True
    if text in {"0", "false", "no", "off", "hide"}:
        return False
    raise ValueError(f"Expected a boolean value, got {value!r}")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_color(value: object, default: Color) -> Color:
    if value is None:
        return default
    if isinstance(value, tuple) and len(value) == 3:
        return tuple(int(part) for part in value)  # type: ignore[return-value]

    text = str(value).strip()
    if not text:
        return default
    if text.startswith("#"):
        text = text[1:]
    if len(text) == 6:
        try:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
        except ValueError:
            pass
    parts = [part.strip() for part in text.split(",")]
    if len(parts) == 3:
        try:
            color = tuple(int(part) for part in parts)
        except ValueError:
            color = ()
        if len(color) == 3 and all(0 <= part <= 255 for part in color):
            return color  # type: ignore[return-value]
    raise ValueError(f"Expected a color like #5BBEFF or 91,190,255, got {value!r}")


@dataclass
class Config:
    circle_id: int
    monthly_quota: int = 60_000_000
    low_day_threshold: int = 500_000
    output_dir: Path = field(default_factory=lambda: Path("out"))
    joiner_quota: str = "strict"
    tally: str = "complete"
    expected_fans_style: str = "numbers"
    show_daily_avg: bool = True
    show_on_pace: bool = True
    show_needed_per_day: bool = True
    show_days_below_threshold: bool = True
    show_latest_day: bool = True
    pin_leader: bool = False
    highlight_leader: bool = False
    on_pace_color: Color = (91, 190, 255)
    finished_color: Color = (119, 221, 139)
    off_pace_color: Color = (235, 82, 82)
    save_output: bool = False
    club_logo: Path | None = None
    discord_webhook: str | None = None
    uma_moe_api_key: str | None = None

    def __post_init__(self) -> None:
        if self.joiner_quota not in JOINER_QUOTA_MODES:
            raise ValueError(
                f"joiner_quota must be one of {JOINER_QUOTA_MODES}, got {self.joiner_quota!r}"
            )
        if self.tally not in TALLY_MODES:
            raise ValueError(
                f"tally must be one of {TALLY_MODES}, got {self.tally!r}"
            )
        if self.expected_fans_style not in EXPECTED_FANS_STYLES:
            raise ValueError(
                f"expected_fans_style must be one of {EXPECTED_FANS_STYLES}, got {self.expected_fans_style!r}"
            )

    @classmethod
    def from_env(cls, path: Path, today: date | None = None) -> "Config":
        return cls.from_mapping(_read_env(path), today=today)

    @classmethod
    def from_mapping(cls, data: dict[str, object], today: date | None = None) -> "Config":
        return cls(
            circle_id=int(data["circle_id"]),
            monthly_quota=int(data.get("monthly_quota", 60_000_000)),
            low_day_threshold=int(data.get("low_day_threshold", 500_000)),
            output_dir=Path(data.get("output_dir", "out")),
            joiner_quota=str(data.get("joiner_quota", "strict")),
            tally=str(data.get("tally", "complete")),
            expected_fans_style=str(data.get("expected_fans_style", "numbers")),
            show_daily_avg=_as_bool(data.get("show_daily_avg"), True),
            show_on_pace=_as_bool(data.get("show_on_pace"), True),
            show_needed_per_day=_as_bool(data.get("show_needed_per_day"), True),
            show_days_below_threshold=_as_bool(data.get("show_days_below_threshold"), True),
            show_latest_day=_as_bool(data.get("show_latest_day"), True),
            pin_leader=_as_bool(data.get("pin_leader"), False),
            highlight_leader=_as_bool(data.get("highlight_leader"), False),
            on_pace_color=_as_color(data.get("on_pace_color"), (91, 190, 255)),
            finished_color=_as_color(data.get("finished_color"), (119, 221, 139)),
            off_pace_color=_as_color(data.get("off_pace_color"), (235, 82, 82)),
            save_output=_as_bool(data.get("save_output"), False),
            club_logo=Path(logo) if (logo := _optional_str(data.get("club_logo"))) else None,
            discord_webhook=_optional_str(data.get("discord_webhook")),
            uma_moe_api_key=_optional_str(data.get("uma_api_key")),
        )

    @classmethod
    def from_environ(cls, env: Mapping[str, str] | None = None) -> "Config":
        return cls.from_mapping(_read_env_mapping(environ if env is None else env))


_ENV_KEYS = {
    "CIRCLE_ID": "circle_id",
    "MONTHLY_QUOTA": "monthly_quota",
    "LOW_DAY_THRESHOLD": "low_day_threshold",
    "OUTPUT_DIR": "output_dir",
    "JOINER_QUOTA": "joiner_quota",
    "TALLY": "tally",
    "EXPECTED_FANS_STYLE": "expected_fans_style",
    "EXPACTED_FANS_STYLE": "expected_fans_style",
    "SHOW_DAILY_AVG": "show_daily_avg",
    "SHOW_ON_PACE": "show_on_pace",
    "SHOW_NEEDED_PER_DAY": "show_needed_per_day",
    "SHOW_DAYS_BELOW_THRESHOLD": "show_days_below_threshold",
    "SHOW_DAYS_BELOW_500K": "show_days_below_threshold",
    "SHOW_LATEST_DAY": "show_latest_day",
    "SHOW_DAY_X": "show_latest_day",
    "PIN_LEADER": "pin_leader",
    "HIGHLIGHT_LEADER": "highlight_leader",
    "ON_PACE_COLOR": "on_pace_color",
    "FINISHED_COLOR": "finished_color",
    "OFF_PACE_COLOR": "off_pace_color",
    "SAVE_OUTPUT": "save_output",
    "CLUB_LOGO": "club_logo",
    "DISCORD_WEBHOOK": "discord_webhook",
    "UMA_API_KEY": "uma_api_key",
}


def _strip_env_comment(raw: str) -> str:
    quote: str | None = None
    escaped = False
    for i, ch in enumerate(raw):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch == "#" and i > 0 and raw[i - 1].isspace():
            return raw[:i]
    return raw


def _strip_env_value(raw: str) -> str:
    raw = _strip_env_comment(raw)
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, raw_value = line.partition("=")
        if not sep:
            continue
        field = _ENV_KEYS.get(key.strip().upper())
        if field is None:
            continue
        data[field] = _strip_env_value(raw_value)
    return data


def _read_env_mapping(env: Mapping[str, str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for key, value in env.items():
        field = _ENV_KEYS.get(key.strip().upper())
        if field is not None:
            data[field] = value
    return data
