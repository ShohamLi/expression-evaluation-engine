"""Stage 4: the expression evaluator (arithmetic and variable lookup only).

This module walks an immutable AST from :mod:`expression_engine._ast` and
produces a runtime Python value. Stage 4 implements only the smallest useful
subset:

* literals (integer, float, string, boolean, ``null``, ``undefined``);
* external variable lookup;
* unary numeric ``+`` and ``-``;
* binary numeric ``+``, ``-``, ``*``, and ``/`` (true division).

Everything else the parser can produce -- ``not``, comparisons, ``and``/``or``,
and conditional expressions -- is intentionally outside this stage and raises a
clear :class:`~expression_engine.errors.ExpressionEvaluationError` without
evaluating its operands.

Runtime rules (consistent with ``docs/decisions.md``):

* an integer literal evaluates to ``int``; a float literal to ``float``; a
  string literal to its decoded ``str``; ``true``/``false`` to ``bool``;
  ``null`` to ``None``; ``undefined`` to the :data:`UNDEFINED` singleton;
* a missing external variable evaluates to ``UNDEFINED`` rather than raising;
* arithmetic accepts only the exact built-in numeric types ``int`` and
  ``float``. ``bool`` is not numeric, strings are never converted to numbers,
  and no caller-defined numeric subclasses are accepted;
* ``/`` always performs true division and returns a ``float``; a zero divisor
  raises :class:`~expression_engine.errors.DivisionByZeroError`.

The evaluator never re-tokenizes or re-parses, holds no global state, and never
mutates the AST, the caller's mapping, or the caller's values.
"""

from __future__ import annotations

from collections.abc import Mapping

from .errors import (
    DivisionByZeroError,
    ExpressionEvaluationError,
    ExpressionTypeError,
)
from ._ast import (
    BinaryExpr,
    ConditionalExpr,
    Expr,
    LiteralExpr,
    UnaryExpr,
    VariableExpr,
)
from ._tokens import TokenType
from ._values import UNDEFINED

__all__ = ["evaluate"]


# Readable symbols for error messages only. This is not an operation-dispatch
# table: evaluation behavior is selected by the explicit branches below.
_OPERATOR_SYMBOL: dict[TokenType, str] = {
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.NOT: "not",
    TokenType.AND: "and",
    TokenType.OR: "or",
    TokenType.EQ: "==",
    TokenType.NE: "!=",
    TokenType.LT: "<",
    TokenType.LE: "<=",
    TokenType.GT: ">",
    TokenType.GE: ">=",
}

_ARITHMETIC_OPERATORS: frozenset[TokenType] = frozenset(
    {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}
)


def _is_number(value: object) -> bool:
    # Exact built-in numeric types only. ``type(True) is bool`` (not in the
    # tuple), so booleans are rejected, and caller-defined int/float subclasses
    # are not accepted (which also avoids invoking overloaded arithmetic).
    return type(value) in (int, float)


def evaluate(node: Expr, variables: Mapping[str, object] | None = None) -> object:
    """Evaluate an expression AST to a runtime value.

    Args:
        node: The expression AST returned by
            :func:`expression_engine._parser.parse`.
        variables: External variables as a read-only mapping from name to
            value. ``None`` means an empty mapping. A name that is absent
            evaluates to :data:`UNDEFINED`. The mapping is never mutated.

    Returns:
        The evaluated value: ``int``, ``float``, ``str``, ``bool``, ``None``,
        or :data:`UNDEFINED`.

    Raises:
        ExpressionTypeError: If an operator receives operands of unsupported
            types (for example a boolean, string, ``null``, or ``undefined``
            operand to arithmetic).
        DivisionByZeroError: If ``/`` is applied with a zero divisor.
        ExpressionEvaluationError: If the expression uses an operation outside
            Stage 4 (``not``, comparisons, ``and``/``or``, conditional), or if a
            numeric literal cannot be converted. The relevant AST anchor
            position is attached.
    """

    if variables is None:
        variables = {}
    return _eval(node, variables)


def _eval(node: Expr, variables: Mapping[str, object]) -> object:
    if isinstance(node, LiteralExpr):
        return _eval_literal(node)
    if isinstance(node, VariableExpr):
        return variables.get(node.name, UNDEFINED)
    if isinstance(node, UnaryExpr):
        return _eval_unary(node, variables)
    if isinstance(node, BinaryExpr):
        return _eval_binary(node, variables)
    if isinstance(node, ConditionalExpr):
        raise ExpressionEvaluationError(
            "conditional expressions are not supported in this version",
            node.position,
        )
    # Unreachable for the current AST, but guard against silently returning
    # None for an unexpected node type.
    raise ExpressionEvaluationError(
        "cannot evaluate unsupported expression node", node.position
    )


def _eval_literal(node: LiteralExpr) -> object:
    kind = node.kind
    if kind is TokenType.INTEGER:
        try:
            return int(node.value)
        except (ValueError, OverflowError) as error:
            raise ExpressionEvaluationError(
                f"invalid integer literal {node.value!r}", node.position
            ) from error
    if kind is TokenType.FLOAT:
        try:
            return float(node.value)
        except (ValueError, OverflowError) as error:
            raise ExpressionEvaluationError(
                f"invalid float literal {node.value!r}", node.position
            ) from error
    if kind is TokenType.STRING:
        return node.value
    if kind is TokenType.TRUE:
        return True
    if kind is TokenType.FALSE:
        return False
    if kind is TokenType.NULL:
        return None
    if kind is TokenType.UNDEFINED:
        return UNDEFINED
    # Unreachable: the parser only assigns the literal kinds handled above.
    raise ExpressionEvaluationError(
        "cannot evaluate unknown literal kind", node.position
    )


def _eval_unary(node: UnaryExpr, variables: Mapping[str, object]) -> object:
    if node.operator is TokenType.NOT:
        # `not` is outside Stage 4; do not evaluate the operand.
        raise ExpressionEvaluationError(
            "the 'not' operator is not supported in this version", node.position
        )

    operand = _eval(node.operand, variables)
    if not _is_number(operand):
        raise ExpressionTypeError(
            f"unary {_OPERATOR_SYMBOL[node.operator]!r} requires a number, "
            f"got {type(operand).__name__}",
            node.position,
        )
    if node.operator is TokenType.PLUS:
        return +operand
    return -operand


def _eval_binary(node: BinaryExpr, variables: Mapping[str, object]) -> object:
    operator = node.operator
    if operator not in _ARITHMETIC_OPERATORS:
        # Comparisons and boolean and/or are outside Stage 4; do not evaluate
        # the operands.
        raise ExpressionEvaluationError(
            f"the {_OPERATOR_SYMBOL[operator]!r} operator is not supported "
            f"in this version",
            node.position,
        )

    # Evaluate operands left-to-right, then validate types and compute.
    left = _eval(node.left, variables)
    right = _eval(node.right, variables)
    if not _is_number(left) or not _is_number(right):
        raise ExpressionTypeError(
            f"unsupported operand type(s) for {_OPERATOR_SYMBOL[operator]!r}: "
            f"{type(left).__name__} and {type(right).__name__}",
            node.position,
        )

    if operator is TokenType.PLUS:
        return left + right
    if operator is TokenType.MINUS:
        return left - right
    if operator is TokenType.STAR:
        return left * right
    # SLASH: true division, always returns a float.
    if right == 0:
        raise DivisionByZeroError("division by zero", node.position)
    return left / right
