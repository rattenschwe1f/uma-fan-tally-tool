from uma_tally_tool.config import Config
from uma_tally_tool.compute import MemberReport
from uma_tally_tool.render.classic import _columns
from uma_tally_tool.render.classic import _sort_rows
from uma_tally_tool.render.classic import _status_color


def test_numbers_layout_keeps_original_expected_columns():
    cfg = Config(circle_id=1, expected_fans_style="numbers")

    columns = _columns(12, 500_000, cfg)

    assert [c.key for c in columns[:5]] == ["rank", "trainer", "expected", "total", "behind"]


def test_bar_layout_replaces_expected_columns_with_progress():
    cfg = Config(circle_id=1, expected_fans_style="bar")

    columns = _columns(12, 500_000, cfg)

    assert [c.key for c in columns[:4]] == ["rank", "trainer", "progress", "quota"]
    assert "expected" not in [c.key for c in columns]
    assert "total" not in [c.key for c in columns]
    assert "behind" not in [c.key for c in columns]


def test_bar_layout_reallocates_hidden_metric_width_to_progress():
    cfg = Config(
        circle_id=1,
        expected_fans_style="bar",
        show_daily_avg=False,
        show_needed_per_day=False,
        show_latest_day=False,
    )

    progress = next(c for c in _columns(12, 500_000, cfg) if c.key == "progress")

    assert progress.width == 330 + 150 + 150 + 140


def _report(name: str, total: int, staff_role: str | None = None, quota_total: int = 60_000_000) -> MemberReport:
    return MemberReport(
        viewer_id=total,
        trainer_name=name,
        days_elapsed=1,
        total=total,
        previous_total=total,
        daily_avg=total,
        expected_so_far=0,
        quota_total=quota_total,
        on_target=True,
        off_by=0,
        needed_per_day=0,
        low_days=0,
        latest_day_delta=total,
        join_day=1,
        pill_tier="yes",
        staff_role=staff_role,
    )


def test_pin_leader_sorts_leader_then_members():
    cfg = Config(circle_id=1, pin_leader=True)
    rows = [
        _report("Member", 9_000_000),
        _report("Officer", 1_000_000, "officer"),
        _report("Leader", 500_000, "leader"),
    ]

    assert [r.trainer_name for r in _sort_rows(rows, cfg)] == ["Leader", "Member", "Officer"]


def test_leader_sort_is_ignored_when_pin_leader_is_disabled():
    cfg = Config(circle_id=1, pin_leader=False)
    rows = [
        _report("Member", 9_000_000),
        _report("Officer", 1_000_000, "officer"),
        _report("Leader", 500_000, "leader"),
    ]

    assert [r.trainer_name for r in _sort_rows(rows, cfg)] == ["Member", "Officer", "Leader"]


def test_sort_rows_uses_percent_of_effective_quota():
    cfg = Config(circle_id=1)
    rows = [
        _report("More Fans Lower Percent", 20_000_000, quota_total=100_000_000),
        _report("Fewer Fans Higher Percent", 15_000_000, quota_total=30_000_000),
    ]

    assert [r.trainer_name for r in _sort_rows(rows, cfg)] == [
        "Fewer Fans Higher Percent",
        "More Fans Lower Percent",
    ]


def test_status_color_uses_shared_expected_ratio():
    cfg = Config(circle_id=1, on_pace_color=(1, 2, 3), finished_color=(4, 5, 6), off_pace_color=(7, 8, 9))

    assert _status_color(14, 100, 0.14, 0.22, cfg) == (7, 8, 9)
    assert _status_color(25, 100, 0.25, 0.22, cfg) == (1, 2, 3)
    assert _status_color(100, 100, 1.0, 0.22, cfg) == (4, 5, 6)
