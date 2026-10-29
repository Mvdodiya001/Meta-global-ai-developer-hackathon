"""T1.3: rule-card loading with verbatim span verification (F2).

Cards live in `corpus/rulecards/*.yaml` and are hand-curated readings of the
T1.2 provisions for claim types CT1–CT3:

- CT1 processor contract: the clause must rest on a valid fiduciary–processor
  contract carrying security-safeguard terms (s8(1)-(2), Rule 6(1)(f)).
- CT2 security safeguards: the clause must commit to reasonable safeguards
  (s8(4)-(5), Rule 6(1)(a), Rule 6(1)(e)).
- CT3 breach intimation: the clause must assign the Board/Principal
  intimation duty and its timeline (s8(6), Rule 7(2)(b)).

No PyYAML dependency: the loader parses only this documented card shape and
rejects everything else with `RuleCardError`:

- top-level `key: value` lines with keys from a fixed set, no duplicates;
- `key: |` block scalars (indented continuation lines, spaces only);
- a `requires: [a, b]` flow list of requirement names;
- full-line `#` comments and blank lines ignored (no inline comments).

Every card cites a verbatim span: `provision.text[span_start:span_end]`
must equal `span_text`, else the card is rejected before anything is written.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app import models
from app.core.errors import RuleCardError

DEFAULT_CARDS_DIR = Path(__file__).resolve().parents[3] / "corpus" / "rulecards"

REQUIRED_KEYS = frozenset(
    {
        "id",
        "provision_id",
        "kind",
        "claim_type",
        "trust_class",
        "approved_by",
        "requires",
        "span_start",
        "span_end",
        "interpretation",
        "span_text",
    }
)

KINDS = frozenset({"statutory", "interpretation"})
CLAIM_TYPES = frozenset({"CT1", "CT2", "CT3", "CT4"})
TRUST_CLASSES = frozenset(
    {"lawyer_confirmed", "document_extracted", "ai_inferred", "disputed"}
)


def _parse_block(lines: list[str], start: int) -> tuple[str, int]:
    """Parse a `|` block scalar starting at line `start` (T1.3)."""
    indent: int | None = None
    taken: list[str] = []
    i = start
    while i < len(lines):
        raw = lines[i]
        if raw.strip() == "":
            taken.append("")
            i += 1
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise RuleCardError(f"line {i + 1}: tabs are not allowed in indentation")
        stripped = raw.lstrip(" ")
        level = len(raw) - len(stripped)
        if level == 0:
            break
        if indent is None:
            indent = level
        if level < indent:
            break
        taken.append(raw[indent:])
        i += 1
    while taken and taken[-1] == "":
        taken.pop()
    return "\n".join(taken), i


def parse_rulecard_file(path: str | Path) -> dict[str, Any]:
    """Parse one card file, accepting only the documented shape (T1.3)."""
    where = str(path)
    raw_lines = Path(path).read_text(encoding="utf-8").splitlines()
    lines = [line for line in raw_lines if line.strip() != "" and not line.lstrip().startswith("#")]
    if lines and lines[0].strip() == "---":
        lines = lines[1:]
    card: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line != line.lstrip():
            raise RuleCardError(f"{where} line {i + 1}: unexpected indentation")
        if line.lstrip().startswith("- "):
            raise RuleCardError(f"{where} line {i + 1}: block sequences are not supported")
        head, sep, value = line.partition(":")
        if sep == "" or not head.strip().isidentifier():
            raise RuleCardError(f"{where} line {i + 1}: expected `key: value`")
        key = head.strip()
        if key not in REQUIRED_KEYS:
            raise RuleCardError(f"{where} line {i + 1}: unknown key {key!r}")
        if key in card:
            raise RuleCardError(f"{where} line {i + 1}: duplicate key {key!r}")
        value = value.strip()
        if value == "|":
            if key not in ("interpretation", "span_text"):
                raise RuleCardError(f"{where} line {i + 1}: block scalar only for text fields")
            card[key], i = _parse_block(lines, i + 1)
            continue
        if value == "" or value.startswith(("&", "*", "!", "{", "- ")):
            raise RuleCardError(f"{where} line {i + 1}: unsupported value for {key!r}")
        if key == "requires":
            if not (value.startswith("[") and value.endswith("]")):
                raise RuleCardError(f"{where} line {i + 1}: requires must be `[a, b]`")
            card[key] = [
                item.strip().strip("'\"")
                for item in value[1:-1].split(",")
                if item.strip() != ""
            ]
        elif key in ("span_start", "span_end"):
            if not value.isdigit():
                raise RuleCardError(f"{where} line {i + 1}: {key} must be an integer")
            card[key] = int(value)
        else:
            card[key] = value.strip("'\"")
        i += 1
    missing = sorted(REQUIRED_KEYS - card.keys())
    if missing:
        raise RuleCardError(f"{where}: missing keys {missing}")
    if card["kind"] not in KINDS:
        raise RuleCardError(f"{where}: unknown kind {card['kind']!r}")
    if card["claim_type"] not in CLAIM_TYPES:
        raise RuleCardError(f"{where}: unknown claim_type {card['claim_type']!r}")
    if card["trust_class"] not in TRUST_CLASSES:
        raise RuleCardError(f"{where}: unknown trust_class {card['trust_class']!r}")
    return card


def load_cards(cards_dir: str | Path = DEFAULT_CARDS_DIR) -> list[dict[str, Any]]:
    """Parse every `*.yaml` card in a directory, sorted by filename (T1.3)."""
    files = sorted(Path(cards_dir).glob("*.yaml"))
    if not files:
        raise RuleCardError(f"no rule cards in {cards_dir}")
    return [parse_rulecard_file(path) for path in files]


def verify_card(session: Session, card: dict[str, Any]) -> models.Provision:
    """Check a card against its stored provision snapshot (T1.3)."""
    provision = session.get(models.Provision, card["provision_id"])
    if provision is None:
        raise RuleCardError(f"{card['id']}: unknown provision {card['provision_id']!r}")
    start = int(card["span_start"])
    end = int(card["span_end"])
    if not 0 <= start < end <= len(provision.text):
        raise RuleCardError(
            f"{card['id']}: span [{start}:{end}] out of range "
            f"(provision text length {len(provision.text)})"
        )
    actual = provision.text[start:end]
    if actual != card["span_text"]:
        raise RuleCardError(
            f"{card['id']}: span text mismatch: expected {card['span_text']!r}, "
            f"stored snapshot has {actual!r}"
        )
    return provision


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (T1.3)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def ingest_cards(session: Session, cards: list[dict[str, Any]]) -> list[str]:
    """Insert new cards, refresh re-loaded ones, keep original timestamps (T1.3)."""
    ids: list[str] = []
    for card in cards:
        row = session.get(models.RuleCard, card["id"])
        if row is None:
            row = models.RuleCard(id=card["id"], created_at=_utcnow())
            session.add(row)
        row.provision_id = card["provision_id"]
        row.kind = card["kind"]
        row.claim_type = card["claim_type"]
        row.predicate_json = {"requires": list(card["requires"])}
        row.interpretation_text = card["interpretation"]
        row.span_start = int(card["span_start"])
        row.span_end = int(card["span_end"])
        row.trust_class = card["trust_class"]
        row.approved_by = card["approved_by"]
        row.superseded_by = None
        ids.append(str(row.id))
    session.commit()
    return ids


def load_rulecards(
    session: Session, cards_dir: str | Path = DEFAULT_CARDS_DIR
) -> list[str]:
    """Parse, verify every card, then ingest; a bad card writes nothing (T1.3)."""
    cards = load_cards(cards_dir)
    for card in cards:
        verify_card(session, card)
    return ingest_cards(session, cards)
