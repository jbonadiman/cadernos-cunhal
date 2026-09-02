"""Heuristics to separate transcribed prose from static UI text runs that
live in the same SWF frame (e.g. the always-visible page-number footer)."""

import re

_DIGITS_AND_WHITESPACE_RE = re.compile(r"^[\d\s]+$")


def is_navigation_label(text: str) -> bool:
    """True for text runs that are purely digits/whitespace, e.g. the
    "1  2  3 ... 16" page-number footer. Empty/whitespace-only text is not
    considered a navigation label (it's just empty, not a footer)."""
    stripped = text.strip()
    if not stripped:
        return False
    return bool(_DIGITS_AND_WHITESPACE_RE.match(stripped))
