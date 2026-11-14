from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app import goal_plans
from app.api_errors import ApiError


def test_goal_draft_resolves_calendar_months_using_browser_timezone(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz):
            return cls(2026, 8, 30, 23, 30, tzinfo=UTC)

    provider = Mock()
    provider.generate.return_value = '{"goal":{"title":"Build a portfolio","description":null,"target_date":null}}'
    monkeypatch.setattr(goal_plans, "get_planning_provider", lambda: provider)
    monkeypatch.setattr(goal_plans, "datetime", Clock)
    goal = goal_plans.draft_goal(None, "owner", "Create a goal to build a portfolio in six months.", "Africa/Lagos")
    assert goal.target_date.isoformat() == "2027-02-28"
    assert provider.generate.call_args.args[0]["today"] == "2026-08-31"


@pytest.mark.parametrize("roadmap", [False, True])
def test_draft_handles_clarification_malformed_output_and_provider_failure(monkeypatch, roadmap):
    provider = Mock()
    monkeypatch.setattr(goal_plans, "get_planning_provider", lambda: provider)
    monkeypatch.setattr(goal_plans, "personalization_enabled", lambda _: False)
    provider.generate.return_value = '{"roadmap": null}' if roadmap else '{"goal": null}'
    assert goal_plans.draft_goal(None, "owner", "Help me plan", "UTC", roadmap=roadmap) is None
    provider.generate.return_value = '{"reply":"Goal and tasks saved."}'
    with pytest.raises(ApiError) as error:
        goal_plans.draft_goal(None, "owner", "Help me plan", "UTC", roadmap=roadmap)
    assert error.value.code == "INVALID_GOAL_DRAFT"
    provider.generate.side_effect = ApiError(504, "AI_TIMEOUT", "Retry.")
    with pytest.raises(ApiError) as error:
        goal_plans.draft_goal(None, "owner", "Help me plan", "UTC", roadmap=roadmap)
    assert error.value.code == "AI_TIMEOUT"
