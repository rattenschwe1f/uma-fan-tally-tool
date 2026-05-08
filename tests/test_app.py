from datetime import date

from uma_tally_tool.app import build_member_reports
from uma_tally_tool.config import Config
from uma_tally_tool.model import Circle, CircleResponse, Member


def _member(name: str, viewer_id: int, total: int) -> Member:
    return Member(
        viewer_id=viewer_id,
        trainer_name=name,
        year=2026,
        month=5,
        daily_fans=[100_000_000, 100_000_000 + total],
    )


def test_build_member_reports_marks_leader_by_api_leader_name():
    response = CircleResponse(
        circle=Circle(circle_id=1, name="Club", leader_name="Lead"),
        members=[
            _member("Member", 1, 2_000_000),
            _member("Lead", 2, 1_000_000),
        ],
    )

    reports = build_member_reports(response, Config(circle_id=1), date(2026, 5, 1))

    roles = {report.trainer_name: report.staff_role for report in reports}
    assert roles["Lead"] == "leader"
    assert roles["Member"] is None
