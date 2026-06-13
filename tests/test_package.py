"""Stage 1 tests: package import, the UNDEFINED singleton, and the error hierarchy.

These tests exercise only what Stage 1 actually implements. They intentionally
do not assume any expression-language behavior.
"""

from __future__ import annotations

import copy
import pickle

import pytest

import expression_engine
from expression_engine import (
    UNDEFINED,
    DivisionByZeroError,
    ExpressionError,
    ExpressionEvaluationError,
    ExpressionSyntaxError,
    ExpressionTypeError,
    ExpressionValidationError,
    FunctionArityError,
    UnknownFunctionError,
)


def test_package_imports() -> None:
    assert expression_engine.__file__ is not None
    assert isinstance(expression_engine.__version__, str)


def test_undefined_is_distinct_from_none() -> None:
    assert UNDEFINED is not None


def test_undefined_repr_is_stable() -> None:
    assert repr(UNDEFINED) == "UNDEFINED"


def test_undefined_is_a_singleton_via_constructor() -> None:
    assert type(UNDEFINED)() is UNDEFINED


def test_undefined_singleton_survives_copy_and_pickle() -> None:
    assert copy.copy(UNDEFINED) is UNDEFINED
    assert copy.deepcopy(UNDEFINED) is UNDEFINED
    assert pickle.loads(pickle.dumps(UNDEFINED)) is UNDEFINED


def test_undefined_is_immutable() -> None:
    with pytest.raises(AttributeError):
        UNDEFINED.foo = 1  # type: ignore[attr-defined]


def test_all_errors_inherit_from_base() -> None:
    for exc in (
        ExpressionSyntaxError,
        ExpressionValidationError,
        ExpressionEvaluationError,
        ExpressionTypeError,
        DivisionByZeroError,
        UnknownFunctionError,
        FunctionArityError,
    ):
        assert issubclass(exc, ExpressionError)


def test_error_hierarchy_relationships() -> None:
    assert issubclass(ExpressionSyntaxError, ExpressionError)
    assert issubclass(ExpressionValidationError, ExpressionError)
    assert issubclass(ExpressionEvaluationError, ExpressionError)

    assert issubclass(ExpressionTypeError, ExpressionEvaluationError)
    assert issubclass(DivisionByZeroError, ExpressionEvaluationError)

    assert issubclass(UnknownFunctionError, ExpressionValidationError)
    assert issubclass(FunctionArityError, ExpressionValidationError)


def test_base_error_is_an_exception() -> None:
    assert issubclass(ExpressionError, Exception)
