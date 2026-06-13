"""String concatenation tests for the ``+`` operator.

These tests run end-to-end through ``tokenize -> parse -> evaluate`` and assert
on the returned ``str`` or on the raised engine-specific error. They cover
concatenation of two exact strings, string variables, use inside a conditional,
rejection of mixed string/non-string operands, the error position, preserved
numeric addition, repeated evaluation, and input preservation.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine.errors import ExpressionTypeError
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


def run(source: str, variables: Mapping[str, object] | None = None) -> object:
    return evaluate(parse(tokenize(source)), variables)


# --------------------------------------------------------------------------- #
# Valid concatenation of two exact strings
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source,expected",
    [
        ('"hello" + " world"', "hello world"),
        ('"a" + "b"', "ab"),
        ('"" + "a"', "a"),
        ('"a" + ""', "a"),
        ('"" + ""', ""),
    ],
)
def test_string_concatenation(source: str, expected: str) -> None:
    result = run(source)
    assert result == expected
    assert type(result) is str


def test_concatenation_with_string_variables() -> None:
    assert run("a + b", {"a": "foo", "b": "bar"}) == "foobar"


def test_concatenation_inside_conditional() -> None:
    assert run('("a" + "b") if true else "c"') == "ab"
    assert run('"c" if false else ("a" + "b")') == "ab"


# --------------------------------------------------------------------------- #
# Mixed string and non-string operands raise (no implicit conversion)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        '"a" + 1',
        '1 + "a"',
        '"a" + 1.5',
        '"a" + true',
        'true + "a"',
        '"a" + null',
        'null + "a"',
        '"a" + undefined',
        'undefined + "a"',
        '"a" + missing',
        'missing + "a"',
    ],
)
def test_mixed_operands_raise_type_error(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


def test_concatenation_error_position_is_operator() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run('"a" + 1')
    # The `+` is at offset 4 (column 5): `"a"` then a space.
    assert (info.value.position.line, info.value.position.column) == (1, 5)


# --------------------------------------------------------------------------- #
# Numeric addition is unchanged
# --------------------------------------------------------------------------- #


def test_numeric_addition_is_unchanged() -> None:
    result = run("2 + 3")
    assert result == 5
    assert type(result) is int


# --------------------------------------------------------------------------- #
# Repeated evaluation and caller-input preservation
# --------------------------------------------------------------------------- #


def test_repeated_evaluation_of_same_ast_is_stable() -> None:
    ast = parse(tokenize("a + b"))
    assert evaluate(ast, {"a": "x", "b": "y"}) == "xy"
    assert evaluate(ast, {"a": "1", "b": "2"}) == "12"


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"a": "foo", "b": "bar"}
    before = dict(variables)
    run("a + b", variables)
    assert variables == before
