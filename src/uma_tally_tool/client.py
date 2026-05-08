import time

import httpx

from .model import CircleResponse

UMA_MOE_API = "https://uma.moe/api/v4/circles"
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class CircleNotFound(Exception):
    """uma.moe returned 404 for the given circle id."""


class FetchError(Exception):
    """uma.moe was unreachable or returned an unexpected response."""


def fetch_circle(
    circle_id: int,
    *,
    api_key: str,
    timeout: float = 15.0,
    retries: int = 3,
    backoff_base: float = 1.0,
    sleep=time.sleep,
) -> CircleResponse:
    if not api_key:
        raise ValueError("uma.moe API key is required")
    last_err: Exception | None = None
    headers = {"X-API-Key": api_key}
    for attempt in range(retries):
        try:
            resp = httpx.get(UMA_MOE_API, params={"circle_id": circle_id}, headers=headers, timeout=timeout)
        except httpx.RequestError as e:
            last_err = FetchError(f"couldn't reach uma.moe ({type(e).__name__}: {e})")
            last_err.__cause__ = e
        else:
            if resp.status_code == 404:
                raise CircleNotFound(f"circle id {circle_id} doesn't exist on uma.moe")
            if resp.is_success:
                return CircleResponse.model_validate(resp.json())
            if resp.status_code not in RETRYABLE_STATUSES:
                raise FetchError(f"uma.moe returned HTTP {resp.status_code}")
            last_err = FetchError(f"uma.moe returned HTTP {resp.status_code}")

        if attempt < retries - 1:
            sleep(backoff_base * (2 ** attempt))

    assert last_err is not None
    raise last_err
