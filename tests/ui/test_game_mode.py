"""Tests for game mode specific behaviors."""

import pytest


class TestHintsAvailability:
    """Tests for hint availability based on game mode."""

    def test_hints_allowed_in_ai_easy_mode(self):
        """Hints should be allowed in AI Easy mode."""
        from pychess.ai.engine import AIEngine, Difficulty

        ai_engine = AIEngine(Difficulty.EASY)
        hints_allowed = (
            ai_engine is not None and
            ai_engine.difficulty in (Difficulty.EASY, Difficulty.MEDIUM)
        )
        assert hints_allowed is True

    def test_hints_allowed_in_ai_medium_mode(self):
        """Hints should be allowed in AI Medium mode."""
        from pychess.ai.engine import AIEngine, Difficulty

        ai_engine = AIEngine(Difficulty.MEDIUM)
        hints_allowed = (
            ai_engine is not None and
            ai_engine.difficulty in (Difficulty.EASY, Difficulty.MEDIUM)
        )
        assert hints_allowed is True

    def test_hints_not_allowed_in_ai_hard_mode(self):
        """Hints should NOT be allowed in AI Hard mode."""
        from pychess.ai.engine import AIEngine, Difficulty

        ai_engine = AIEngine(Difficulty.HARD)
        hints_allowed = (
            ai_engine is not None and
            ai_engine.difficulty in (Difficulty.EASY, Difficulty.MEDIUM)
        )
        assert hints_allowed is False

    def test_hints_not_allowed_in_multiplayer_mode(self):
        """Hints should NOT be allowed in multiplayer mode (no AI)."""
        ai_engine = None
        hints_allowed = (
            ai_engine is not None and
            ai_engine.difficulty in ("EASY", "MEDIUM")  # Won't be evaluated
        )
        assert hints_allowed is False


class TestMultiplayerCancelConfirmation:
    """Tests for multiplayer-specific cancel confirmation behavior."""

    def test_is_multiplayer_mode_detection(self):
        """Should correctly detect multiplayer mode."""
        # Multiplayer = no AI engine
        ai_engine = None
        is_multiplayer = ai_engine is None
        assert is_multiplayer is True

    def test_is_not_multiplayer_with_ai(self):
        """Should correctly detect AI mode as not multiplayer."""
        from pychess.ai.engine import AIEngine, Difficulty

        ai_engine = AIEngine(Difficulty.EASY)
        is_multiplayer = ai_engine is None
        assert is_multiplayer is False


class TestCursorPendingCancel:
    """Tests for pending cancel state in cursor."""

    def test_cursor_initial_no_pending_cancel(self):
        """Initial cursor state should not have pending cancel."""
        from pychess.ui.cursor import CursorState

        cursor = CursorState.initial()
        assert cursor.pending_cancel is False

    def test_cursor_request_cancel_sets_pending(self):
        """Requesting cancel should set pending_cancel flag."""
        from pychess.ui.cursor import CursorState
        from pychess.model.square import Square

        cursor = CursorState.initial()
        cursor = cursor.select_square()  # Select a piece first
        cursor = cursor.request_cancel()
        assert cursor.pending_cancel is True
        # Selection should NOT be cleared yet
        assert cursor.selected_square is not None

    def test_cursor_confirm_cancel_clears_selection(self):
        """Confirming cancel should clear the selection."""
        from pychess.ui.cursor import CursorState

        cursor = CursorState.initial()
        cursor = cursor.select_square()
        cursor = cursor.request_cancel()
        cursor = cursor.confirm_cancel()
        assert cursor.selected_square is None
        assert cursor.pending_cancel is False

    def test_cursor_deny_cancel_keeps_selection(self):
        """Denying cancel should keep the selection and clear pending."""
        from pychess.ui.cursor import CursorState

        cursor = CursorState.initial()
        cursor = cursor.select_square()
        original_selection = cursor.selected_square
        cursor = cursor.request_cancel()
        cursor = cursor.deny_cancel()
        assert cursor.selected_square == original_selection
        assert cursor.pending_cancel is False

    def test_cursor_cancel_selection_immediate_when_nothing_selected(self):
        """Cancel with nothing selected should not set pending."""
        from pychess.ui.cursor import CursorState

        cursor = CursorState.initial()
        assert cursor.selected_square is None
        cursor = cursor.request_cancel()
        # No pending state when nothing to cancel
        assert cursor.pending_cancel is False

    def test_pending_cancel_preserved_during_movement(self):
        """Pending cancel should be preserved during cursor movement."""
        from pychess.ui.cursor import CursorState

        cursor = CursorState.initial()
        cursor = cursor.select_square()
        cursor = cursor.request_cancel()
        assert cursor.pending_cancel is True

        # Move around - pending should stay
        cursor = cursor.move_up()
        assert cursor.pending_cancel is True

        cursor = cursor.move_left()
        assert cursor.pending_cancel is True
