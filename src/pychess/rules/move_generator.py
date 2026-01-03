"""Move generation for all piece types.

This module generates pseudo-legal moves (moves that are legal except
they might leave the king in check). Full legality checking happens
in the validator module.
"""

from typing import Optional

from pychess.rules.move import Move
from pychess.model.board import Board
from pychess.model.square import Square
from pychess.model.piece import Piece, Color


class MoveGenerator:
    """Generator for pseudo-legal chess moves."""

    @staticmethod
    def generate_pawn_moves(
        board: Board,
        from_square: Square,
        color: Color,
        en_passant_square: Optional[Square] = None,
    ) -> list[Move]:
        """Generate pseudo-legal pawn moves.

        Args:
            board: Current board position
            from_square: Square the pawn is on
            color: Color of the pawn
            en_passant_square: En passant target square (if any)

        Returns:
            List of pseudo-legal moves
        """
        moves = []
        file_idx = from_square.file_index
        rank = from_square.rank

        # Direction: white moves up (+1), black moves down (-1)
        direction = 1 if color == Color.WHITE else -1
        start_rank = 2 if color == Color.WHITE else 7
        promotion_rank = 8 if color == Color.WHITE else 1

        # Single push forward
        target_rank = rank + direction
        if 1 <= target_rank <= 8:
            target = Square(file=from_square.file, rank=target_rank)
            if board.get(target) is None:
                # Check if this is a promotion
                if target_rank == promotion_rank:
                    # Generate all 4 promotion moves
                    for promo_piece in [Piece.QUEEN, Piece.ROOK, Piece.BISHOP, Piece.KNIGHT]:
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=target,
                                promotion=promo_piece,
                            )
                        )
                else:
                    moves.append(
                        Move(
                            from_square=from_square,
                            to_square=target,
                        )
                    )

                # Double push from starting rank
                if rank == start_rank:
                    double_target_rank = rank + (2 * direction)
                    double_target = Square(file=from_square.file, rank=double_target_rank)
                    if board.get(double_target) is None:
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=double_target,
                            )
                        )

        # Captures (diagonal)
        for file_delta in [-1, 1]:
            capture_file_idx = file_idx + file_delta
            if 0 <= capture_file_idx <= 7:
                capture_file = chr(ord('a') + capture_file_idx)
                capture_rank = rank + direction
                if 1 <= capture_rank <= 8:
                    capture_square = Square(file=capture_file, rank=capture_rank)

                    # Regular capture
                    target_piece = board.get(capture_square)
                    if target_piece is not None:
                        target_piece_type, target_color = target_piece
                        if target_color != color:
                            # Check if this is a promotion capture
                            if capture_rank == promotion_rank:
                                for promo_piece in [Piece.QUEEN, Piece.ROOK, Piece.BISHOP, Piece.KNIGHT]:
                                    moves.append(
                                        Move(
                                            from_square=from_square,
                                            to_square=capture_square,
                                            promotion=promo_piece,
                                            is_capture=True,
                                        )
                                    )
                            else:
                                moves.append(
                                    Move(
                                        from_square=from_square,
                                        to_square=capture_square,
                                        is_capture=True,
                                    )
                                )

                    # En passant capture
                    if en_passant_square is not None and capture_square == en_passant_square:
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=capture_square,
                                is_en_passant=True,
                                is_capture=True,
                            )
                        )

        return moves

    @staticmethod
    def generate_knight_moves(
        board: Board,
        from_square: Square,
        color: Color,
    ) -> list[Move]:
        """Generate pseudo-legal knight moves.

        Knights move in an L-shape: 2 squares in one direction and 1 square perpendicular.

        Args:
            board: Current board position
            from_square: Square the knight is on
            color: Color of the knight

        Returns:
            List of pseudo-legal moves
        """
        moves = []
        file_idx = from_square.file_index
        rank = from_square.rank

        # All 8 possible knight move offsets (file_delta, rank_delta)
        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]

        for file_delta, rank_delta in knight_offsets:
            target_file_idx = file_idx + file_delta
            target_rank = rank + rank_delta

            # Check if target is on board
            if 0 <= target_file_idx <= 7 and 1 <= target_rank <= 8:
                target_file = chr(ord('a') + target_file_idx)
                target_square = Square(file=target_file, rank=target_rank)

                target_piece = board.get(target_square)
                if target_piece is None:
                    # Empty square - can move there
                    moves.append(
                        Move(
                            from_square=from_square,
                            to_square=target_square,
                        )
                    )
                else:
                    # Square occupied - can capture if opponent's piece
                    _, target_color = target_piece
                    if target_color != color:
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=target_square,
                                is_capture=True,
                            )
                        )

        return moves

    @staticmethod
    def _generate_sliding_moves(
        board: Board,
        from_square: Square,
        color: Color,
        directions: list[tuple[int, int]],
    ) -> list[Move]:
        """Generate moves for sliding pieces (bishop, rook, queen).

        Args:
            board: Current board position
            from_square: Square the piece is on
            color: Color of the piece
            directions: List of (file_delta, rank_delta) direction tuples

        Returns:
            List of pseudo-legal moves
        """
        moves = []
        file_idx = from_square.file_index
        rank = from_square.rank

        for file_delta, rank_delta in directions:
            # Slide along this direction until blocked or off board
            current_file_idx = file_idx + file_delta
            current_rank = rank + rank_delta

            while 0 <= current_file_idx <= 7 and 1 <= current_rank <= 8:
                current_file = chr(ord('a') + current_file_idx)
                target_square = Square(file=current_file, rank=current_rank)

                target_piece = board.get(target_square)
                if target_piece is None:
                    # Empty square - can move there and continue sliding
                    moves.append(
                        Move(
                            from_square=from_square,
                            to_square=target_square,
                        )
                    )
                else:
                    # Square occupied
                    _, target_color = target_piece
                    if target_color != color:
                        # Can capture opponent's piece
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=target_square,
                                is_capture=True,
                            )
                        )
                    # Blocked - stop sliding in this direction
                    break

                current_file_idx += file_delta
                current_rank += rank_delta

        return moves

    @staticmethod
    def generate_bishop_moves(
        board: Board,
        from_square: Square,
        color: Color,
    ) -> list[Move]:
        """Generate pseudo-legal bishop moves (diagonal sliding).

        Args:
            board: Current board position
            from_square: Square the bishop is on
            color: Color of the bishop

        Returns:
            List of pseudo-legal moves
        """
        diagonal_directions = [
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # SW, NW, SE, NE
        ]
        return MoveGenerator._generate_sliding_moves(
            board, from_square, color, diagonal_directions
        )

    @staticmethod
    def generate_rook_moves(
        board: Board,
        from_square: Square,
        color: Color,
    ) -> list[Move]:
        """Generate pseudo-legal rook moves (orthogonal sliding).

        Args:
            board: Current board position
            from_square: Square the rook is on
            color: Color of the rook

        Returns:
            List of pseudo-legal moves
        """
        orthogonal_directions = [
            (0, -1), (0, 1), (-1, 0), (1, 0)  # Down, Up, Left, Right
        ]
        return MoveGenerator._generate_sliding_moves(
            board, from_square, color, orthogonal_directions
        )

    @staticmethod
    def generate_queen_moves(
        board: Board,
        from_square: Square,
        color: Color,
    ) -> list[Move]:
        """Generate pseudo-legal queen moves (bishop + rook combined).

        Args:
            board: Current board position
            from_square: Square the queen is on
            color: Color of the queen

        Returns:
            List of pseudo-legal moves
        """
        all_directions = [
            (-1, -1), (-1, 1), (1, -1), (1, 1),  # Diagonals
            (0, -1), (0, 1), (-1, 0), (1, 0)     # Orthogonals
        ]
        return MoveGenerator._generate_sliding_moves(
            board, from_square, color, all_directions
        )

    @staticmethod
    def generate_king_moves(
        board: Board,
        from_square: Square,
        color: Color,
        castling_rights: Optional["CastlingRights"] = None,
    ) -> list[Move]:
        """Generate pseudo-legal king moves (single step + castling).

        Args:
            board: Current board position
            from_square: Square the king is on
            color: Color of the king
            castling_rights: Current castling rights (optional)

        Returns:
            List of pseudo-legal moves
        """
        from pychess.model.game_state import CastlingRights

        moves = []
        file_idx = from_square.file_index
        rank = from_square.rank

        # All 8 single-step directions
        king_directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1)
        ]

        for file_delta, rank_delta in king_directions:
            target_file_idx = file_idx + file_delta
            target_rank = rank + rank_delta

            if 0 <= target_file_idx <= 7 and 1 <= target_rank <= 8:
                target_file = chr(ord('a') + target_file_idx)
                target_square = Square(file=target_file, rank=target_rank)

                target_piece = board.get(target_square)
                if target_piece is None:
                    moves.append(
                        Move(
                            from_square=from_square,
                            to_square=target_square,
                        )
                    )
                else:
                    _, target_color = target_piece
                    if target_color != color:
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=target_square,
                                is_capture=True,
                            )
                        )

        # Castling moves
        if castling_rights is not None:
            # Check position requirements for castling
            if color == Color.WHITE and from_square == Square.from_algebraic("e1"):
                # Kingside castling (O-O)
                if castling_rights.white_kingside:
                    if MoveGenerator._can_castle_kingside(board, color):
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=Square.from_algebraic("g1"),
                                is_castling=True,
                            )
                        )
                # Queenside castling (O-O-O)
                if castling_rights.white_queenside:
                    if MoveGenerator._can_castle_queenside(board, color):
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=Square.from_algebraic("c1"),
                                is_castling=True,
                            )
                        )
            elif color == Color.BLACK and from_square == Square.from_algebraic("e8"):
                # Kingside castling (O-O)
                if castling_rights.black_kingside:
                    if MoveGenerator._can_castle_kingside(board, color):
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=Square.from_algebraic("g8"),
                                is_castling=True,
                            )
                        )
                # Queenside castling (O-O-O)
                if castling_rights.black_queenside:
                    if MoveGenerator._can_castle_queenside(board, color):
                        moves.append(
                            Move(
                                from_square=from_square,
                                to_square=Square.from_algebraic("c8"),
                                is_castling=True,
                            )
                        )

        return moves

    @staticmethod
    def _can_castle_kingside(board: Board, color: Color) -> bool:
        """Check if kingside castling path is clear (no pieces between king and rook)."""
        rank = 1 if color == Color.WHITE else 8

        # Check f and g files are empty
        f_square = Square(file="f", rank=rank)
        g_square = Square(file="g", rank=rank)

        return board.get(f_square) is None and board.get(g_square) is None

    @staticmethod
    def _can_castle_queenside(board: Board, color: Color) -> bool:
        """Check if queenside castling path is clear (no pieces between king and rook)."""
        rank = 1 if color == Color.WHITE else 8

        # Check b, c, d files are empty
        b_square = Square(file="b", rank=rank)
        c_square = Square(file="c", rank=rank)
        d_square = Square(file="d", rank=rank)

        return (
            board.get(b_square) is None
            and board.get(c_square) is None
            and board.get(d_square) is None
        )
