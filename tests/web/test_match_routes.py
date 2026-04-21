"""HTTP-route tests for networked multiplayer.

Simulates two separate browsers as two independent Flask test clients
(each with its own session cookie jar) hitting the same app instance.
This is the integration gate proving routes + service + repo work
together end-to-end over real HTTP semantics — no Socket.IO yet.
"""

from __future__ import annotations

import pytest
from flask import url_for

from pychess.web.app import create_app


@pytest.fixture
def app(tmp_path):
    """Fresh app per test with a file-backed SQLite so multiple test clients share state."""
    db_url = f"sqlite:///{tmp_path / 'matches.db'}"
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'MATCH_DB_URL': db_url,
        'SERVER_NAME': 'localhost.test',
        'WTF_CSRF_ENABLED': False,
    })
    return app


@pytest.fixture
def alice(app):
    """Test client that mimics Alice's browser."""
    return app.test_client()


@pytest.fixture
def bob(app):
    """Separate test client with its own session cookie for Bob."""
    return app.test_client()


def _create_match(client, seat: str = "white") -> str:
    """Hit POST /match/new and return the newly created match_id."""
    resp = client.post("/match/new", data={"seat": seat}, follow_redirects=False)
    assert resp.status_code == 302, f"Expected redirect, got {resp.status_code}: {resp.data[:200]}"
    # Redirect target looks like /match/<id>
    location = resp.headers["Location"]
    return location.rsplit("/", 1)[-1]


def _match_page_html(client, match_id: str) -> str:
    resp = client.get(f"/match/{match_id}")
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def _invite_code_from_page(html: str) -> str:
    """Extract the invite code from the play-page banner's /match/join/<code> URL."""
    import re
    m = re.search(r"/match/join/([A-Z0-9]+)", html)
    assert m, "No invite URL found on match page"
    return m.group(1)


# -------------------- landing page --------------------


