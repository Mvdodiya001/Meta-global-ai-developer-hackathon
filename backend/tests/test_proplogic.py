"""T7.3: deterministic propositional-logic entailment (truth table)."""

import pytest

from checker.proplogic import PropLogicError, entails, evaluate, parse


def test_parse_and_evaluate() -> None:
    """Operators: not, and, or, implies, iff, parentheses."""
    formula = parse("(A & B) -> C")
    assert evaluate(formula, {"A": True, "B": True, "C": False}) is False
    assert evaluate(formula, {"A": True, "B": False, "C": False}) is True
    assert evaluate(parse("~A | B"), {"A": True, "B": False}) is False
    assert evaluate(parse("A <-> B"), {"A": True, "B": True}) is True
    assert evaluate(parse("A -> B"), {"A": False, "B": False}) is True


def test_entails_modus_ponens() -> None:
    """A, A -> B entails B, with no counterexample."""
    result = entails(["A", "A -> B"], "B")
    assert result["valid"] is True
    assert result["consistent"] is True
    assert result["counterexample"] is None


def test_not_entails_gives_counterexample() -> None:
    """A alone does not entail B; the counterexample shows A true, B false."""
    result = entails(["A"], "B")
    assert result["valid"] is False
    assert result["counterexample"] == {"A": True, "B": False}


def test_inconsistent_premises_flagged() -> None:
    """Contradictory premises are reported inconsistent, never endorsed."""
    result = entails(["A", "~A"], "B")
    assert result["consistent"] is False
    assert result["valid"] is False


def test_proof_shaped_entailment() -> None:
    """The counterfactual shape: all step atoms plus the inference rule entail C."""
    atoms = ["fact_F1", "rule_R1", "evidence_CL10"]
    rule = f"({' & '.join(atoms)}) -> conclusion_holds"
    assert entails(atoms + [rule], "conclusion_holds")["valid"] is True
    broken = entails(["fact_F1", "evidence_CL10", rule], "conclusion_holds")
    assert broken["valid"] is False
    assert broken["counterexample"]["rule_R1"] is False


def test_errors_are_typed() -> None:
    """Malformed formulas and oversized atom sets raise PropLogicError."""
    with pytest.raises(PropLogicError):
        parse("A &")
    with pytest.raises(PropLogicError):
        parse("(A")
    with pytest.raises(PropLogicError):
        entails([f"X{i}" for i in range(25)], "X0")
