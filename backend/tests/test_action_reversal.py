from datetime import date, datetime, UTC, timedelta
from unittest.mock import Mock
from uuid import uuid4
import pytest
from app.actions import Proposal, restore_deadline
from app.api_errors import ApiError


@pytest.mark.parametrize('changed', ['date', 'version', None])
def test_deadline_undo_preserves_later_changes(changed):
    applied = datetime(2026, 11, 14, tzinfo=UTC)
    proposal = Proposal(kind='reschedule_task', title='Synthetic task', reason='User approved',
                        target_id=uuid4(), due_date=date(2026, 12, 2), previous_due_date=None)
    cursor = Mock()
    cursor.execute.return_value.fetchone.return_value = {
        'due_date': date(2026, 12, 3) if changed == 'date' else proposal.due_date,
        'updated_at': applied + timedelta(seconds=1) if changed == 'version' else applied,
    }
    if changed:
        with pytest.raises(ApiError) as failure:
            restore_deadline(cursor, 'synthetic-owner', proposal, applied)
        assert failure.value.code == 'TARGET_CHANGED'
        assert cursor.execute.call_count == 1
    else:
        restore_deadline(cursor, 'synthetic-owner', proposal, applied)
        sql, params = cursor.execute.call_args.args
        assert 'WHERE id=%s AND owner_id=%s' in sql
        assert params == (None, proposal.target_id, 'synthetic-owner')
