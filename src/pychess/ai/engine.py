"""AI engine for selecting moves at different difficulty levels."""

from enum import Enum
from typing import Optional
import random

from pychess.model.game_state import GameState
from pychess.rules.move import Move
from pychess.rules.validator import get_legal_moves


class Difficulty(Enum):
    """AI difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AIEngine:
    """AI engine for move selection."""

    def __init__(self, difficulty: Difficulty, seed: Optional[int] = None):
        """Initialize AI engine.

        Args:
            difficulty: AI difficulty level
            seed: Random seed for deterministic behavior (testing)
        """
        self.difficulty = difficulty
        if seed is not None:
            random.seed(seed)

    def select_move(self, game_state: GameState) -> Move:
        """Select a move based on difficulty level.

        Args:
            game_state: Current game state

        Returns:
            Selected move

        Raises:
            ValueError: If no legal moves available
        """
        legal_moves = get_legal_moves(game_state)

        if not legal_moves:
            raise ValueError("No legal moves available")

        if self.difficulty == Difficulty.EASY:
            return self._select_random(legal_moves)
        elif self.difficulty == Difficulty.MEDIUM:
            return self._select_material_based(game_state, legal_moves)
        elif self.difficulty == Difficulty.HARD:
            return self._select_positional(game_state, legal_moves)

        return random.choice(legal_moves)

    def _select_random(self, legal_moves: list[Move]) -> Move:
        """Select a random legal move (Easy difficulty).

        Args:
            legal_moves: List of legal moves

        Returns:
            Random move
        """
        return random.choice(legal_moves)

    def _select_material_based(self, game_state: GameState, legal_moves: list[Move]) -> Move:
        """Select move based on material evaluation (Medium difficulty).

        Args:
            game_state: Current game state
            legal_moves: List of legal moves

        Returns:
            Best move based on material
        """
        from pychess.ai.evaluation import evaluate_material_balance, evaluate_move_material

        best_move = None
        best_score = float('-inf')

        for move in legal_moves:
            # Evaluate material gain from this move
            score = evaluate_move_material(game_state, move)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move if best_move else random.choice(legal_moves)

    def _select_positional(self, game_state: GameState, legal_moves: list[Move]) -> Move:
        """Select move with positional evaluation (Hard difficulty).

        Args:
            game_state: Current game state
            legal_moves: List of legal moves

        Returns:
            Best move based on material + position
        """
        from pychess.ai.evaluation import evaluate_position

        best_move = None
        best_score = float('-inf')

        for move in legal_moves:
            # Evaluate position after move
            score = evaluate_position(game_state, move)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move if best_move else random.choice(legal_moves)
