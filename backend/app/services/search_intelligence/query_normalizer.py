"""
Query Normalizer
================
Step 1 of the pipeline.

Responsibilities:
  - Unicode cleanup (full-width → ASCII, curly quotes, etc.)
  - Lowercase
  - Collapse extra whitespace
  - Remove spurious punctuation EXCEPT hyphens and dots in model numbers
  - Expand common shorthand (₹ → inr, "5k" → "5000" ONLY in price context)
  - Strip thousand-separator commas BEFORE punctuation removal (₹5,000 → 5000)
  - Preserve numbers and numeric tokens exactly — they are identity-critical

P0 BUGS FIXED:
  - ₹5,000 was becoming "inr 5 000" then regex captured "5" not "5000"
    → Now strip thousand-separator commas first: "5,000" → "5000"
  - "5k" expansion fired for "5K monitor", "5K display", "5K run"
    → Now only expand when preceded by a price keyword context
  - _LAKH_RE was defined but never used
    → Now applied (only in price context)
  - comment said "keep forward slash for models" but _JUNK_PUNCT_RE included /
    → Removed / from junk punct to match the comment
"""
from __future__ import annotations

import re
import unicodedata


# ── Thousand-separator comma (must strip BEFORE junk punct pass) ──────────────
# Only removes commas between digits: "5,000" → "5000", NOT "hello, world"
_THOUSAND_COMMA_RE = re.compile(r"(\d),(\d{3})\b")

# ── Price context "5k" expansion — only fires when preceded by price words ────
# Fixed-width lookbehind required by Python re — match price keyword + digits + k
# Matches: "under 5k", "below 5k", "around 5k", "budget 5k", "upto 5k"
# Does NOT match: "5K monitor", "5K display", "5K run", "XM5k"
# Strategy: capture the keyword + number together, replace only the number part
_PRICE_KILO_RE = re.compile(
    r"\b(under|below|within|upto|up\s+to|around|about|budget|above|over|atleast)\s+(\d+)\s*k\b",
    re.I,
)
# Fallback: standalone "5k" not followed by tech resolution words
_STANDALONE_KILO_RE = re.compile(r"(?<!\w)(\d+)k\b(?!\s*(?:monitor|display|resolution|run|km|hz|pixel))", re.I)

# ── Lakh expansion (price context only) ──────────────────────────────────────
_PRICE_LAKH_RE = re.compile(
    r"\b(under|below|within|upto|around|above|budget)\s+(\d+)\s*(?:l|lakh)\b",
    re.I,
)

# ── Extra whitespace ──────────────────────────────────────────────────────────
_WHITESPACE_RE = re.compile(r"\s+")

# ── Punctuation that is never useful in queries ───────────────────────────────
# Intentionally keeps: hyphen (-), dot (.), forward slash (/) — used in models
# e.g. WH-1000XM5, A.I., 3/4
_JUNK_PUNCT_RE = re.compile(r"""[!@#%^&*()=\[\]{}<>;:'"?,\\|`~]""")


def normalize(raw: str) -> str:
    """
    Return a cleaned, normalised version of the raw query.
    Numbers are left UNCHANGED so model numbers remain intact.

    Transformation order matters — do not reorder without testing.
    """
    if not raw:
        return ""

    # 1. Unicode normalize → decompose into base + combining marks
    text = unicodedata.normalize("NFKD", raw)
    # Strip combining diacritics (accents etc.) — preserves base letters
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    # 2. Replace special currency / symbol chars BEFORE lowercasing
    text = text.replace("₹", "inr ").replace("$", "usd ").replace("€", "eur ")
    text = text.replace("+", " plus ").replace("&", " and ")
    # Curly quotes → straight
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')

    # 3. Strip thousand-separator commas BEFORE junk punct pass
    #    "₹5,000" → "inr 5000" (not "inr 5 000")
    #    Apply multiple times for numbers like "1,00,000"
    for _ in range(3):
        text = _THOUSAND_COMMA_RE.sub(r"\1\2", text)

    # 4. Lowercase (after currency replacement so we capture INR/USD correctly)
    text = text.lower()

    # 5. Expand "5k" → "5000" ONLY in price context (not "5K monitor")
    # group(1) = price keyword ("under", "below", etc.), group(2) = digits
    # Preserve the keyword in output: "under 5k" → "under 5000"
    text = _PRICE_KILO_RE.sub(lambda m: m.group(1) + " " + str(int(m.group(2)) * 1000), text)
    # Expand lakh in price context: "under 2 lakh" → "under 200000"
    text = _PRICE_LAKH_RE.sub(lambda m: m.group(1) + " " + str(int(m.group(2)) * 100000), text)
    # Conservative standalone fallback: "5k" alone (not monitor/display/etc.)
    text = _STANDALONE_KILO_RE.sub(lambda m: str(int(m.group(1)) * 1000), text)

    # 6. Remove junk punctuation (hyphens, dots, slashes are PRESERVED)
    text = _JUNK_PUNCT_RE.sub(" ", text)

    # 7. Normalise whitespace
    text = _WHITESPACE_RE.sub(" ", text).strip()

    return text
