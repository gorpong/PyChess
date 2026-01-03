"""Square representation for chess board positions."""

from dataclasses import dataclass

VALID_FILES = "abcdefgh"
VALID_RANKS = range(1, 9)


@dataclass(frozen=True)
class Square:
    """An immutable chess board square.

    Squares are identified by file (a-h) and rank (1-8).
    Immutable and hashable for use as dict keys or in sets.
    """

    file: str
    rank: int

    def __post_init__(self) -> None:
        """Validate file and rank after construction."""
        if self.file not in VALID_FILES:
            raise ValueError(
                f"Invalid file '{self.file}': must be one of {VALID_FILES}"
            )
        if self.rank not in VALID_RANKS:
            raise ValueError(
                f"Invalid rank {self.rank}: must be between 1 and 8"
            )

    @classmethod
    def from_algebraic(cls, notation: str) -> "Square":
        """Create a Square from algebraic notation like 'e4'.

        Accepts both uppercase and lowercase file letters.
        Raises ValueError for invalid notation.
        """
        if len(notation) < 2:
            raise ValueError(f"Invalid algebraic notation: '{notation}'")

        file = notation[0].lower()
        try:
            rank = int(notation[1])
        except ValueError:
            raise ValueError(f"Invalid rank in notation: '{notation}'")

        return cls(file=file, rank=rank)

    def to_algebraic(self) -> str:
        """Return algebraic notation for this square (e.g., 'e4')."""
        return f"{self.file}{self.rank}"

    @property
    def file_index(self) -> int:
        """Return 0-based index of the file (a=0, h=7)."""
        return ord(self.file) - ord("a")

    @property
    def rank_index(self) -> int:
        """Return 0-based index of the rank (1=0, 8=7)."""
        return self.rank - 1

    @property
    def is_light(self) -> bool:
        """Return True if this is a light square.

        A square is light if the sum of file_index and rank_index is even.
        (a1 is dark, h1 is light, a8 is light, h8 is dark)
        """
        return (self.file_index + self.rank_index) % 2 == 1

    def __str__(self) -> str:
        """Return algebraic notation."""
        return self.to_algebraic()

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"Square(file='{self.file}', rank={self.rank})"
