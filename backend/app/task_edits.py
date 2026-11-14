"""Validated single-field edits for existing tasks."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.api_errors import ApiError
from app.private_store import require_row
from app.records import TaskInput, write_record_update

EditField = Literal["title", "status", "priority", "due_date"]
TASK_EDIT_FIELDS = "id, title, status, priority, due_date, updated_at"


class TaskEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: EditField
    value: str
    previous: str | None = None
    version: datetime | None = None

    def validated_value(self):
        return getattr(TaskInput.model_validate({"title": "Task", self.field: self.value}), self.field)

    @model_validator(mode="after")
    def validate_value(self):
        self.value = str(self.validated_value())
        return self


def task_edit_snapshot(cursor, owner, target_id, *, lock=False):
    suffix = " FOR UPDATE" if lock else ""
    return require_row(cursor.execute(
        f"SELECT {TASK_EDIT_FIELDS} FROM public.momentum_tasks WHERE owner_id = %s AND id = %s{suffix}",
        (owner, target_id),
    ).fetchone())


def edit_baseline(edit, task):
    old = task[edit.field]
    if old == edit.validated_value():
        raise ApiError(409, "TASK_UNCHANGED", "The task already has that value.")
    return edit.model_copy(update={"previous": str(old) if old is not None else None, "version": task["updated_at"]})


def apply_task_edit(cursor, owner, target_id, title, edit):
    task = task_edit_snapshot(cursor, owner, target_id, lock=True)
    old = task[edit.field]
    if (edit.version is None or task["updated_at"] != edit.version or task["title"] != title
            or (str(old) if old is not None else None) != edit.previous):
        raise ApiError(409, "TARGET_CHANGED", "The task changed after review. Reject this proposal and ask for a new one.")
    return require_row(write_record_update(
        cursor, "momentum_tasks", owner, target_id, {edit.field: edit.validated_value()},
    ))["id"]
