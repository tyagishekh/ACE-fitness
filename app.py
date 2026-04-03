from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any, Dict, List, cast, Union

from flask import Flask, jsonify, request


PROGRAM_CATALOG: Dict[str, Dict[str, Union[str, int]]] = {
    "fat-loss": {
        "name": "Fat Loss Foundation",
        "days_per_week": 4,
        "focus": "Conditioning, calorie control, and progressive overload",
        "calorie_multiplier": 24,
    },
    "muscle-gain": {
        "name": "Muscle Gain Builder",
        "days_per_week": 5,
        "focus": "Hypertrophy, strength blocks, and recovery tracking",
        "calorie_multiplier": 33,
    },
    "general-fitness": {
        "name": "General Fitness Starter",
        "days_per_week": 3,
        "focus": "Movement quality, mobility, and sustainable habits",
        "calorie_multiplier": 28,
    },
}


@dataclass
class Member:
    id: int
    name: str
    age: int
    weight_kg: float
    goal: str
    adherence_score: int
    membership_status: str

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["recommended_calories"] = recommend_calories(self.weight_kg, self.goal)
        payload["program"] = PROGRAM_CATALOG[self.goal]
        return payload


def recommend_calories(weight_kg: float, goal: str) -> int:
    if goal not in PROGRAM_CATALOG:
        raise ValueError(f"Unsupported goal '{goal}'")
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero")
    multiplier = int(PROGRAM_CATALOG[goal]["calorie_multiplier"])
    return round(weight_kg * multiplier)


def validate_member_payload(payload: Dict[str, object]) -> Dict[str, object]:
    required_fields = {"name", "age", "weight_kg", "goal", "adherence_score"}
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    name = str(payload["name"]).strip()
    if not name:
        raise ValueError("Name cannot be empty")

    try:
        age = int(cast(Any, payload["age"]))
        adherence_score = int(cast(Any, payload["adherence_score"]))
        weight_kg = float(cast(Any, payload["weight_kg"]))
    except (TypeError, ValueError) as exc:
        raise ValueError("Age, weight_kg, and adherence_score must be numeric") from exc

    goal = str(payload["goal"]).strip()
    if goal not in PROGRAM_CATALOG:
        raise ValueError(f"Goal must be one of: {', '.join(PROGRAM_CATALOG)}")

    if age < 14:
        raise ValueError("Age must be 14 or above")
    if not 0 <= adherence_score <= 100:
        raise ValueError("Adherence score must be between 0 and 100")
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero")

    membership_status = str(payload.get("membership_status", "active")).strip().lower()
    if membership_status not in {"active", "inactive"}:
        raise ValueError("Membership status must be 'active' or 'inactive'")

    return {
        "name": name,
        "age": age,
        "weight_kg": weight_kg,
        "goal": goal,
        "adherence_score": adherence_score,
        "membership_status": membership_status,
    }


class GymService:
    def __init__(self) -> None:
        self._members: List[Member] = [
            Member(
                id=1,
                name="Ananya Sharma",
                age=27,
                weight_kg=62.0,
                goal="fat-loss",
                adherence_score=88,
                membership_status="active",
            ),
            Member(
                id=2,
                name="Rohit Mehta",
                age=31,
                weight_kg=78.5,
                goal="muscle-gain",
                adherence_score=91,
                membership_status="active",
            ),
        ]
        self._next_id = 3

    def list_members(self) -> List[Dict[str, object]]:
        return [member.to_dict() for member in self._members]

    def add_member(self, payload: Dict[str, object]) -> Dict[str, object]:
        data = validate_member_payload(payload)
        # Generate a unique ID by finding the max existing ID and adding 1
        next_id = max((member.id for member in self._members), default=0) + 1

        member_name = cast(str, data["name"])
        member_age = cast(int, data["age"])
        member_weight = cast(float, data["weight_kg"])
        member_goal = cast(str, data["goal"])
        member_adherence = cast(int, data["adherence_score"])
        member_status = cast(str, data["membership_status"])

        member = Member(
            id=next_id,
            name=member_name,
            age=member_age,
            weight_kg=member_weight,
            goal=member_goal,
            adherence_score=member_adherence,
            membership_status=member_status,
        )
        self._members.append(member)
        self._next_id = next_id + 1
        return member.to_dict()

    def get_member(self, member_id: int) -> Dict[str, object]:
        for member in self._members:
            if member.id == member_id:
                return member.to_dict()
        raise LookupError(f"Member with id {member_id} was not found")

    def get_dashboard_stats(self) -> Dict[str, object]:
        active_members = [member for member in self._members if member.membership_status == "active"]
        average_adherence = round(mean(member.adherence_score for member in self._members), 2)
        return {
            "total_members": len(self._members),
            "active_members": len(active_members),
            "average_adherence": average_adherence,
            "goals_available": len(PROGRAM_CATALOG),
        }


def create_app() -> Flask:
    app = Flask(__name__)
    service = GymService()
    app.config["SERVICE"] = service

    @app.get("/")
    def index():
        return jsonify(
            {
                "application": "ACEest Fitness & Gym API",
                "status": "running",
                "available_endpoints": ["/health", "/programs", "/members", "/stats"],
            }
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    @app.get("/programs")
    def programs():
        return jsonify({"programs": PROGRAM_CATALOG})

    @app.get("/members")
    def list_members():
        return jsonify({"members": service.list_members()})

    @app.post("/members")
    def add_member():
        payload = request.get_json(silent=True) or {}
        try:
            member = service.add_member(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(member), 201

    @app.get("/members/<int:member_id>")
    def get_member(member_id: int):
        try:
            member = service.get_member(member_id)
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404
        return jsonify(member)

    @app.get("/stats")
    def stats():
        return jsonify(service.get_dashboard_stats())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
