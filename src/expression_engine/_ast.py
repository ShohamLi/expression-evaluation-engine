"""Stage 3: the immutable abstract syntax tree (AST) for the expression engine.

This module defines *data only*: the immutable node types produced by the
parser in :mod:`expression_engine._parser`. The AST is a pure syntactic
representation of one expression. It carries no evaluation state, performs no
computation, and does not convert literals to Python runtime values; that work
belongs to a later (evaluation) stage.

Design notes (consistent with ``docs/decisions.md``):

* Every node is a frozen dataclass with ``slots=True`` and therefore immutable
  after construction. Frozen dataclasses also provide structural ``__eq__``,
  which makes the parser's output easy to assert against in tests.
* Nodes reuse the existing lexical types from
  :mod:`expression_engine._tokens` rather than duplicating them: operator and
  literal *kinds* are recorded as :class:`~._tokens.TokenType` members, and
  source locations are :class:`~._tokens.Position` values.
* Each node stores a single **anchor** :class:`~._tokens.Position` (see the
  field docs below). An anchor marks one representative location for the node;
  it is **not** a full start/end source span and cannot reconstruct one.
* Parentheses only affect grouping; they do not produce a node, and redundant
  parentheses are not preserved.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._tokens import Position, TokenType

__all__ = [
    "LiteralExpr",
    "VariableExpr",
    "UnaryExpr",
    "BinaryExpr",
    "ConditionalExpr",
    "LetExpr",
    "CallExpr",
    "Expr",
]


@dataclass(frozen=True, slots=True)
class LiteralExpr:
    """A literal value: an integer, float, string, boolean, ``null``, or
    ``undefined``.

    Attributes:
        kind: The literal's lexical category, one of
            :attr:`~._tokens.TokenType.INTEGER`,
            :attr:`~._tokens.TokenType.FLOAT`,
            :attr:`~._tokens.TokenType.STRING`,
            :attr:`~._tokens.TokenType.TRUE`,
            :attr:`~._tokens.TokenType.FALSE`,
            :attr:`~._tokens.TokenType.NULL`, or
            :attr:`~._tokens.TokenType.UNDEFINED`.
        value: The tokenizer-provided ``Token.value``, copied verbatim: the
            source text for numbers, the *decoded* text for strings, and the
            keyword spelling for ``true``/``false``/``null``/``undefined``. No
            conversion to a Python ``int``/``float``/``bool``/``None``/
            ``UNDEFINED`` happens at this stage.
        position: Anchor position of the literal token's first character.
    """

    kind: TokenType
    value: str
    position: Position


@dataclass(frozen=True, slots=True)
class VariableExpr:
    """A reference to a named external variable.

    Attributes:
        name: The identifier text.
        position: Anchor position of the identifier's first character.
    """

    name: str
    position: Position


@dataclass(frozen=True, slots=True)
class UnaryExpr:
    """A unary operation: ``not``, unary ``+``, or unary ``-``.

    Attributes:
        operator: The operator token type, one of
            :attr:`~._tokens.TokenType.NOT`,
            :attr:`~._tokens.TokenType.PLUS`, or
            :attr:`~._tokens.TokenType.MINUS`.
        operand: The expression the operator applies to.
        position: Anchor position of the operator token.
    """

    operator: TokenType
    operand: "Expr"
    position: Position


@dataclass(frozen=True, slots=True)
class BinaryExpr:
    """A binary operation: arithmetic, comparison, or boolean ``and``/``or``.

    Attributes:
        operator: The operator token type (for example
            :attr:`~._tokens.TokenType.PLUS` or
            :attr:`~._tokens.TokenType.AND`).
        left: The left-hand operand.
        right: The right-hand operand.
        position: Anchor position of the operator token.
    """

    operator: TokenType
    left: "Expr"
    right: "Expr"
    position: Position


@dataclass(frozen=True, slots=True)
class ConditionalExpr:
    """A Python-style conditional ``value_if_true if condition else value_if_false``.

    Attributes:
        condition: The expression tested for truthiness.
        if_true: The value when ``condition`` is true.
        if_false: The value when ``condition`` is false.
        position: Anchor position of the ``if`` keyword token.
    """

    condition: "Expr"
    if_true: "Expr"
    if_false: "Expr"
    position: Position


@dataclass(frozen=True, slots=True)
class LetExpr:
    """A local binding ``let name = value in body``.

    Attributes:
        name: The bound identifier.
        value: The expression whose result is bound to ``name``.
        body: The expression evaluated with the binding in scope.
        position: Anchor position of the ``let`` keyword.
    """

    name: str
    value: "Expr"
    body: "Expr"
    position: Position


@dataclass(frozen=True, slots=True)
class CallExpr:
    """A function call ``name(arg0, arg1, ...)``.

    Only an identifier may be called (no arbitrary callable expressions and no
    chaining); the callee is therefore stored as its identifier text rather than
    as a nested node.

    Attributes:
        name: The called function's identifier.
        arguments: The argument expressions in source order, as an immutable
            tuple (empty for a zero-argument call ``name()``).
        position: Anchor position of the function identifier's first character.
    """

    name: str
    arguments: tuple["Expr", ...]
    position: Position


Expr = (
    LiteralExpr
    | VariableExpr
    | UnaryExpr
    | BinaryExpr
    | ConditionalExpr
    | LetExpr
    | CallExpr
)
"""Any expression node. The parser returns one ``Expr`` per parse."""
