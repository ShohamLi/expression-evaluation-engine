"""expression_engine: a reusable expression-evaluation library.

This package is under development. Only the values and exceptions exported here
are implemented at this stage: the ``UNDEFINED`` sentinel and the exception
hierarchy rooted at ``ExpressionError``. Expression compilation and evaluation
(the ``Engine`` and ``Expression`` types) are not implemented yet and are
deliberately not exported until they have real, tested behavior.
"""

from __future__ import annotations

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
