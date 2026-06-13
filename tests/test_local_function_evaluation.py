"""Local-function validation, scope, and evaluation tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from expression_engine import (
    UNDEFINED,
    Engine,
    ExpressionEvaluationError,
    ExpressionValidationError,
    FunctionArityError,
    UnknownFunctionError,
)


def evaluate(source: str, variables: dict[str, object] | None = None) -> object:
    return Engine().compile(source).evaluate(variables)


# --------------------------------------------------------------------------- #
# Basic evaluation and return values
# --------------------------------------------------------------------------- #


def test_zero_parameter_function() -> None:
    assert evaluate("let constant() = 5 in constant()") == 5


def test_one_parameter_function() -> None:
    assert evaluate("let double(x) = x * 2 in double(4)") == 8


def test_multiple_parameter_function() -> None:
    assert evaluate("let add(a, b) = a + b in add(1, 2)") == 3


def test_string_result() -> None:
    assert evaluate('let greet(name) = "hello " + name in greet("Ada")') == "hello Ada"


def test_boolean_result() -> None:
    assert evaluate("let positive(x) = x > 0 in positive(2)") is True


@pytest.mark.parametrize(
    ("argument", "expected"),
    [("null", None), ("undefined", UNDEFINED)],
)
def test_null_and_undefined_are_preserved(
    argument: str, expected: object
) -> None:
    assert evaluate(f"let identity(x) = x in identity({argument})") is expected


def test_builtin_call_from_local_function() -> None:
    assert evaluate("let root(x) = sqrt(x) in root(9)") == 3.0


def test_registered_call_from_local_function() -> None:
    engine = Engine(functions={"triple": lambda value: value * 3})
    assert engine.compile("let apply(x) = triple(x) in apply(4)").evaluate() == 12


def test_function_body_is_evaluated_again_for_each_call() -> None:
    calls: list[str] = []

    def probe() -> int:
        calls.append("probe")
        return 1

    engine = Engine(functions={"probe": probe})
    expression = engine.compile("let call() = probe() in call() + call()")

    assert expression.evaluate() == 2
    assert calls == ["probe", "probe"]


def test_local_function_result_does_not_use_host_return_validation() -> None:
    value = object()
    result = evaluate("let identity(x) = x in identity(value)", {"value": value})
    assert result is value


# --------------------------------------------------------------------------- #
# Evaluation order and laziness
# --------------------------------------------------------------------------- #


def test_arguments_are_evaluated_left_to_right_exactly_once() -> None:
    events: list[str] = []

    def first() -> int:
        events.append("first")
        return 1

    def second() -> int:
        events.append("second")
        return 2

    def body(left: int, right: int) -> int:
        events.append("body")
        return left + right

    engine = Engine(functions={"first": first, "second": second, "body": body})
    expression = engine.compile(
        "let combine(a, b) = body(a, b) in combine(first(), second())"
    )

    assert expression.evaluate() == 3
    assert events == ["first", "second", "body"]


def test_function_body_is_not_evaluated_at_definition_time() -> None:
    events: list[str] = []

    def body() -> int:
        events.append("body")
        return 1

    engine = Engine(functions={"body": body})
    assert engine.compile("let unused() = body() in 5").evaluate() == 5
    assert events == []


def test_runtime_error_in_unused_function_body_is_lazy() -> None:
    assert evaluate("let unused() = 1 / 0 in 5") == 5


def test_argument_failure_prevents_function_body_evaluation() -> None:
    events: list[str] = []

    def fail_argument() -> int:
        events.append("argument")
        raise ValueError("stop")

    def body() -> int:
        events.append("body")
        return 1

    engine = Engine(functions={"fail_argument": fail_argument, "body": body})
    expression = engine.compile(
        "let use(x) = body() in use(fail_argument())"
    )

    with pytest.raises(ExpressionEvaluationError):
        expression.evaluate()
    assert events == ["argument"]


@pytest.mark.parametrize(
    ("function_body", "expected"),
    [("true or fail()", True), ("1 if true else fail()", 1)],
)
def test_short_circuit_remains_lazy_inside_function_body(
    function_body: str, expected: object
) -> None:
    events: list[str] = []

    def fail() -> bool:
        events.append("fail")
        return False

    engine = Engine(functions={"fail": fail})
    expression = engine.compile(
        f"let check() = {function_body} in check()"
    )

    assert expression.evaluate() == expected
    assert events == []


# --------------------------------------------------------------------------- #
# Lexical variable and function scope
# --------------------------------------------------------------------------- #


def test_captures_outer_local_variable() -> None:
    assert evaluate("let x = 4 in let get() = x in get()") == 4


def test_capture_uses_definition_scope_not_call_scope() -> None:
    source = "let x = 1 in let get() = x in let x = 2 in get()"
    assert evaluate(source) == 1


def test_parameter_shadows_captured_variable() -> None:
    source = "let x = 10 in let add_one(x) = x + 1 in add_one(2)"
    assert evaluate(source) == 3


def test_local_binding_inside_function_body() -> None:
    source = "let calculate(x) = let y = x + 1 in y * 2 in calculate(3)"
    assert evaluate(source) == 8


def test_nested_function_captures_outer_parameter() -> None:
    source = (
        "let outer(x) = let inner(y) = x + y in inner(2) "
        "in outer(3)"
    )
    assert evaluate(source) == 5


def test_nested_function_calls_visible_outer_local_function() -> None:
    source = (
        "let increment(x) = x + 1 in "
        "let outer(y) = let inner() = increment(y) in inner() "
        "in outer(3)"
    )
    assert evaluate(source) == 4


def test_local_function_shadows_registered_function() -> None:
    engine = Engine(functions={"value": lambda: 99})
    expression = engine.compile("let value() = 1 in value()")
    assert expression.evaluate() == 1


def test_local_function_definition_does_not_leak() -> None:
    with pytest.raises(UnknownFunctionError):
        Engine().compile("(let local() = 1 in local()) + local()")


def test_caller_variable_mapping_is_not_mutated() -> None:
    variables = {"x": 4}
    before = dict(variables)

    result = evaluate("let add_one(value) = value + 1 in add_one(x)", variables)

    assert result == 5
    assert variables == before


# --------------------------------------------------------------------------- #
# Compile-time validation
# --------------------------------------------------------------------------- #


def test_duplicate_parameter_names_are_rejected_at_definition_position() -> None:
    with pytest.raises(ExpressionValidationError) as info:
        Engine().compile("  let f(x, x) = x in f(1, 2)")

    assert "duplicate parameter" in str(info.value)
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 3)


@pytest.mark.parametrize("name", ["abs", "sqrt"])
def test_builtin_function_names_are_reserved(name: str) -> None:
    with pytest.raises(ExpressionValidationError) as info:
        Engine().compile(f"let {name}(x) = x in {name}(1)")

    assert "built-in name" in str(info.value)
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 1)


@pytest.mark.parametrize(
    "source",
    [
        "let f(x) = x in f()",
        "let f(x) = x in f(1, 2)",
    ],
)
def test_local_function_arity_is_validated_during_compile(source: str) -> None:
    with pytest.raises(FunctionArityError) as info:
        Engine().compile(source)

    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 17)


def test_unknown_call_in_unused_function_is_rejected() -> None:
    with pytest.raises(UnknownFunctionError):
        Engine().compile("let unused() = unknown() in 1")


def test_unknown_call_in_nested_unused_function_body_is_rejected() -> None:
    source = "let outer() = let inner() = unknown() in 1 in 1"
    with pytest.raises(UnknownFunctionError):
        Engine().compile(source)


def test_invalid_local_arity_in_skipped_conditional_branch_is_rejected() -> None:
    source = "let unused(x) = x in 1 if true else unused()"
    with pytest.raises(FunctionArityError):
        Engine().compile(source)


def test_direct_recursion_is_rejected_at_call_position() -> None:
    with pytest.raises(ExpressionValidationError) as info:
        Engine().compile("let f(x) = f(x) in 1")

    assert "recursion" in str(info.value)
    assert info.value.position is not None
    assert (info.value.position.line, info.value.position.column) == (1, 12)


def test_recursion_in_skipped_branch_is_rejected() -> None:
    source = "let f(x) = x if true else f(x) in 1"
    with pytest.raises(ExpressionValidationError, match="recursion"):
        Engine().compile(source)


def test_recursion_through_nested_local_function_is_rejected() -> None:
    source = "let f(x) = let inner() = f(x) in 1 in 1"
    with pytest.raises(ExpressionValidationError, match="recursion"):
        Engine().compile(source)


def test_recursive_name_does_not_fall_through_to_registered_function() -> None:
    engine = Engine(functions={"f": lambda value: value})
    with pytest.raises(ExpressionValidationError, match="recursion"):
        engine.compile("let f(x) = f(x) in f(1)")


# --------------------------------------------------------------------------- #
# Reuse, isolation, and concurrency
# --------------------------------------------------------------------------- #


def test_compiled_local_function_reuses_different_variable_mappings() -> None:
    expression = Engine().compile("let get() = x in get()")
    assert expression.evaluate({"x": 1}) == 1
    assert expression.evaluate({"x": 2}) == 2


def test_closure_state_does_not_leak_between_evaluations() -> None:
    expression = Engine().compile(
        "let x = external in let get() = x in get()"
    )
    assert expression.evaluate({"external": 10}) == 10
    assert expression.evaluate({"external": 20}) == 20
    assert expression.evaluate({"external": 10}) == 10


def test_compiled_local_function_is_safe_for_concurrent_evaluation() -> None:
    expression = Engine().compile("let add_one(value) = value + 1 in add_one(x)")
    mappings = [{"x": value} for value in range(8)]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(expression.evaluate, mappings))

    assert results == [value + 1 for value in range(8)]
