"""Stage 12 tests: the public Engine / Expression compilation and evaluation API.

These tests exercise only the public package surface
(``from expression_engine import Engine, Expression``) except for the
compile/evaluate boundary test, which spies on symbols in the private
``_engine`` module.
"""

from __future__ import annotations

import dataclasses
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

import expression_engine
import expression_engine._engine as engine_module
from expression_engine import (
    UNDEFINED,
    Engine,
    Expression,
    ExpressionSyntaxError,
    ExpressionTypeError,
    DivisionByZeroError,
    UnknownFunctionError,
)


def test_engine_and_expression_are_importable() -> None:
    assert expression_engine.Engine is Engine
    assert expression_engine.Expression is Expression


def test_basic_compile_and_evaluate() -> None:
    expression = Engine().compile("2 + 3")
    assert expression.evaluate() == 5


def test_repeated_evaluation_with_different_mappings() -> None:
    expression = Engine().compile("x * 2")
    assert expression.evaluate({"x": 3}) == 6
    assert expression.evaluate({"x": 10}) == 20


def test_compile_once_evaluate_many_does_not_retokenize_or_reparse() -> None:
    with patch.object(
        engine_module, "tokenize", wraps=engine_module.tokenize
    ) as spy_tokenize, patch.object(
        engine_module, "parse", wraps=engine_module.parse
    ) as spy_parse:
        expression = Engine().compile("2 + x")

        assert spy_tokenize.call_count == 1
        assert spy_parse.call_count == 1

        assert expression.evaluate({"x": 3}) == 5
        assert expression.evaluate({"x": 10}) == 12

        assert spy_tokenize.call_count == 1
        assert spy_parse.call_count == 1


def test_evaluate_with_none_uses_empty_mapping() -> None:
    expression = Engine().compile("missing")
    assert expression.evaluate(None) is UNDEFINED


def test_evaluate_with_omitted_variables_uses_empty_mapping() -> None:
    expression = Engine().compile("missing")
    assert expression.evaluate() is UNDEFINED


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"x": 10}
    before = dict(variables)
    Engine().compile("x + 1").evaluate(variables)
    assert variables == before


def test_invalid_syntax_raises_during_compile() -> None:
    with pytest.raises(ExpressionSyntaxError):
        Engine().compile("1 +")


def test_division_by_zero_is_raised_during_evaluate() -> None:
    expression = Engine().compile("1 / 0")
    with pytest.raises(DivisionByZeroError):
        expression.evaluate()


def test_type_error_is_raised_during_evaluate() -> None:
    expression = Engine().compile('"a" + 1')
    with pytest.raises(ExpressionTypeError):
        expression.evaluate()


def test_null_evaluates_to_none() -> None:
    assert Engine().compile("null").evaluate() is None


def test_missing_variable_evaluates_to_undefined() -> None:
    assert Engine().compile("missing").evaluate() is UNDEFINED


def test_local_bindings_through_public_api() -> None:
    assert Engine().compile("let x = 1 in x + 2").evaluate() == 3


def test_expression_is_immutable() -> None:
    expression = Engine().compile("1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        expression._ast = expression._ast  # type: ignore[misc]


def test_no_public_ast_attribute() -> None:
    expression = Engine().compile("1")
    assert not hasattr(expression, "ast")


def test_repr_omits_ast() -> None:
    expression = Engine().compile("1 + 2")
    assert "_ast" not in repr(expression)


def test_concurrent_evaluation_with_independent_mappings() -> None:
    expression = Engine().compile("x + 1")
    mappings = [{"x": i} for i in range(8)]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(expression.evaluate, mappings))

    assert results == [i + 1 for i in range(8)]


def test_unknown_function_call_fails_during_compile() -> None:
    with pytest.raises(UnknownFunctionError):
        Engine().compile("f(1)")


def test_local_function_through_public_api() -> None:
    expression = Engine().compile(
        "let add(a, b) = a + b in add(1, 2)"
    )
    assert expression.evaluate() == 3
