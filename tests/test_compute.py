from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from uma_tally_tool.compute import (
    build_report as _build_report,
)
from uma_tally_tool.compute import (
    club_latest_day,
    current_game_day,
    day_deltas,
    is_active,
    join_day,
)
from uma_tally_tool.model import Circle, CircleResponse, Member, circle_leader_name


def build_report(member, *, today, **kwargs):
    """Test wrapper: defaults cutoff_day to today.day so test bodies stay terse."""
    return _build_report(member, today=today, cutoff_day=kwargs.pop("cutoff_day", today.day), **kwargs)


def _member(daily_fans: list[int], name: str = "Test", year: int = 2026, month: int = 5) -> Member:
    padded = daily_fans + [0] * (32 - len(daily_fans))
    return Member(
        viewer_id=1,
        trainer_name=name,
        year=year,
        month=month,
        daily_fans=padded,
    )


def test_member_normalizes_staff_role_from_role_fields():
    leader = Member(
        viewer_id=1,
        trainer_name="Lead",
        year=2026,
        month=5,
        daily_fans=[1, 2],
        role="leader",
    )
    officer = Member(
        viewer_id=2,
        trainer_name="Officer",
        year=2026,
        month=5,
        daily_fans=[1, 2],
        is_officer=True,
    )

    assert leader.staff_role == "leader"
    assert officer.staff_role == "officer"


def test_circle_leader_name_accepts_top_level_or_circle_field():
    nested = CircleResponse(circle=Circle(circle_id=1, name="Club", leader_name="Nested"), members=[])
    top = CircleResponse(circle=Circle(circle_id=1, name="Club"), members=[], leader_name="Top")

    assert circle_leader_name(nested) == "Nested"
    assert circle_leader_name(top) == "Top"


def test_day_deltas_returns_simple_diffs_when_monotonic():
    fans = [1000, 1100, 1250, 1400]
    assert day_deltas(fans, days_elapsed=3) == [100, 150, 150]


def test_day_deltas_credits_prior_club_carry_over_to_day_one():
    # daily_fans[0] is the prior club's balance stored as negative.
    # Day 1 = daily_fans[1] - abs(daily_fans[0]).
    fans = [-694_000_000, 703_000_000, 705_000_000]
    deltas = day_deltas(fans, days_elapsed=2)
    assert deltas[0] == 9_000_000
    assert deltas[1] == 2_000_000


def test_day_deltas_returns_zero_for_day_one_when_baseline_is_missing():
    # daily_fans[0] == 0 means no prior-month snapshot was captured.
    fans = [0, 552_806_481, 553_500_000]
    deltas = day_deltas(fans, days_elapsed=2)
    assert deltas[0] == 0
    assert deltas[1] == 553_500_000 - 552_806_481


def test_day_deltas_returns_empty_when_zero_days_elapsed():
    assert day_deltas([100, 200], days_elapsed=0) == []


