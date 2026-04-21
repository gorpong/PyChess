"""MatchService behavioural tests.

Runs against every registered repository implementation via the
parametrized `service` fixture in `conftest.py`. The SQLAlchemy repo
must be indistinguishable from the in-memory repo at this layer.
"""

import random

import pytest

from pychess.match import (
    IllegalMatchMove,
    InMemoryMatchRepository,
    InviteCodeExhausted,
    Match,
    MatchFull,
    MatchNotActive,
    MatchNotFound,
    MatchService,
    MatchStatus,
    NotInMatch,
    NotYourTurn,
    PromotionPending,
    SeatChoice,
)
from pychess.model.board import Board
from pychess.model.piece import Color, Piece
from pychess.model.square import Square
from pychess.rules.move import Move


def sq(s: str) -> Square:
    return Square.from_algebraic(s)


def move(frm: str, to: str, promotion: Piece | None = None) -> Move:
    return Move(from_square=sq(frm), to_square=sq(to), promotion=promotion)


def _white_pawn_on_e7_match(service: MatchService) -> Match:
    """Set up a match with both players seated and a white pawn one step from promotion.

    Bypasses the engine's move generation to reach the position directly, then
    persists via the repository so the custom state survives a refetch — which
    is what happens inside the service on the very next call.
    """
    created = service.create_match("alice", SeatChoice.WHITE)
    service.join(created.invite_code, "bob")
    # Refetch so we don't overwrite the ACTIVE status set by join when we save.
    match = service.get_match(created.match_id)

    board = Board.empty()
    board = board.set(sq("e1"), Piece.KING, Color.WHITE)
    board = board.set(sq("a8"), Piece.KING, Color.BLACK)
    board = board.set(sq("e7"), Piece.PAWN, Color.WHITE)
    match.game_state = match.game_state.with_board(board)
    service._repo.save(match)
    return match


# -------------------- creation --------------------


class TestCreateMatch:
    def test_creator_seated_on_white_when_requested(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)

        assert match.white_player_id == "alice"
        assert match.black_player_id is None
        assert match.status == MatchStatus.WAITING
        assert match.invite_code  # non-empty
        assert match.game_state.active_color == Color.WHITE  # standard initial pos

    def test_creator_seated_on_black_when_requested(self, service):
        match = service.create_match("alice", SeatChoice.BLACK)

        assert match.black_player_id == "alice"
        assert match.white_player_id is None

    def test_random_seat_respects_rng(self):
        # Seed chosen so choice([WHITE, BLACK]) is deterministic for this test.
        svc = MatchService(InMemoryMatchRepository(), rng=random.Random(0))

        match = svc.create_match("alice", SeatChoice.RANDOM)
        seat = match.seat_of("alice")

        assert seat in (Color.WHITE, Color.BLACK)
        # Unseated side is empty.
        assert match.open_seat() is not None
        assert match.open_seat() != seat

    def test_random_over_many_matches_fills_both_sides(self):
        """Across many creations, RANDOM should produce both colors."""
        svc = MatchService(InMemoryMatchRepository(), rng=random.Random(1))
        seats = {
            svc.create_match(f"player-{i}", SeatChoice.RANDOM).seat_of(f"player-{i}")
            for i in range(20)
        }
        assert seats == {Color.WHITE, Color.BLACK}

    def test_default_seat_choice_is_random(self, service):
        # No explicit seat_choice argument.
        match = service.create_match("alice")
        assert match.seat_of("alice") in (Color.WHITE, Color.BLACK)


# -------------------- invite codes --------------------


class TestInviteCodes:
    def test_invite_codes_are_unique_across_matches(self, service):
        codes = {
            service.create_match(f"p{i}", SeatChoice.WHITE).invite_code
            for i in range(50)
        }
        assert len(codes) == 50

    def test_collision_retries_until_fresh_code(self):
        # Deterministic collision-then-success sequence.
        sequence = iter(["DUPL1234", "DUPL1234", "UNIQUE01"])

        repo = InMemoryMatchRepository()
        svc = MatchService(repo, code_generator=lambda: next(sequence))
        first = svc.create_match("alice", SeatChoice.WHITE)
        second = svc.create_match("bob", SeatChoice.WHITE)

        assert first.invite_code == "DUPL1234"
        assert second.invite_code == "UNIQUE01"

    def test_exhausted_retries_raise(self):
        # Always produce the same code; first one lands, subsequent creations fail.
        svc = MatchService(InMemoryMatchRepository(), code_generator=lambda: "STATIC00")
        svc.create_match("alice", SeatChoice.WHITE)

        with pytest.raises(InviteCodeExhausted):
            svc.create_match("bob", SeatChoice.WHITE)


