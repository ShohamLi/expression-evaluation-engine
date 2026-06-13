"""Stage 4 tests: the evaluator (arithmetic and variable lookup).

These tests run end-to-end through the intended pipeline
``tokenize -> parse -> evaluate`` (with a small helper) and assert on returned
runtime values or on the raised engine-specific errors. They cover literals,
external variables, the missing/null/undefined/false/zero distinctions, unary
and binary numeric operations, precedence/parentheses, invalid operands,
division by zero, error positions, left-to-right evaluation, repeated and
multi-mapping evaluation, input preservation, and operations outside Stage 4.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine import UNDEFINED
from expression_engine.errors import (
    DivisionByZeroError,
    ExpressionEvaluationError,
    ExpressionTypeError,
)
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


def run(source: str, variables: Mapping[str, object] | None = None) -> object:
    """Evaluate ``source`` through tokenize -> parse -> evaluate."""
    return evaluate(parse(tokenize(source)), variables)


# --------------------------------------------------------------------------- #
# Literal types
# --------------------------------------------------------------------------- #


def test_integer_literal() -> None:
    result = run("42")
    assert result == 42
    assert type(result) is int


def test_float_literal() -> None:
    result = run("3.14")
    assert result == 3.14
    assert type(result) is float


def test_scientific_float_literal() -> None:
    assert run("2.5e-4") == 2.5e-4


def test_string_literal_is_decoded_str() -> None:
    assert run(r'"a\nb"') == "a\nb"


def test_true_literal_is_bool() -> None:
    result = run("true")
    assert result is True


def test_false_literal_is_bool() -> None:
    result = run("false")
    assert result is False


def test_null_literal_is_none() -> None:
    assert run("null") is None


def test_undefined_literal_is_singleton() -> None:
    assert run("undefined") is UNDEFINED


# --------------------------------------------------------------------------- #
# External variables and the missing-variable rule
# --------------------------------------------------------------------------- #


def test_variable_lookup() -> None:
    assert run("x", {"x": 10}) == 10


def test_variable_lookup_float() -> None:
    assert run("price", {"price": 2.5}) == 2.5


def test_missing_variable_is_undefined() -> None:
    assert run("missing", {"x": 1}) is UNDEFINED


def test_missing_variable_with_no_mapping_is_undefined() -> None:
    assert run("anything") is UNDEFINED


def test_explicit_undefined_value_is_undefined() -> None:
    assert run("x", {"x": UNDEFINED}) is UNDEFINED


def test_variable_can_be_none() -> None:
    assert run("x", {"x": None}) is None


def test_variable_can_be_false() -> None:
    assert run("x", {"x": False}) is False


def test_variable_can_be_zero() -> None:
    result = run("x", {"x": 0})
    assert result == 0
    assert type(result) is int


# --------------------------------------------------------------------------- #
# Distinctness of missing / null / undefined / false / zero
# --------------------------------------------------------------------------- #


def test_distinct_runtime_values() -> None:
    missing = run("a")  # absent -> UNDEFINED
    explicit_undefined = run("undefined")
    null = run("null")
    false = run("false")
    zero = run("0")

    assert missing is UNDEFINED
    assert explicit_undefined is UNDEFINED
    assert null is None
    assert false is False
    assert zero == 0 and type(zero) is int

    # Each sentinel keeps its own identity/type; none collapses into another or
    # into numeric zero. (Note: Python treats ``False == 0`` as true, so the
    # guarantee here is about distinct objects and types, not ``==``.)
    assert null is not UNDEFINED
    assert false is not None
    assert type(false) is bool and type(zero) is int
    assert false is not zero
    assert null is not zero
    assert UNDEFINED is not zero
    assert UNDEFINED is not None


# --------------------------------------------------------------------------- #
# Unary numeric operations
# --------------------------------------------------------------------------- #


def test_unary_minus_integer() -> None:
    result = run("-5")
    assert result == -5
    assert type(result) is int


def test_unary_minus_float() -> None:
    assert run("-3.5") == -3.5


def test_unary_plus_integer() -> None:
    result = run("+5")
    assert result == 5
    assert type(result) is int


def test_repeated_unary_minus() -> None:
    assert run("- - 5") == 5


def test_unary_minus_on_variable() -> None:
    assert run("-x", {"x": 7}) == -7


@pytest.mark.parametrize("source", ["-true", "+false", "-null", "+undefined", '-"s"'])
def test_unary_on_non_number_raises_type_error(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


def test_unary_minus_on_missing_variable_raises() -> None:
    with pytest.raises(ExpressionTypeError):
        run("-missing")


# --------------------------------------------------------------------------- #
# Binary arithmetic
# --------------------------------------------------------------------------- #


def test_addition() -> None:
    result = run("2 + 3")
    assert result == 5
    assert type(result) is int


def test_subtraction() -> None:
    assert run("10 - 4") == 6


def test_multiplication() -> None:
    assert run("6 * 7") == 42


def test_true_division_returns_float() -> None:
    result = run("6 / 2")
    assert result == 3.0
    assert type(result) is float


def test_division_non_integer_result() -> None:
    assert run("7 / 2") == 3.5


def test_mixed_int_and_float_promotes_to_float() -> None:
    result = run("2 + 3.0")
    assert result == 5.0
    assert type(result) is float


def test_integer_arithmetic_stays_int() -> None:
    assert type(run("2 * 3")) is int


def test_arithmetic_with_variables() -> None:
    assert run("a + b * c", {"a": 1, "b": 2, "c": 3}) == 7


# --------------------------------------------------------------------------- #
# Precedence and parentheses (parser-driven, confirmed by evaluation)
# --------------------------------------------------------------------------- #


def test_multiplication_before_addition() -> None:
    assert run("2 + 3 * 4") == 14


def test_parentheses_override_precedence() -> None:
    assert run("(2 + 3) * 4") == 20


def test_left_associative_subtraction() -> None:
    assert run("10 - 3 - 2") == 5


def test_left_associative_division() -> None:
    assert run("12 / 2 / 3") == 2.0


def test_unary_minus_binds_before_multiplication() -> None:
    assert run("-2 * 3") == -6


def test_nested_parentheses() -> None:
    assert run("((1 + 2) * (3 + 4))") == 21


# --------------------------------------------------------------------------- #
# Invalid operands for binary arithmetic
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        "true + 1",  # bool is not numeric
        "1 + false",
        '"a" + "b"',  # string operations are out of scope in Stage 4
        '"a" + 1',
        "null + 1",
        "1 + null",
        "undefined + 1",
        "1 * undefined",
    ],
)
def test_invalid_binary_operands_raise_type_error(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        run(source)


def test_missing_variable_in_arithmetic_raises_type_error() -> None:
    with pytest.raises(ExpressionTypeError):
        run("missing + 1")


def test_custom_object_operand_raises_type_error() -> None:
    class Weird:
        def __add__(self, other: object) -> object:  # pragma: no cover
            return "should never be called"

    with pytest.raises(ExpressionTypeError):
        run("x + 1", {"x": Weird()})


def test_int_subclass_is_not_accepted() -> None:
    class MyInt(int):
        pass

    with pytest.raises(ExpressionTypeError):
        run("x + 1", {"x": MyInt(5)})


def test_bool_is_not_numeric_even_though_python_allows_it() -> None:
    # Plain Python would compute True + 1 == 2; the engine rejects it.
    with pytest.raises(ExpressionTypeError):
        run("x + 1", {"x": True})


# --------------------------------------------------------------------------- #
# Division by zero
# --------------------------------------------------------------------------- #


def test_integer_division_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        run("1 / 0")


def test_float_division_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        run("1 / 0.0")


def test_division_by_zero_variable() -> None:
    with pytest.raises(DivisionByZeroError):
        run("x / y", {"x": 10, "y": 0})


def test_division_by_zero_is_evaluation_error() -> None:
    with pytest.raises(ExpressionEvaluationError):
        run("1 / 0")


# --------------------------------------------------------------------------- #
# Error positions
# --------------------------------------------------------------------------- #


def test_type_error_position_is_operator() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run('"a" + 1')
    # The `+` is at offset 4 (column 5): `"a"` then a space.
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 5)


def test_division_by_zero_position_is_slash() -> None:
    with pytest.raises(DivisionByZeroError) as info:
        run("1 / 0")
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 3)


def test_unary_type_error_position_is_operator() -> None:
    with pytest.raises(ExpressionTypeError) as info:
        run("-true")
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 1)


def test_unsupported_operation_position() -> None:
    with pytest.raises(ExpressionEvaluationError) as info:
        run("a if b else c")
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 3)


def test_error_message_includes_line_and_column() -> None:
    with pytest.raises(DivisionByZeroError) as info:
        run("1 / 0")
    message = str(info.value)
    assert "line 1" in message
    assert "column 3" in message


# --------------------------------------------------------------------------- #
# Left-to-right evaluation and no partial evaluation of unsupported ops
# --------------------------------------------------------------------------- #


class RecordingMapping(Mapping):
    """A read-only mapping that records the order of variable lookups."""

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data
        self.lookups: list[str] = []

    def __getitem__(self, key: str) -> object:
        self.lookups.append(key)
        return self._data[key]

    def get(self, key: str, default: object = None) -> object:
        self.lookups.append(key)
        return self._data.get(key, default)

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


def test_operands_evaluated_left_to_right() -> None:
    variables = RecordingMapping({"a": 1, "b": 2, "c": 3})
    run("a + b - c", variables)
    assert variables.lookups == ["a", "b", "c"]


def test_conditional_is_unsupported_and_skips_operands() -> None:
    variables = RecordingMapping({"a": 1, "b": 2, "c": 3})
    with pytest.raises(ExpressionEvaluationError):
        run("a if b else c", variables)
    assert variables.lookups == []


# --------------------------------------------------------------------------- #
# Unsupported Stage 4 operations
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        "1 if true else 2",
    ],
)
def test_unsupported_operations_raise_evaluation_error(source: str) -> None:
    with pytest.raises(ExpressionEvaluationError):
        run(source)


def test_unsupported_operation_is_not_type_error() -> None:
    # Unsupported ops are base evaluation errors, not type errors.
    with pytest.raises(ExpressionEvaluationError) as info:
        run("1 if true else 2")
    assert not isinstance(info.value, ExpressionTypeError)


# --------------------------------------------------------------------------- #
# State isolation and input preservation
# --------------------------------------------------------------------------- #


def test_repeated_evaluation_of_same_ast_is_stable() -> None:
    ast = parse(tokenize("a + b"))
    assert evaluate(ast, {"a": 1, "b": 2}) == 3
    assert evaluate(ast, {"a": 1, "b": 2}) == 3


def test_same_ast_with_different_mappings() -> None:
    ast = parse(tokenize("a * 2"))
    assert evaluate(ast, {"a": 3}) == 6
    assert evaluate(ast, {"a": 10}) == 20


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"a": 1, "b": 2}
    before = dict(variables)
    run("a + b", variables)
    assert variables == before


def test_caller_values_are_not_mutated() -> None:
    value = [1, 2, 3]  # a non-numeric object stored as a variable
    variables = {"x": value}
    with pytest.raises(ExpressionTypeError):
        run("x + 1", variables)
    assert value == [1, 2, 3]


def test_evaluation_does_not_require_module_state() -> None:
    # Two independent expressions evaluated back to back do not interfere.
    assert run("1 + 1") == 2
    assert run("10 - 3") == 7
