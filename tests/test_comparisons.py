"""Stage 5 tests: comparison evaluation (``== != < <= > >=``).

These tests run end-to-end through ``tokenize -> parse -> evaluate`` and assert
on the returned ``bool`` or on the raised engine-specific error. They cover the
six operators, numeric comparison, string equality (ordered string comparison is
deferred), the boolean/null/undefined rules, rejection of unsupported operand
combinations, operator error positions, and input preservation.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine.errors import ExpressionTypeError
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


def run(source: str, variables: Mapping[str, object] | None = None) -> object:
    """Evaluate ``source`` through tokenize -> parse -> evaluate."""
    return evaluate(parse(tokenize(source)), variables)


# --------------------------------------------------------------------------- #
# All six operators (numeric) return a real bool
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ("1 == 1", True),
        ("1 == 2", False),
        ("1 != 2", True),
        ("1 != 1", False),
        ("1 < 2", True),
        ("2 < 1", False),
        ("2 <= 2", True),
        ("3 <= 2", False),
        ("2 > 1", True),
        ("1 > 2", False),
        ("2 >= 2", True),
        ("1 >= 2", False),
    ],
)
def test_integer_comparison_operators(source: str, expected: bool) -> None:
    result = run(source)
    assert result is expected
    assert type(result) is bool


# --------------------------------------------------------------------------- #
# Float and mixed int/float
# --------------------------------------------------------------------------- #


def test_float_comparison() -> None:
    assert run("1.5 < 2.5") is True
    assert run("2.5 <= 2.5") is True
    assert run("3.0 > 2.9") is True


def test_mixed_int_and_float() -> None:
    assert run("1 == 1.0") is True
    assert run("1 < 1.5") is True
    assert run("2.0 >= 2") is True
    assert run("3 <= 2.999") is False


# --------------------------------------------------------------------------- #
# Strings: equality and inequality only; ordered comparison is rejected
# --------------------------------------------------------------------------- #


def test_string_equality_and_inequality() -> None:
    assert run('"a" == "a"') is True
    assert run('"a" != "b"') is True
    assert run('"abc" == "abd"') is False
    assert run('"1" == 1') is False  # no coercion between string and number


@pytest.mark.parametrize("source", ['"a" < "b"', '"a" <= "b"', '"a" > "b"', '"a" >= "b"'])
def test_ordered_string_comparison_is_rejected(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


# --------------------------------------------------------------------------- #
# Booleans: equality within bool, never equal to numbers; no ordering
# --------------------------------------------------------------------------- #


def test_boolean_equality() -> None:
    assert run("true == true") is True
    assert run("true == false") is False
    assert run("true != false") is True
    assert run("true == 1") is False  # booleans are not numbers
    assert run("false == 0") is False


@pytest.mark.parametrize("source", ["true < false", "true <= true", "false > true", "true < 1"])
def test_ordered_boolean_comparison_is_rejected(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


# --------------------------------------------------------------------------- #
# null and undefined
# --------------------------------------------------------------------------- #


def test_null_equality() -> None:
    assert run("null == null") is True
    assert run("null != null") is False


def test_undefined_equality() -> None:
    assert run("undefined == undefined") is True
    assert run("undefined != undefined") is False


def test_null_versus_undefined_are_distinct() -> None:
    assert run("null == undefined") is False
    assert run("null != undefined") is True


def test_missing_variable_equals_undefined() -> None:
    assert run("missing == undefined") is True
    assert run("missing != undefined", {"x": 1}) is False


def test_null_and_undefined_versus_other_types_are_unequal() -> None:
    assert run("null == 0") is False
    assert run("undefined == 0") is False
    assert run("null == false") is False


# --------------------------------------------------------------------------- #
# Ordered comparison with incompatible types is rejected
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    ['"a" < 1', '1 > "a"', "null < 1", "undefined > 0", "null >= undefined"],
)
def test_incompatible_type_ordering_is_rejected(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


# --------------------------------------------------------------------------- #
# Error positions: anchored at the comparison operator
# --------------------------------------------------------------------------- #


def test_ordered_type_error_position_is_operator() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run('"a" < 1')
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 5)


def test_error_message_includes_line_and_column() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run("null < 1")
    message = str(info.value)
    assert "line 1" in message
    assert "column 6" in message


# --------------------------------------------------------------------------- #
# Repeated evaluation and caller-input preservation
# --------------------------------------------------------------------------- #


def test_repeated_evaluation_of_same_ast_is_stable() -> None:
    ast = parse(tokenize("a < b"))
    assert evaluate(ast, {"a": 1, "b": 2}) is True
    assert evaluate(ast, {"a": 5, "b": 2}) is False


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"a": 1, "b": 2}
    before = dict(variables)
    run("a < b", variables)
    assert variables == before
