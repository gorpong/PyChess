"""Shared fixtures for match tests.

The `service` fixture is parametrized over both repository implementations
so every behavioural test runs against both. This is the test gate that
proves the SQLAlchemy repo is behaviourally equivalent to the in-memory one.
"""

import random

import pytest

from pychess.match import (
    InMemoryMatchRepository,
    MatchService,
    SqlAlchemyMatchRepository,
)


@pytest.fixture(params=["memory", "sqlalchemy"])
def service(request):
    """Yield a `MatchService` backed by each repository in turn.

    Tests receive a fresh, empty repo every time. The deterministic RNG
    seed makes the `SeatChoice.RANDOM` path stable across runs.
    """
    if request.param == "memory":
        repo = InMemoryMatchRepository()
    else:
        repo = SqlAlchemyMatchRepository.from_url("sqlite://", create_schema=True)

    yield MatchService(repo, rng=random.Random(42))
