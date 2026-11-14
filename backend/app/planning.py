from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal, require_authenticated_principal
from app.planning_context import load_planning_context
from app.planning_provider import get_planning_provider

router = APIRouter(prefix="/api/v1/ai", tags=["planning"])
Principal = Annotated[AuthenticatedPrincipal, Depends(require_authenticated_principal)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
PlanText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=480)]


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    objective: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=800)]
    available_minutes: Annotated[int, Field(ge=5, le=480)]
    focus_area: ShortText | None = None


class Activity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: ShortText
    duration_minutes: Annotated[int, Field(ge=1, le=480)]
    reason: PlanText


class DraftActivity(Activity):
    task_ref: ShortText | None
    project_ref: ShortText | None


class PlanDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: ShortText
    summary: PlanText
    deadline_considerations: Annotated[list[PlanText], Field(max_length=5)]


class DraftPlan(PlanDetails):
    activities: Annotated[list[DraftActivity], Field(min_length=1, max_length=8)]


class RecordReference(BaseModel):
    id: UUID
    title: str


class PlannedActivity(Activity):
    task: RecordReference | None
    project: RecordReference | None


class Plan(PlanDetails):
    activities: list[PlannedActivity]
    total_minutes: int


def alias_context(context: dict[str, Any]) -> dict[str, dict[str, RecordReference]]:
    references: dict[str, dict[str, RecordReference]] = {"projects": {}, "tasks": {}}
    project_aliases = {}
    for domain, title_field, prefix in (("projects", "name", "P"), ("tasks", "title", "T")):
        for index, row in enumerate(context.get(domain, []), 1):
            alias = f"{prefix}{index}"
            record_id = row.pop("id")
            references[domain][alias] = RecordReference(id=record_id, title=row[title_field])
            row["ref"] = alias
            if domain == "projects":
                project_aliases[record_id] = alias
            else:
                project_ref = project_aliases.get(row.pop("project_id"))
                if project_ref:
                    row["project_ref"] = project_ref
    return references


def validate_plan(
    raw: str, minutes: int, references: dict[str, dict[str, RecordReference]],
) -> Plan:
    try:
        draft = DraftPlan.model_validate_json(raw)
        total = sum(item.duration_minutes for item in draft.activities)
        if total > minutes:
            raise ValueError("Time budget exceeded.")
        activities = [
            PlannedActivity(
                **item.model_dump(exclude={"task_ref", "project_ref"}),
                task=references["tasks"][item.task_ref] if item.task_ref is not None else None,
                project=references["projects"][item.project_ref] if item.project_ref is not None else None,
            )
            for item in draft.activities
        ]
        return Plan(**draft.model_dump(exclude={"activities"}), activities=activities, total_minutes=total)
    except (ValueError, KeyError):
        # Validation errors can contain private provider text.
        raise ApiError(502, "AI_INVALID_PLAN", "The planning service returned an invalid plan. Try again.") from None


@router.post("/plan")
def generate_plan(body: PlanRequest, principal: Principal, response: Response) -> Plan:
    response.headers["Cache-Control"] = "no-store"
    provider = get_planning_provider()
    context = load_planning_context(principal.subject)
    references = alias_context(context)
    raw = provider.generate(
        {"request": body.model_dump(exclude_none=True), "workspace": context},
        DraftPlan.model_json_schema(),
    )
    return validate_plan(raw, body.available_minutes, references)
