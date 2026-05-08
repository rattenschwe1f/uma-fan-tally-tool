from pathlib import Path

import httpx


def post_image(webhook_url: str, image_path: Path, content: str = "") -> None:
    with image_path.open("rb") as fh:
        resp = httpx.post(
            webhook_url,
            data={"content": content},
            files={"file": (image_path.name, fh, "image/png")},
            timeout=30.0,
        )
    resp.raise_for_status()
