"""Stage 11 tests: parsing and AST for function calls ``name(arg, ...)``.

These tests exercise the parser through ``tokenize -> parse`` and assert on the
immutable :class:`~expression_engine._ast.CallExpr` structure (or on the raised
``ParserError``). They cover only the new call syntax; no ``CallExpr`` is
evaluated (function evaluation is out of scope for this stage).
"""

from __future__ import annotations

import dataclasses

import pytest

from expression_engine.errors import ParserError
from expression_engine._ast import (
    BinaryExpr,
    CallExpr,
    ConditionalExpr,
    Expr,
    LetExpr,
    LiteralExpr,
    UnaryExpr,
    VariableExpr,
)
from expression_engine._parser import parse
from expression_engine._tokens import Position, TokenType
from expression_engine._tokenizer import tokenize


def parse_source(source: str) -> Expr:
    """Tokenize ``source`` and parse it into an expression AST."""
    return parse(tokenize(source))


# --------------------------------------------------------------------------- #
# Arity: zero, one, and multiple arguments
# --------------------------------------------------------------------------- #


def test_zero_argument_call() -> None:
    node = parse_source("f()")
    assert node == CallExpr("f", (), Position(0, 1, 1))


def test_single_argument_call() -> None:
    node = parse_source("f(1)")
    assert node == CallExpr(
        "f", (LiteralExpr(TokenType.INTEGER, "1", Position(2, 1, 3)),), Position(0, 1, 1)
    )


def test_multiple_argument_call() -> None:
    node = parse_source("f(1, 2 + 3)")
    assert isinstance(node, CallExpr)
    assert node.name == "f"
    assert len(node.arguments) == 2
    assert node.arguments[0] == LiteralExpr(TokenType.INTEGER, "1", Position(2, 1, 3))
    assert isinstance(node.arguments[1], BinaryExpr)
    assert node.arguments[1].operator is TokenType.PLUS


# --------------------------------------------------------------------------- #
# Nested calls and expression arguments
# --------------------------------------------------------------------------- #


def test_nested_calls() -> None:
    node = parse_source("f(g(1), h(2))")
    assert isinstance(node, CallExpr)
    assert node.name == "f"
    assert isinstance(node.arguments[0], CallExpr)
    assert node.arguments[0].name == "g"
    assert isinstance(node.arguments[1], CallExpr)
    assert node.arguments[1].name == "h"


def test_arithmetic_argument() -> None:
    node = parse_source("f(a * 2)")
    assert isinstance(node, CallExpr)
    assert isinstance(node.arguments[0], BinaryExpr)
    assert node.arguments[0].operator is TokenType.STAR


def test_comparison_argument() -> None:
    node = parse_source("f(a == b)")
    assert isinstance(node, CallExpr)
    assert isinstance(node.arguments[0], BinaryExpr)
    assert node.arguments[0].operator is TokenType.EQ


def test_boolean_argument() -> None:
    node = parse_source("f(a and b)")
    assert isinstance(node, CallExpr)
    assert isinstance(node.arguments[0], BinaryExpr)
    assert node.arguments[0].operator is TokenType.AND


def test_conditional_argument() -> None:
    node = parse_source("f(a if b else c)")
    assert isinstance(node, CallExpr)
    assert isinstance(node.arguments[0], ConditionalExpr)


def test_bare_let_argument() -> None:
    node = parse_source("f(let x = 1 in x, 2)")
    assert isinstance(node, CallExpr)
    assert len(node.arguments) == 2
    assert isinstance(node.arguments[0], LetExpr)
    assert node.arguments[1] == LiteralExpr(TokenType.INTEGER, "2", Position(18, 1, 19))


# --------------------------------------------------------------------------- #
# A bare identifier remains a VariableExpr
# --------------------------------------------------------------------------- #


def test_bare_identifier_is_variable() -> None:
    node = parse_source("f")
    assert node == VariableExpr("f", Position(0, 1, 1))


def test_identifier_followed_by_operator_is_variable() -> None:
    node = parse_source("f + 1")
    assert isinstance(node, BinaryExpr)
    assert node.left == VariableExpr("f", Position(0, 1, 1))


# --------------------------------------------------------------------------- #
# Source-position anchor (at the identifier)
# --------------------------------------------------------------------------- #


def test_position_anchored_at_identifier_zero_offset() -> None:
    node = parse_source("f(1)")
    assert isinstance(node, CallExpr)
    assert node.position == Position(0, 1, 1)


def test_position_anchored_at_identifier_nonzero_offset() -> None:
    node = parse_source("  f(1)")
    assert isinstance(node, CallExpr)
    assert node.position == Position(2, 1, 3)


# --------------------------------------------------------------------------- #
# Immutability and tuple arguments
# --------------------------------------------------------------------------- #


def test_call_node_is_frozen() -> None:
    node = parse_source("f(1)")
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.name = "g"  # type: ignore[misc]


def test_call_node_has_no_dict_due_to_slots() -> None:
    node = parse_source("f(1)")
    assert not hasattr(node, "__dict__")


def test_arguments_is_a_tuple() -> None:
    node = parse_source("f(1, 2)")
    assert isinstance(node, CallExpr)
    assert type(node.arguments) is tuple


# --------------------------------------------------------------------------- #
# Precedence: a call binds tighter than every operator level
# --------------------------------------------------------------------------- #


def test_call_binds_tighter_than_unary() -> None:
    node = parse_source("-f(2)")
    assert isinstance(node, UnaryExpr)
    assert node.operator is TokenType.MINUS
    assert isinstance(node.operand, CallExpr)


def test_call_in_arithmetic() -> None:
    node = parse_source("f(2) + 1")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.left, CallExpr)


def test_call_in_comparison() -> None:
    node = parse_source("f(2) == 4")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.EQ
    assert isinstance(node.left, CallExpr)


def test_call_in_boolean() -> None:
    node = parse_source("f(a) and g(b)")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.AND
    assert isinstance(node.left, CallExpr)
    assert isinstance(node.right, CallExpr)


def test_call_in_conditional() -> None:
    node = parse_source("f(1) if c else g(2)")
    assert isinstance(node, ConditionalExpr)
    assert isinstance(node.if_true, CallExpr)
    assert isinstance(node.if_false, CallExpr)


def test_call_in_let_value() -> None:
    node = parse_source("let x = f(1) in x")
    assert isinstance(node, LetExpr)
    assert isinstance(node.value, CallExpr)


# --------------------------------------------------------------------------- #
# Rejected: chained calls and arbitrary (non-identifier) callees
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        "f(1)(2)",  # chained call
        "(f)(1)",  # parenthesized expression is not callable
        "1(2)",  # literal is not callable
    ],
)
def test_chained_and_arbitrary_calls_are_rejected(source: str) -> None:
    with pytest.raises(ParserError):
        parse_source(source)


# --------------------------------------------------------------------------- #
# Malformed commas and parentheses, with anchored error positions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("source", "position"),
    [
        ("f(", Position(2, 1, 3)),  # reached end of input
        ("f(,1)", Position(2, 1, 3)),  # leading comma
        ("f(1,)", Position(4, 1, 5)),  # trailing comma
        ("f(1 2)", Position(4, 1, 5)),  # missing comma
        ("f(1,,2)", Position(4, 1, 5)),  # double comma
        ("f)", Position(1, 1, 2)),  # stray close paren after a variable
    ],
)
def test_malformed_calls_raise_parser_error(source: str, position: Position) -> None:
    with pytest.raises(ParserError) as exc_info:
        parse_source(source)
    assert exc_info.value.position == position
