from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from .model import Member

PillTier = Literal["done", "yes", "no"]

GAME_DAY_RESET_HOUR_UTC = 15


def current_game_day(now: datetime) -> date:
    """Calendar date of the in-progress game day; Uma rolls over at 15:00 UTC.
    Caller must pass a tz-aware datetime; naive inputs are rejected."""
    if now.tzinfo is None:
        raise ValueError("current_game_day requires a tz-aware datetime")
    now_utc = now.astimezone(UTC)
    if now_utc.hour < GAME_DAY_RESET_HOUR_UTC:
        return (now_utc - timedelta(days=1)).date()
    return now_utc.date()


@dataclass(frozen=True)
class MemberReport:
    viewer_id: int
    trainer_name: str
    days_elapsed: int
    total: int
    previous_total: int
    daily_avg: float
    expected_so_far: int
    on_target: bool
    off_by: int
    needed_per_day: float
    low_days: int
    latest_day_delta: int
    join_day: int
    pill_tier: PillTier
    staff_role: str | None = None


def _classify_pill(daily_avg: float, quota_per_day: int, quota_complete: bool) -> PillTier:
    """Three pill states: done (hit monthly), yes (on pace), no (behind)."""
    if quota_complete:
        return "done"
    if quota_per_day and daily_avg >= quota_per_day:
        return "yes"
    return "no"


def day_deltas(daily_fans: list[int], days_elapsed: int) -> list[int]:
    """Per-day fan deltas. Negative entries encode the member's prior-club
    balance; positive = balance after joining this club; zero = no snapshot."""
    out: list[int] = []
    for i in range(1, days_elapsed + 1):
        if i >= len(daily_fans):
            break
        prev = daily_fans[i - 1]
        curr = daily_fans[i]
        if prev == 0:
            out.append(0)
            continue
        if prev < 0:
            # Member was still in prior club yesterday. If still negative
            # today, they haven't joined yet (delta 0); if positive today,
            # this is their join day and the gain is curr - abs(prior balance).
            if curr <= 0:
                out.append(0)
                continue
            out.append(max(0, curr - abs(prev)))
            continue
        out.append(max(0, curr - prev))
    return out


def last_recorded_day(daily_fans: list[int], days_elapsed: int) -> int:
    """Highest index i in [1, days_elapsed] with non-zero daily_fans[i],
    or 0 if no day has been recorded yet."""
    for i in range(min(days_elapsed, len(daily_fans) - 1), 0, -1):
        if daily_fans[i] > 0:
            return i
    return 0


def club_latest_day(members: list[Member], days_elapsed: int) -> int:
    """The most recent in-club snapshot day across the whole roster."""
    return max(
        (last_recorded_day(m.daily_fans, days_elapsed) for m in members),
        default=0,
    )


def is_active(member: Member, club_latest: int) -> bool:
    """A member is active if they have a positive snapshot on the club's
    most recent snapshot day. Filters out leavers (zero from leave-day on)
    and pre-month transferers (df[0] positive, df[1..] zero)."""
    if club_latest <= 0 or club_latest >= len(member.daily_fans):
        return False
    return member.daily_fans[club_latest] > 0


def join_day(daily_fans: list[int], days_elapsed: int) -> int:
    """First day in [1, days_elapsed] where the member is in this club
    (daily_fans[i] > 0). Returns 0 if they never joined within the window."""
    for i in range(1, min(days_elapsed + 1, len(daily_fans))):
        if daily_fans[i] > 0:
            return i
    return 0


def build_report(
    member: Member,
    *,
    today: date,
    cutoff_day: int,
    quota_per_day: int,
    low_day_threshold: int,
    joiner_quota: str = "strict",
) -> MemberReport:
    days_in_month = monthrange(today.year, today.month)[1]
    days_elapsed = last_recorded_day(member.daily_fans, cutoff_day)
    days_remaining = days_in_month - days_elapsed

    deltas = day_deltas(member.daily_fans, days_elapsed)
    # A "real" day for low-day counting needs an in-club snapshot today
    # (daily_fans[i] > 0) and any baseline yesterday (daily_fans[i-1] != 0),
    # so synthesised pre-join and missing-snapshot zeros don't tally as misses.
    measured = [
        deltas[i - 1]
        for i in range(1, days_elapsed + 1)
        if i < len(member.daily_fans)
        and member.daily_fans[i] > 0
        and member.daily_fans[i - 1] != 0
    ]
    total = sum(deltas)
    previous_total = sum(deltas[:-1])
    daily_avg = total / days_elapsed if days_elapsed else 0.0
    if days_elapsed == 0:
        return MemberReport(
            viewer_id=member.viewer_id,
            trainer_name=member.trainer_name,
            days_elapsed=0,
            total=0,
            previous_total=0,
            daily_avg=0.0,
            expected_so_far=0,
            on_target=False,
            off_by=0,
            needed_per_day=float(quota_per_day),
            low_days=0,
            latest_day_delta=0,
            join_day=0,
            pill_tier="no",
            staff_role=member.staff_role,
        )
    if joiner_quota == "prorated":
        join = join_day(member.daily_fans, days_elapsed) or 1
        days_in_club = max(1, days_elapsed - join + 1)
        daily_avg = total / days_in_club
        expected_total = quota_per_day * (days_in_month - join + 1)
        expected_so_far = quota_per_day * days_in_club
    else:
        expected_total = quota_per_day * days_in_month
        expected_so_far = quota_per_day * days_elapsed
    on_target = daily_avg >= quota_per_day
    quota_complete = total >= expected_total
    off_by = max(0, expected_so_far - total)
    needed_per_day = (
        (expected_total - total) / days_remaining if days_remaining > 0 else 0.0
    )
    low_days = sum(1 for d in measured if d < low_day_threshold)
    latest_day_delta = deltas[-1] if deltas else 0

    return MemberReport(
        viewer_id=member.viewer_id,
        trainer_name=member.trainer_name,
        days_elapsed=days_elapsed,
        total=total,
        previous_total=previous_total,
        daily_avg=daily_avg,
        expected_so_far=expected_so_far,
        on_target=on_target,
        off_by=off_by,
        needed_per_day=max(0.0, needed_per_day),
        low_days=low_days,
        latest_day_delta=latest_day_delta,
        join_day=join_day(member.daily_fans, days_elapsed),
        pill_tier=_classify_pill(daily_avg, quota_per_day, quota_complete),
        staff_role=member.staff_role,
    )
