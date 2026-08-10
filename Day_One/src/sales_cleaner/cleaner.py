"""Row-level cleaning, validation and deduplication.

Design decision worth being able to defend in a review: bad rows are *rejected*,
not dropped. Every row that does not make it into the clean output comes out in
the rejects list with a human-readable reason. A pipeline that silently discards
rows is a pipeline nobody can trust, and "the numbers don't match" is the most
expensive conversation in data engineering.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from .parsing import normalise_text, parse_amount, parse_date, parse_int

# The columns the downstream contract requires. Anything else in the file is
# ignored rather than passed through — an unexpected column is not our problem
# to solve, but it is our problem to not propagate.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "order_id",
    "order_date",
    "customer_name",
    "region",
    "product",
    "quantity",
    "unit_price",
)


@dataclass(frozen=True, slots=True)
class CleanRow:
    """A validated sales row. Immutable on purpose — nothing downstream edits it."""

    order_id: str
    order_date: date
    customer_name: str
    region: str
    product: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def as_dict(self) -> dict[str, str]:
        return {
            "order_id": self.order_id,
            "order_date": self.order_date.isoformat(),
            "customer_name": self.customer_name,
            "region": self.region,
            "product": self.product,
            "quantity": str(self.quantity),
            "unit_price": f"{self.unit_price:.2f}",
            "line_total": f"{self.line_total:.2f}",
        }


@dataclass(frozen=True, slots=True)
class RejectedRow:
    """A row that failed validation, kept with the reason and its source line."""

    source_line: int
    reason: str
    raw: dict[str, str]

    def as_dict(self) -> dict[str, str]:
        return {
            "source_line": str(self.source_line),
            "reason": self.reason,
            "order_id": self.raw.get("order_id", ""),
            "raw": "|".join(f"{k}={v}" for k, v in self.raw.items()),
        }


@dataclass(slots=True)
class CleanResult:
    """What came out of a clean run: the good rows, the bad rows, and counts."""

    clean: list[CleanRow] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)
    duplicates_removed: int = 0

    @property
    def total_in(self) -> int:
        return len(self.clean) + len(self.rejected) + self.duplicates_removed

    def summary(self) -> str:
        return (
            f"in={self.total_in} clean={len(self.clean)} "
            f"rejected={len(self.rejected)} duplicates_removed={self.duplicates_removed}"
        )


class MissingColumnsError(ValueError):
    """Raised when the file does not have the columns the contract requires.

    This one *does* raise, unlike the parsing helpers. A missing column is a
    structural failure of the whole file — there is no sensible per-row recovery,
    and continuing would produce a clean-looking output that is silently wrong.
    """

    def __init__(self, missing: Iterable[str]) -> None:
        self.missing = sorted(missing)
        super().__init__(f"missing required columns: {', '.join(self.missing)}")


def _normalise_header(name: str) -> str:
    """Header names arrive with stray spaces, mixed case and the odd BOM."""
    return name.replace("\ufeff", "").strip().lower().replace(" ", "_")


def clean_row(raw: dict[str, str], source_line: int) -> CleanRow | RejectedRow:
    """Validate and convert one raw row.

    Returns a CleanRow or a RejectedRow — never raises, and never returns None.
    A union return type keeps the caller honest: they have to handle both.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.

    # Local helper so every rejection carries the same shape (line number +
    # reason + a copy of the original raw row) without repeating it seven times.
    def reject(reason: str) -> RejectedRow:
        # dict(raw) copies the row so a later mutation of the source dict
        # (e.g. the CSV reader reusing a buffer) can't retroactively change
        # what a rejected row's raw data looked like.
        return RejectedRow(source_line=source_line, reason=reason, raw=dict(raw))

    # Checks run in REQUIRED_COLUMNS order and return on first failure.
    # This matches the test suite's expectation of one specific reason per
    # bad row (test_bad_rows_are_rejected_with_a_readable_reason mutates one
    # field at a time and expects exactly one matching reason string back).

    # order_id: no title_case — an order id is an identifier, not prose.
    order_id = normalise_text(raw.get("order_id"))
    if order_id is None:
        return reject("missing order_id")

    order_date = parse_date(raw.get("order_date"))
    if order_date is None:
        return reject("unparseable or missing order_date")

    # customer_name / region / product: title_case=True because these are
    # the free-text fields the README calls out as arriving in mixed case
    # ("ravi kumar", "PRIYA SHARMA", "SOUTH").
    customer_name = normalise_text(raw.get("customer_name"), title_case=True)
    if customer_name is None:
        return reject("missing customer_name")

    region = normalise_text(raw.get("region"), title_case=True)
    if region is None:
        return reject("missing region")

    product = normalise_text(raw.get("product"), title_case=True)
    if product is None:
        return reject("missing product")

    # Parsing and validation are deliberately separate checks here (per the
    # README's design-decisions section): parse_int can return a value that
    # then still fails a business rule.
    quantity = parse_int(raw.get("quantity"))
    if quantity is None:
        return reject("unparseable or missing quantity")
    if quantity <= 0:
        # Covers both the negative-quantity test (-2) and the zero-quantity
        # test (0) with one rule: a sale of zero or fewer units isn't a sale.
        return reject("quantity must be positive")

    # Same parse-then-validate split for money: (1200.00) parses fine to
    # -1200.00, and *that's* what gets rejected here, not the parsing step.
    # This is the credit-note-vs-sale distinction the README warns about.
    unit_price = parse_amount(raw.get("unit_price"))
    if unit_price is None:
        return reject("unparseable or missing unit_price")
    if unit_price < 0:
        return reject("unit_price must not be negative")

    return CleanRow(
        order_id=order_id,
        order_date=order_date,
        customer_name=customer_name,
        region=region,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
    )