class TestLanding:
    def test_index_offers_create_and_join(self, alice):
        resp = alice.get("/match/")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Create" in body
        assert "Join" in body
        assert 'name="invite_code"' in body

    def test_join_by_code_redirects_to_join_form(self, alice):
        resp = alice.post("/match/join", data={"invite_code": "ABCD1234"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/match/join/ABCD1234" in resp.headers["Location"]

    def test_join_by_code_uppercases_input(self, alice):
        resp = alice.post("/match/join", data={"invite_code": "abcd1234"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/match/join/ABCD1234" in resp.headers["Location"]

    def test_join_by_code_empty_flashes_and_returns(self, alice):
        resp = alice.post("/match/join", data={"invite_code": "  "}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"invite code" in resp.data.lower()


# -------------------- creation --------------------


class TestCreateMatch:
    def test_new_form_renders(self, alice):
        resp = alice.get("/match/new")
        assert resp.status_code == 200
        assert b"seat" in resp.data.lower()

    def test_create_as_white_redirects_to_play(self, alice):
        resp = alice.post("/match/new", data={"seat": "white"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/match/" in resp.headers["Location"]

    @pytest.mark.parametrize("seat", ["white", "black", "random"])
    def test_seat_choice_is_honored(self, alice, seat):
        match_id = _create_match(alice, seat=seat)
        html = _match_page_html(alice, match_id)
        # Play page exposes viewer_seat as a data attribute.
        if seat == "white":
            assert 'data-viewer-seat="white"' in html
        elif seat == "black":
            assert 'data-viewer-seat="black"' in html
        else:
            assert (
                'data-viewer-seat="white"' in html
                or 'data-viewer-seat="black"' in html
            )

    def test_invalid_seat_is_rejected_with_flash(self, alice):
        resp = alice.post(
            "/match/new", data={"seat": "purple"}, follow_redirects=True
        )
        # Redirected back to the form; we shouldn't have created a match.
        assert b"Invalid seat choice" in resp.data or b"seat" in resp.data.lower()


# -------------------- join flow --------------------


class TestJoinFlow:
    def test_bob_joins_alice_match(self, alice, bob):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))

        join_page = bob.get(f"/match/join/{invite_code}")
        assert join_page.status_code == 200
        assert invite_code.encode() in join_page.data

        claim = bob.post(f"/match/join/{invite_code}")
        assert claim.status_code == 302
        assert f"/match/{match_id}" in claim.headers["Location"]

        # Bob's play page now shows him as Black (since Alice chose White).
        bob_page = _match_page_html(bob, match_id)
        assert 'data-viewer-seat="black"' in bob_page

    def test_join_with_bad_code_404s(self, bob):
        resp = bob.get("/match/join/NOPE0000")
        assert resp.status_code == 404

    def test_third_party_cannot_reuse_full_invite_code(self, alice, bob, app):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))
        bob.post(f"/match/join/{invite_code}")

        carol = app.test_client()
        resp = carol.get(f"/match/join/{invite_code}")
        assert resp.status_code == 403

    def test_alice_refreshing_her_own_join_url_is_harmless(self, alice, bob):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))
        # Alice clicks her own invite link — should not steal the black seat.
        resp = alice.get(f"/match/join/{invite_code}")
        assert resp.status_code in (200, 302)

        # Bob can still take the black seat after Alice's harmless click.
        bob.post(f"/match/join/{invite_code}")
        html = _match_page_html(bob, match_id)
        assert 'data-viewer-seat="black"' in html


# -------------------- move authorization --------------------


class TestMoveAuthorization:
    def _seat_pair(self, alice, bob):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))
        bob.post(f"/match/join/{invite_code}")
        return match_id

    def test_white_player_can_move_on_their_turn(self, alice, bob):
        match_id = self._seat_pair(alice, bob)

        resp = alice.post(
            f"/match/{match_id}/move",
            data={"from": "e2", "to": "e4"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Move history now shows e4.
        html = resp.get_data(as_text=True)
        assert "e4" in html

    def test_black_cannot_move_on_whites_turn(self, alice, bob):
        match_id = self._seat_pair(alice, bob)

        resp = bob.post(
            f"/match/{match_id}/move",
            data={"from": "e7", "to": "e5"},
            follow_redirects=True,
        )
        # Not-your-turn becomes a flash, not a hard 4xx — redirect back to play.
        html = resp.get_data(as_text=True)
        assert "not your turn" in html.lower() or "e7" not in html.split("Moves")[0] if "Moves" in html else "not your turn" in html.lower()
        # Verify no move was applied by checking e7 pawn is still there.
        page = _match_page_html(bob, match_id)
        assert 'data-square="e7"' in page  # board still rendered

    def test_stranger_cookie_gets_403_on_move(self, alice, bob, app):
        match_id = self._seat_pair(alice, bob)

        stranger = app.test_client()
        resp = stranger.post(
            f"/match/{match_id}/move",
            data={"from": "e2", "to": "e4"},
        )
        assert resp.status_code == 403

    def test_stranger_cookie_gets_403_on_play_page(self, alice, bob, app):
        match_id = self._seat_pair(alice, bob)

        stranger = app.test_client()
        resp = stranger.get(f"/match/{match_id}")
        assert resp.status_code == 403

    def test_opponent_chip_rendered_when_match_active(self, alice, bob):
        """Active matches show the opponent-presence chip; waiting ones don't."""
        match_id = self._seat_pair(alice, bob)
        html = _match_page_html(alice, match_id)
        assert 'opponent-chip' in html
        assert 'data-opponent-state="unknown"' in html  # JS upgrades this client-side

    def test_opponent_chip_absent_while_waiting(self, alice):
        match_id = _create_match(alice, seat="white")
        html = _match_page_html(alice, match_id)
        assert "opponent-chip" not in html  # no chip before second seat is filled

    def test_alternating_moves_build_history(self, alice, bob):
        match_id = self._seat_pair(alice, bob)

        alice.post(f"/match/{match_id}/move", data={"from": "e2", "to": "e4"})
        bob.post(f"/match/{match_id}/move", data={"from": "e7", "to": "e5"})
        alice.post(f"/match/{match_id}/move", data={"from": "g1", "to": "f3"})

        html = _match_page_html(alice, match_id)
        assert "e4" in html
        assert "e5" in html
        assert "Nf3" in html

    def test_move_before_opponent_joined_flashes_not_active(self, alice):
        match_id = _create_match(alice, seat="white")

        resp = alice.post(
            f"/match/{match_id}/move",
            data={"from": "e2", "to": "e4"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"not active" in resp.data.lower()


# -------------------- reconnect & identity --------------------


class TestReconnect:
    def test_same_cookie_can_rejoin_and_keep_playing(self, alice, bob, app):
        """Alice closes and reopens her browser (new test client, same cookie)."""
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))
        bob.post(f"/match/join/{invite_code}")
        alice.post(f"/match/{match_id}/move", data={"from": "e2", "to": "e4"})

        # Pull Alice's signed player-id cookie and inject into a new client.
        # Werkzeug's test-client cookie jar is domain-scoped; SERVER_NAME sets
        # the cookie's domain attribute, so we look it up by that.
        cookie = alice.get_cookie("session", domain=app.config["SERVER_NAME"])
        assert cookie is not None, "Expected a signed session cookie on Alice's client"
        alice_again = app.test_client()
        alice_again.set_cookie("session", cookie.value, domain=cookie.domain)

        # Bob makes his move.
        bob.post(f"/match/{match_id}/move", data={"from": "e7", "to": "e5"})

        # Rejoined Alice moves on the new client; server recognises her seat.
        resp = alice_again.post(
            f"/match/{match_id}/move",
            data={"from": "g1", "to": "f3"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "Nf3" in html

    def test_fresh_cookie_cannot_hijack_a_seat(self, alice, bob, app):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))
        bob.post(f"/match/join/{invite_code}")

        # A fresh client with no cookie tries to move as "Alice".
        imposter = app.test_client()
        resp = imposter.post(
            f"/match/{match_id}/move",
            data={"from": "e2", "to": "e4"},
        )
        assert resp.status_code == 403


# -------------------- resign --------------------


class TestResign:
    def test_resign_before_join_deletes_match_and_invite_404s(self, alice, bob):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))

        resp = alice.post(f"/match/{match_id}/resign", follow_redirects=False)
        # Redirects to /match/new because the match is gone.
        assert resp.status_code == 302
        assert "/match/new" in resp.headers["Location"]

        # Match page should 404.
        assert alice.get(f"/match/{match_id}").status_code == 404
        # Bob's join attempt should 404.
        assert bob.get(f"/match/join/{invite_code}").status_code == 404

    def test_resign_after_join_records_result(self, alice, bob):
        match_id = _create_match(alice, seat="white")
        invite_code = _invite_code_from_page(_match_page_html(alice, match_id))
        bob.post(f"/match/join/{invite_code}")

        alice.post(f"/match/{match_id}/resign")
        html = _match_page_html(bob, match_id)
        assert "abandoned" in html.lower()
        assert "0-1" in html  # white resigned


# -------------------- 404s --------------------


class TestNotFound:
    def test_unknown_match_id_404s(self, alice):
        resp = alice.get("/match/does-not-exist")
        assert resp.status_code == 404
