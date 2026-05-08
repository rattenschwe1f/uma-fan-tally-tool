from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


StaffRole = Literal["leader", "officer"]


class Circle(BaseModel):
    circle_id: int
    name: str
    monthly_rank: int | None = None
    leader_name: str | None = None


class Member(BaseModel):
    viewer_id: int
    trainer_name: str
    year: int
    month: int
    daily_fans: list[int] = Field(default_factory=list)
    staff_role: StaffRole | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_staff_role(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("staff_role"):
            return data

        role = _staff_role_from_mapping(data)
        if role is not None:
            data = dict(data)
            data["staff_role"] = role
        return data


class CircleResponse(BaseModel):
    circle: Circle
    members: list[Member]
    club_rank: int | None = None
    leader_name: str | None = None


def circle_leader_name(response: CircleResponse) -> str | None:
    return response.leader_name or response.circle.leader_name


def _staff_role_from_mapping(data: dict[str, Any]) -> StaffRole | None:
    leader_flags = ("is_leader", "leader", "is_owner", "owner")
    officer_flags = ("is_officer", "officer", "is_subleader", "subleader", "sub_leader")
    if any(data.get(key) is True for key in leader_flags):
        return "leader"
    if any(data.get(key) is True for key in officer_flags):
        return "officer"

    text_fields = (
        "role",
        "club_role",
        "circle_role",
        "member_role",
        "position",
        "club_position",
        "circle_position",
        "member_type",
    )
    for key in text_fields:
        value = data.get(key)
        if isinstance(value, str):
            normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
            if normalized in {"leader", "owner", "captain", "circle_leader", "club_leader"}:
                return "leader"
            if normalized in {"officer", "subleader", "sub_leader", "vice_leader", "deputy", "admin"}:
                return "officer"
        elif isinstance(value, int):
            if "role" in key:
                if value == 1:
                    return "leader"
                if value == 2:
                    return "officer"

    return None
