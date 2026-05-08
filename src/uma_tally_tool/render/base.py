from importlib.resources import files

from PIL import ImageFont

_FONTS_DIR = files("uma_tally_tool.assets.fonts")

_FONT_FILES = {
    ("uma", False):    "UmaFont.ttf",
    ("uma", True):     "UmaFont.ttf",
    ("mplus", False):  "MPlusRounded1c-Regular.ttf",
    ("mplus", True):   "MPlusRounded1c-Bold.ttf",
    ("dejavu", False): "DejaVuSans.ttf",
    ("dejavu", True):  "DejaVuSans-Bold.ttf",
}

_FONT_FAMILY = "uma"


def set_font_family(name: str) -> None:
    global _FONT_FAMILY
    if name not in {"uma", "mplus", "dejavu"}:
        raise ValueError(f"unknown font family: {name}")
    _FONT_FAMILY = name


def load_font(size: int, *, bold: bool = False, game: bool = False) -> ImageFont.FreeTypeFont:
    """game=True picks the configured game family (uma/mplus); game=False always uses DejaVu."""
    family = _FONT_FAMILY if game else "dejavu"
    name = _FONT_FILES[(family, bold)]
    with _FONTS_DIR.joinpath(name).open("rb") as fh:
        return ImageFont.truetype(fh, size=size)


def fmt_int(n: int | float) -> str:
    return f"{int(round(n)):,}"


def fmt_blank_if_zero(n: int | float) -> str:
    return fmt_int(n) if n else ""
