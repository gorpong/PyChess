"""Tests for Standard Algebraic Notation (SAN) parsing and generation."""

import pytest

from pychess.model.board import Board
from pychess.model.game_state import GameState, CastlingRights
from pychess.model.piece import Piece, Color
from pychess.model.square import Square
from pychess.rules.move import Move
from pychess.notation.san import move_to_san, san_to_move


class TestMoveToSanPawnMoves:
    """Tests for converting pawn moves to SAN."""

    def test_pawn_single_push_e4(self):
        """Pawn e2-e4 becomes 'e4'."""
        state = GameState.initial()
        move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4")
        )
        assert move_to_san(state, move) == "e4"

    def test_pawn_single_push_d3(self):
        """Pawn d2-d3 becomes 'd3'."""
        state = GameState.initial()
        move = Move(
            from_square=Square.from_algebraic("d2"),
            to_square=Square.from_algebraic("d3")
        )
        assert move_to_san(state, move) == "d3"

    def test_pawn_capture(self):
        """Pawn capture exd5."""
        board = (Board.initial()
                 .remove(Square.from_algebraic("e2"))
                 .set(Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE)
                 .remove(Square.from_algebraic("d7"))
                 .set(Square.from_algebraic("d5"), Piece.PAWN, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e4"),
            to_square=Square.from_algebraic("d5"),
            is_capture=True
        )
        assert move_to_san(state, move) == "exd5"

    def test_pawn_promotion(self):
        """Pawn promotion e8=Q."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.QUEEN
        )
        assert move_to_san(state, move) == "e8=Q"

    def test_pawn_promotion_knight(self):
        """Pawn promotion to knight e8=N."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("e8"),
            promotion=Piece.KNIGHT
        )
        assert move_to_san(state, move) == "e8=N"

    def test_pawn_capture_promotion(self):
        """Pawn capture with promotion exd8=Q."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("d8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.KING, Color.BLACK))  # King far from d8 queen
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e7"),
            to_square=Square.from_algebraic("d8"),
            promotion=Piece.QUEEN,
            is_capture=True
        )
        assert move_to_san(state, move) == "exd8=Q"

    def test_en_passant_capture(self):
        """En passant capture exd6."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e5"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("d5"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = (GameState.initial()
                 .with_board(board)
                 .with_en_passant(Square.from_algebraic("d6")))

        move = Move(
            from_square=Square.from_algebraic("e5"),
            to_square=Square.from_algebraic("d6"),
            is_en_passant=True,
            is_capture=True
        )
        assert move_to_san(state, move) == "exd6"


class TestMoveToSanPieceMoves:
    """Tests for converting piece moves to SAN."""

    def test_knight_move(self):
        """Knight move Nf3."""
        state = GameState.initial()
        move = Move(
            from_square=Square.from_algebraic("g1"),
            to_square=Square.from_algebraic("f3")
        )
        assert move_to_san(state, move) == "Nf3"

    def test_bishop_move(self):
        """Bishop move after opening."""
        board = (Board.initial()
                 .remove(Square.from_algebraic("e2"))
                 .set(Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("f1"),
            to_square=Square.from_algebraic("b5")
        )
        assert move_to_san(state, move) == "Bb5"

    def test_rook_move(self):
        """Rook move."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("a1"),
            to_square=Square.from_algebraic("a5")
        )
        assert move_to_san(state, move) == "Ra5"

    def test_queen_move(self):
        """Queen move."""
        board = (Board.empty()
                 .set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK))  # Not on e-file or h5 diagonal
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("d1"),
            to_square=Square.from_algebraic("h5")
        )
        assert move_to_san(state, move) == "Qh5"

    def test_king_move(self):
        """King move."""
        state = GameState.initial()
        # First need to move pawn to allow king move
        board = (Board.initial()
                 .remove(Square.from_algebraic("e2"))
                 .set(Square.from_algebraic("e3"), Piece.PAWN, Color.WHITE))
        state = state.with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e1"),
            to_square=Square.from_algebraic("e2")
        )
        assert move_to_san(state, move) == "Ke2"

    def test_piece_capture(self):
        """Piece capture Bxc6."""
        board = (Board.empty()
                 .set(Square.from_algebraic("b5"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("c6"), Piece.KNIGHT, Color.BLACK)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK))  # Not on bishop diagonal
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("b5"),
            to_square=Square.from_algebraic("c6"),
            is_capture=True
        )
        assert move_to_san(state, move) == "Bxc6"


class TestMoveToSanDisambiguation:
    """Tests for disambiguation in SAN."""

    def test_disambiguation_by_file(self):
        """Two rooks on same rank - disambiguate by file: Rad1."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("f1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.KING, Color.WHITE)  # Moved king off d-file
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK))  # Not on d-file
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("a1"),
            to_square=Square.from_algebraic("d1")
        )
        assert move_to_san(state, move) == "Rad1"

    def test_disambiguation_by_rank(self):
        """Two rooks on same file - disambiguate by rank: R1a3."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("a7"), Piece.ROOK, Color.WHITE)  # Changed to a7 instead of a8
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK))  # Not on a-file
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("a1"),
            to_square=Square.from_algebraic("a3")
        )
        assert move_to_san(state, move) == "R1a3"

    def test_disambiguation_by_both(self):
        """Three queens - need both file and rank: Qd4d2."""
        # d4 queen can reach d2 (same file)
        # d1 queen can reach d2 (same file)
        # a4 queen can reach d4 via rank (but we move to d2)
        # Actually, let's use a cleaner setup:
        # Queens on d4, d1, and b4 - moving d4 to d2
        # d1 shares file with d4
        # b4 shares rank with d4 (but can't reach d2)
        # Hmm, b4 can't reach d2 either (file diff 2, rank diff -2, so diagonal yes!)
        # Let's use d4, d1, b2 all reaching d2
        board = (Board.empty()
                 .set(Square.from_algebraic("d4"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("d1"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("b2"), Piece.QUEEN, Color.WHITE)  # Can reach d2 diagonally
                 .set(Square.from_algebraic("a1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        # d4 to d2: d1 is on same file (d), b2 is on same rank (would be 2 after move but b2 is on rank 2)
        # Wait, candidates are pieces that can reach d2, not the moving piece's position
        # d1 shares file 'd' with d4
        # b2: to check if it can reach d2: file diff = 2, rank diff = 0, orthogonal, yes!
        # So both d1 and b2 can reach d2
        # From d4's perspective:
        # - same_file: d1 has file 'd' same as d4, yes
        # - same_rank: b2 has rank 2, d4 has rank 4, no
        # So just rank would work: Q4d2
        # For true "both" disambiguation, we need:
        # Queens on d4, d8, h4 all able to reach d2... but d8 can reach d2 (same file), h4 can reach d2 if diagonal
        # h4 to d2: file diff = -4, rank diff = -2, not diagonal
        # Let me try: d4, f4, d2 all reaching f2
        # d4 to f2: diagonal (diff 2, -2) yes
        # f4 to f2: same file, yes
        # d2 to f2: same rank, yes
        # From d4: f4 not same file, d2 not same rank -> file alone works! Qdf2
        # Actually I need candidates that share BOTH file AND rank with the source
        # That requires 3+ queens where at least one shares file and another shares rank
        # d4, d6, b4 -> d4 to c3 (diagonal)
        # d6 to c3: file diff -1, rank diff -3, no
        # b4 to c3: file diff 1, rank diff -1, diagonal yes
        # Only b4 can reach c3, so no disambiguation needed
        # Let me try d5, d3, f5 all reaching e4
        # d5 to e4: file 1, rank -1, diagonal yes
        # d3 to e4: file 1, rank 1, diagonal yes
        # f5 to e4: file -1, rank -1, diagonal yes
        # From d5: d3 same file 'd', f5 same rank '5'
        # So we need both: Qd5e4
        board = (Board.empty()
                 .set(Square.from_algebraic("d5"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("d3"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("f5"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("d5"),
            to_square=Square.from_algebraic("e4")
        )
        assert move_to_san(state, move) == "Qd5e4"

    def test_knight_disambiguation_by_file(self):
        """Two knights can reach same square - disambiguate: Nbd2."""
        board = (Board.empty()
                 .set(Square.from_algebraic("b1"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("f3"), Piece.KNIGHT, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("b1"),
            to_square=Square.from_algebraic("d2")
        )
        assert move_to_san(state, move) == "Nbd2"


class TestMoveToSanCastling:
    """Tests for castling notation."""

    def test_kingside_castling(self):
        """Kingside castling O-O."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e1"),
            to_square=Square.from_algebraic("g1"),
            is_castling=True
        )
        assert move_to_san(state, move) == "O-O"

    def test_queenside_castling(self):
        """Queenside castling O-O-O."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("e1"),
            to_square=Square.from_algebraic("c1"),
            is_castling=True
        )
        assert move_to_san(state, move) == "O-O-O"

    def test_black_kingside_castling(self):
        """Black kingside castling O-O."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("h8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE))
        state = GameState.initial().with_board(board).with_turn(Color.BLACK)

        move = Move(
            from_square=Square.from_algebraic("e8"),
            to_square=Square.from_algebraic("g8"),
            is_castling=True
        )
        assert move_to_san(state, move) == "O-O"


