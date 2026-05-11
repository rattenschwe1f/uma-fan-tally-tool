from importlib.resources import files

from PIL import ImageFont

_FONTS_DIR = files("uma_tally_tool.assets.fonts")

_FONT_FILES = {
    ("display", False): "MPlusRounded1c-Regular.ttf",
    ("display", True):  "MPlusRounded1c-Bold.ttf",
    ("dejavu", False): "DejaVuSans.ttf",
    ("dejavu", True):  "DejaVuSans-Bold.ttf",
}


def load_font(size: int, *, bold: bool = False, game: bool = False) -> ImageFont.FreeTypeFont:
    """game=True picks the display family; game=False uses DejaVu."""
    family = "display" if game else "dejavu"
    name = _FONT_FILES[(family, bold)]
    with _FONTS_DIR.joinpath(name).open("rb") as fh:
        return ImageFont.truetype(fh, size=size)


def fmt_int(n: int | float) -> str:
    return f"{int(round(n)):,}"


def fmt_blank_if_zero(n: int | float) -> str:
    return fmt_int(n) if n else ""
