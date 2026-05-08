import re
from pathlib import Path

import httpx

_ICON_URL = "https://chronogenesis.net/images/chara_icon/chr_icon_{chara}_{dress:06d}_01.png"
_FNAME_RE = re.compile(r"^chr_icon_(\d+)_(\d+)_01\.png$")
_ICONS_DIR = Path("icons")

_RANK_URL = "https://uma.moe/assets/images/icon/circle_rank/utx_ico_circle_rank_{n:02d}.webp"


def resolve_rank_icon(
    rank: int | None,
    *,
    icons_dir: Path = _ICONS_DIR,
    timeout: float = 15.0,
) -> Path | None:
    """Resolve the in-game rank-tier icon for a given club_rank (1-11). Cached
    under icons_dir/_fetched/circle_rank/. Returns None if rank is missing,
    out of range, or the fetch fails."""
    if rank is None or rank < 1:
        return None
    cache = icons_dir / "_fetched" / "circle_rank" / f"utx_ico_circle_rank_{rank:02d}.webp"
    if cache.exists():
        return cache
    try:
        resp = httpx.get(_RANK_URL.format(n=rank), timeout=timeout)
    except httpx.HTTPError:
        return None
    if (
        resp.status_code != 200
        or not resp.headers.get("content-type", "").startswith("image/")
    ):
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(resp.content)
    return cache


def resolve_club_logo(
    path: Path | None,
    *,
    icons_dir: Path = _ICONS_DIR,
    timeout: float = 15.0,
) -> Path | None:
    """Best-effort resolve a configured club_logo Path to a real file.
    Tries as-is, then a basename match under icons/, then a chronogenesis fetch."""
    if path is None:
        return None
    if path.exists():
        return path
    if icons_dir.is_dir():
        for found in icons_dir.rglob(path.name):
            if found.is_file():
                return found
    m = _FNAME_RE.match(path.name)
    if not m:
        return None
    chara, dress = int(m.group(1)), int(m.group(2))
    try:
        resp = httpx.get(_ICON_URL.format(chara=chara, dress=dress), timeout=timeout)
    except httpx.HTTPError:
        return None
    if (
        resp.status_code != 200
        or not resp.headers.get("content-type", "").startswith("image/")
        or not resp.content.startswith(b"\x89PNG")
    ):
        return None
    save_to = path if path.parent not in (Path(""), Path(".")) else icons_dir / "_fetched" / path.name
    save_to.parent.mkdir(parents=True, exist_ok=True)
    save_to.write_bytes(resp.content)
    return save_to
