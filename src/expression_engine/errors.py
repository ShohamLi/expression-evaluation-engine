"""Exception hierarchy for the expression engine.

The hierarchy is intentionally small and stable so that later stages (lexer,
parser, validator, evaluator) and library consumers can catch errors at the
granularity they need:

    ExpressionError                     base for everything raised by this library
    ├── ExpressionSyntaxError           lexing/parsing problems (compile time)
    ├── ExpressionValidationError       static checks after a successful parse
    │   ├── UnknownFunctionError        call to a name that resolves to no function
    │   └── FunctionArityError          call with the wrong number of arguments
    └── ExpressionEvaluationError       failures while evaluating a compiled tree
        ├── ExpressionTypeError         operation applied to unsupported operand types
        └── DivisionByZeroError         division (``/``) by a zero divisor

Function resolution (local / registered / built-in) and declared arities are
known once an expression has been parsed, so ``UnknownFunctionError`` and
``FunctionArityError`` are classified as validation errors rather than runtime
errors. This classification is part of the library's documented contract.

No behavior beyond construction is attached to these classes in this stage.
"""

from __future__ import annotations

__all__ = [
    "ExpressionError",
    "ExpressionSyntaxError",
    "ExpressionValidationError",
    "ExpressionEvaluationError",
    "ExpressionTypeError",
    "DivisionByZeroError",
    "UnknownFunctionError",
    "FunctionArityError",
]


class ExpressionError(Exception):
    """Base class for every error raised by the expression engine."""


class ExpressionSyntaxError(ExpressionError):
    """Raised when source text cannot be tokenized or parsed."""


class ExpressionValidationError(ExpressionError):
    """Raised when a parsed expression fails a static validation check."""


class ExpressionEvaluationError(ExpressionError):
    """Raised when a compiled expression fails during evaluation."""


class ExpressionTypeError(ExpressionEvaluationError):
    """Raised when an operation is applied to unsupported operand types."""


class DivisionByZeroError(ExpressionEvaluationError):
    """Raised when ``/`` is applied with a zero divisor."""


class UnknownFunctionError(ExpressionValidationError):
    """Raised when a call references a name that resolves to no function."""


class FunctionArityError(ExpressionValidationError):
    """Raised when a function is called with the wrong number of arguments."""
