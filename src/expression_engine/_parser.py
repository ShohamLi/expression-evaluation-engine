"""Stage 3: the recursive-descent parser for the expression engine.

This module turns the flat token sequence produced by
:func:`expression_engine._tokenizer.tokenize` into the immutable AST defined in
:mod:`expression_engine._ast`. It performs *only* syntactic analysis: it builds
nodes, it does not evaluate, validate names, resolve functions, or convert
literals to Python runtime values.

The intended interface is the module-level :func:`parse` function. It consumes
the token sequence (which must end with the tokenizer's ``EOF`` token) and
returns a single :class:`~._ast.Expr`. Syntax problems are reported by raising
:class:`~expression_engine.errors.ParserError` with the offending source
position attached.

Grammar and precedence (lowest binding first; one method per level):

    conditional    := or_expr ( "if" or_expr "else" conditional )?   right-assoc
    or_expr        := and_expr ( "or" and_expr )*                    left-assoc
    and_expr       := comparison ( "and" comparison )*               left-assoc
    comparison     := additive ( COMPARE additive )?                 non-chaining
    additive       := multiplicative ( ("+"|"-") multiplicative )*   left-assoc
    multiplicative := unary ( ("*"|"/") unary )*                     left-assoc
    unary          := ("not"|"+"|"-") unary | primary                repeatable
    primary        := literal | identifier | "(" conditional ")"

Left-associative levels are written as iterative loops; recursion is used only
where it is the natural shape of the grammar: nested parentheses, repeated
unary operators, and the right-associative conditional. Comparisons do not
chain: ``a < b < c`` is rejected. Parentheses only group; they produce no node.
"""

from __future__ import annotations

from collections.abc import Sequence

from .errors import ParserError
from ._ast import (
    BinaryExpr,
    ConditionalExpr,
    Expr,
    LiteralExpr,
    UnaryExpr,
    VariableExpr,
)
from ._tokens import Position, Token, TokenType

__all__ = ["parse"]


_LITERAL_TYPES: frozenset[TokenType] = frozenset(
    {
        TokenType.INTEGER,
        TokenType.FLOAT,
        TokenType.STRING,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.NULL,
        TokenType.UNDEFINED,
    }
)

_UNARY_TYPES: frozenset[TokenType] = frozenset(
    {TokenType.NOT, TokenType.PLUS, TokenType.MINUS}
)

_MULTIPLICATIVE_TYPES: frozenset[TokenType] = frozenset(
    {TokenType.STAR, TokenType.SLASH}
)

_ADDITIVE_TYPES: frozenset[TokenType] = frozenset(
    {TokenType.PLUS, TokenType.MINUS}
)

_COMPARISON_TYPES: frozenset[TokenType] = frozenset(
    {
        TokenType.EQ,
        TokenType.NE,
        TokenType.LT,
        TokenType.LE,
        TokenType.GT,
        TokenType.GE,
    }
)


