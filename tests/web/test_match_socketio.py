"""Socket.IO tests for the /match namespace.

Uses `flask_socketio.SocketIOTestClient` — no real server, no real network.
Auth piggy-backs on the Flask session cookie, so each client is built from
a paired HTTP test client that already went through `/match/new` or
`/match/join` to acquire the signed cookie.
"""

from __future__ import annotations

import pytest

from pychess.web.app import create_app


@pytest.fixture
def app(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'matches.db'}"
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "MATCH_DB_URL": db_url,
        "SERVER_NAME": "localhost.test",
    })
    return app


def _http_create(client, seat: str = "white") -> str:
    """Hit /match/new over HTTP so the session cookie is issued."""
    resp = client.post("/match/new", data={"seat": seat}, follow_redirects=False)
    assert resp.status_code == 302
    return resp.headers["Location"].rsplit("/", 1)[-1]


def _invite_code(client, match_id: str) -> str:
    import re
    html = client.get(f"/match/{match_id}").get_data(as_text=True)
    m = re.search(r"/match/join/([A-Z0-9]+)", html)
    assert m
    return m.group(1)


def _socket(app, http_client, match_id: str):
    """Open a Socket.IO connection on /match using an already-authenticated HTTP client."""
    return app.socketio.test_client(
        app,
        namespace="/match",
        query_string=f"match_id={match_id}",
        flask_test_client=http_client,
    )


# -------------------- connect --------------------


