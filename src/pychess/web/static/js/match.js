/* Minimal Socket.IO glue for the match play page.
 *
 * Strategy: the server already renders the full match page with every move
 * history item, resign button, etc. We don't try to diff-patch the DOM.
 * When the server pushes `move_applied` or `match_deleted`, we simply
 * reload the page — the re-rendered HTML is the authoritative view for
 * this seat, including orientation flip. Cheap, predictable, and avoids
 * a client-side state machine.
 */
(function () {
  const section = document.querySelector(".match-play");
  if (!section) return;
  if (typeof io === "undefined") {
    console.warn("Socket.IO client missing; real-time updates disabled.");
    return;
  }

  const matchId = section.dataset.matchId;
  if (!matchId) return;

  const socket = io("/match", {
    query: { match_id: matchId },
    transports: ["websocket", "polling"],
  });

  socket.on("connect_error", (err) => {
    console.warn("match socket connect error:", err.message);
  });

  socket.on("move_applied", () => {
    // Reload so the re-rendered page reflects the new game state for this seat.
    window.location.reload();
  });

  socket.on("match_deleted", () => {
    window.location.href = "/match/new";
  });

  socket.on("opponent_connected", () => {
    setOpponentState("online", "online");
    showBanner("Opponent connected.");
  });

  socket.on("opponent_disconnected", () => {
    setOpponentState("offline", "offline — game resumes when they rejoin");
    showBanner("Opponent disconnected. The game resumes when they rejoin.");
  });

  socket.on("match_state", (payload) => {
    // The initial handshake emits match_state; the opposing seat is
    // occupied iff both seats field names are populated and neither is us.
    if (!payload || !payload.seats) return;
    const bothSeated = payload.seats.white && payload.seats.black;
    if (bothSeated && getOpponentState() === "unknown") {
      // We have no live signal yet but both seats are filled; assume offline
      // and let a subsequent opponent_connected event upgrade the chip.
      setOpponentState("offline", "offline");
    }
  });

  function setOpponentState(state, labelText) {
    const chip = section.querySelector(".opponent-chip");
    if (!chip) return;
    chip.dataset.opponentState = state;
    const label = chip.querySelector(".label");
    if (label) label.textContent = labelText;
  }

  function getOpponentState() {
    const chip = section.querySelector(".opponent-chip");
    return chip ? chip.dataset.opponentState : "unknown";
  }

  socket.on("error", (payload) => {
    showBanner(payload && payload.message ? payload.message : "Error", "error");
  });

  // A single, unobtrusive banner slot above the board so transient status
  // text doesn't cause layout shifts or replace flash messages from the
  // HTTP path.
  function showBanner(text, kind) {
    let el = section.querySelector(".ws-banner");
    if (!el) {
      el = document.createElement("div");
      el.className = "ws-banner";
      section.insertBefore(el, section.firstChild.nextSibling);
    }
    el.textContent = text;
    el.dataset.kind = kind || "info";
    clearTimeout(el._timer);
    el._timer = setTimeout(() => {
      el.textContent = "";
    }, 4000);
  }
})();
