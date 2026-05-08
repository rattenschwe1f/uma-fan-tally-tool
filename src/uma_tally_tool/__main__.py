import argparse
import os
import sys
import traceback
from pathlib import Path

from .app import run_once
from .bootstrap import binary_dir, open_in_editor, pause_before_exit, write_starter_config
from .config import Config


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="uma-tally-tool", description="Render a daily Uma Musume circle fan tally.")
    p.add_argument("--env", type=Path, default=Path(".env"), help="Path to .env settings file")
    p.add_argument("--circle-id", type=int, help="Override config circle_id")
    p.add_argument("--monthly-quota", type=int, help="Override monthly quota")
    p.add_argument("--threshold", type=int, dest="low_day_threshold", help="Override low-day threshold")
    p.add_argument("--font", choices=("uma", "mplus"), help="Override game font family")
    p.add_argument(
        "--joiner-quota",
        choices=("strict", "prorated"),
        dest="joiner_quota",
        help="Override joiner quota mode (strict = full month, prorated = scaled to days in club)",
    )
    p.add_argument(
        "--tally",
        choices=("live", "complete"),
        help="complete = trim the in-progress game day (avoids partial tallies for top-100 clubs); live = include it",
    )
    p.add_argument(
        "--expected-fans-style",
        choices=("numbers", "bar"),
        help="numbers = current Expected/Total/Behind columns; bar = monthly quota progress bar",
    )
    for name in ("daily-avg", "on-pace", "needed-per-day", "days-below-threshold", "latest-day"):
        dest = "show_" + name.replace("-", "_")
        group = p.add_mutually_exclusive_group()
        group.add_argument(f"--show-{name}", dest=dest, action="store_true", default=None)
        group.add_argument(f"--hide-{name}", dest=dest, action="store_false", default=None)
    leader = p.add_mutually_exclusive_group()
    leader.add_argument("--pin-leader", dest="pin_leader", action="store_true", default=None)
    leader.add_argument("--no-pin-leader", dest="pin_leader", action="store_false", default=None)
    highlight = p.add_mutually_exclusive_group()
    highlight.add_argument("--highlight-leader", dest="highlight_leader", action="store_true", default=None)
    highlight.add_argument("--no-highlight-leader", dest="highlight_leader", action="store_false", default=None)
    p.add_argument("--out", type=Path, dest="output_dir", help="Override output directory")
    output = p.add_mutually_exclusive_group()
    output.add_argument("--save-output", dest="save_output", action="store_true", default=None)
    output.add_argument("--no-save-output", dest="save_output", action="store_false", default=None)
    p.add_argument("--logo", type=Path, dest="club_logo", help="Override club logo path")
    p.add_argument("--discord-webhook", dest="discord_webhook", help="Override Discord webhook URL")
    p.add_argument("--uma-api-key", dest="uma_moe_api_key", help="Override uma.moe API key")
    return p.parse_args(argv)


def _load_config(args: argparse.Namespace) -> Config:
    binary_env = binary_dir() / ".env"
    if args.env.exists():
        cfg = Config.from_env(args.env)
    elif binary_env.exists():
        cfg = Config.from_env(binary_env)
    elif "CIRCLE_ID" in os.environ:
        cfg = Config.from_environ()
    elif args.circle_id is None:
        target = binary_env
        target.parent.mkdir(parents=True, exist_ok=True)
        write_starter_config(target)
        print(f"No .env found. Wrote a starter at {target}.", file=sys.stderr)
        print("Edit it with your circle id, then run uma-tally-tool again.", file=sys.stderr)
        if open_in_editor(target):
            print("(Opened it in your default editor.)", file=sys.stderr)
        raise SystemExit(2)
    else:
        cfg = Config(circle_id=args.circle_id)

    for field_name in (
        "circle_id", "monthly_quota", "low_day_threshold", "font", "joiner_quota", "tally",
        "expected_fans_style", "show_daily_avg", "show_on_pace", "show_needed_per_day",
        "show_days_below_threshold", "show_latest_day", "pin_leader", "highlight_leader", "save_output",
        "output_dir", "club_logo", "discord_webhook", "uma_moe_api_key",
    ):
        val = getattr(args, field_name)
        if val is not None:
            setattr(cfg, field_name, val)
    return cfg


def _main_impl(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    cfg = _load_config(args)
    return run_once(cfg)


def main(argv: list[str] | None = None) -> int:
    try:
        return _main_impl(argv)
    except KeyboardInterrupt:
        return 130
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else (1 if e.code else 0)
        if code != 0:
            if e.code and not isinstance(e.code, int):
                print(e.code, file=sys.stderr)
            pause_before_exit()
        return code
    except Exception:
        traceback.print_exc()
        pause_before_exit()
        return 1


if __name__ == "__main__":
    sys.exit(main())
