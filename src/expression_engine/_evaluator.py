"""Stages 4-6: the expression evaluator (arithmetic, variables, comparisons,
Boolean operators).

This module walks an immutable AST from :mod:`expression_engine._ast` and
produces a runtime Python value. It currently implements:

* literals (integer, float, string, boolean, ``null``, ``undefined``);
* external variable lookup;
* unary numeric ``+`` and ``-``;
* binary numeric ``+``, ``-``, ``*``, and ``/`` (true division);
* comparisons ``==``, ``!=``, ``<``, ``<=``, ``>``, ``>=`` (Stage 5);
* strict Boolean ``not``, ``and``, and ``or`` with real short-circuit
  evaluation (Stage 6).

Conditional expressions are the only remaining parser output that is
intentionally outside this stage; they raise a clear
:class:`~expression_engine.errors.ExpressionEvaluationError` without evaluating
their operands.

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

_COMPARISON_OPERATORS: frozenset[TokenType] = frozenset(
    {
        TokenType.EQ,
        TokenType.NE,
        TokenType.LT,
        TokenType.LE,
        TokenType.GT,
        TokenType.GE,
    }
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
        ExpressionEvaluationError: If the expression uses an operation that is
            still unsupported (a conditional expression), or if a numeric
            literal cannot be converted. The relevant AST anchor position is
            attached.
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
    operand = _eval(node.operand, variables)

    if node.operator is TokenType.NOT:
        # Strict Boolean: only an exact bool is accepted, no truthiness.
        if type(operand) is not bool:
            raise ExpressionTypeError(
                f"'not' requires a bool, got {type(operand).__name__}",
                node.position,
            )
        return not operand

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
    if operator is TokenType.AND or operator is TokenType.OR:
        # Strict Boolean operators with real short-circuit evaluation. The left
        # operand is evaluated once and must be an exact bool; the right operand
        # is evaluated (and validated) only when the result is not yet decided.
        left = _eval(node.left, variables)
        if type(left) is not bool:
            raise ExpressionTypeError(
                f"{_OPERATOR_SYMBOL[operator]!r} requires a bool, "
                f"got {type(left).__name__}",
                node.position,
            )
        if operator is TokenType.AND and not left:
            return False
        if operator is TokenType.OR and left:
            return True
        right = _eval(node.right, variables)
        if type(right) is not bool:
            raise ExpressionTypeError(
                f"{_OPERATOR_SYMBOL[operator]!r} requires a bool, "
                f"got {type(right).__name__}",
                node.position,
            )
        return right

    if operator in _COMPARISON_OPERATORS:
        return _eval_comparison(node, variables)
    if operator not in _ARITHMETIC_OPERATORS:
        # Defensive: the parser only produces the operators handled above.
        raise ExpressionEvaluationError(
            f"cannot evaluate operator {_OPERATOR_SYMBOL[operator]!r}",
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


def _eval_comparison(node: BinaryExpr, variables: Mapping[str, object]) -> bool:
    operator = node.operator
    # Evaluate operands left-to-right, exactly once each.
    left = _eval(node.left, variables)
    right = _eval(node.right, variables)

    # Only the engine's own value types take part in comparison. Rejecting
    # caller objects and built-in subclasses here guarantees their overloaded
    # comparison methods are never invoked.
    left_supported = (
        type(left) in (int, float, str, bool) or left is None or left is UNDEFINED
    )
    right_supported = (
        type(right) in (int, float, str, bool) or right is None or right is UNDEFINED
    )
    if not left_supported or not right_supported:
        raise ExpressionTypeError(
            f"unsupported operand type(s) for {_OPERATOR_SYMBOL[operator]!r}: "
            f"{type(left).__name__} and {type(right).__name__}",
            node.position,
        )

    if operator is TokenType.EQ or operator is TokenType.NE:
        # Equality is type-aware and never coerces across categories: numbers
        # (int/float) compare by value; bool, str, null, and undefined each
        # compare only within their own category; any cross-category pair
        # (for example a number and a bool, or null and undefined) is unequal.
        if _is_number(left) and _is_number(right):
            equal = left == right
        elif type(left) is str and type(right) is str:
            equal = left == right
        elif type(left) is bool and type(right) is bool:
            equal = left is right
        elif left is None and right is None:
            equal = True
        elif left is UNDEFINED and right is UNDEFINED:
            equal = True
        else:
            equal = False
        return equal if operator is TokenType.EQ else not equal

    # Ordered comparisons (< <= > >=) accept only two numbers. Ordered string
    # comparison is deferred to a later stage; strings support == and != only.
    if not (_is_number(left) and _is_number(right)):
        raise ExpressionTypeError(
            f"unsupported operand type(s) for {_OPERATOR_SYMBOL[operator]!r}: "
            f"{type(left).__name__} and {type(right).__name__}",
            node.position,
        )

    if operator is TokenType.LT:
        return left < right
    if operator is TokenType.LE:
        return left <= right
    if operator is TokenType.GT:
        return left > right
    return left >= right
