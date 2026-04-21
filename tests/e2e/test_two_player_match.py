"""External-process end-to-end test of a networked match.

These run against whatever server `PYCHESS_E2E_BASE_URL` points at —
a Docker Compose stack, a dev server, or a deployed instance. They are
the last line of defence before declaring a build shippable: they exercise
the HTTP surface, the SQLite persistence, Alembic migrations on fresh
containers, and the Socket.IO handshake, all from a separate process.

The detailed Socket.IO protocol tests live in `tests/web/test_match_socketio.py`
and run in-process. Here we just smoke-test that a handshake succeeds
and that initial state is pushed to the client — enough to prove the
external socket transport is wired up end-to-end.
"""

from __future__ import annotations

import pytest


class TestFullMatchOverHttp:
    def test_alice_and_bob_play_fools_mate_end_to_end(self, alice, bob):
        match_id = alice.create_match(seat="white")
        invite = alice.invite_code_for(match_id)
        bob.join(invite)

        # 1. f3 e5 2. g4 Qh4#
        alice.submit_move(match_id, "f2", "f3")
        bob.submit_move(match_id, "e7", "e5")
        alice.submit_move(match_id, "g2", "g4")
        bob.submit_move(match_id, "d8", "h4")

        # Both players see the finished match.
        alice_page = alice.match_page(match_id)
        bob_page = bob.match_page(match_id)
        for html in (alice_page, bob_page):
            assert "finished" in html.lower()
            assert "0-1" in html
            assert "Qh4" in html

    def test_seat_choice_reflected_in_both_browsers(self, alice, bob):
        """Alice picks Black; Bob joins as White; each browser orients its own way."""
        match_id = alice.create_match(seat="black")
        invite = alice.invite_code_for(match_id)
        bob.join(invite)

        assert 'data-viewer-seat="black"' in alice.match_page(match_id)
        assert 'data-viewer-seat="white"' in bob.match_page(match_id)

    def test_move_auth_rejects_wrong_seat(self, alice, bob):
        match_id = alice.create_match(seat="white")
        invite = alice.invite_code_for(match_id)
        bob.join(invite)

        # Bob tries to move White's pawn — must be a flash, not a 500.
        resp = bob.http.post(
            f"{bob.base_url}/match/{match_id}/move",
            data={"from": "e2", "to": "e4"},
            allow_redirects=True,
            timeout=5,
        )
        assert resp.status_code == 200
        # The flash message is the only legitimate "not your turn" signal.
        assert "not your turn" in resp.text.lower()
        # And no move was recorded: the Moves section (if present) must not list e4.
        page = alice.match_page(match_id)
        if "<h2>Moves</h2>" in page:
            moves_block = page.split("<h2>Moves</h2>", 1)[1]
            assert "e4" not in moves_block


class TestResignLifecycle:
    def test_resign_before_join_invalidates_invite(self, alice, bob):
        match_id = alice.create_match(seat="white")
        invite = alice.invite_code_for(match_id)

        # Alice bails before Bob arrives.
        resp = alice.http.post(
            f"{alice.base_url}/match/{match_id}/resign",
            allow_redirects=False,
            timeout=5,
        )
        assert resp.status_code == 302

        # Invite is now dead.
        join = bob.http.get(f"{bob.base_url}/match/join/{invite}", timeout=5)
        assert join.status_code == 404


class TestSocketIoHandshake:
    """Smoke test: external process can reach the /match namespace over WS.

    The in-process tests already cover the full event protocol; here we
    only prove the handshake works through whatever reverse proxy /
    Docker networking layer the deployed server sits behind.
    """

    def test_connect_receives_initial_match_state(self, alice):
        import socketio

        match_id = alice.create_match(seat="white")
        received: list[tuple[str, dict]] = []

        sio = socketio.Client(reconnection=False)

        @sio.on("match_state", namespace="/match")
        def _on_state(payload):
            received.append(("match_state", payload))

        try:
            sio.connect(
                f"{alice.base_url}?match_id={match_id}",
                namespaces=["/match"],
                transports=["websocket"],
                wait=True,
                wait_timeout=10,
                headers={"Cookie": alice.cookie_header()},
            )
            # Small grace period for the server to emit the initial event.
            sio.sleep(0.5)
        finally:
            try:
                sio.disconnect()
            except Exception:
                pass

        state_events = [e for e in received if e[0] == "match_state"]
        assert state_events, "Expected match_state event after connect"
        payload = state_events[0][1]
        assert payload["match_id"] == match_id
        assert payload["your_seat"] == "white"


class TestPersistenceAcrossRequests:
    """Whatever database the server is using must persist through multiple requests."""

    def test_play_sequence_is_replayable_from_server(self, alice, bob):
        match_id = alice.create_match(seat="white")
        invite = alice.invite_code_for(match_id)
        bob.join(invite)

        alice.submit_move(match_id, "e2", "e4")
        bob.submit_move(match_id, "c7", "c5")
        alice.submit_move(match_id, "g1", "f3")

        # A fresh request from either player shows the full move list.
        page = alice.match_page(match_id)
        assert "e4" in page and "c5" in page and "Nf3" in page
