"""Exception hierarchy for the expression engine.

The hierarchy is intentionally small and stable so that the lexer, parser,
validator, evaluator, and library consumers can catch errors at the
granularity they need:

    ExpressionError                     base for everything raised by this library
    ├── ExpressionSyntaxError           lexing/parsing problems (compile time)
    │   ├── LexerError                  tokenization failure carrying a source position
    │   └── ParserError                 parsing failure carrying a source position
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

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._tokens import Position

__all__ = [
    "ExpressionError",
    "ExpressionSyntaxError",
    "LexerError",
    "ParserError",
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


class LexerError(ExpressionSyntaxError):
    """Raised when source text cannot be tokenized (lexical analysis).

    Covers invalid characters, malformed numbers, invalid string escapes, and
    unterminated strings. The offending source :class:`~._tokens.Position` is
    kept on the ``position`` attribute and folded into the message so callers
    can locate the problem.
    """

    def __init__(self, message: str, position: "Position") -> None:
        self.position = position
        super().__init__(
            f"{message} at line {position.line}, column {position.column}"
        )


class ParserError(ExpressionSyntaxError):
    """Raised when a token sequence cannot be parsed into an expression.

    Covers unexpected tokens, missing operands, unbalanced parentheses,
    incomplete conditional expressions, chained comparisons, and trailing
    tokens after a complete expression. Mirrors :class:`LexerError`: the
    offending :class:`~._tokens.Position` is kept on ``position`` and folded
    into the message so callers can locate the problem.
    """

    def __init__(self, message: str, position: "Position") -> None:
        self.position = position
        super().__init__(
            f"{message} at line {position.line}, column {position.column}"
        )


class ExpressionValidationError(ExpressionError):
    """Raised when a parsed expression fails a static validation check."""

    def __init__(self, message: str, position: "Position | None" = None) -> None:
        self.position = position
        if position is not None:
            message = f"{message} at line {position.line}, column {position.column}"
        super().__init__(message)


class ExpressionEvaluationError(ExpressionError):
    """Raised when an expression fails during evaluation.

    The source ``position`` is optional so existing message-only construction
    keeps working, but when the evaluator supplies the offending AST anchor it
    is kept on the ``position`` attribute and folded into the message (matching
    :class:`LexerError` and :class:`ParserError`). The two subclasses below
    inherit this behavior.
    """

    def __init__(self, message: str, position: "Position | None" = None) -> None:
        self.position = position
        if position is not None:
            message = f"{message} at line {position.line}, column {position.column}"
        super().__init__(message)


class ExpressionTypeError(ExpressionEvaluationError):
    """Raised when an operation is applied to unsupported operand types."""


class DivisionByZeroError(ExpressionEvaluationError):
    """Raised when ``/`` is applied with a zero divisor."""


class UnknownFunctionError(ExpressionValidationError):
    """Raised when a call references a name that resolves to no function."""

    def __init__(self, message: str, position: "Position | None" = None) -> None:
        super().__init__(message, position)


class FunctionArityError(ExpressionValidationError):
    """Raised when a function is called with the wrong number of arguments."""

    def __init__(self, message: str, position: "Position | None" = None) -> None:
        super().__init__(message, position)
