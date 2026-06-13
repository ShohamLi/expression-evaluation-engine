"""Stage 13 tests: built-in mathematical functions through the public API."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine import (
    UNDEFINED,
    Engine,
    ExpressionEvaluationError,
    ExpressionTypeError,
    FunctionArityError,
    UnknownFunctionError,
)


def evaluate(source: str, variables: Mapping[str, object] | None = None) -> object:
    return Engine().compile(source).evaluate(variables)


class RecordingMapping(Mapping):
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


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("abs(-3)", 3),
        ("abs(3.5)", 3.5),
        ("floor(3.7)", 3),
        ("ceil(3.2)", 4),
        ("sqrt(9)", 3.0),
        ("log(2.718281828459045)", pytest.approx(1.0)),
        ("pow(2, 3)", 8),
        ("pow(2, 3.0)", 8.0),
        ("round(2.5)", 2),
        ("round(3.5)", 4),
        ("round(2.675, 2)", 2.67),
        ("min(1, 2)", 1),
        ("max(1, 2.5)", 2.5),
        ("min(1, 2, 3)", 1),
        ("max(1.0, 2, 3)", 3.0),
    ],
)
def test_builtin_success_paths(source: str, expected: object) -> None:
    assert evaluate(source) == expected


@pytest.mark.parametrize(
    ("source", "expected_type"),
    [
        ("abs(-3)", int),
        ("abs(-3.5)", float),
        ("floor(3.7)", int),
        ("ceil(3.2)", int),
        ("sqrt(9)", float),
        ("log(1)", float),
        ("pow(2, 3)", int),
        ("pow(2, -1)", float),
        ("pow(2.0, 3)", float),
        ("round(2.5)", int),
        ("round(2.5, 1)", float),
    ],
)
def test_builtin_result_types(source: str, expected_type: type[object]) -> None:
    assert type(evaluate(source)) is expected_type


@pytest.mark.parametrize(
    "source",
    [
        "abs(true)",
        "sqrt(false)",
        "min(1, null)",
        "max(undefined, 1)",
        "log(null)",
        'abs("1")',
        "round(1, true)",
    ],
)
def test_builtin_rejects_non_numeric_arguments(source: str) -> None:
    with pytest.raises(ExpressionTypeError):
        evaluate(source)


def test_builtin_rejects_missing_variable_argument() -> None:
    with pytest.raises(ExpressionTypeError):
        evaluate("abs(missing)")


@pytest.mark.parametrize("value", [[], {}, object()])
def test_builtin_rejects_containers_and_arbitrary_objects(value: object) -> None:
    with pytest.raises(ExpressionTypeError):
        evaluate("abs(value)", {"value": value})


@pytest.mark.parametrize("value", [type("IntSubclass", (int,), {})(1), type("FloatSubclass", (float,), {})(1.0)])
def test_builtin_rejects_numeric_subclasses(value: object) -> None:
    with pytest.raises(ExpressionTypeError):
        evaluate("max(value, 2)", {"value": value})


@pytest.mark.parametrize(
    ("source", "error"),
    [
        ("abs()", FunctionArityError),
        ("abs(1, 2)", FunctionArityError),
        ("floor()", FunctionArityError),
        ("floor(1, 2)", FunctionArityError),
        ("ceil()", FunctionArityError),
        ("ceil(1, 2)", FunctionArityError),
        ("sqrt()", FunctionArityError),
        ("sqrt(1, 2)", FunctionArityError),
        ("log()", FunctionArityError),
        ("log(1, 2)", FunctionArityError),
        ("pow(1)", FunctionArityError),
        ("pow(1, 2, 3)", FunctionArityError),
        ("round()", FunctionArityError),
        ("min(1)", FunctionArityError),
        ("max()", FunctionArityError),
        ("max(1)", FunctionArityError),
        ("round(1, 2, 3)", FunctionArityError),
    ],
)
def test_builtin_arity_errors_during_compile(source: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        Engine().compile(source)


def test_unknown_function_during_compile() -> None:
    with pytest.raises(UnknownFunctionError):
        Engine().compile("unknown(1)")


@pytest.mark.parametrize(
    "source",
    [
        "unknown() + 1",
        "-unknown()",
        "unknown() == 1",
        "unknown() and false",
        "false and unknown()",
        "unknown() or false",
        "true or unknown()",
        "1 if unknown() else 2",
        "unknown() if false else 1",
        "1 if true else unknown()",
        "abs(unknown())",
        "let x = unknown() in x",
        "let x = 1 in unknown()",
    ],
)
def test_unknown_calls_are_validated_through_every_ast_shape(source: str) -> None:
    with pytest.raises(UnknownFunctionError):
        Engine().compile(source)


def test_arity_is_validated_in_branch_that_will_not_execute() -> None:
    with pytest.raises(FunctionArityError):
        Engine().compile("1 if true else sqrt()")


@pytest.mark.parametrize("source", ["false and abs()", "true or abs()"])
def test_arity_is_validated_in_short_circuited_boolean_branch(
    source: str,
) -> None:
    with pytest.raises(FunctionArityError):
        Engine().compile(source)


@pytest.mark.parametrize(
    ("source", "error_type"),
    [
        ("  missing()", UnknownFunctionError),
        ("  abs()", FunctionArityError),
    ],
)
def test_compile_time_function_errors_use_call_position(
    source: str, error_type: type[Exception]
) -> None:
    with pytest.raises(error_type) as info:
        Engine().compile(source)

    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 3)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("sqrt(-1)", "non-negative"),
        ("log(0)", "positive"),
        ("log(-2)", "positive"),
    ],
)
def test_builtin_domain_failures(source: str, message: str) -> None:
    with pytest.raises(ExpressionEvaluationError) as info:
        evaluate(source)
    assert message in str(info.value)


def test_pow_complex_result_is_rejected() -> None:
    with pytest.raises(ExpressionEvaluationError):
        evaluate("pow(-1, 0.5)")


@pytest.mark.parametrize(
    ("source", "variables"),
    [
        ("floor(value)", {"value": float("inf")}),
        ("ceil(value)", {"value": float("nan")}),
        ("round(value)", {"value": float("inf")}),
        ("round(value)", {"value": float("nan")}),
        ("sqrt(value)", {"value": 10**1000}),
        ("pow(value, 2)", {"value": 1e308}),
        ("pow(0, -1)", None),
    ],
)
def test_builtin_calculation_failures_are_engine_errors(
    source: str, variables: Mapping[str, object] | None
) -> None:
    with pytest.raises(ExpressionEvaluationError) as info:
        evaluate(source, variables)
    assert info.value.position is not None
    assert info.value.__cause__ is not None


def test_nested_builtin_calls() -> None:
    assert evaluate("sqrt(pow(2, 2))") == 2.0


def test_builtin_in_conditional() -> None:
    assert evaluate("abs(-1) if true else abs(-2)") == 1


def test_builtin_in_boolean_expression() -> None:
    assert evaluate("abs(-1) == 1 and max(1, 2) == 2") is True


def test_builtin_in_local_binding() -> None:
    assert evaluate("let x = sqrt(4) in x + 1") == 3.0


def test_builtin_arguments_evaluated_left_to_right() -> None:
    variables = RecordingMapping({"a": 1, "b": 2})
    assert evaluate("min(a, b)", variables) == 1
    assert variables.lookups == ["a", "b"]


def test_builtin_arguments_evaluated_exactly_once() -> None:
    variables = RecordingMapping({"source": 7})
    assert evaluate("max(source, source)", variables) == 7
    assert variables.lookups == ["source", "source"]


def test_repeated_evaluation_of_same_compiled_expression() -> None:
    expression = Engine().compile("abs(x)")
    assert expression.evaluate({"x": -1}) == 1
    assert expression.evaluate({"x": -5}) == 5
