from datetime import UTC, date, datetime, time
from contextlib import contextmanager, nullcontext
from unittest.mock import Mock
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.chat_reminders import local_instant
from app.reminder_worker import next_daily
import pytest

from app import push, push_worker
from app.api_errors import ApiError
from app.auth import AuthenticatedPrincipal


def test_local_reminder_time_rejects_dst_gaps_and_folds():
    zone = ZoneInfo("America/New_York")
    assert local_instant(date(2026, 3, 8), time(2, 30), zone) is None
    assert local_instant(date(2026, 11, 1), time(1, 30), zone) is None
    assert local_instant(date(2026, 11, 2), time(18), zone).hour == 23
    assert local_instant(date(2026, 11, 2), time(18), zone).tzinfo is UTC


def test_daily_reminder_skips_a_nonexistent_time_without_drifting():
    due = datetime(2026, 3, 7, 7, 30, tzinfo=UTC)
    assert next_daily(due, due, "America/New_York") == datetime(2026, 3, 9, 6, 30, tzinfo=UTC)


def test_push_dispatch_skips_rescheduled_occurrences_and_retries_transient_failure(monkeypatch):
    now = datetime(2026, 11, 14, 18, tzinfo=UTC)
    base = dict(notification_id=uuid4(), subscription_id=uuid4(), owner_id="owner",
                created_at=now, state="unread", reminder_status="scheduled",
                reminder_occurrence=2, repeat="none", occurrence=1,
                enabled=True, device_expired=False, timezone="Africa/Lagos", quiet_start=0, quiet_end=0, attempts=0)
    current = dict(base, notification_id=uuid4(), occurrence=2)
    cursor = Mock()
    cursor.execute.return_value.fetchall.return_value = [base, current]
    connection = Mock()
    connection.cursor.return_value = nullcontext(cursor)
    monkeypatch.setattr(push_worker, "configuration", lambda: {"configured": True})
    send = Mock(return_value=503)
    monkeypatch.setattr(push_worker, "send", send)
    assert push_worker.dispatch_push(connection, now)["sent"] == 0
    send.assert_called_once_with(current, current["notification_id"])
    assert cursor.execute.call_args.args[1][:2] == ("pending", 1)
    send.return_value = 201
    cursor.execute.return_value.fetchall.return_value = [dict(current, attempts=1)]
    assert push_worker.dispatch_push(connection, now)["sent"] == 1
    assert cursor.execute.call_args.args[1][:2] == ("sent", 2)


@pytest.mark.parametrize(("provider_status", "failure"), [(201, None), (410, "SUBSCRIPTION_EXPIRED"),
                                                        (503, "PUSH_TEST_FAILED"), (None, "NO_PUSH_DEVICE")])
def test_device_push_test_uses_only_owned_subscription_and_reports_acceptance(monkeypatch, provider_status, failure):
    endpoint = push.Endpoint(endpoint="https://fcm.googleapis.com/fcm/send/fixture")
    subscription = {"endpoint": endpoint.endpoint, "p256dh": "fixture", "auth": "fixture"}
    notice_id = uuid4()
    cursor = Mock()
    cursor.execute.return_value.fetchone.side_effect = [subscription if provider_status else None, None]
    committed = False

    @contextmanager
    def storage(owner, *tables):
        nonlocal committed
        assert owner == "owner"
        yield cursor
        committed = True

    def send(row, notification_id):
        assert committed
        assert row == subscription and notification_id == notice_id
        return provider_status

    monkeypatch.setattr(push, "private_cursor", storage)
    monkeypatch.setattr(push, "configuration", lambda: {"configured": True})
    monkeypatch.setattr(push, "insert_test_notification", lambda *args: {"id": notice_id})
    sender = Mock(side_effect=send)
    monkeypatch.setattr(push, "send", sender)
    if failure:
        with pytest.raises(ApiError) as error:
            push.test_push(endpoint, AuthenticatedPrincipal("owner"))
        assert error.value.code == failure
    else:
        assert push.test_push(endpoint, AuthenticatedPrincipal("owner")) == {"id": notice_id, "accepted": True}
    assert cursor.execute.call_args_list[1].args[1] == ("owner", endpoint.endpoint)
    assert sender.call_count == (1 if provider_status else 0)