def test_build_report_marks_on_target_when_daily_avg_meets_quota():
    member = _member([100_000_000, 102_000_000, 104_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.on_target is True
    assert r.daily_avg == 2_000_000
    assert r.off_by == 0


def test_build_report_carries_staff_role():
    member = _member([100_000_000, 102_000_000])
    member.staff_role = "leader"
    r = build_report(member, today=date(2026, 5, 1), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.staff_role == "leader"


def test_build_report_reports_off_by_when_behind_quota():
    member = _member([100_000_000, 101_000_000, 102_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.on_target is False
    assert r.total == 2_000_000
    assert r.off_by == 2_000_000


def test_build_report_computes_needed_per_day_to_hit_monthly_target():
    member = _member([100_000_000, 101_000_000, 102_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    # 31 days * 2M = 62M target; have 2M so far; 29 days remaining.
    assert r.needed_per_day == (62_000_000 - 2_000_000) / 29


def test_build_report_counts_low_days_below_threshold():
    member = _member([100_000_000, 100_100_000, 100_700_000, 101_300_000])
    r = build_report(member, today=date(2026, 5, 3), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.low_days == 1


def test_build_report_handles_exact_on_pace_boundary():
    member = _member([100_000_000, 102_000_000])
    r = build_report(member, today=date(2026, 5, 1), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.on_target is True
    assert r.off_by == 0


def test_build_report_returns_zero_needed_per_day_at_end_of_month():
    fans = [100_000_000] + [100_000_000 + 2_000_000 * i for i in range(1, 32)]
    member = _member(fans)
    r = build_report(member, today=date(2026, 5, 31), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.needed_per_day == 0.0


def test_is_active_returns_false_when_no_fans_gained_this_month():
    member = _member([500_000_000, 0, 0, 0])
    assert is_active(member, club_latest=0) is False


def test_is_active_returns_true_when_member_has_positive_snapshot_on_club_latest_day():
    member = _member([500_000_000, 502_000_000, 0, 0])
    assert is_active(member, club_latest=1) is True


def test_is_active_returns_true_for_mid_month_joiner():
    fans = [0, 0, 0, 0, 100_000_000, 102_000_000]
    member = _member(fans)
    assert is_active(member, club_latest=5) is True


def test_is_active_returns_false_when_member_left_mid_month():
    # Member's last in-club snapshot is day 1; the club moved on to day 2.
    leaver = _member([100_000_000, 100_000_000, 0, 0, 0])
    assert is_active(leaver, club_latest=2) is False


def test_is_active_returns_false_when_member_left_before_month_started():
    # Pre-month transferer: positive prior-month balance, no in-club snapshots.
    leaver = _member([100_000_000, 0, 0, 0])
    assert is_active(leaver, club_latest=2) is False


def test_club_latest_day_returns_max_across_members():
    leaver = _member([100_000_000, 100_000_000, 0, 0, 0])
    active = _member([200_000_000, 202_000_000, 204_000_000])
    assert club_latest_day([leaver, active], days_elapsed=3) == 2


def test_club_latest_day_returns_zero_when_no_member_has_in_club_snapshot():
    no_one = _member([100_000_000, 0, 0, 0])
    assert club_latest_day([no_one], days_elapsed=3) == 0


def test_club_latest_day_returns_zero_for_empty_roster():
    assert club_latest_day([], days_elapsed=3) == 0


def test_build_report_reports_zero_day_one_when_baseline_missing():
    member = _member([0, 100_000_000, 102_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    # Day 1 gain not credited (baseline missing); only day 2's 2M counts.
    assert r.total == 2_000_000


def test_build_report_does_not_count_synthesized_day_one_as_low_day():
    member = _member([0, 100_000_000, 102_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.low_days == 0


def test_build_report_credits_carry_over_for_club_transfer_member():
    member = _member([-100_000_000, 109_000_000, 111_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    # Day 1 = 109M - abs(-100M) = 9M; day 2 = 2M; total = 11M.
    assert r.total == 11_000_000
    assert r.latest_day_delta == 2_000_000


def test_build_report_handles_mid_month_joiner_with_prior_club_carryover():
    # Negative on day 1 (still in old club), positive on day 2 (join day).
    member = _member([-100_000_000, -100_500_000, 102_000_000])
    r = build_report(member, today=date(2026, 5, 3), quota_per_day=2_000_000, low_day_threshold=500_000)
    # Day 1 contributes 0 (still in prior club), day 2 contributes 1.5M.
    assert day_deltas(member.daily_fans, days_elapsed=2) == [0, 1_500_000]
    assert r.total == 1_500_000
    assert r.join_day == 2
    assert r.low_days == 0


def test_build_report_uses_latest_day_delta_for_last_column():
    # Days 1-3 deltas: 100, 1_000_000, 2_500_000, latest_day_delta should be the day-3 figure.
    member = _member([100_000_000, 100_000_100, 101_000_100, 103_500_100])
    r = build_report(member, today=date(2026, 5, 3), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.latest_day_delta == 2_500_000


def test_build_report_tracks_previous_total_for_rank_movement():
    member = _member([100_000_000, 101_000_000, 103_500_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.total == 3_500_000
    assert r.previous_total == 1_000_000


def test_build_report_marks_quota_complete_when_total_meets_monthly_target():
    fans = [100_000_000] + [100_000_000 + 2_500_000 * i for i in range(1, 32)]
    member = _member(fans)
    r = build_report(member, today=date(2026, 5, 31), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.pill_tier == "done"
    assert r.on_target is True


def test_build_report_marks_quota_incomplete_when_short_of_monthly_target():
    member = _member([100_000_000, 102_000_000, 104_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    # Total 4M is far short of monthly 62M target; pill stays at "yes" or "no".
    assert r.pill_tier != "done"


def test_join_day_returns_first_positive_index():
    assert join_day([100_000_000, 102_000_000, 104_000_000], days_elapsed=2) == 1


def test_join_day_skips_negative_prior_club_days():
    assert join_day([-100_000_000, -100_000_000, 102_000_000], days_elapsed=2) == 2


def test_join_day_returns_zero_when_member_never_appears_in_window():
    assert join_day([100_000_000, 0, 0, 0], days_elapsed=3) == 0


def test_build_report_strict_mode_expects_full_month_for_mid_month_joiner():
    # Joined day 2, gained 2M on join day. Strict expects 2 days × 2M = 4M.
    member = _member([-100_000_000, -100_000_000, 102_000_000])
    r = build_report(
        member, today=date(2026, 5, 3), quota_per_day=2_000_000,
        low_day_threshold=500_000, joiner_quota="strict",
    )
    assert r.expected_so_far == 2_000_000 * 2  # strict treats them as if from day 1
    assert r.quota_total == 2_000_000 * 31
    assert r.off_by == 2_000_000  # 4M expected - 2M total


def test_build_report_prorated_mode_scales_to_days_in_club():
    # Joined day 2, gained 2M on join day. Prorated expects 1 day × 2M = 2M.
    member = _member([-100_000_000, -100_000_000, 102_000_000])
    r = build_report(
        member, today=date(2026, 5, 3), quota_per_day=2_000_000,
        low_day_threshold=500_000, joiner_quota="prorated",
    )
    assert r.expected_so_far == 2_000_000  # one day in club
    assert r.quota_total == 2_000_000 * 30  # joined on day 2 of a 31-day month
    assert r.off_by == 0  # gained 2M in 1 day, hits prorated quota exactly
    assert r.daily_avg == 2_000_000  # rate over their 1 day in club
    assert r.on_target is True


def test_build_report_prorated_mode_matches_strict_for_full_month_member():
    # Full-month member: prorated and strict should be identical.
    member = _member([100_000_000, 102_000_000, 104_000_000])
    strict = build_report(
        member, today=date(2026, 5, 2), quota_per_day=2_000_000,
        low_day_threshold=500_000, joiner_quota="strict",
    )
    prorated = build_report(
        member, today=date(2026, 5, 2), quota_per_day=2_000_000,
        low_day_threshold=500_000, joiner_quota="prorated",
    )
    assert strict.expected_so_far == prorated.expected_so_far
    assert strict.off_by == prorated.off_by
    assert strict.daily_avg == prorated.daily_avg


def test_build_report_expected_so_far_strict_mode_scales_with_days_elapsed():
    member = _member([100_000_000, 102_000_000, 104_000_000])
    r = build_report(member, today=date(2026, 5, 2), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.expected_so_far == 2_000_000 * 2


def test_build_report_expected_so_far_prorated_mode_scales_with_days_in_club():
    # Joined day 2; days_in_club=1 at today=day 3.
    member = _member([-100_000_000, -100_000_000, 102_000_000])
    r = build_report(
        member, today=date(2026, 5, 3), quota_per_day=2_000_000,
        low_day_threshold=500_000, joiner_quota="prorated",
    )
    assert r.expected_so_far == 2_000_000 * 1


def test_build_report_expected_so_far_is_zero_when_no_data():
    member = _member([0, 0, 0, 0])
    r = build_report(member, today=date(2026, 5, 3), quota_per_day=2_000_000, low_day_threshold=500_000)
    assert r.days_elapsed == 0
    assert r.expected_so_far == 0


def test_build_report_cutoff_day_clips_to_earlier_day_than_today():
    # Member has data through day 4, but cutoff=2 should treat only days 1-2.
    member = _member([100_000_000, 102_000_000, 104_000_000, 106_000_000, 108_000_000])
    r = _build_report(
        member, today=date(2026, 5, 4), cutoff_day=2,
        quota_per_day=2_000_000, low_day_threshold=500_000,
    )
    assert r.days_elapsed == 2
    assert r.total == 4_000_000
    assert r.expected_so_far == 4_000_000
    assert r.latest_day_delta == 2_000_000


def test_build_report_cutoff_day_zero_returns_empty_report():
    member = _member([100_000_000, 102_000_000])
    r = _build_report(
        member, today=date(2026, 5, 1), cutoff_day=0,
        quota_per_day=2_000_000, low_day_threshold=500_000,
    )
    assert r.days_elapsed == 0
    assert r.total == 0
    assert r.expected_so_far == 0
    assert r.pill_tier == "no"


def test_current_game_day_returns_today_at_or_after_15_utc():
    assert current_game_day(datetime(2026, 5, 4, 15, 0, tzinfo=UTC)) == date(2026, 5, 4)
    assert current_game_day(datetime(2026, 5, 4, 23, 59, tzinfo=UTC)) == date(2026, 5, 4)


def test_current_game_day_returns_yesterday_before_15_utc():
    assert current_game_day(datetime(2026, 5, 4, 14, 59, tzinfo=UTC)) == date(2026, 5, 3)
    assert current_game_day(datetime(2026, 5, 4, 0, 0, tzinfo=UTC)) == date(2026, 5, 3)


def test_current_game_day_crosses_month_boundary():
    # 03:00 UTC on May 1 is still in April's game day 30.
    assert current_game_day(datetime(2026, 5, 1, 3, 0, tzinfo=UTC)) == date(2026, 4, 30)
    # 15:00 UTC on May 1 starts game day May 1.
    assert current_game_day(datetime(2026, 5, 1, 15, 0, tzinfo=UTC)) == date(2026, 5, 1)


def test_current_game_day_converts_non_utc_tz():
    # 00:30 JST on May 5 == 15:30 UTC on May 4 → game day May 4.
    jst = timezone(timedelta(hours=9))
    assert current_game_day(datetime(2026, 5, 5, 0, 30, tzinfo=jst)) == date(2026, 5, 4)


def test_current_game_day_rejects_naive_datetime():
    with pytest.raises(ValueError, match="tz-aware"):
        current_game_day(datetime(2026, 5, 4, 12, 0))
