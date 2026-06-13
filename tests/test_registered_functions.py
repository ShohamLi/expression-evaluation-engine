"""Registered host function tests through the public API."""

from __future__ import annotations

import functools
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from expression_engine import (
    UNDEFINED,
    Engine,
    ExpressionEvaluationError,
    ExpressionTypeError,
    ExpressionValidationError,
    FunctionArityError,
    UnknownFunctionError,
)


def test_successful_one_argument_function() -> None:
    engine = Engine(functions={"double": lambda x: x * 2})
    assert engine.compile("double(3)").evaluate() == 6


def test_successful_multi_argument_function() -> None:
    engine = Engine(functions={"add": lambda a, b: a + b})
    assert engine.compile("add(2, 3)").evaluate() == 5


def test_zero_argument_function() -> None:
    engine = Engine(functions={"answer": lambda: 42})
    assert engine.compile("answer()").evaluate() == 42


def test_positional_parameters_with_defaults() -> None:
    engine = Engine(functions={"scale": lambda value, factor=2: value * factor})
    assert engine.compile("scale(5)").evaluate() == 10
    assert engine.compile("scale(5, 3)").evaluate() == 15


def test_positional_only_parameters_are_supported() -> None:
    def subtract(left: int, right: int = 1, /) -> int:
        return left - right

    engine = Engine(functions={"subtract": subtract})
    assert engine.compile("subtract(5)").evaluate() == 4
    assert engine.compile("subtract(5, 2)").evaluate() == 3


def test_inspectable_builtin_callable_with_positional_only_parameter() -> None:
    engine = Engine(functions={"length": len})
    assert engine.compile('length("abc")').evaluate() == 3


def test_bound_method_signature_is_supported() -> None:
    class Calculator:
        def add(self, left: int, right: int = 1) -> int:
            return left + right

    engine = Engine(functions={"add": Calculator().add})
    assert engine.compile("add(2)").evaluate() == 3
    assert engine.compile("add(2, 3)").evaluate() == 5


def test_callable_object_signature_is_supported() -> None:
    class Add:
        def __call__(self, left: int, right: int = 1) -> int:
            return left + right

    engine = Engine(functions={"add": Add()})
    assert engine.compile("add(2)").evaluate() == 3


def test_positional_partial_signature_is_supported() -> None:
    def add(left: int, right: int) -> int:
        return left + right

    engine = Engine(functions={"add_one": functools.partial(add, 1)})
    assert engine.compile("add_one(2)").evaluate() == 3


def test_keyword_partial_is_rejected_when_it_creates_keyword_only_parameter() -> None:
    def add(left: int, right: int) -> int:
        return left + right

    with pytest.raises(ExpressionValidationError, match="keyword-only"):
        Engine(functions={"bad": functools.partial(add, right=1)})


@pytest.mark.parametrize(
    "source",
    ["add(1)", "add(1, 2, 3)"],
)
def test_registered_arity_errors_during_compile(source: str) -> None:
    engine = Engine(functions={"add": lambda a, b: a + b})
    with pytest.raises(FunctionArityError):
        engine.compile(source)


@pytest.mark.parametrize("source", ["  scale()", "  scale(1, 2, 3)"])
def test_optional_registered_arity_bounds_are_validated_during_compile(
    source: str,
) -> None:
    engine = Engine(functions={"scale": lambda value, factor=2: value * factor})
    with pytest.raises(FunctionArityError) as info:
        engine.compile(source)

    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 3)


def test_unknown_registered_function_during_compile() -> None:
    engine = Engine(functions={"known": lambda: 1})
    with pytest.raises(UnknownFunctionError):
        engine.compile("missing()")


@pytest.mark.parametrize("functions", [[], [("f", lambda: 1)], 1, "f"])
def test_functions_argument_must_be_a_mapping(functions: object) -> None:
    with pytest.raises(ExpressionValidationError, match="mapping or None"):
        Engine(functions=functions)  # type: ignore[arg-type]


def test_registered_function_name_must_be_a_string() -> None:
    with pytest.raises(ExpressionValidationError, match="function names must be str"):
        Engine(functions={1: lambda: 1})  # type: ignore[dict-item]


@pytest.mark.parametrize(
    "name",
    ["1bad", "bad-name", "bad name"],
)
def test_invalid_registered_function_names(name: str) -> None:
    with pytest.raises(ExpressionValidationError):
        Engine(functions={name: lambda: 1})


def test_keyword_registered_name_is_rejected() -> None:
    with pytest.raises(ExpressionValidationError):
        Engine(functions={"if": lambda: 1})


@pytest.mark.parametrize(
    "name", ["abs", "min", "max", "round", "floor", "ceil", "sqrt", "pow", "log"]
)
def test_cannot_override_builtin_name(name: str) -> None:
    with pytest.raises(ExpressionValidationError):
        Engine(functions={name: lambda x: x})


def test_non_callable_registration_is_rejected() -> None:
    with pytest.raises(ExpressionValidationError):
        Engine(functions={"bad": 1})  # type: ignore[dict-item]


@pytest.mark.parametrize(
    "fn",
    [
        lambda *args: sum(args),
        lambda a, *, b: a + b,
        lambda **kwargs: 0,
    ],
)
def test_unsupported_callable_signatures_are_rejected(fn: object) -> None:
    with pytest.raises(ExpressionValidationError):
        Engine(functions={"bad": fn})  # type: ignore[dict-item]


