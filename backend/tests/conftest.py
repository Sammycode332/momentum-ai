from dataclasses import dataclass
from typing import Literal

import pytest


@dataclass(frozen=True)
class TestPrincipal:
    subject: str
    access: Literal["user", "privileged"]


@pytest.fixture
def user_a() -> TestPrincipal:
    return TestPrincipal(subject="test-user-a", access="user")


@pytest.fixture
def user_b() -> TestPrincipal:
    return TestPrincipal(subject="test-user-b", access="user")


@pytest.fixture
def privileged_actor() -> TestPrincipal:
    return TestPrincipal(subject="test-privileged-actor", access="privileged")
