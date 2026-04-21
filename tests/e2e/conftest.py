"""End-to-end test fixtures.

These tests target a live server reachable at `PYCHESS_E2E_BASE_URL`.
Unless that env var is set, every test in this directory is skipped —
the normal developer pytest run stays fast and hermetic. The Docker
Compose overlay (`docker-compose.e2e.yml`) sets the URL when the e2e
container runs.
"""

from __future__ import annotations

import os
import re
import time
import urllib.parse

import pytest
import requests


def pytest_collection_modifyitems(config, items):
    """Skip only the e2e tests when no live server URL is configured.

    pytest calls this hook once with the full collected test list regardless
    of which conftest defined it, so we filter to items rooted in this dir
    rather than marking everything the session saw.
    """
    if os.environ.get("PYCHESS_E2E_BASE_URL"):
        return
    skip = pytest.mark.skip(
        reason="Set PYCHESS_E2E_BASE_URL=http://host:port to run end-to-end tests"
    )
    here = os.path.dirname(__file__)
    for item in items:
        if str(item.fspath).startswith(here):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ["PYCHESS_E2E_BASE_URL"].rstrip("/")


@pytest.fixture(scope="session", autouse=True)
def _wait_for_server(base_url: str) -> None:
    """Block until the server responds; defends against Docker startup race."""
    deadline = time.time() + 30
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            resp = requests.get(f"{base_url}/match/new", timeout=2)
            if resp.status_code == 200:
                return
        except Exception as exc:
            last_err = exc
        time.sleep(0.5)
    raise RuntimeError(f"Server at {base_url} never became ready: {last_err}")


_INVITE_PATTERN = re.compile(r"/match/join/([A-Z0-9]+)")


class Player:
    """requests.Session wrapper with match-flow helpers.

    Each Player is its own browser: separate cookie jar, separate seat.
    Kept deliberately thin; the point of the e2e suite is integration,
    not to reimplement the service.
    """

    def __init__(self, base_url: str, name: str) -> None:
        self.base_url = base_url
        self.name = name
        self.http = requests.Session()

    def create_match(self, seat: str = "white") -> str:
        resp = self.http.post(
            f"{self.base_url}/match/new",
            data={"seat": seat},
            allow_redirects=False,
            timeout=5,
        )
        assert resp.status_code == 302, f"create_match: {resp.status_code} {resp.text[:200]}"
        return resp.headers["Location"].rsplit("/", 1)[-1]

    def invite_code_for(self, match_id: str) -> str:
        resp = self.http.get(f"{self.base_url}/match/{match_id}", timeout=5)
        resp.raise_for_status()
        m = _INVITE_PATTERN.search(resp.text)
        assert m, f"No invite code on match page for {match_id}"
        return m.group(1)

    def join(self, invite_code: str) -> str:
        resp = self.http.post(
            f"{self.base_url}/match/join/{invite_code}",
            allow_redirects=False,
            timeout=5,
        )
        assert resp.status_code == 302, f"join: {resp.status_code}"
        return resp.headers["Location"].rsplit("/", 1)[-1]

    def submit_move(self, match_id: str, frm: str, to: str, promotion: str | None = None) -> None:
        data = {"from": frm, "to": to}
        if promotion:
            data["promotion"] = promotion
        resp = self.http.post(
            f"{self.base_url}/match/{match_id}/move",
            data=data,
            allow_redirects=True,
            timeout=5,
        )
        resp.raise_for_status()

    def match_page(self, match_id: str) -> str:
        resp = self.http.get(f"{self.base_url}/match/{match_id}", timeout=5)
        resp.raise_for_status()
        return resp.text

    def cookie_header(self) -> str:
        """Serialize the requests cookie jar as a `Cookie:` header value."""
        host = urllib.parse.urlparse(self.base_url).hostname
        cookies = self.http.cookies.get_dict(domain=host) if host else {}
        if not cookies:
            cookies = {c.name: c.value for c in self.http.cookies}
        return "; ".join(f"{k}={v}" for k, v in cookies.items())


@pytest.fixture
def alice(base_url) -> Player:
    return Player(base_url, "alice")


@pytest.fixture
def bob(base_url) -> Player:
    return Player(base_url, "bob")