class TestMoveToSanCheckAndMate:
    """Tests for check and checkmate notation."""

    def test_move_gives_check(self):
        """Move that gives check: Bb5+."""
        board = (Board.empty()
                 .set(Square.from_algebraic("c4"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("c4"),
            to_square=Square.from_algebraic("b5")
        )
        # After Bb5, black king on e8 would be in check from bishop on diagonal
        assert move_to_san(state, move) == "Bb5+"

    def test_move_gives_checkmate(self):
        """Move that gives checkmate: Qxf7#."""
        # Scholar's mate final position setup - king trapped
        board = (Board.empty()
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("d7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("d8"), Piece.QUEEN, Color.BLACK)  # Blocks d8 escape
                 .set(Square.from_algebraic("f8"), Piece.BISHOP, Color.BLACK)  # Blocks f8 escape
                 .set(Square.from_algebraic("h5"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("c4"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE))
        state = GameState.initial().with_board(board)

        move = Move(
            from_square=Square.from_algebraic("h5"),
            to_square=Square.from_algebraic("f7"),
            is_capture=True
        )
        assert move_to_san(state, move) == "Qxf7#"


class TestSanToMovePawnMoves:
    """Tests for parsing pawn moves from SAN."""

    def test_parse_e4(self):
        """Parse 'e4' to pawn move."""
        state = GameState.initial()
        move = san_to_move(state, "e4")

        assert move.from_square == Square.from_algebraic("e2")
        assert move.to_square == Square.from_algebraic("e4")

    def test_parse_d3(self):
        """Parse 'd3' to pawn move."""
        state = GameState.initial()
        move = san_to_move(state, "d3")

        assert move.from_square == Square.from_algebraic("d2")
        assert move.to_square == Square.from_algebraic("d3")

    def test_parse_pawn_capture(self):
        """Parse 'exd5' to pawn capture."""
        board = (Board.initial()
                 .remove(Square.from_algebraic("e2"))
                 .set(Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE)
                 .remove(Square.from_algebraic("d7"))
                 .set(Square.from_algebraic("d5"), Piece.PAWN, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "exd5")

        assert move.from_square == Square.from_algebraic("e4")
        assert move.to_square == Square.from_algebraic("d5")
        assert move.is_capture

    def test_parse_promotion(self):
        """Parse 'e8=Q' to pawn promotion."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "e8=Q")

        assert move.from_square == Square.from_algebraic("e7")
        assert move.to_square == Square.from_algebraic("e8")
        assert move.promotion == Piece.QUEEN

    def test_parse_capture_promotion(self):
        """Parse 'exd8=N' to capture with promotion."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.WHITE)
                 .set(Square.from_algebraic("d8"), Piece.ROOK, Color.BLACK)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "exd8=N")

        assert move.from_square == Square.from_algebraic("e7")
        assert move.to_square == Square.from_algebraic("d8")
        assert move.promotion == Piece.KNIGHT
        assert move.is_capture


class TestSanToMovePieceMoves:
    """Tests for parsing piece moves from SAN."""

    def test_parse_nf3(self):
        """Parse 'Nf3' to knight move."""
        state = GameState.initial()
        move = san_to_move(state, "Nf3")

        assert move.from_square == Square.from_algebraic("g1")
        assert move.to_square == Square.from_algebraic("f3")

    def test_parse_bb5(self):
        """Parse 'Bb5' to bishop move."""
        board = (Board.initial()
                 .remove(Square.from_algebraic("e2"))
                 .set(Square.from_algebraic("e4"), Piece.PAWN, Color.WHITE))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "Bb5")

        assert move.from_square == Square.from_algebraic("f1")
        assert move.to_square == Square.from_algebraic("b5")

    def test_parse_piece_capture(self):
        """Parse 'Bxc6' to bishop capture."""
        board = (Board.empty()
                 .set(Square.from_algebraic("b5"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("c6"), Piece.KNIGHT, Color.BLACK)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "Bxc6")

        assert move.from_square == Square.from_algebraic("b5")
        assert move.to_square == Square.from_algebraic("c6")
        assert move.is_capture


class TestSanToMoveDisambiguation:
    """Tests for parsing disambiguated moves."""

    def test_parse_rad1(self):
        """Parse 'Rad1' - disambiguated by file."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("f1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "Rad1")

        assert move.from_square == Square.from_algebraic("a1")
        assert move.to_square == Square.from_algebraic("d1")

    def test_parse_r1a3(self):
        """Parse 'R1a3' - disambiguated by rank."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("a8"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "R1a3")

        assert move.from_square == Square.from_algebraic("a1")
        assert move.to_square == Square.from_algebraic("a3")

    def test_parse_qh4e1(self):
        """Parse 'Qh4e1' - disambiguated by both file and rank."""
        board = (Board.empty()
                 .set(Square.from_algebraic("h4"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("a4"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "Qh4e1")

        assert move.from_square == Square.from_algebraic("h4")
        assert move.to_square == Square.from_algebraic("e1")


class TestSanToMoveCastling:
    """Tests for parsing castling notation."""

    def test_parse_kingside_castling(self):
        """Parse 'O-O' to kingside castling."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "O-O")

        assert move.from_square == Square.from_algebraic("e1")
        assert move.to_square == Square.from_algebraic("g1")
        assert move.is_castling

    def test_parse_queenside_castling(self):
        """Parse 'O-O-O' to queenside castling."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "O-O-O")

        assert move.from_square == Square.from_algebraic("e1")
        assert move.to_square == Square.from_algebraic("c1")
        assert move.is_castling


class TestSanToMoveCheckAnnotations:
    """Tests for parsing check/mate annotations."""

    def test_parse_with_check(self):
        """Parse 'Bb5+' - move with check annotation."""
        board = (Board.empty()
                 .set(Square.from_algebraic("c4"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "Bb5+")

        assert move.from_square == Square.from_algebraic("c4")
        assert move.to_square == Square.from_algebraic("b5")

    def test_parse_with_checkmate(self):
        """Parse 'Qxf7#' - move with checkmate annotation."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK)
                 .set(Square.from_algebraic("f7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("d7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("e7"), Piece.PAWN, Color.BLACK)
                 .set(Square.from_algebraic("h5"), Piece.QUEEN, Color.WHITE)
                 .set(Square.from_algebraic("c4"), Piece.BISHOP, Color.WHITE)
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE))
        state = GameState.initial().with_board(board)

        move = san_to_move(state, "Qxf7#")

        assert move.from_square == Square.from_algebraic("h5")
        assert move.to_square == Square.from_algebraic("f7")
        assert move.is_capture


class TestSanRoundTrip:
    """Tests for round-trip conversion (move -> SAN -> move)."""

    def test_roundtrip_pawn_move(self):
        """Round-trip pawn move."""
        state = GameState.initial()
        original_move = Move(
            from_square=Square.from_algebraic("e2"),
            to_square=Square.from_algebraic("e4")
        )

        san = move_to_san(state, original_move)
        parsed_move = san_to_move(state, san)

        assert parsed_move.from_square == original_move.from_square
        assert parsed_move.to_square == original_move.to_square

    def test_roundtrip_knight_move(self):
        """Round-trip knight move."""
        state = GameState.initial()
        original_move = Move(
            from_square=Square.from_algebraic("g1"),
            to_square=Square.from_algebraic("f3")
        )

        san = move_to_san(state, original_move)
        parsed_move = san_to_move(state, san)

        assert parsed_move.from_square == original_move.from_square
        assert parsed_move.to_square == original_move.to_square

    def test_roundtrip_castling(self):
        """Round-trip castling move."""
        board = (Board.empty()
                 .set(Square.from_algebraic("e1"), Piece.KING, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("e8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)
        original_move = Move(
            from_square=Square.from_algebraic("e1"),
            to_square=Square.from_algebraic("g1"),
            is_castling=True
        )

        san = move_to_san(state, original_move)
        parsed_move = san_to_move(state, san)

        assert parsed_move.from_square == original_move.from_square
        assert parsed_move.to_square == original_move.to_square
        assert parsed_move.is_castling == original_move.is_castling


class TestSanInvalidInput:
    """Tests for handling invalid SAN input."""

    def test_invalid_san_raises_error(self):
        """Invalid SAN should raise ValueError."""
        state = GameState.initial()
        with pytest.raises(ValueError):
            san_to_move(state, "xyz123")

    def test_illegal_move_raises_error(self):
        """SAN for illegal move should raise ValueError."""
        state = GameState.initial()
        # e5 is not legal for white on first move (pawn is on e2)
        with pytest.raises(ValueError):
            san_to_move(state, "e5")

    def test_ambiguous_move_raises_error(self):
        """Ambiguous move without disambiguation should raise ValueError."""
        board = (Board.empty()
                 .set(Square.from_algebraic("a1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("f1"), Piece.ROOK, Color.WHITE)
                 .set(Square.from_algebraic("h1"), Piece.KING, Color.WHITE)  # King on h1, both rooks can reach d1
                 .set(Square.from_algebraic("h8"), Piece.KING, Color.BLACK))
        state = GameState.initial().with_board(board)

        # Both rooks can go to d1, so "Rd1" is ambiguous
        with pytest.raises(ValueError):
            san_to_move(state, "Rd1")
