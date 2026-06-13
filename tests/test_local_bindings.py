"""Stage 10 tests: runtime evaluation of ``let name = value in body``.

These tests drive the real public pipeline ``tokenize -> parse -> evaluate``
(via the ``run`` helper) and assert on returned runtime values or on the raised
engine-specific errors. They cover only local-binding evaluation: scope and
shadowing, value-evaluated-once semantics, null/undefined preservation, error
propagation with original positions, and caller-input/state isolation.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from expression_engine import UNDEFINED
from expression_engine.errors import (
    DivisionByZeroError,
    ExpressionTypeError,
)
from expression_engine._ast import BinaryExpr, LetExpr
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


def run(source: str, variables: Mapping[str, object] | None = None) -> object:
    """Evaluate ``source`` through tokenize -> parse -> evaluate."""
    return evaluate(parse(tokenize(source)), variables)


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


# --------------------------------------------------------------------------- #
# Basic binding, arithmetic, and strings
# --------------------------------------------------------------------------- #


def test_basic_binding() -> None:
    assert run("let x = 1 in x") == 1


def test_arithmetic_using_local() -> None:
    assert run("let x = 2 in x + 3") == 5


def test_string_concatenation_using_local() -> None:
    assert run('let x = "a" in x + "b"') == "ab"


# --------------------------------------------------------------------------- #
# null / undefined / missing values (kept distinct)
# --------------------------------------------------------------------------- #


def test_bind_null_returns_none() -> None:
    assert run("let x = null in x") is None


def test_bind_undefined_returns_undefined() -> None:
    assert run("let x = undefined in x") is UNDEFINED


def test_bind_missing_variable_is_undefined() -> None:
    # `y` is absent, so the bound value (and thus `x`) is UNDEFINED, not None.
    assert run("let x = y in x") is UNDEFINED


# --------------------------------------------------------------------------- #
# Scope: value uses outer scope, binding not visible in its own value
# --------------------------------------------------------------------------- #


def test_external_variable_used_in_bound_value() -> None:
    assert run("let x = x + 1 in x", {"x": 2}) == 3


def test_binding_not_visible_in_its_own_value() -> None:
    # Inside the value, `x` resolves to the external `x` (10), never to the
    # binding being defined; the body then sees the new binding (11).
    assert run("let x = x + 1 in x", {"x": 10}) == 11


def test_local_shadows_external_variable() -> None:
    assert run("let x = 1 in x", {"x": 10}) == 1


# --------------------------------------------------------------------------- #
# Nesting, shadowing, and outer-scope restoration
# --------------------------------------------------------------------------- #


def test_nested_bindings() -> None:
    assert run("let x = 1 in let y = x + 1 in y") == 2


def test_nested_shadowing() -> None:
    assert run("let x = 1 in let x = 2 in x") == 2


def test_outer_binding_available_after_inner() -> None:
    assert run("let x = 1 in (let x = 2 in x) + x") == 3


# --------------------------------------------------------------------------- #
# Conditionals in value and body
# --------------------------------------------------------------------------- #


def test_conditional_in_bound_value() -> None:
    assert run("let x = 1 if b else 2 in x", {"b": True}) == 1
    assert run("let x = 1 if b else 2 in x", {"b": False}) == 2


def test_conditional_in_body() -> None:
    assert run("let x = 5 in x if c else 0", {"c": True}) == 5
    assert run("let x = 5 in x if c else 0", {"c": False}) == 0


# --------------------------------------------------------------------------- #
# Error propagation (errors are not swallowed or converted)
# --------------------------------------------------------------------------- #


def test_error_in_bound_value_propagates() -> None:
    with pytest.raises(DivisionByZeroError):
        run("let x = 1 / 0 in x")


def test_error_in_body_propagates() -> None:
    with pytest.raises(ExpressionTypeError):
        run('let x = 1 in x + "a"')


# --------------------------------------------------------------------------- #
# Value evaluated exactly once, in the outer scope
# --------------------------------------------------------------------------- #


def test_bound_value_evaluated_exactly_once() -> None:
    # `let x = source in x + x` must read the external `source` exactly once:
    # the value is evaluated a single time, and the two `x` uses resolve to the
    # local binding (not back to `source`).
    variables = RecordingMapping({"source": 7})
    assert run("let x = source in x + x", variables) == 14
    assert variables.lookups == ["source"]


# --------------------------------------------------------------------------- #
# State isolation and input preservation
# --------------------------------------------------------------------------- #


def test_caller_mapping_is_not_mutated() -> None:
    variables = {"x": 10}
    before = dict(variables)
    run("let x = 1 in x", variables)
    assert variables == before


def test_repeated_evaluation_with_different_mappings() -> None:
    ast = parse(tokenize("let y = x + 1 in y"))
    assert evaluate(ast, {"x": 1}) == 2
    assert evaluate(ast, {"x": 41}) == 42
    # The AST carries no per-evaluation state, so order does not matter.
    assert evaluate(ast, {"x": 1}) == 2


# --------------------------------------------------------------------------- #
# Error position anchored at the failing operator, not at `let`
# --------------------------------------------------------------------------- #


def test_error_position_anchored_at_failing_operator() -> None:
    source = 'let x = 1 in x + "a"'
    ast = parse(tokenize(source))
    assert isinstance(ast, LetExpr)
    assert isinstance(ast.body, BinaryExpr)
    operator_position = ast.body.position

    with pytest.raises(ExpressionTypeError) as exc_info:
        evaluate(ast)

    # The error points at the `+` operator inside the body, not at `let`.
    assert exc_info.value.position == operator_position
    assert exc_info.value.position != ast.position