class TestConnect:
    def test_connect_emits_initial_match_state(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")

        alice_ws = _socket(app, alice_http, match_id)
        received = alice_ws.get_received("/match")

        state_events = [e for e in received if e["name"] == "match_state"]
        assert state_events, f"Expected match_state, got {[e['name'] for e in received]}"
        payload = state_events[0]["args"][0]
        assert payload["match_id"] == match_id
        assert payload["status"] == "waiting"
        assert payload["your_seat"] == "white"

    def test_connect_without_cookie_is_rejected(self, app):
        # No prior HTTP request → no cookie → no player_id.
        http_client = app.test_client()
        http_client.get("/")  # some GET that doesn't create a session cookie
        ws = _socket(app, http_client, "bogus")
        assert not ws.is_connected("/match")

    def test_connect_without_match_id_is_rejected(self, app):
        http = app.test_client()
        _http_create(http, seat="white")  # arm the cookie

        ws = app.socketio.test_client(app, namespace="/match", flask_test_client=http)
        assert not ws.is_connected("/match")

    def test_connect_to_unknown_match_rejected(self, app):
        http = app.test_client()
        _http_create(http, seat="white")
        ws = _socket(app, http, "does-not-exist")
        assert not ws.is_connected("/match")

    def test_non_member_cannot_connect_to_match(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")

        spectator_http = app.test_client()
        spectator_http.get("/match/")  # create a session cookie without seating

        ws = _socket(app, spectator_http, match_id)
        assert not ws.is_connected("/match")

    def test_second_player_triggers_opponent_connected_for_first(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")
        invite = _invite_code(alice_http, match_id)

        bob_http = app.test_client()
        bob_http.post(f"/match/join/{invite}")  # bob claims black, both seated now

        alice_ws = _socket(app, alice_http, match_id)
        alice_ws.get_received("/match")  # drain initial match_state

        bob_ws = _socket(app, bob_http, match_id)
        alice_inbox = alice_ws.get_received("/match")

        event_names = [e["name"] for e in alice_inbox]
        assert "opponent_connected" in event_names


# -------------------- move broadcast --------------------


class TestMoveBroadcast:
    def _both_connected(self, app):
        """Return (alice_http, bob_http, alice_ws, bob_ws, match_id)."""
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")
        invite = _invite_code(alice_http, match_id)
        bob_http = app.test_client()
        bob_http.post(f"/match/join/{invite}")

        alice_ws = _socket(app, alice_http, match_id)
        bob_ws = _socket(app, bob_http, match_id)
        alice_ws.get_received("/match")
        bob_ws.get_received("/match")
        return alice_http, bob_http, alice_ws, bob_ws, match_id

    def test_alice_move_reaches_bob(self, app):
        _, _, alice_ws, bob_ws, match_id = self._both_connected(app)

        alice_ws.emit(
            "submit_move",
            {"match_id": match_id, "from": "e2", "to": "e4"},
            namespace="/match",
        )

        bob_inbox = bob_ws.get_received("/match")
        applied = [e for e in bob_inbox if e["name"] == "move_applied"]
        assert applied, f"Expected move_applied on Bob, got {[e['name'] for e in bob_inbox]}"
        assert applied[0]["args"][0]["san"] == "e4"
        assert applied[0]["args"][0]["turn"] == "black"

    def test_illegal_move_emits_error_and_no_broadcast(self, app):
        _, _, alice_ws, bob_ws, match_id = self._both_connected(app)

        alice_ws.emit(
            "submit_move",
            {"match_id": match_id, "from": "e2", "to": "e5"},
            namespace="/match",
        )

        alice_inbox = alice_ws.get_received("/match")
        bob_inbox = bob_ws.get_received("/match")

        assert any(e["name"] == "error" for e in alice_inbox)
        assert not any(e["name"] == "move_applied" for e in alice_inbox)
        assert not any(e["name"] == "move_applied" for e in bob_inbox)

    def test_wrong_player_on_turn_gets_not_your_turn(self, app):
        _, _, alice_ws, bob_ws, match_id = self._both_connected(app)

        # Bob tries to move on White's turn.
        bob_ws.emit(
            "submit_move",
            {"match_id": match_id, "from": "e7", "to": "e5"},
            namespace="/match",
        )
        inbox = bob_ws.get_received("/match")
        errs = [e for e in inbox if e["name"] == "error"]
        assert errs
        assert errs[0]["args"][0]["code"] == "not_your_turn"

    def test_rest_move_is_broadcast_to_websocket_peer(self, app):
        """A player who submits via HTTP still triggers a WS event for peers."""
        alice_http, bob_http, alice_ws, bob_ws, match_id = self._both_connected(app)

        resp = alice_http.post(
            f"/match/{match_id}/move",
            data={"from": "e2", "to": "e4"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        bob_inbox = bob_ws.get_received("/match")
        applied = [e for e in bob_inbox if e["name"] == "move_applied"]
        assert applied
        assert applied[0]["args"][0]["san"] == "e4"


# -------------------- request_state --------------------


class TestRequestState:
    def test_request_state_returns_current_snapshot(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")
        ws = _socket(app, alice_http, match_id)
        ws.get_received("/match")  # drain initial

        ws.emit("request_state", {"match_id": match_id}, namespace="/match")

        inbox = ws.get_received("/match")
        states = [e for e in inbox if e["name"] == "match_state"]
        assert states
        assert states[0]["args"][0]["match_id"] == match_id


# -------------------- disconnect --------------------


class TestDisconnect:
    def test_disconnect_notifies_room(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")
        invite = _invite_code(alice_http, match_id)
        bob_http = app.test_client()
        bob_http.post(f"/match/join/{invite}")

        alice_ws = _socket(app, alice_http, match_id)
        bob_ws = _socket(app, bob_http, match_id)
        alice_ws.get_received("/match")
        bob_ws.get_received("/match")

        alice_ws.disconnect("/match")

        bob_inbox = bob_ws.get_received("/match")
        assert any(e["name"] == "opponent_disconnected" for e in bob_inbox)


# -------------------- resign over socket --------------------


class TestSocketResign:
    def test_resign_while_waiting_broadcasts_match_deleted(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")
        ws = _socket(app, alice_http, match_id)
        ws.get_received("/match")

        ws.emit("resign", {"match_id": match_id}, namespace="/match")

        inbox = ws.get_received("/match")
        assert any(e["name"] == "match_deleted" for e in inbox)

    def test_resign_active_match_broadcasts_move_applied_with_result(self, app):
        alice_http = app.test_client()
        match_id = _http_create(alice_http, seat="white")
        invite = _invite_code(alice_http, match_id)
        bob_http = app.test_client()
        bob_http.post(f"/match/join/{invite}")
        alice_ws = _socket(app, alice_http, match_id)
        bob_ws = _socket(app, bob_http, match_id)
        alice_ws.get_received("/match")
        bob_ws.get_received("/match")

        alice_ws.emit("resign", {"match_id": match_id}, namespace="/match")

        bob_inbox = bob_ws.get_received("/match")
        applied = [e for e in bob_inbox if e["name"] == "move_applied"]
        assert applied
        # White resigned -> black wins 0-1 and status abandoned.
        assert applied[0]["args"][0]["result"] == "0-1"
        assert applied[0]["args"][0]["status"] == "abandoned"
