"""Tests for PGN parsing and serialization."""

import pytest

from pychess.model.game_state import GameState
from pychess.model.square import Square
from pychess.model.piece import Piece, Color
from pychess.notation.pgn import game_to_pgn, pgn_to_game, PGNHeaders


class TestPGNHeaders:
    """Tests for PGN header handling."""

    def test_default_headers(self):
        """Default headers have sensible values."""
        headers = PGNHeaders()
        assert headers.event == "Casual Game"
        assert headers.site == "Terminal"
        assert headers.result == "*"
        assert len(headers.date) == 10  # YYYY.MM.DD

    def test_custom_headers(self):
        """Custom headers are preserved."""
        headers = PGNHeaders(
            event="Tournament",
            site="Online",
            white="Magnus",
            black="Hikaru",
            result="1-0"
        )
        assert headers.event == "Tournament"
        assert headers.white == "Magnus"
        assert headers.black == "Hikaru"
        assert headers.result == "1-0"


class TestGameToPGN:
    """Tests for serializing games to PGN."""

    def test_empty_game(self):
        """Empty game produces valid PGN."""
        state = GameState.initial()
        pgn = game_to_pgn(state)

        assert '[Event "Casual Game"]' in pgn
        assert '[White "White"]' in pgn
        assert '[Black "Black"]' in pgn

    def test_game_with_moves(self):
        """Game with moves includes move text."""
        state = GameState.initial()
        # Add some moves to history
        state = state.with_move_added("e4").with_move_added("e5")
        state = state.with_move_added("Nf3").with_move_added("Nc6")

        headers = PGNHeaders(result="*")
        pgn = game_to_pgn(state, headers)

        assert "1. e4 e5" in pgn
        assert "2. Nf3 Nc6" in pgn

    def test_game_with_result(self):
        """Game with result includes result in move text."""
        state = GameState.initial()
        state = state.with_move_added("e4").with_move_added("e5")

        headers = PGNHeaders(result="1-0")
        pgn = game_to_pgn(state, headers)

        assert "1-0" in pgn
        assert '[Result "1-0"]' in pgn

    def test_game_with_comments(self):
        """Game with comments includes them in braces."""
        state = GameState.initial()
        state = state.with_move_added("e4").with_move_added("e5")

        headers = PGNHeaders()
        comments = {1: "King's pawn opening", 2: "Symmetric response"}
        pgn = game_to_pgn(state, headers, comments)

        assert "{King's pawn opening}" in pgn
        assert "{Symmetric response}" in pgn


