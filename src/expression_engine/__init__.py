"""expression_engine: a reusable expression-evaluation library.

This package provides :class:`Engine` and :class:`Expression` for compiling
expression source text once and evaluating it repeatedly against variable
mappings, plus the ``UNDEFINED`` sentinel and the exception hierarchy rooted at
:class:`ExpressionError`.
"""

from __future__ import annotations

from ._engine import Engine, Expression
from ._values import UNDEFINED
from .errors import (
    DivisionByZeroError,
    ExpressionError,
    ExpressionEvaluationError,
    ExpressionSyntaxError,
    ExpressionTypeError,
    ExpressionValidationError,
    FunctionArityError,
    UnknownFunctionError,
)

__version__ = "0.0.0"

__all__ = [
    "Engine",
    "Expression",
    "UNDEFINED",
    "ExpressionError",
    "ExpressionSyntaxError",
    "ExpressionValidationError",
    "ExpressionEvaluationError",
    "ExpressionTypeError",
    "DivisionByZeroError",
    "UnknownFunctionError",
    "FunctionArityError",
    "__version__",
]