def test_uninspectable_callable_signature_is_rejected() -> None:
    class Uninspectable:
        @property
        def __signature__(self) -> object:
            raise ValueError("no signature")

        def __call__(self) -> int:
            return 1

    with pytest.raises(ExpressionValidationError, match="cannot be inspected"):
        Engine(functions={"bad": Uninspectable()})


def test_callable_signature_is_inspected_only_during_engine_construction() -> None:
    engine = Engine(functions={"double": lambda value: value * 2})
    with patch(
        "expression_engine._functions.inspect.signature",
        side_effect=AssertionError("signature inspected after construction"),
    ):
        expression = engine.compile("double(2)")
        assert expression.evaluate() == 4


def test_functions_mapping_is_snapshotted() -> None:
    functions = {"double": lambda x: x * 2}
    engine = Engine(functions=functions)
    functions["double"] = lambda x: x * 3  # type: ignore[index]
    assert engine.compile("double(2)").evaluate() == 4


def test_registered_functions_mapping_is_not_mutated() -> None:
    functions = {"double": lambda x: x * 2}
    before = dict(functions)
    Engine(functions=functions).compile("double(1)").evaluate()
    assert functions == before


@pytest.mark.parametrize(
    ("fn", "expected"),
    [
        (lambda: 1, 1),
        (lambda: 1.5, 1.5),
        (lambda: "x", "x"),
        (lambda: True, True),
        (lambda: None, None),
        (lambda: UNDEFINED, UNDEFINED),
    ],
)
def test_allowed_return_values(fn: object, expected: object) -> None:
    engine = Engine(functions={"f": fn})  # type: ignore[dict-item]
    result = engine.compile("f()").evaluate()
    if expected is None or expected is UNDEFINED:
        assert result is expected
    else:
        assert type(result) is type(expected)
        assert result == expected


@pytest.mark.parametrize(
    "value",
    [
        [1],
        (1,),
        object(),
        type("IntSubclass", (int,), {})(1),
        type("FloatSubclass", (float,), {})(1.0),
        type("StrSubclass", (str,), {})("x"),
    ],
)
def test_unsupported_return_value_is_rejected(value: object) -> None:
    engine = Engine(functions={"bad": lambda: value})
    with pytest.raises(ExpressionTypeError):
        engine.compile("bad()").evaluate()


def test_unsupported_return_value_error_uses_call_position() -> None:
    engine = Engine(functions={"bad": object})
    with pytest.raises(ExpressionTypeError) as info:
        engine.compile("  bad()").evaluate()

    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 3)


def test_registered_functions_receive_null_and_undefined_without_coercion() -> None:
    engine = Engine(functions={"identity": lambda value: value})
    assert engine.compile("identity(null)").evaluate() is None
    assert engine.compile("identity(undefined)").evaluate() is UNDEFINED


def test_registered_exception_is_wrapped_with_cause() -> None:
    def fail() -> int:
        raise ValueError("boom")

    engine = Engine(functions={"fail": fail})
    with pytest.raises(ExpressionEvaluationError) as info:
        engine.compile("  fail()").evaluate()
    assert type(info.value.__cause__) is ValueError
    assert "fail()" in str(info.value)
    assert info.value.position is not None
    assert info.value.position.column == 3


def test_existing_engine_error_propagates_from_callable() -> None:
    error = ExpressionEvaluationError("expected")

    def fail() -> int:
        raise error

    engine = Engine(functions={"fail": fail})
    with pytest.raises(ExpressionEvaluationError, match="expected") as info:
        engine.compile("fail()").evaluate()
    assert info.value is error


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_base_exception_from_callable_is_not_wrapped(
    error_type: type[BaseException],
) -> None:
    error = error_type("stop")

    def stop() -> int:
        raise error

    engine = Engine(functions={"stop": stop})
    with pytest.raises(error_type, match="stop") as info:
        engine.compile("stop()").evaluate()

    assert info.value is error


def test_registered_arguments_are_evaluated_left_to_right_exactly_once() -> None:
    events: list[str] = []

    def first() -> int:
        events.append("first")
        return 1

    def second() -> int:
        events.append("second")
        return 2

    engine = Engine(
        functions={
            "first": first,
            "second": second,
            "combine": lambda left, right: left + right,
        }
    )
    assert engine.compile("combine(first(), second())").evaluate() == 3
    assert events == ["first", "second"]


def test_registered_arity_is_validated_in_skipped_branch() -> None:
    engine = Engine(functions={"one": lambda value: value})
    with pytest.raises(FunctionArityError):
        engine.compile("1 if true else one()")


def test_nested_registered_and_builtin_calls() -> None:
    engine = Engine(functions={"double": lambda x: x * 2})
    assert engine.compile("double(sqrt(9))").evaluate() == 6.0


def test_repeated_evaluation_of_registered_expression() -> None:
    engine = Engine(functions={"double": lambda x: x * 2})
    expression = engine.compile("double(x)")
    assert expression.evaluate({"x": 2}) == 4
    assert expression.evaluate({"x": 5}) == 10


def test_concurrent_evaluation_with_pure_registered_function() -> None:
    engine = Engine(functions={"inc": lambda x: x + 1})
    expression = engine.compile("inc(x)")
    mappings = [{"x": i} for i in range(8)]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(expression.evaluate, mappings))

    assert results == [i + 1 for i in range(8)]


def test_registered_with_external_variables() -> None:
    engine = Engine(functions={"double": lambda value: value * 2})
    assert engine.compile("double(x) + sqrt(9)").evaluate({"x": 4}) == 11.0
