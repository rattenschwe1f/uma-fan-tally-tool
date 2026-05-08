from pathlib import Path

import httpx

from uma_tally_tool import icons
from uma_tally_tool.icons import resolve_club_logo


def test_resolve_club_logo_returns_none_when_path_is_none():
    assert resolve_club_logo(None) is None


def test_resolve_club_logo_returns_path_when_file_exists(tmp_path: Path):
    target = tmp_path / "logo.png"
    target.write_bytes(b"\x89PNGfake")
    assert resolve_club_logo(target) == target


def test_resolve_club_logo_finds_basename_match_under_icons_dir(tmp_path: Path):
    icons_dir = tmp_path / "icons"
    char_dir = icons_dir / "King_Halo"
    char_dir.mkdir(parents=True)
    real = char_dir / "chr_icon_1061_106150_01.png"
    real.write_bytes(b"\x89PNGfake")
    bare = Path("chr_icon_1061_106150_01.png")
    assert resolve_club_logo(bare, icons_dir=icons_dir) == real


def test_resolve_club_logo_fetches_when_filename_matches_pattern(tmp_path, monkeypatch):
    icons_dir = tmp_path / "icons"
    fetched = b"\x89PNG" + b"x" * 32

    class FakeResp:
        status_code = 200
        headers = {"content-type": "image/png"}
        content = fetched

    def fake_get(url, timeout):
        assert "chr_icon_1061_106150_01.png" in url
        return FakeResp()

    monkeypatch.setattr(icons.httpx, "get", fake_get)
    out = resolve_club_logo(Path("chr_icon_1061_106150_01.png"), icons_dir=icons_dir)
    assert out == icons_dir / "_fetched" / "chr_icon_1061_106150_01.png"
    assert out.read_bytes() == fetched


def test_resolve_club_logo_returns_none_when_filename_doesnt_match_pattern(tmp_path):
    icons_dir = tmp_path / "icons"
    icons_dir.mkdir()
    assert resolve_club_logo(Path("not-an-icon.png"), icons_dir=icons_dir) is None


def test_resolve_club_logo_returns_none_when_fetch_fails(tmp_path, monkeypatch):
    icons_dir = tmp_path / "icons"

    def fake_get(url, timeout):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(icons.httpx, "get", fake_get)
    assert resolve_club_logo(Path("chr_icon_1061_106150_01.png"), icons_dir=icons_dir) is None