# -------------------- joining --------------------


class TestJoin:
    def test_joiner_takes_open_seat_and_activates_match(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)

        joined = service.join(match.invite_code, "bob")

        assert joined.white_player_id == "alice"
        assert joined.black_player_id == "bob"
        assert joined.status == MatchStatus.ACTIVE

    def test_joiner_takes_open_seat_when_creator_is_black(self, service):
        match = service.create_match("alice", SeatChoice.BLACK)

        joined = service.join(match.invite_code, "bob")

        assert joined.white_player_id == "bob"
        assert joined.black_player_id == "alice"

    def test_join_with_bad_code_raises(self, service):
        with pytest.raises(MatchNotFound):
            service.join("NOPE0000", "bob")

    def test_third_joiner_rejected(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        with pytest.raises(MatchFull):
            service.join(match.invite_code, "carol")

    def test_creator_cannot_claim_both_seats(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        # Rejoining by the seated player is idempotent; it does NOT claim the other seat.
        rejoined = service.join(match.invite_code, "alice")

        assert rejoined.black_player_id is None
        assert rejoined.status == MatchStatus.WAITING

    def test_rejoin_by_seated_player_is_idempotent(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        # bob refreshes the page — rejoining should not error or mutate seats.
        again = service.join(match.invite_code, "bob")

        assert again.white_player_id == "alice"
        assert again.black_player_id == "bob"


# -------------------- submit_move authorization --------------------


class TestSubmitMoveAuthorization:
    def test_correct_seat_on_turn_accepted(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        after = service.submit_move(match.match_id, "alice", move("e2", "e4"))

        assert after.game_state.active_color == Color.BLACK
        # Verify the board actually changed.
        assert after.game_state.board.get(sq("e4")) is not None

    def test_opponent_cannot_move_on_players_turn(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        with pytest.raises(NotYourTurn):
            service.submit_move(match.match_id, "bob", move("e7", "e5"))

    def test_stranger_cannot_submit_moves(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        with pytest.raises(NotInMatch):
            service.submit_move(match.match_id, "eve", move("e2", "e4"))

    def test_cannot_move_before_second_player_joins(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)

        with pytest.raises(MatchNotActive):
            service.submit_move(match.match_id, "alice", move("e2", "e4"))

    def test_match_not_found_for_bogus_id(self, service):
        with pytest.raises(MatchNotFound):
            service.submit_move("bogus", "alice", move("e2", "e4"))

    def test_illegal_move_is_rejected(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        with pytest.raises(IllegalMatchMove):
            service.submit_move(match.match_id, "alice", move("e2", "e5"))


# -------------------- promotion flow --------------------


class TestPromotion:
    def test_promotion_without_piece_raises_pending(self, service):
        match = _white_pawn_on_e7_match(service)

        with pytest.raises(PromotionPending):
            service.submit_move(match.match_id, "alice", move("e7", "e8"))

        # The service should have parked the pending move.
        stored = service.get_match(match.match_id)
        assert stored.pending_promotion is not None
        assert stored.pending_promotion.from_square == sq("e7")

    def test_complete_promotion_applies_chosen_piece(self, service):
        match = _white_pawn_on_e7_match(service)
        with pytest.raises(PromotionPending):
            service.submit_move(match.match_id, "alice", move("e7", "e8"))

        after = service.complete_promotion(match.match_id, "alice", Piece.QUEEN)

        assert after.pending_promotion is None
        piece_info = after.game_state.board.get(sq("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.QUEEN

    def test_only_the_mover_can_complete_the_promotion(self, service):
        match = _white_pawn_on_e7_match(service)
        with pytest.raises(PromotionPending):
            service.submit_move(match.match_id, "alice", move("e7", "e8"))

        # It's still white to move, so bob (black) completing it is NotYourTurn.
        with pytest.raises(NotYourTurn):
            service.complete_promotion(match.match_id, "bob", Piece.QUEEN)

    def test_complete_promotion_with_no_pending_raises(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        with pytest.raises(IllegalMatchMove):
            service.complete_promotion(match.match_id, "alice", Piece.QUEEN)

    def test_direct_submit_with_promotion_piece_bypasses_pending(self, service):
        """If the client already knows the promotion piece, one call is enough."""
        match = _white_pawn_on_e7_match(service)

        after = service.submit_move(
            match.match_id, "alice", move("e7", "e8", promotion=Piece.KNIGHT)
        )

        assert after.pending_promotion is None
        piece_info = after.game_state.board.get(sq("e8"))
        assert piece_info is not None
        assert piece_info[0] == Piece.KNIGHT


# -------------------- game end --------------------


class TestGameEnd:
    def test_checkmate_flips_status_and_records_result(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        # Fool's mate: 1. f3 e5 2. g4 Qh4#
        service.submit_move(match.match_id, "alice", move("f2", "f3"))
        service.submit_move(match.match_id, "bob", move("e7", "e5"))
        service.submit_move(match.match_id, "alice", move("g2", "g4"))
        final = service.submit_move(match.match_id, "bob", move("d8", "h4"))

        assert final.status == MatchStatus.FINISHED
        assert final.result == "0-1"

    def test_cannot_move_after_match_finished(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")
        service.submit_move(match.match_id, "alice", move("f2", "f3"))
        service.submit_move(match.match_id, "bob", move("e7", "e5"))
        service.submit_move(match.match_id, "alice", move("g2", "g4"))
        service.submit_move(match.match_id, "bob", move("d8", "h4"))

        with pytest.raises(MatchNotActive):
            service.submit_move(match.match_id, "alice", move("e2", "e4"))


# -------------------- resign --------------------


class TestResign:
    def test_white_resigns_gives_black_the_win(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        after = service.resign(match.match_id, "alice")

        assert after.status == MatchStatus.ABANDONED
        assert after.result == "0-1"

    def test_black_resigns_gives_white_the_win(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        after = service.resign(match.match_id, "bob")

        assert after.status == MatchStatus.ABANDONED
        assert after.result == "1-0"

    def test_non_participant_cannot_resign(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")

        with pytest.raises(NotInMatch):
            service.resign(match.match_id, "eve")

    def test_cannot_resign_finished_match(self, service):
        match = service.create_match("alice", SeatChoice.WHITE)
        service.join(match.invite_code, "bob")
        service.resign(match.match_id, "alice")

        with pytest.raises(MatchNotActive):
            service.resign(match.match_id, "alice")

    def test_resign_before_join_deletes_the_match(self, service):
        """Creator abandons a match no one joined yet — the invite should die with it."""
        match = service.create_match("alice", SeatChoice.WHITE)

        result = service.resign(match.match_id, "alice")

        assert result is None
        with pytest.raises(MatchNotFound):
            service.get_match(match.match_id)
        with pytest.raises(MatchNotFound):
            service.get_by_invite(match.invite_code)

    def test_late_joiner_to_abandoned_waiting_match_gets_not_found(self, service):
        """Invite code becomes dead once the creator resigns while WAITING."""
        match = service.create_match("alice", SeatChoice.WHITE)
        service.resign(match.match_id, "alice")

        with pytest.raises(MatchNotFound):
            service.join(match.invite_code, "bob")


# -------------------- read helpers --------------------


class TestReads:
    def test_get_match_returns_saved(self, service):
        created = service.create_match("alice", SeatChoice.WHITE)

        again = service.get_match(created.match_id)

        assert again.match_id == created.match_id

    def test_get_match_missing_raises(self, service):
        with pytest.raises(MatchNotFound):
            service.get_match("nope")

    def test_get_by_invite(self, service):
        created = service.create_match("alice", SeatChoice.WHITE)
        fetched = service.get_by_invite(created.invite_code)
        assert fetched.match_id == created.match_id

    def test_get_by_invite_missing_raises(self, service):
        with pytest.raises(MatchNotFound):
            service.get_by_invite("NOPE0000")
