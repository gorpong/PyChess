"""URL-safe invite-code generation.

Codes are short enough to text ("P4-K9N2X7"-style) and long enough that a
guessing attack on a live invite is not practical for a family-use server.
The service layer rejects collisions with a retry loop; this module only
knows how to produce a code.
"""

import secrets
import string

# 8 chars from an unambiguous 32-char alphabet (no 0/O, 1/I/L) gives
# 32**8 ≈ 1.1 * 10**12 possibilities. Collision risk at <1000 active
# matches is negligible; the service still checks uniqueness defensively.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_DEFAULT_LENGTH = 8


def generate_invite_code(length: int = _DEFAULT_LENGTH) -> str:
    """Generate a single URL-safe invite code from a cryptographic RNG."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