class _Parser:
    """Single-use recursive-descent parser over one token sequence.

    The instance holds the token sequence and the read cursor (``_index``).
    Create one per call to :func:`parse`; all mutable state is local to the
    instance, so there is no global state and nothing is retained between calls.
    """

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens = tokens
        self._index = 0

    def parse(self) -> Expr:
        """Parse exactly one complete expression, then require ``EOF``."""
        expression = self._conditional()
        trailing = self._current()
        if trailing.type is not TokenType.EOF:
            raise ParserError(
                f"unexpected trailing {self._describe(trailing)} "
                f"after a complete expression",
                trailing.position,
            )
        return expression

    def _conditional(self) -> Expr:
        # value_if_true if condition else value_if_false
        # The else-branch recurses, making the conditional right-associative.
        if_true = self._or()
        if self._current().type is TokenType.IF:
            if_token = self._advance()
            condition = self._or()
            self._expect(TokenType.ELSE, "'else'")
            if_false = self._conditional()
            return ConditionalExpr(
                condition, if_true, if_false, if_token.position
            )
        return if_true

    def _or(self) -> Expr:
        expression = self._and()
        while self._current().type is TokenType.OR:
            operator = self._advance()
            right = self._and()
            expression = BinaryExpr(
                operator.type, expression, right, operator.position
            )
        return expression

    def _and(self) -> Expr:
        expression = self._comparison()
        while self._current().type is TokenType.AND:
            operator = self._advance()
            right = self._comparison()
            expression = BinaryExpr(
                operator.type, expression, right, operator.position
            )
        return expression

    def _comparison(self) -> Expr:
        expression = self._additive()
        if self._current().type in _COMPARISON_TYPES:
            operator = self._advance()
            right = self._additive()
            expression = BinaryExpr(
                operator.type, expression, right, operator.position
            )
            # Comparisons do not chain: a second comparison operator here is an
            # error rather than a silently associated operation.
            following = self._current()
            if following.type in _COMPARISON_TYPES:
                raise ParserError(
                    "chained comparison is not supported; parenthesize to "
                    "compare results explicitly",
                    following.position,
                )
        return expression

    def _additive(self) -> Expr:
        expression = self._multiplicative()
        while self._current().type in _ADDITIVE_TYPES:
            operator = self._advance()
            right = self._multiplicative()
            expression = BinaryExpr(
                operator.type, expression, right, operator.position
            )
        return expression

    def _multiplicative(self) -> Expr:
        expression = self._unary()
        while self._current().type in _MULTIPLICATIVE_TYPES:
            operator = self._advance()
            right = self._unary()
            expression = BinaryExpr(
                operator.type, expression, right, operator.position
            )
        return expression

    def _unary(self) -> Expr:
        token = self._current()
        if token.type in _UNARY_TYPES:
            self._advance()
            operand = self._unary()
            return UnaryExpr(token.type, operand, token.position)
        return self._primary()

    def _primary(self) -> Expr:
        token = self._current()
        if token.type in _LITERAL_TYPES:
            self._advance()
            return LiteralExpr(token.type, token.value, token.position)
        if token.type is TokenType.IDENTIFIER:
            self._advance()
            return VariableExpr(token.value, token.position)
        if token.type is TokenType.LPAREN:
            self._advance()
            grouped = self._conditional()
            self._expect(TokenType.RPAREN, "')'")
            return grouped
        raise self._unexpected(token, "an expression")

    def _current(self) -> Token:
        return self._tokens[self._index]

    def _advance(self) -> Token:
        token = self._tokens[self._index]
        if token.type is not TokenType.EOF:
            self._index += 1
        return token

    def _expect(self, expected: TokenType, description: str) -> Token:
        token = self._current()
        if token.type is not expected:
            raise self._unexpected(token, description)
        return self._advance()

    def _unexpected(self, token: Token, expected: str) -> ParserError:
        if token.type is TokenType.EOF:
            message = f"expected {expected} but reached end of input"
        else:
            message = f"expected {expected} but found {self._describe(token)}"
        return ParserError(message, token.position)

    def _describe(self, token: Token) -> str:
        if token.type is TokenType.EOF:
            return "end of input"
        return repr(token.value)


def parse(tokens: Sequence[Token]) -> Expr:
    """Parse a token sequence into a single expression AST.

    Args:
        tokens: The tokens to parse, as returned by
            :func:`expression_engine._tokenizer.tokenize`. The sequence must be
            non-empty and end with an :attr:`~._tokens.TokenType.EOF` token.

    Returns:
        The root :class:`~._ast.Expr` of the parsed expression.

    Raises:
        ParserError: If the tokens do not form exactly one complete expression,
            if tokens remain after a complete expression, or if the sequence is
            empty or not terminated by an ``EOF`` token. The error carries the
            relevant :class:`~._tokens.Position`.
    """

    if not tokens or tokens[-1].type is not TokenType.EOF:
        position = tokens[-1].position if tokens else Position(0, 1, 1)
        raise ParserError(
            "parser requires a non-empty token sequence terminated by EOF",
            position,
        )
    return _Parser(tokens).parse()
