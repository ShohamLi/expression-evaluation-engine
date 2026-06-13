"""Conditional expression tests for ``a if condition else b``.

These tests run end-to-end through ``tokenize -> parse -> evaluate`` and assert
on the returned value or on the raised engine-specific error. They cover branch
selection, branch result types, selected-branch-only evaluation (proved with
branches that would raise if evaluated), strict Boolean conditions, error
positions, a couple of nesting/precedence cases, repeated evaluation, and input
preservation.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine import UNDEFINED
from expression_engine.errors import (
    DivisionByZeroError,
    ExpressionTypeError,
)
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


def run(source: str, variables: Mapping[str, object] | None = None) -> object:
    return evaluate(parse(tokenize(source)), variables)


# --------------------------------------------------------------------------- #
# Branch selection
# --------------------------------------------------------------------------- #


def test_true_condition_selects_true_branch() -> None:
    assert run("1 if true else 2") == 1


def test_false_condition_selects_false_branch() -> None:
    assert run("1 if false else 2") == 2


# --------------------------------------------------------------------------- #
# Branch result types are returned unchanged
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ("7 if true else 0", 7),
        ("3.5 if true else 0", 3.5),
        ('"a" if true else "b"', "a"),
        ("false if true else true", False),
    ],
)
def test_branch_result_types(source: str, expected: object) -> None:
    assert run(source) == expected


def test_branch_result_null_is_returned_unchanged() -> None:
    assert run("null if true else 1") is None


def test_branch_result_undefined_is_returned_unchanged() -> None:
    assert run("undefined if true else 1") is UNDEFINED


# --------------------------------------------------------------------------- #
# Only the selected branch is evaluated
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ("1 if true else (1 / 0)", 1),
        ("(1 / 0) if false else 2", 2),
        ("1 if true else (null < 1)", 1),
        ("(null < 1) if false else 2", 2),
    ],
)
def test_unselected_branch_is_not_evaluated(source: str, expected: object) -> None:
    assert run(source) == expected


def test_selected_branch_division_error_propagates() -> None:
    with pytest.raises(DivisionByZeroError):
        run("(1 / 0) if true else 2")


def test_selected_branch_type_error_propagates() -> None:
    with pytest.raises(ExpressionTypeError):
        run("(null < 1) if true else 2")


# --------------------------------------------------------------------------- #
# Strict Boolean condition: no truthiness, no coercion
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        "1 if 1 else 2",
        '1 if "s" else 2',
        "1 if null else 2",
        "1 if undefined else 2",
        "1 if missing else 2",
    ],
)
def test_non_boolean_condition_raises(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


def test_condition_error_position_is_if_token() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run("1 if 1 else 2")
    # The `if` token is at offset 2 (column 3): `1 ` then `if`.
    assert (info.value.position.line, info.value.position.column) == (1, 3)


# --------------------------------------------------------------------------- #
# Nesting and precedence (parser-driven)
# --------------------------------------------------------------------------- #


def test_right_associative_nesting() -> None:
    # 1 if false else 2 if true else 3 parses as 1 if false else (2 if true else 3).
    assert run("1 if false else 2 if true else 3") == 2


def test_condition_uses_boolean_expression() -> None:
    assert run("1 if (2 > 1) else 0") == 1
    assert run('"yes" if (1 < 2 and 3 < 4) else "no"') == "yes"


# --------------------------------------------------------------------------- #
# Repeated evaluation and caller-input preservation
# --------------------------------------------------------------------------- #


def test_repeated_evaluation_of_same_ast_is_stable() -> None:
    ast = parse(tokenize("a if c else b"))
    assert evaluate(ast, {"a": 1, "b": 2, "c": True}) == 1
    assert evaluate(ast, {"a": 1, "b": 2, "c": False}) == 2


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"a": 1, "b": 2, "c": True}
    before = dict(variables)
    run("a if c else b", variables)
    assert variables == before
