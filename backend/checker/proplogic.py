"""T7.3: deterministic propositional-logic entailment (pure, no imports
from `app` — same isolation rules as the rest of `checker/`).

Formulas are strings over named atoms with `~` (not), `&` (and), `|`
(or), `->` (implies) and `<->` (iff); parentheses group. `entails`
decides validity by exhaustive truth table: a conclusion is valid iff
every assignment that makes all premises true also makes it true. The
counterexample (an assignment with premises true, conclusion false) is
returned when invalid, so the answer is checkable, not asserted.
Inconsistent premises are reported as such and never entail validity.
"""

from dataclasses import dataclass
from typing import Any

MAX_ATOMS = 20


class PropLogicError(Exception):
    """A formula is malformed or too large to decide (T7.3)."""


@dataclass(frozen=True)
class Atom:
    """One propositional variable."""

    name: str


@dataclass(frozen=True)
class Not:
    """Negation of one formula."""

    inner: Any


@dataclass(frozen=True)
class Bin:
    """A binary connective: and/or/implies/iff."""

    op: str
    left: Any
    right: Any


_TOKENS = ("<->", "->", "~", "&", "|", "(", ")")


def _tokenize(text: str) -> list[str]:
    """Split a formula string into atoms and operator tokens (T7.3)."""
    tokens: list[str] = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        matched = next((tok for tok in _TOKENS if text.startswith(tok, i)), None)
        if matched is not None:
            tokens.append(matched)
            i += len(matched)
            continue
        if text[i].isalpha() or text[i] == "_":
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(text[i:j])
            i = j
            continue
        raise PropLogicError(f"unexpected character {text[i]!r} in formula")
    return tokens


class _Parser:
    """Recursive-descent parser: iff < implies < or < and < not < atom."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise PropLogicError(f"expected {expected or 'a token'}, got {token!r}")
        self.pos += 1
        return token

    def parse_iff(self) -> Any:
        left = self.parse_implies()
        while self.peek() == "<->":
            self.take()
            left = Bin("iff", left, self.parse_implies())
        return left

    def parse_implies(self) -> Any:
        left = self.parse_or()
        if self.peek() == "->":
            self.take()
            return Bin("implies", left, self.parse_implies())
        return left

    def parse_or(self) -> Any:
        left = self.parse_and()
        while self.peek() == "|":
            self.take()
            left = Bin("or", left, self.parse_and())
        return left

    def parse_and(self) -> Any:
        left = self.parse_not()
        while self.peek() == "&":
            self.take()
            left = Bin("and", left, self.parse_not())
        return left

    def parse_not(self) -> Any:
        if self.peek() == "~":
            self.take()
            return Not(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Any:
        token = self.peek()
        if token == "(":
            self.take()
            inner = self.parse_iff()
            self.take(")")
            return inner
        if token is None or token in _TOKENS:
            raise PropLogicError(f"expected an atom, got {token!r}")
        return Atom(self.take())


def parse(text: str) -> Any:
    """Parse one formula string into an AST or raise PropLogicError (T7.3)."""
    if not isinstance(text, str) or not text.strip():
        raise PropLogicError("formula must be a non-empty string")
    parser = _Parser(_tokenize(text))
    result = parser.parse_iff()
    if parser.peek() is not None:
        raise PropLogicError(f"trailing token {parser.peek()!r} in formula")
    return result


def atoms_of(formula: Any) -> set[str]:
    """All atom names in a parsed formula (T7.3)."""
    if isinstance(formula, Atom):
        return {formula.name}
    if isinstance(formula, Not):
        return atoms_of(formula.inner)
    if isinstance(formula, Bin):
        return atoms_of(formula.left) | atoms_of(formula.right)
    raise PropLogicError("unknown formula node")


def evaluate(formula: Any, assignment: dict[str, bool]) -> bool:
    """Evaluate a parsed formula under one truth assignment (T7.3)."""
    if isinstance(formula, Atom):
        return bool(assignment.get(formula.name, False))
    if isinstance(formula, Not):
        return not evaluate(formula.inner, assignment)
    if isinstance(formula, Bin):
        left = evaluate(formula.left, assignment)
        right = evaluate(formula.right, assignment)
        if formula.op == "and":
            return left and right
        if formula.op == "or":
            return left or right
        if formula.op == "implies":
            return (not left) or right
        if formula.op == "iff":
            return left == right
    raise PropLogicError("unknown formula node")


def entails(premises: list[str], conclusion: str) -> dict[str, Any]:
    """Decide premises |= conclusion by truth table (T7.3).

    Returns `{valid, consistent, counterexample, atoms}`. `valid` is
    True only when the premises are consistent and every satisfying
    assignment satisfies the conclusion.
    """
    parsed = [parse(item) for item in premises]
    target = parse(conclusion)
    names: set[str] = set()
    for formula in parsed + [target]:
        names |= atoms_of(formula)
    if len(names) > MAX_ATOMS:
        raise PropLogicError(f"too many atoms ({len(names)} > {MAX_ATOMS})")
    ordered = sorted(names)
    consistent = False
    for mask in range(1 << len(ordered)):
        assignment = {
            name: bool(mask >> index & 1) for index, name in enumerate(ordered)
        }
        if all(evaluate(formula, assignment) for formula in parsed):
            consistent = True
            if not evaluate(target, assignment):
                return {
                    "valid": False,
                    "consistent": True,
                    "counterexample": assignment,
                    "atoms": ordered,
                }
    return {
        "valid": consistent,
        "consistent": consistent,
        "counterexample": None,
        "atoms": ordered,
    }
