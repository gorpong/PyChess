"""Exception hierarchy for match-service operations.

Each exception corresponds to a user-visible failure mode that the
transport layer (HTTP routes, WebSocket handlers) translates into an HTTP
status or socket `error` event. Keeping them as typed classes rather than
ValueError strings lets the transport layer pattern-match cleanly.
"""


class MatchError(Exception):
    """Base class for all match-service failures."""


class MatchNotFound(MatchError):
    """Lookup failed: no match exists with the given id or invite code."""


class MatchFull(MatchError):
    """Both seats are already claimed; no room for another joiner."""


class InviteCodeExhausted(MatchError):
    """Unable to produce a unique invite code after many retries.

    Signals a pathological collision rate or a broken RNG; defensive only.
    """


class NotInMatch(MatchError):
    """The requesting player is not seated in this match."""


class NotYourTurn(MatchError):
    """The player is in the match but it is not their turn to move."""


class MatchNotActive(MatchError):
    """The match is not in ACTIVE status (still waiting, or already finished)."""


class IllegalMatchMove(MatchError):
    """The move was rejected by the shared game controller.

    Carries the controller's reason string so routes/sockets can surface it.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class PromotionPending(MatchError):
    """A move was submitted that resolves to a promotion and no piece was chosen.

    Not strictly an error — callers catch this to prompt the player and then
    retry via `MatchService.complete_promotion`. Modeled as an exception so
    the happy-path return type of `submit_move` stays clean.
    """
