"""Palette for the classic renderer."""

from typing import TypedDict


class PillStyle(TypedDict):
    outer: tuple[int, int, int]
    inner: tuple[int, int, int]
    body: tuple[tuple[int, int, int], tuple[int, int, int]]


THEME = {
    "bg": (16, 18, 24),
    "panel": (24, 27, 36),
    "row_alt": (28, 31, 41),
    "header_bg": (40, 45, 60),
    "header_top": (60, 68, 90),
    "header_bottom": (24, 27, 38),
    "title": (235, 238, 245),
    "text": (235, 238, 245),
    "muted": (150, 156, 170),
    "subtle": (110, 116, 130),
    "yes_bg": (76, 175, 80),
    "yes_fg": (10, 30, 12),
    "no_bg": (224, 102, 102),
    "no_fg": (40, 8, 8),
    "done_bg": (240, 188, 60),
    "done_fg": (60, 38, 8),
    "low": (224, 102, 102),
    "pill_tiers": {
        "done": {
            "outer": (240, 20, 91),
            "inner": (255, 175, 200),
            "body": ((255, 134, 165), (247, 73, 130)),
        },
        "yes": {
            "outer": (240, 95, 10),
            "inner": (255, 200, 130),
            "body": ((255, 165, 65), (255, 130, 50)),
        },
        "no": {
            "outer": (131, 56, 205),
            "inner": (220, 185, 255),
            "body": ((199, 131, 255), (170, 110, 235)),
        },
    },
    "pill_label": {
        "done": "Done",
        "yes": "Yes",
        "no": "No",
    },
    "pill_fg": (255, 255, 255),
    "progress_on": (91, 190, 255),
    "progress_off": (235, 82, 82),
    "rank_up": (92, 210, 138),
    "rank_down": (235, 82, 82),
    "rank_flat": (140, 146, 160),
    "severity_steps": [
        (130, 140, 160),
        (240, 188, 60),
        (224, 102, 102),
    ],
    "use_game_font": True,
}
