import sys
import tempfile
from calendar import monthrange
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import discord
from .client import CircleNotFound, FetchError, fetch_circle
from .compute import build_report, club_latest_day, current_game_day, is_active
from .config import Config
from .icons import resolve_club_logo, resolve_rank_icon
from .model import CircleResponse, Member, circle_leader_name
from .render import render
from .render.base import set_font_family


def require_api_key(config: Config) -> None:
    if config.uma_moe_api_key:
        return
    print("\nError: UMA_API_KEY is required.", file=sys.stderr)
    print("Create an uma.moe account, generate an API key in settings, then add it to your config.", file=sys.stderr)
    raise SystemExit(2)


def fetch_circle_snapshot(config: Config):
    print(f"Fetching circle {config.circle_id}...", file=sys.stderr)
    try:
        return fetch_circle(config.circle_id, api_key=config.uma_moe_api_key or "")
    except CircleNotFound as e:
        print(f"\nError: {e}.", file=sys.stderr)
        print("Edit your .env or pass --circle-id with a valid id.", file=sys.stderr)
        raise SystemExit(2) from e
    except FetchError as e:
        print(f"\nError: {e}.", file=sys.stderr)
        print("Check your network connection and try again.", file=sys.stderr)
        raise SystemExit(2) from e


def report_date(config: Config, now: datetime | None = None):
    game_day = current_game_day(now or datetime.now(UTC))
    return game_day if config.tally == "live" else game_day - timedelta(days=1)


def data_is_ready(response, cutoff_date) -> bool:
    if not response.members:
        return True
    data_year = response.members[0].year
    data_month = response.members[0].month
    if (cutoff_date.year, cutoff_date.month) == (data_year, data_month):
        return True
    print(
        f"No data yet for {cutoff_date:%B %Y}. The game day just rolled "
        "into a new month and uma.moe hasn't snapshotted it yet.",
        file=sys.stderr,
    )
    return False


def _same_trainer_name(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return left.strip().casefold() == right.strip().casefold()


def _leader_role(member: Member, leader_name: str | None) -> str | None:
    if _same_trainer_name(member.trainer_name, leader_name):
        return "leader"
    return None


def build_member_reports(response: CircleResponse, config: Config, today):
    quota_per_day = round(config.monthly_quota / monthrange(today.year, today.month)[1])
    latest_day = club_latest_day(response.members, today.day)
    leader_name = circle_leader_name(response)
    reports = []
    for member in response.members:
        if not is_active(member, latest_day):
            continue
        report = build_report(
            member,
            today=today,
            quota_per_day=quota_per_day,
            low_day_threshold=config.low_day_threshold,
            joiner_quota=config.joiner_quota,
            cutoff_day=today.day,
        )
        if role := _leader_role(member, leader_name):
            report = replace(report, staff_role=role)
        reports.append(report)
    print(f"Active members: {len(reports)} / {len(response.members)}", file=sys.stderr)
    return reports


def with_resolved_logo(config: Config) -> Config:
    if not config.club_logo:
        return config
    resolved = resolve_club_logo(config.club_logo)
    if resolved is None:
        print(f"  club_logo {config.club_logo} not found locally and couldn't be fetched", file=sys.stderr)
        return replace(config, club_logo=None)
    if resolved != config.club_logo:
        print(f"  club_logo: using {resolved}", file=sys.stderr)
        return replace(config, club_logo=resolved)
    return config


def rank_icon_for(response) -> Path | None:
    if not response.club_rank:
        return None
    rank_icon = resolve_rank_icon(response.club_rank)
    if rank_icon is None:
        print(f"  rank icon for tier {response.club_rank} not available", file=sys.stderr)
    return rank_icon


def render_and_deliver(response, reports, today, config: Config, rank_icon: Path | None) -> None:
    should_save = config.save_output or not config.discord_webhook
    if should_save:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = config.output_dir / f"{response.circle.name}-{today.isoformat()}.png"
        render("classic", response.circle, reports, today, config, out_path, rank_icon=rank_icon)
        print(f"  wrote {out_path}", file=sys.stderr)
        if config.discord_webhook:
            discord.post_image(config.discord_webhook, out_path, content=f"{response.circle.name}, {today.isoformat()}")
            print(f"  posted {out_path.name} to Discord", file=sys.stderr)
        return

    with tempfile.TemporaryDirectory(prefix="uma-tally-tool-") as tmp:
        out_path = Path(tmp) / f"{response.circle.name}-{today.isoformat()}.png"
        render("classic", response.circle, reports, today, config, out_path, rank_icon=rank_icon)
        discord.post_image(config.discord_webhook or "", out_path, content=f"{response.circle.name}, {today.isoformat()}")
        print(f"  posted {out_path.name} to Discord", file=sys.stderr)


def run_once(config: Config, now: datetime | None = None) -> int:
    require_api_key(config)
    today = report_date(config, now)
    response = fetch_circle_snapshot(config)
    if not data_is_ready(response, today):
        return 0

    reports = build_member_reports(response, config, today)
    set_font_family(config.font)
    config = with_resolved_logo(config)
    render_and_deliver(response, reports, today, config, rank_icon_for(response))
    return 0