def deduplicate(rows: Iterable[CleanRow]) -> tuple[list[CleanRow], int]:
    """Keep the latest row per order_id.

    'Latest' means the highest order_date; where two rows share a date, the one
    that appeared later in the file wins, because that is the convention this
    source uses for corrections.

    Returns (kept_rows, number_removed). Order of the input is preserved for the
    rows that survive, which makes the output diffable between runs.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.
    rows = list(rows)

    # Track the winning (index, row) per order_id. Keeping the original
    # index alongside the row is what lets the tie-break rule ("later row
    # in the file wins") work without depending on dict insertion order.
    best_by_id: dict[str, tuple[int, CleanRow]] = {}

    for index, row in enumerate(rows):
        current = best_by_id.get(row.order_id)
        if current is None:
            best_by_id[row.order_id] = (index, row)
            continue
        current_index, current_row = current
        # A row wins if its date is strictly later, OR the date ties and it
        # appeared later in the file (higher index = later = the correction).
        is_later = row.order_date > current_row.order_date or (
            row.order_date == current_row.order_date and index > current_index
        )
        if is_later:
            best_by_id[row.order_id] = (index, row)

    # Sort survivors back into original file order (not insertion order of
    # the dict) so re-running the pipeline is diffable, per the docstring.
    kept_indices = sorted(index for index, _ in best_by_id.values())
    kept = [rows[i] for i in kept_indices]
    removed = len(rows) - len(kept)
    return kept, removed

def clean_rows(raw_rows: Iterable[dict[str, str]], *, first_line: int = 2) -> CleanResult:
    """Clean an iterable of raw rows and deduplicate the survivors.

    first_line defaults to 2 because line 1 of a CSV is the header, and reporting
    a rejected row as "line 7" only helps if it matches what the person sees when
    they open the file.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.
    candidates: list[CleanRow] = []
    rejected: list[RejectedRow] = []

    # First pass: validate every row independently. Deduplication only
    # applies to rows that already passed validation — a rejected row was
    # never a candidate to be "the latest" of anything.
    for offset, raw in enumerate(raw_rows):
        outcome = clean_row(raw, source_line=first_line + offset)
        if isinstance(outcome, CleanRow):
            candidates.append(outcome)
        else:
            rejected.append(outcome)

    # Second pass: dedupe the survivors. duplicates_removed + len(clean) +
    # len(rejected) == total rows in, satisfying the "nothing is lost"
    # invariant the README's test suite asserts on directly.
    kept, duplicates_removed = deduplicate(candidates)
    return CleanResult(clean=kept, rejected=rejected, duplicates_removed=duplicates_removed)

def read_raw_csv(path: Path) -> Iterator[dict[str, str]]:
    """Read a CSV, normalising headers and tolerating a BOM.

    Raises MissingColumnsError if the contract columns are not all present.
    Rows with the wrong number of fields come back with None values, which the
    row validator then rejects with a readable reason.
    """
    # IMPLEMENTED: was `raise NotImplementedError`.

    # utf-8-sig transparently strips a leading BOM; _normalise_header strips
    # any that slips through some other way (e.g. mid-content re-encoding).
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        return iter(())

    header = [_normalise_header(name) for name in rows[0]]

    # Structural failure, not a per-row one: check immediately (eagerly, not
    # lazily on first iteration) so `read_raw_csv(broken_file)` raises right
    # away rather than only once someone starts consuming the generator.
    missing = set(REQUIRED_COLUMNS) - set(header)
    if missing:
        raise MissingColumnsError(missing)

    def _rows() -> Iterator[dict[str, str]]:
        for raw_row in rows[1:]:
            # A row shorter than the header (e.g. a trailing field got
            # dropped) is padded with None so downstream parsers see a
            # missing value instead of an IndexError from zip() truncating.
            if len(raw_row) < len(header):
                raw_row = raw_row + [None] * (len(header) - len(raw_row))
            elif len(raw_row) > len(header):
                # An extra stray field (e.g. an unescaped comma) is dropped
                # rather than raising — same "don't fail structurally on a
                # per-row problem" principle as the padding case above.
                raw_row = raw_row[: len(header)]
            yield dict(zip(header, raw_row))

    return _rows()

def clean_file(source: Path) -> CleanResult:
    """Read and clean a CSV file. Thin wrapper so the CLI stays trivial."""
    return clean_rows(read_raw_csv(source))


def write_clean_csv(rows: Iterable[CleanRow], destination: Path) -> int:
    """Write clean rows. Returns the count written."""
    # IMPLEMENTED: was `raise NotImplementedError`.
    rows = list(rows)
    # mkdir(parents=True, exist_ok=True) so callers can point at
    # out/clean.csv without having to create out/ themselves first.
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "order_id", "order_date", "customer_name", "region",
        "product", "quantity", "unit_price", "line_total",
    ]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # CleanRow.as_dict() already owns the string formatting
            # (2-decimal money, ISO date) — this function just plumbs it out.
            writer.writerow(row.as_dict())
    return len(rows)

def write_rejects_csv(rows: Iterable[RejectedRow], destination: Path) -> int:
    """Write rejected rows with their reasons. Returns the count written."""
    # IMPLEMENTED: was `raise NotImplementedError`.
    rows = list(rows)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["source_line", "reason", "order_id", "raw"]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())
    return len(rows)