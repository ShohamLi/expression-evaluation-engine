"""Stage 6 tests: strict Boolean operators ``not``, ``and``, ``or``.

These tests run end-to-end through ``tokenize -> parse -> evaluate`` and assert
on the returned ``bool`` or on the raised engine-specific error. They cover the
truth tables, exact ``bool`` results, real short-circuit evaluation (proved with
right operands that would raise if evaluated), strict operand typing, error
positions, precedence interplay, repeated evaluation, and input preservation.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine.errors import (
    DivisionByZeroError,
    ExpressionTypeError,
)
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


def run(source: str, variables: Mapping[str, object] | None = None) -> object:
    """Evaluate ``source`` through tokenize -> parse -> evaluate."""
    return evaluate(parse(tokenize(source)), variables)


# --------------------------------------------------------------------------- #
# Truth tables and exact bool results
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ("not true", False),
        ("not false", True),
        ("true and true", True),
        ("true and false", False),
        ("false and true", False),
        ("false and false", False),
        ("true or true", True),
        ("true or false", True),
        ("false or true", True),
        ("false or false", False),
    ],
)
def test_boolean_truth_tables(source: str, expected: bool) -> None:
    result = run(source)
    assert result is expected
    assert type(result) is bool


# --------------------------------------------------------------------------- #
# Real short-circuit evaluation: the right operand is not evaluated
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ("false and (1 / 0 > 0)", False),
        ("true or (1 / 0 > 0)", True),
        ("false and (null < 1)", False),
        ("true or (undefined < 1)", True),
    ],
)
def test_short_circuit_skips_right_operand(source: str, expected: bool) -> None:
    assert run(source) is expected


# --------------------------------------------------------------------------- #
# The right operand is evaluated when the result is not yet decided
# --------------------------------------------------------------------------- #


def test_and_evaluates_right_operand_errors_propagate() -> None:
    with pytest.raises(DivisionByZeroError):
        run("true and (1 / 0 > 0)")


def test_or_evaluates_right_operand_errors_propagate() -> None:
    with pytest.raises(ExpressionTypeError):
        run("false or (null < 1)")


def test_and_returns_validated_right_operand() -> None:
    assert run("true and (2 > 1)") is True
    assert run("true and (2 < 1)") is False


def test_or_returns_validated_right_operand() -> None:
    assert run("false or (2 > 1)") is True
    assert run("false or (2 < 1)") is False


# --------------------------------------------------------------------------- #
# Strict operand typing: only exact bool, no truthiness
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("source", ["not 1", 'not "s"', "not null", "not undefined", "not missing"])
def test_not_requires_bool(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


@pytest.mark.parametrize(
    "source",
    ["1 and true", '"s" and true', "null and true", "undefined and true", "missing and true"],
)
def test_and_rejects_non_bool_left(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


@pytest.mark.parametrize(
    "source",
    ["1 or true", '"s" or true', "null or true", "undefined or true", "missing or true"],
)
def test_or_rejects_non_bool_left(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


@pytest.mark.parametrize("source", ["true and 1", 'true and "s"', "true and null", "true and undefined"])
def test_and_rejects_non_bool_right(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


@pytest.mark.parametrize("source", ["false or 1", 'false or "s"', "false or null", "false or undefined"])
def test_or_rejects_non_bool_right(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


def test_invalid_right_operand_is_skipped_when_short_circuited() -> None:
    # The bad right operand is never validated because it is never evaluated.
    assert run("false and 1") is False
    assert run("true or 1") is True


# --------------------------------------------------------------------------- #
# Error positions anchored at the boolean operator
# --------------------------------------------------------------------------- #


def test_not_error_position() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run("not 1")
    assert (info.value.position.line, info.value.position.column) == (1, 1)


def test_and_error_position() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run("1 and true")
    assert (info.value.position.line, info.value.position.column) == (1, 3)


def test_or_error_position() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run("1 or true")
    assert (info.value.position.line, info.value.position.column) == (1, 3)


# --------------------------------------------------------------------------- #
# Precedence interplay (a few focused end-to-end cases)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ("not true and false", False),  # (not true) and false
        ("true or false and false", True),  # true or (false and false)
        ("1 < 2 and 3 < 4", True),  # comparisons feed booleans
        ("not (true and false)", True),
    ],
)
def test_precedence_end_to_end(source: str, expected: bool) -> None:
    assert run(source) is expected


# --------------------------------------------------------------------------- #
# Repeated evaluation and caller-input preservation
# --------------------------------------------------------------------------- #


def test_repeated_evaluation_of_same_ast_is_stable() -> None:
    ast = parse(tokenize("a and b"))
    assert evaluate(ast, {"a": True, "b": False}) is False
    assert evaluate(ast, {"a": True, "b": True}) is True


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"a": True, "b": False}
    before = dict(variables)
    run("a or b", variables)
    assert variables == before
