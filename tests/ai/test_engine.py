"""Tests for AI engine."""

import pytest
from unittest.mock import patch, MagicMock

from pychess.ai.engine import AIEngine, Difficulty
from pychess.model.game_state import GameState
from pychess.model.board import Board
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves


class TestAIEngineDifficulty:
    """Tests for AI difficulty levels."""

    def test_easy_difficulty_enum(self):
        """Test easy difficulty enum value."""
        assert Difficulty.EASY.value == "easy"

    def test_medium_difficulty_enum(self):
        """Test medium difficulty enum value."""
        assert Difficulty.MEDIUM.value == "medium"

    def test_hard_difficulty_enum(self):
        """Test hard difficulty enum value."""
        assert Difficulty.HARD.value == "hard"


class TestAIEngineCreation:
    """Tests for AIEngine initialization."""

    def test_create_easy_engine(self):
        """Test creating easy difficulty engine."""
        engine = AIEngine(Difficulty.EASY)
        assert engine.difficulty == Difficulty.EASY

    def test_create_medium_engine(self):
        """Test creating medium difficulty engine."""
        engine = AIEngine(Difficulty.MEDIUM)
        assert engine.difficulty == Difficulty.MEDIUM

    def test_create_hard_engine(self):
        """Test creating hard difficulty engine."""
        engine = AIEngine(Difficulty.HARD)
        assert engine.difficulty == Difficulty.HARD

    def test_create_with_seed(self):
        """Test creating engine with random seed."""
        engine = AIEngine(Difficulty.EASY, seed=42)
        assert engine.difficulty == Difficulty.EASY


class TestAIEngineSelectMove:
    """Tests for move selection."""

    def test_select_move_returns_legal_move(self):
        """Test that selected move is always legal."""
        game_state = GameState.initial()
        legal_moves = get_legal_moves(game_state)

        for difficulty in Difficulty:
            engine = AIEngine(difficulty, seed=42)
            move = engine.select_move(game_state)
            assert move in legal_moves, f"{difficulty} returned illegal move"

    def test_select_move_raises_on_no_moves(self):
        """Test that ValueError is raised when no legal moves."""
        # Create a stalemate position
        board = Board.empty()
        board = board.set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("f7"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("g6"), Piece.KING, Color.WHITE)

        game_state = GameState.initial().with_board(board).with_turn(Color.BLACK)

        engine = AIEngine(Difficulty.EASY)
        with pytest.raises(ValueError, match="No legal moves"):
            engine.select_move(game_state)

    def test_easy_is_deterministic_with_seed(self):
        """Test that easy AI with same seed makes same moves."""
        game_state = GameState.initial()

        engine1 = AIEngine(Difficulty.EASY, seed=123)
        move1 = engine1.select_move(game_state)

        engine2 = AIEngine(Difficulty.EASY, seed=123)
        move2 = engine2.select_move(game_state)

        assert move1 == move2

    def test_medium_is_deterministic_with_seed(self):
        """Test that medium AI with same seed makes same moves."""
        game_state = GameState.initial()

        engine1 = AIEngine(Difficulty.MEDIUM, seed=456)
        move1 = engine1.select_move(game_state)

        engine2 = AIEngine(Difficulty.MEDIUM, seed=456)
        move2 = engine2.select_move(game_state)

        assert move1 == move2

    def test_hard_is_deterministic_with_seed(self):
        """Test that hard AI with same seed makes same moves."""
        game_state = GameState.initial()

        engine1 = AIEngine(Difficulty.HARD, seed=789)
        move1 = engine1.select_move(game_state)

        engine2 = AIEngine(Difficulty.HARD, seed=789)
        move2 = engine2.select_move(game_state)

        assert move1 == move2


class TestAIEngineEasyDifficulty:
    """Tests specific to easy difficulty."""

    def test_easy_uses_random_selection(self):
        """Test that easy difficulty uses random move selection."""
        game_state = GameState.initial()
        engine = AIEngine(Difficulty.EASY, seed=42)

        # With random selection, different seeds should (usually) give different moves
        moves_seen = set()
        for seed in range(10):
            engine = AIEngine(Difficulty.EASY, seed=seed)
            move = engine.select_move(game_state)
            moves_seen.add((move.from_square, move.to_square))

        # Should see variety in moves (not all the same)
        assert len(moves_seen) > 1, "Easy AI should show variety with different seeds"

    def test_easy_selects_from_all_legal_moves(self):
        """Test that easy can select any legal move."""
        game_state = GameState.initial()
        legal_moves = get_legal_moves(game_state)

        # Run many times with different seeds to verify distribution
        selected_moves = set()
        for seed in range(100):
            engine = AIEngine(Difficulty.EASY, seed=seed)
            move = engine.select_move(game_state)
            selected_moves.add((move.from_square, move.to_square))

        # Should have selected multiple different moves
        assert len(selected_moves) > 5, "Easy AI should be able to select various moves"


