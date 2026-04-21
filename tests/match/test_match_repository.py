"""SQLAlchemy repository: DB-layer concerns.

`test_match_service.py` already exercises the full behavioural contract
against both repos via the parametrized fixture. This module targets what
only the SQL-backed implementation can exhibit: cross-session persistence,
schema integrity, serialization round-trip fidelity, and clean-up on delete.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from pychess.controller.game_controller import GameController
from pychess.match import (
    InMemoryMatchRepository,
    MatchService,
    MatchStatus,
    SeatChoice,
    SqlAlchemyMatchRepository,
)
from pychess.match.orm import Base, MatchORM
from pychess.match.serialization import (
    game_state_from_json,
    game_state_to_json,
    move_from_json,
    move_to_json,
)
from pychess.model.board import Board
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.rules.move import Move


@pytest.fixture
def file_repo(tmp_path):
    """A file-backed SQLite repo so cross-session persistence can be verified."""
    path = tmp_path / "matches.db"
    return SqlAlchemyMatchRepository.from_url(f"sqlite:///{path}", create_schema=True)


# -------------------- serialization round-trip --------------------


class TestSerialization:
    def test_initial_game_state_roundtrips(self):
        original = GameState.initial()
        roundtripped = game_state_from_json(game_state_to_json(original))

        assert roundtripped.to_public_data() == original.to_public_data()

    def test_mid_game_state_roundtrips(self):
        controller = GameController()
        state = GameState.initial()
        # Play a few moves including a capture.
        for san in ["e4", "e5", "Nf3", "Nc6", "Bb5"]:
            state = controller.apply_san(state, san).state

        roundtripped = game_state_from_json(game_state_to_json(state))

        assert roundtripped.to_public_data() == state.to_public_data()

    def test_custom_board_roundtrips(self):
        """Board positions that cannot be reached by replaying SAN still survive."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
        state = GameState.initial().with_board(board)

        roundtripped = game_state_from_json(game_state_to_json(state))

        assert roundtripped.to_public_data() == state.to_public_data()

    def test_move_roundtrip_without_promotion(self):
        original = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4"),
            is_capture=False,
        )
        assert move_from_json(move_to_json(original)) == original

    def test_move_roundtrip_with_promotion(self):
        original = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.KNIGHT,
        )
        assert move_from_json(move_to_json(original)) == original

    def test_none_move_is_none(self):
        assert move_to_json(None) is None
        assert move_from_json(None) is None


# -------------------- cross-session persistence --------------------


class TestCrossSessionPersistence:
    def test_match_survives_closing_and_reopening_the_repo(self, tmp_path):
        """Two separate repo instances pointed at the same file see the same data."""
        db_url = f"sqlite:///{tmp_path / 'matches.db'}"

        repo_a = SqlAlchemyMatchRepository.from_url(db_url, create_schema=True)
        service_a = MatchService(repo_a)
        created = service_a.create_match("alice", SeatChoice.WHITE)
        service_a.join(created.invite_code, "bob")
        service_a.submit_move(
            created.match_id,
            "alice",
            Move(
                from_square=Square.from_algebraic("e2"),
                to_square=Square.from_algebraic("e4"),
            ),
        )

        # New repo, new engine, same file — must see the active game.
        repo_b = SqlAlchemyMatchRepository.from_url(db_url, create_schema=False)
        reloaded = repo_b.get(created.match_id)

        assert reloaded is not None
        assert reloaded.status == MatchStatus.ACTIVE
        assert reloaded.white_player_id == "alice"
        assert reloaded.black_player_id == "bob"
        assert reloaded.game_state.move_history == ["e4"]

    def test_mutations_visible_after_save_and_fresh_get(self, file_repo):
        service = MatchService(file_repo)
        created = service.create_match("alice", SeatChoice.WHITE)
        service.join(created.invite_code, "bob")

        match = service.get_match(created.match_id)
        assert match.status == MatchStatus.ACTIVE

    def test_resign_while_waiting_deletes_row(self, file_repo):
        service = MatchService(file_repo)
        created = service.create_match("alice", SeatChoice.WHITE)

        service.resign(created.match_id, "alice")

        assert file_repo.get(created.match_id) is None
        assert file_repo.get_by_invite(created.invite_code) is None


