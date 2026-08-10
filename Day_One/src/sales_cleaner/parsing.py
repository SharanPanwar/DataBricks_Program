"""Field-level parsing helpers.

Every function here follows the same contract: it takes whatever ugly string the
CSV actually contained and returns either a clean typed value or None. None means
"absent or unparseable" — it never means zero, and it never raises. Deciding what
to *do* about a None is the caller's job, not ours.

That separation is deliberate. Parsing that raises forces the caller to wrap every
call in try/except, and the usual result is a bare `except:` that swallows real
bugs alongside bad data.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Values that different upstream systems use to mean "nothing here".
# Compared case-insensitively after stripping.
NULL_TOKENS: frozenset[str] = frozenset(
    {"", "na", "n/a", "null", "none", "-", "--", "nil", "nan", "?"}
)

# The three date formats this source is known to emit. Order matters:
# %d/%m/%Y is tried before %m/%d/%Y because this feed is European-formatted.
DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",      # 2024-01-15
    "%d/%m/%Y",      # 15/01/2024
    "%d-%m-%Y",      # 15-01-2024
    "%b %d %Y",      # Jan 15 2024
    "%d %b %Y",      # 15 Jan 2024
    "%Y/%m/%d",      # 2024/01/15
)

# Currency symbols and separators we strip before parsing a number.
_AMOUNT_STRIP = re.compile(r"[₹$€£,\s]")
_TRAILING_MINUS = re.compile(r"^(?P<body>[\d.]+)-$")
_PARENTHESISED = re.compile(r"^\((?P<body>.+)\)$")


def is_null(raw: str | None) -> bool:
    """True when the raw field means 'no value'.

    Handles the six different spellings of nothing that show up in this feed.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.
    # None (missing dict key / short CSV row) is null by definition — check
    # this first so .strip() below never runs on None and blows up.
    if raw is None:
        return True
    # Strip + lowercase so "NULL", " null ", "Null" all match one token set.
    return raw.strip().lower() in NULL_TOKENS

def normalise_text(raw: str | None, *, title_case: bool = False) -> str | None:
    """Collapse whitespace and optionally title-case a text field.

    Returns None for null-ish input rather than an empty string, so that a
    missing region and a region literally named "" cannot be confused.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.
    # Reuse is_null rather than re-deriving "empty-ish" logic here — one
    # source of truth for what counts as "no value".
    if is_null(raw):
        return None
    # \s+ -> single space collapses "ravi   kumar" / "  ravi kumar "
    # in one pass, instead of chaining multiple .replace() calls.
    collapsed = re.sub(r"\s+", " ", raw.strip())
    if not collapsed:
        return None
    # title_case is opt-in: order_id/product shouldn't be reshaped the same
    # way customer_name/region are.
    return collapsed.title() if title_case else collapsed

def parse_date(raw: str | None) -> date | None:
    """Parse a date written in any of the formats this feed uses.

    Returns None when the value is missing or matches none of the known formats.
    A date that parses but is obviously wrong (year 1900, year 2999) is still
    returned — range checking is a validation concern, not a parsing one.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.
    if is_null(raw):
        return None
    candidate = raw.strip()
    # Try each known format in turn; DATE_FORMATS already encodes the
    # day-first-over-month-first ordering the module docstring calls out,
    # so we don't need any extra disambiguation logic here.
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).date()  # noqa: DTZ007 (date-only, tz is irrelevant)
        except ValueError:
            continue
    # None of the formats matched — unparseable, not an error.
    return None

def parse_amount(raw: str | None) -> Decimal | None:
    """Parse a monetary amount into a Decimal.

    Handles currency symbols, thousands separators, parenthesised negatives
    (1,200.00) and trailing-minus negatives (1200.00-), both of which appear in
    exports from older accounting systems.

    Decimal rather than float: money in a float is a bug waiting for a reconciliation
    meeting. 0.1 + 0.2 != 0.3 and finance will notice.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.
    if is_null(raw):
        return None
    candidate = raw.strip()

    # Order matters: check for the parenthesised form *before* stripping
    # currency symbols, because the parens wrap the symbol+digits together,
    # e.g. "($1,200.00)" — stripping first would break the regex anchor.
    negative = False
    paren_match = _PARENTHESISED.match(candidate)
    if paren_match:
        negative = True
        candidate = paren_match.group("body")

    # Now it's safe to drop currency symbols, thousands separators, and
    # whitespace — none of them carry sign information.
    candidate = _AMOUNT_STRIP.sub("", candidate)

    # Trailing-minus is the other accounting-negative convention ("1200.00-").
    # Checked after symbol-stripping so "$1200.00-" also works.
    trailing_match = _TRAILING_MINUS.match(candidate)
    if trailing_match:
        negative = True
        candidate = trailing_match.group("body")

    if not candidate:
        return None

    try:
        value = Decimal(candidate)
    except InvalidOperation:
        # e.g. "twelve hundred" — parses to garbage, not a number. Return
        # None rather than raising, per the module contract.
        return None

    # -abs() rather than a plain negation: guards against a value that is
    # already negative (e.g. "-750") getting double-negated by a spurious
    # match on either regex above.
    return -abs(value) if negative else value

def parse_int(raw: str | None) -> int | None:
    """Parse an integer, tolerating separators and a stray decimal .0 suffix."""
    # IMPLEMENTED: was `raise NotImplementedError`.
    if is_null(raw):
        return None
    # Reuse _AMOUNT_STRIP to drop thousands separators/whitespace — the
    # same cleanup a currency amount needs, minus the sign handling.
    candidate = _AMOUNT_STRIP.sub("", raw.strip())
    if not candidate:
        return None
    try:
        # Parse via Decimal (not int()/float()) so "4.0" is accepted but the
        # fractional part is still checked before truncating it away.
        value = Decimal(candidate)
    except InvalidOperation:
        return None
    # to_integral_value() rounds "4.0" -> 4 harmlessly (4 == 4), but for a
    # genuine decimal like "4.5" the rounded value (4 or 5) will not equal
    # the original 4.5, so this correctly rejects it instead of silently
    # truncating/rounding a real fraction into a fake integer.
    if value != value.to_integral_value():
        return None
    return int(value)