class TestPGNToGame:
    """Tests for parsing PGN to game state."""

    def test_parse_headers(self):
        """Headers are correctly parsed."""
        pgn = '''[Event "Test Game"]
[Site "Test Site"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 1-0'''

        state, headers = pgn_to_game(pgn)

        assert headers.event == "Test Game"
        assert headers.site == "Test Site"
        assert headers.date == "2024.01.15"
        assert headers.white == "Player1"
        assert headers.black == "Player2"
        assert headers.result == "1-0"

    def test_parse_simple_moves(self):
        """Simple moves are correctly parsed and applied."""
        pgn = '''[Event "Test"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6'''

        state, headers = pgn_to_game(pgn)

        # Check move history
        assert len(state.move_history) == 4
        assert state.move_history == ["e4", "e5", "Nf3", "Nc6"]

        # Check board state
        assert state.board.get(Square.from_algebraic("e4")) == (Piece.PAWN, Color.WHITE)
        assert state.board.get(Square.from_algebraic("e5")) == (Piece.PAWN, Color.BLACK)
        assert state.board.get(Square.from_algebraic("f3")) == (Piece.KNIGHT, Color.WHITE)
        assert state.board.get(Square.from_algebraic("c6")) == (Piece.KNIGHT, Color.BLACK)

    def test_parse_castling(self):
        """Castling moves are correctly parsed."""
        pgn = '''[Event "Test"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O'''

        state, headers = pgn_to_game(pgn)

        # King should be on g1 after castling
        assert state.board.get(Square.from_algebraic("g1")) == (Piece.KING, Color.WHITE)
        # Rook should be on f1
        assert state.board.get(Square.from_algebraic("f1")) == (Piece.ROOK, Color.WHITE)

    def test_parse_captures(self):
        """Capture moves are correctly parsed."""
        pgn = '''[Event "Test"]
[Result "*"]

1. e4 d5 2. exd5'''

        state, headers = pgn_to_game(pgn)

        # White pawn should be on d5
        assert state.board.get(Square.from_algebraic("d5")) == (Piece.PAWN, Color.WHITE)
        # e4 should be empty
        assert state.board.get(Square.from_algebraic("e4")) is None

    def test_parse_promotion(self):
        """Promotion moves are correctly parsed."""
        # Set up a position where promotion is possible
        # This sequence advances white's e-pawn to promotion
        pgn = '''[Event "Test"]
[Result "*"]

1. e4 d5 2. e5 d4 3. e6 d3 4. exf7+ Kd7 5. fxg8=Q'''

        state, headers = pgn_to_game(pgn)

        # Queen should be on g8
        assert state.board.get(Square.from_algebraic("g8")) == (Piece.QUEEN, Color.WHITE)

    def test_parse_with_comments(self):
        """Comments are ignored during parsing."""
        pgn = '''[Event "Test"]
[Result "*"]

1. e4 {King's pawn} e5 2. Nf3 Nc6'''

        state, headers = pgn_to_game(pgn)

        assert len(state.move_history) == 4

    def test_parse_with_result(self):
        """Result at end is handled."""
        pgn = '''[Event "Test"]
[Result "1-0"]

1. e4 e5 1-0'''

        state, headers = pgn_to_game(pgn)

        assert len(state.move_history) == 2
        assert headers.result == "1-0"


class TestPGNRoundTrip:
    """Tests for round-trip PGN serialization."""

    def test_roundtrip_simple_game(self):
        """Simple game survives round-trip."""
        original_pgn = '''[Event "Test Game"]
[Site "Test Site"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "*"]
[TimeControl "-"]
[TotalTimeSeconds "0"]

1. e4 e5 2. Nf3 Nc6'''

        state, headers = pgn_to_game(original_pgn)
        regenerated_pgn = game_to_pgn(state, headers)
        state2, headers2 = pgn_to_game(regenerated_pgn)

        assert state.move_history == state2.move_history
        assert headers.event == headers2.event
        assert headers.white == headers2.white

    def test_roundtrip_with_castling(self):
        """Game with castling survives round-trip."""
        pgn = '''[Event "Test"]
[Site "Terminal"]
[Date "2024.01.01"]
[White "White"]
[Black "Black"]
[Result "*"]
[TimeControl "-"]
[TotalTimeSeconds "0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6'''

        state1, headers1 = pgn_to_game(pgn)
        regenerated = game_to_pgn(state1, headers1)
        state2, headers2 = pgn_to_game(regenerated)

        # Both should have same board state
        assert state1.board.get(Square.from_algebraic("g1")) == state2.board.get(Square.from_algebraic("g1"))
        assert state1.move_history == state2.move_history


class TestPGNEdgeCases:
    """Tests for edge cases in PGN handling."""

    def test_empty_pgn(self):
        """Empty move text results in initial position."""
        pgn = '''[Event "Test"]
[Result "*"]

'''
        state, headers = pgn_to_game(pgn)
        assert len(state.move_history) == 0
        # Board should be initial position
        assert state.board.get(Square.from_algebraic("e2")) == (Piece.PAWN, Color.WHITE)

    def test_invalid_move_raises(self):
        """Invalid move raises ValueError."""
        pgn = '''[Event "Test"]
[Result "*"]

1. e4 e6 2. Qh5 xyz'''  # xyz is invalid

        with pytest.raises(ValueError):
            pgn_to_game(pgn)

    def test_headers_only(self):
        """PGN with headers but no moves."""
        pgn = '''[Event "Abandoned Game"]
[Site "Terminal"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "*"]'''

        state, headers = pgn_to_game(pgn)
        assert len(state.move_history) == 0
        assert headers.event == "Abandoned Game"