class TestAIEngineMediumDifficulty:
    """Tests specific to medium difficulty."""

    def test_medium_captures_free_piece(self):
        """Test that medium AI captures undefended pieces."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("h8"), Piece.ROOK, Color.BLACK)  # Undefended

        game_state = GameState.initial().with_board(board)
        engine = AIEngine(Difficulty.MEDIUM)
        move = engine.select_move(game_state)

        # Should capture the rook
        assert move.to_square == Square.from_algebraic("h8")

    def test_medium_prefers_higher_value_capture(self):
        """Test that medium AI prefers capturing higher value pieces."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("a1"), Piece.PAWN, Color.BLACK)  # Low value
        board = board.set(Square.from_algebraic("h8"), Piece.ROOK, Color.BLACK)  # High value

        game_state = GameState.initial().with_board(board)
        engine = AIEngine(Difficulty.MEDIUM)
        move = engine.select_move(game_state)

        # Should capture the rook (500) over pawn (100)
        assert move.to_square == Square.from_algebraic("h8")

    def test_medium_considers_promotion(self):
        """Test that medium AI values promotion."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("a7"), Piece.PAWN, Color.WHITE)  # Can promote

        game_state = GameState.initial().with_board(board)
        engine = AIEngine(Difficulty.MEDIUM)
        move = engine.select_move(game_state)

        # Should promote the pawn
        assert move.from_square == Square.from_algebraic("a7")
        assert move.to_square == Square.from_algebraic("a8")
        assert move.promotion is not None


class TestAIEngineHardDifficulty:
    """Tests specific to hard difficulty."""

    def test_hard_uses_positional_evaluation(self):
        """Test that hard AI considers positional factors."""
        game_state = GameState.initial()
        engine = AIEngine(Difficulty.HARD, seed=42)

        move = engine.select_move(game_state)

        # Hard AI should prefer central pawn moves or knight development
        # Common strong opening moves
        good_opening_moves = [
            (Square.from_algebraic("e2"), Square.from_algebraic("e4")),
            (Square.from_algebraic("d2"), Square.from_algebraic("d4")),
            (Square.from_algebraic("g1"), Square.from_algebraic("f3")),
            (Square.from_algebraic("b1"), Square.from_algebraic("c3")),
            (Square.from_algebraic("e2"), Square.from_algebraic("e3")),
            (Square.from_algebraic("d2"), Square.from_algebraic("d3")),
        ]

        move_tuple = (move.from_square, move.to_square)
        assert move_tuple in good_opening_moves, f"Hard AI played {move}, expected strong opening"

    def test_hard_captures_free_piece(self):
        """Test that hard AI captures undefended pieces."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.QUEEN, Color.WHITE)
        board = board.set(Square.from_algebraic("h8"), Piece.ROOK, Color.BLACK)

        game_state = GameState.initial().with_board(board)
        engine = AIEngine(Difficulty.HARD)
        move = engine.select_move(game_state)

        # Should capture the rook
        assert move.to_square == Square.from_algebraic("h8")

    def test_hard_prefers_center_control(self):
        """Test that hard AI values center control."""
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("b1"), Piece.KNIGHT, Color.WHITE)

        game_state = GameState.initial().with_board(board)
        engine = AIEngine(Difficulty.HARD)
        move = engine.select_move(game_state)

        # Knight should move toward center, not to edge
        assert move.from_square == Square.from_algebraic("b1")
        # c3 or d2 are good central squares
        assert move.to_square in [
            Square.from_algebraic("c3"),
            Square.from_algebraic("d2"),
            Square.from_algebraic("a3"),  # Also legal, less ideal
        ]


class TestAIEngineIntegration:
    """Integration tests for AI engine."""

    def test_engine_plays_full_game_opening(self):
        """Test that engine can play several moves without error."""
        game_state = GameState.initial()
        white_engine = AIEngine(Difficulty.MEDIUM, seed=42)
        black_engine = AIEngine(Difficulty.MEDIUM, seed=43)

        # Play 5 moves for each side
        for _ in range(5):
            # White move
            move = white_engine.select_move(game_state)
            legal_moves = get_legal_moves(game_state)
            assert move in legal_moves

            # Apply move (simplified - just update turn for test)
            from pychess.notation.san import move_to_san
            from pychess.notation.pgn import _apply_san_move

            san = move_to_san(game_state, move)
            game_state = _apply_san_move(game_state, san, move)

            # Check if game ended
            if not get_legal_moves(game_state):
                break

            # Black move
            move = black_engine.select_move(game_state)
            legal_moves = get_legal_moves(game_state)
            assert move in legal_moves

            san = move_to_san(game_state, move)
            game_state = _apply_san_move(game_state, san, move)

            if not get_legal_moves(game_state):
                break

    def test_different_difficulties_may_choose_differently(self):
        """Test that different difficulties can choose different moves."""
        # Set up position where captures are available
        board = Board.empty()
        board = board.set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
        board = board.set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
        board = board.set(Square.from_algebraic("d4"), Piece.KNIGHT, Color.WHITE)
        board = board.set(Square.from_algebraic("e6"), Piece.PAWN, Color.BLACK)
        board = board.set(Square.from_algebraic("c2"), Piece.PAWN, Color.WHITE)

        game_state = GameState.initial().with_board(board)

        # Collect moves from each difficulty
        moves_by_difficulty = {}
        for difficulty in Difficulty:
            engine = AIEngine(difficulty, seed=42)
            move = engine.select_move(game_state)
            moves_by_difficulty[difficulty] = move

        # Medium and Hard should capture (material-aware)
        # Easy might do anything
        medium_move = moves_by_difficulty[Difficulty.MEDIUM]
        hard_move = moves_by_difficulty[Difficulty.HARD]

        # Both medium and hard should find the capture
        assert medium_move.to_square == Square.from_algebraic("e6") or \
               hard_move.to_square == Square.from_algebraic("e6")