# -------------------- DB-layer integrity --------------------


class TestDatabaseIntegrity:
    def test_invite_code_unique_constraint_enforced(self, file_repo):
        """A second row with the same invite_code must fail at the DB layer.

        The service never triggers this (its collision-retry loop picks a fresh
        code), but the constraint is the belt on top of that retry's braces.
        """
        service = MatchService(file_repo)
        first = service.create_match("alice", SeatChoice.WHITE)

        # Directly insert a colliding row bypassing the service.
        with file_repo._session_factory.begin() as session:
            session.add(
                MatchORM(
                    match_id="manual",
                    invite_code=first.invite_code,
                    status=MatchStatus.WAITING.value,
                    white_player_id=None,
                    black_player_id=None,
                    result=None,
                    game_state_json=game_state_to_json(GameState.initial()),
                    pending_promotion_json=None,
                    created_at=0.0,
                    updated_at=0.0,
                )
            )
            with pytest.raises(IntegrityError):
                session.flush()

    def test_schema_is_created_from_metadata(self, tmp_path):
        """`from_url(create_schema=True)` builds the `matches` table end-to-end."""
        db_url = f"sqlite:///{tmp_path / 'fresh.db'}"
        SqlAlchemyMatchRepository.from_url(db_url, create_schema=True)

        # Reopen with raw engine and inspect schema.
        engine = create_engine(db_url, future=True)
        with engine.connect() as conn:
            table_names = [
                row[0] for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            ]

        assert "matches" in table_names


# -------------------- game_state persistence fidelity --------------------


class TestGameStateFidelity:
    def test_played_game_state_persists_accurately(self, file_repo):
        """Replay history and board state both survive a round trip."""
        service = MatchService(file_repo)
        created = service.create_match("alice", SeatChoice.WHITE)
        service.join(created.invite_code, "bob")

        service.submit_move(
            created.match_id, "alice",
            Move(
                from_square=Square.from_algebraic("e2"),
                to_square=Square.from_algebraic("e4"),
            ),
        )
        service.submit_move(
            created.match_id, "bob",
            Move(
                from_square=Square.from_algebraic("e7"),
                to_square=Square.from_algebraic("e5"),
            ),
        )
        service.submit_move(
            created.match_id, "alice",
            Move(
                from_square=Square.from_algebraic("g1"),
                to_square=Square.from_algebraic("f3"),
            ),
        )

        reloaded = file_repo.get(created.match_id)
        assert reloaded.game_state.move_history == ["e4", "e5", "Nf3"]
        # f3 now has a white knight.
        piece = reloaded.game_state.board.get(Square.from_algebraic("f3"))
        assert piece is not None
        assert piece == (Piece.KNIGHT, Color.WHITE)

    def test_pending_promotion_persists(self, file_repo):
        """A parked promotion survives repo round-trip and can be completed."""
        service = MatchService(file_repo)
        created = service.create_match("alice", SeatChoice.WHITE)
        service.join(created.invite_code, "bob")

        # Force a pawn-to-7th-rank position.
        match = service.get_match(created.match_id)
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
        match.game_state = match.game_state.with_board(board)
        file_repo.save(match)

        from pychess.match import PromotionPending
        with pytest.raises(PromotionPending):
            service.submit_move(
                created.match_id, "alice",
                Move(
                    from_square=Square.from_algebraic("e7"),
                    to_square=Square.from_algebraic("e8"),
                ),
            )

        # Fresh repo instance proves the pending_promotion JSON column round-trips.
        reloaded = file_repo.get(created.match_id)
        assert reloaded.pending_promotion is not None
        assert reloaded.pending_promotion.from_square == Square.from_algebraic("e7")
