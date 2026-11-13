import os
from uuid import uuid4

import psycopg
import pytest


def test_postgres_goals_policies_enforce_ownership():
    url = os.getenv("GOALS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set GOALS_TEST_DATABASE_URL to an isolated, migrated test database.")

    owner, other = str(uuid4()), str(uuid4())
    goal_id = uuid4()
    try:
        with psycopg.connect(url) as connection:
            try:
                assert connection.execute(
                    "SELECT row_security_active('public.momentum_goals'::regclass)"
                ).fetchone() == (True,)
                connection.execute("SELECT set_config('momentum.user_id', %s, true)", (owner,))
                connection.execute(
                    "INSERT INTO public.momentum_goals (id, owner_id, title) VALUES (%s, %s, %s)",
                    (goal_id, owner, "Synthetic goal"),
                )
                assert connection.execute(
                    "SELECT id FROM public.momentum_goals WHERE id = %s", (goal_id,)
                ).fetchone() == (goal_id,)
                connection.execute("SELECT set_config('momentum.user_id', %s, true)", (other,))
                assert connection.execute(
                    "SELECT id FROM public.momentum_goals WHERE id = %s", (goal_id,)
                ).fetchone() is None
                with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
                    connection.execute(
                        "INSERT INTO public.momentum_goals (id, owner_id, title) VALUES (%s, %s, %s)",
                        (uuid4(), owner, "Spoofed goal"),
                    )
                try:
                    with connection.transaction():
                        result = connection.execute(
                            "UPDATE public.momentum_goals SET title = %s WHERE id = %s",
                            ("Spoofed update", goal_id),
                        )
                        assert result.rowcount == 0
                except psycopg.errors.InsufficientPrivilege:
                    pass
                connection.execute("SELECT set_config('momentum.user_id', '', true)")
                assert connection.execute(
                    "SELECT id FROM public.momentum_goals WHERE id = %s", (goal_id,)
                ).fetchone() is None
            finally:
                connection.rollback()
    except psycopg.Error:
        pytest.fail("PostgreSQL goals policy check failed. Verify the test migration and role.", pytrace=False)
