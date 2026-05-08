from uma_tally_tool.config import Config
from uma_tally_tool.compute import MemberReport
from uma_tally_tool.render.classic import _columns
from uma_tally_tool.render.classic import _sort_rows


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


def _report(name: str, total: int, staff_role: str | None = None) -> MemberReport:
    return MemberReport(
        viewer_id=total,
        trainer_name=name,
        days_elapsed=1,
        total=total,
        previous_total=total,
        daily_avg=total,
        expected_so_far=0,
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
