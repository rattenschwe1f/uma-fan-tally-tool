from datetime import date
from pathlib import Path

from ..compute import MemberReport
from ..config import Config
from ..model import Circle


def render(
    style: str,
    circle: Circle,
    reports: list[MemberReport],
    today: date,
    config: Config,
    out_path: Path,
    *,
    rank_icon: Path | None = None,
) -> None:
    if style == "classic":
        from . import classic

        classic.render(circle, reports, today, config, out_path, rank_icon=rank_icon)
    else:
        raise ValueError(f"Unknown style: {style}")
