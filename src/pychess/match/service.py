"""MatchService — authoritative orchestrator for networked multiplayer.

All writes to the match domain go through this service: creating, joining,
submitting moves, completing promotions, resigning. The service is the
single place that enforces seat authorization, so HTTP routes and
WebSocket handlers are thin transport-layer translators over this API.

The service is stateless; all state lives in a `MatchRepository`. Swapping
the in-memory repo for a database-backed one requires no changes here.
"""

import random
import secrets
from typing import Callable, Optional

from pychess.controller.game_controller import GameController
from pychess.match.errors import (
    IllegalMatchMove,
    InviteCodeExhausted,
    MatchFull,
    MatchNotActive,
    MatchNotFound,
    NotInMatch,
    NotYourTurn,
    PromotionPending,
)
from pychess.match.invite_code import generate_invite_code
from pychess.match.models import Match, MatchStatus, SeatChoice
from pychess.match.repository import MatchRepository
from pychess.model.game_state import GameState
from pychess.model.piece import Color, Piece
from pychess.rules.move import Move

_MAX_INVITE_RETRIES = 32


class MatchService:
    def __init__(
        self,
        repository: MatchRepository,
        controller: Optional[GameController] = None,
        *,
        rng: Optional[random.Random] = None,
        code_generator: Callable[[], str] = generate_invite_code,
    ) -> None:
        """Create a service wired to a repository.

        Args:
            repository: persistence for `Match` aggregates.
            controller: shared rule-application controller; a fresh one is
                created when omitted.
            rng: seedable RNG used only for `SeatChoice.RANDOM`; tests inject
                a deterministic instance. Defaults to `random.SystemRandom()`.
            code_generator: override hook for invite-code collision tests.
        """
        self._repo = repository
        self._controller = controller or GameController()
        self._rng = rng or random.SystemRandom()
        self._code_generator = code_generator

    # -------------------- creation & joining --------------------

    def create_match(
        self,
        creator_player_id: str,
        seat_choice: SeatChoice = SeatChoice.RANDOM,
    ) -> Match:
        """Create a new match with the creator seated on their chosen side.

        Seat choice is deliberate, not auto-assigned: the networked use-case
        is teaching-with-family, and always giving the creator White would
        force the opponent into only ever defending.
        """
        seat = seat_choice.to_color()
        if seat is None:
            seat = self._rng.choice([Color.WHITE, Color.BLACK])

        invite_code = self._allocate_invite_code()
        match = Match(
            match_id=secrets.token_urlsafe(16),
            invite_code=invite_code,
            game_state=GameState.initial(),
            status=MatchStatus.WAITING,
        )
        match.assign_seat(seat, creator_player_id)
        self._repo.save(match)
        return match

    def join(self, invite_code: str, joiner_player_id: str) -> Match:
        """Claim the open seat in the match identified by `invite_code`.

        Idempotent for the same player: calling join twice with the same
        player_id on the same code returns the existing match unchanged
        (the user refreshed the join page).
        """
        match = self._repo.get_by_invite(invite_code)
        if match is None:
            raise MatchNotFound(f"No match for invite code: {invite_code}")

        # Idempotent rejoin by the seated player.
        if match.seat_of(joiner_player_id) is not None:
            return match

        open_seat = match.open_seat()
        if open_seat is None:
            raise MatchFull("This match already has two players")

        match.assign_seat(open_seat, joiner_player_id)
        match.status = MatchStatus.ACTIVE
        match.touch()
        self._repo.save(match)
        return match

    # -------------------- move submission --------------------

    def submit_move(
        self,
        match_id: str,
        player_id: str,
        move: Move,
    ) -> Match:
        """Authorize and apply a move from `player_id`.

        Raises:
            MatchNotFound: no match with `match_id`.
            NotInMatch: `player_id` is not seated in the match.
            MatchNotActive: the match isn't in ACTIVE status.
            NotYourTurn: it is the other seat's turn to move.
            IllegalMatchMove: the move was rejected by the game controller.
            PromotionPending: the from/to pair is a promotion and `move`
                has no promotion piece. Call `complete_promotion` next.
        """
        match = self._require_match(match_id)
        self._require_active(match)
        seat = self._require_seat(match, player_id)
        self._require_turn(match, seat)

        outcome = self._controller.apply_from_to(
            match.game_state,
            move.from_square,
            move.to_square,
            promotion=move.promotion,
        )

        if outcome.promotion_required:
            # Park the pending move; only the mover can resolve it.
            match.pending_promotion = move
            match.touch()
            self._repo.save(match)
            raise PromotionPending()

        if outcome.illegal:
            raise IllegalMatchMove(outcome.illegal.reason)

        self._commit_outcome(match, outcome)
        self._repo.save(match)
        return match

    def complete_promotion(
        self,
        match_id: str,
        player_id: str,
        promotion: Piece,
    ) -> Match:
        """Resolve a pending promotion with the chosen piece.

        Authorization and turn checks are re-applied; a promotion choice from
        a player who is no longer on the active seat is rejected.
        """
        match = self._require_match(match_id)
        self._require_active(match)
        seat = self._require_seat(match, player_id)
        self._require_turn(match, seat)

        if match.pending_promotion is None:
            raise IllegalMatchMove("No promotion pending")

        pending = match.pending_promotion
        outcome = self._controller.apply_from_to(
            match.game_state,
            pending.from_square,
            pending.to_square,
            promotion=promotion,
        )
        if outcome.illegal:
            raise IllegalMatchMove(outcome.illegal.reason)
        if outcome.promotion_required:
            # Should not happen: a concrete piece was supplied.
            raise IllegalMatchMove("Promotion could not be completed")

        match.pending_promotion = None
        self._commit_outcome(match, outcome)
        self._repo.save(match)
        return match

    def resign(self, match_id: str, player_id: str) -> Optional[Match]:
        """Record a resignation.

        If the match is ACTIVE (both seats filled), the opposing seat wins
        and the match flips to ABANDONED. If the creator resigns while still
        WAITING for a second player, the match is deleted outright — there
        is no opponent to award the win to, and a stale invite code should
        not remain live. In that case the return value is None.
        """
        match = self._require_match(match_id)
        seat = self._require_seat(match, player_id)

        if match.status == MatchStatus.WAITING:
            self._repo.delete(match.match_id)
            return None

        if match.status != MatchStatus.ACTIVE:
            raise MatchNotActive(f"Cannot resign a {match.status.value} match")

        match.result = "0-1" if seat == Color.WHITE else "1-0"
        match.status = MatchStatus.ABANDONED
        match.pending_promotion = None
        match.touch()
        self._repo.save(match)
        return match

    # -------------------- read path --------------------

    def get_match(self, match_id: str) -> Match:
        """Fetch a match by id. Raises `MatchNotFound` on miss."""
        return self._require_match(match_id)

    def get_by_invite(self, invite_code: str) -> Match:
        match = self._repo.get_by_invite(invite_code)
        if match is None:
            raise MatchNotFound(f"No match for invite code: {invite_code}")
        return match

    # -------------------- internals --------------------

    def _require_match(self, match_id: str) -> Match:
        match = self._repo.get(match_id)
        if match is None:
            raise MatchNotFound(f"No match with id: {match_id}")
        return match

    @staticmethod
    def _require_active(match: Match) -> None:
        if match.status != MatchStatus.ACTIVE:
            raise MatchNotActive(f"Match is {match.status.value}")

    @staticmethod
    def _require_seat(match: Match, player_id: str) -> Color:
        seat = match.seat_of(player_id)
        if seat is None:
            raise NotInMatch(f"Player {player_id} is not in match {match.match_id}")
        return seat

    @staticmethod
    def _require_turn(match: Match, seat: Color) -> None:
        if match.game_state.active_color != seat:
            raise NotYourTurn(f"It is {match.game_state.active_color.value} to move")

    def _commit_outcome(self, match: Match, outcome) -> None:
        """Apply a successful `MoveOutcome` to `match`."""
        match.game_state = outcome.state
        match.pending_promotion = None
        if outcome.game_over:
            match.status = MatchStatus.FINISHED
            match.result = outcome.game_over.result
        match.touch()

    def _allocate_invite_code(self) -> str:
        for _ in range(_MAX_INVITE_RETRIES):
            code = self._code_generator()
            if not self._repo.invite_code_exists(code):
                return code
        raise InviteCodeExhausted(
            f"Could not allocate a unique invite code after {_MAX_INVITE_RETRIES} attempts"
        )
