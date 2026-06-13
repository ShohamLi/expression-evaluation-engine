"""Parser and AST tests for ``let name = value in body``.

These tests exercise the parser through ``tokenize -> parse`` and assert on the
immutable :class:`~expression_engine._ast.LetExpr` structure (or on the raised
``ParserError``). They cover local-binding syntax; broad parser coverage and
evaluation are tested separately.
"""

from __future__ import annotations

import dataclasses

import pytest

from expression_engine.errors import ParserError
from expression_engine._ast import (
    BinaryExpr,
    ConditionalExpr,
    Expr,
    LetExpr,
    LiteralExpr,
    VariableExpr,
)
from expression_engine._parser import parse
from expression_engine._tokens import Position, TokenType
from expression_engine._tokenizer import tokenize


def parse_source(source: str) -> Expr:
    return parse(tokenize(source))


# --------------------------------------------------------------------------- #
# Basic binding and exact fields
# --------------------------------------------------------------------------- #


def test_basic_binding() -> None:
    node = parse_source("let x = 1 in x")
    assert node == LetExpr(
        "x",
        LiteralExpr(TokenType.INTEGER, "1", Position(8, 1, 9)),
        VariableExpr("x", Position(13, 1, 14)),
        Position(0, 1, 1),
    )


def test_let_fields() -> None:
    node = parse_source("let total = 1 in total")
    assert isinstance(node, LetExpr)
    assert node.name == "total"
    assert node.value == LiteralExpr(TokenType.INTEGER, "1", Position(12, 1, 13))
    assert node.body == VariableExpr("total", Position(17, 1, 18))


# --------------------------------------------------------------------------- #
# Arithmetic, nesting, and conditionals in value/body
# --------------------------------------------------------------------------- #


def test_arithmetic_in_value_and_body() -> None:
    node = parse_source("let x = 1 + 2 in x * 3")
    assert isinstance(node, LetExpr)
    assert isinstance(node.value, BinaryExpr)
    assert node.value.operator is TokenType.PLUS
    assert isinstance(node.body, BinaryExpr)
    assert node.body.operator is TokenType.STAR


def test_nested_binding_in_body() -> None:
    # let x = 1 in let y = x + 1 in y
    node = parse_source("let x = 1 in let y = x + 1 in y")
    assert isinstance(node, LetExpr)
    assert node.name == "x"
    assert isinstance(node.body, LetExpr)
    assert node.body.name == "y"
    assert node.body.body == VariableExpr("y", Position(30, 1, 31))


def test_nested_binding_in_value() -> None:
    # let x = let y = 1 in y in x  ==  let x = (let y = 1 in y) in x
    node = parse_source("let x = let y = 1 in y in x")
    assert isinstance(node, LetExpr)
    assert node.name == "x"
    assert isinstance(node.value, LetExpr)
    assert node.value.name == "y"
    assert node.body == VariableExpr("x", Position(26, 1, 27))


def test_conditional_in_value() -> None:
    node = parse_source("let x = a if b else c in x")
    assert isinstance(node, LetExpr)
    assert isinstance(node.value, ConditionalExpr)


def test_conditional_in_body() -> None:
    node = parse_source("let x = 1 in a if x else b")
    assert isinstance(node, LetExpr)
    assert isinstance(node.body, ConditionalExpr)


# --------------------------------------------------------------------------- #
# Precedence: let is lowest, only valid where an expression begins
# --------------------------------------------------------------------------- #


def test_parenthesized_let_in_arithmetic() -> None:
    node = parse_source("(let x = 1 in x) + 2")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.left, LetExpr)
    assert node.right == LiteralExpr(TokenType.INTEGER, "2", Position(19, 1, 20))


def test_bare_let_as_operand_is_rejected() -> None:
    with pytest.raises(ParserError):
        parse_source("1 + let x = 2 in x")


# --------------------------------------------------------------------------- #
# Source position and immutability
# --------------------------------------------------------------------------- #


def test_position_anchored_at_let_token() -> None:
    node = parse_source("  let x = 1 in x")
    assert isinstance(node, LetExpr)
    assert node.position == Position(2, 1, 3)  # the `let` keyword


def test_let_node_is_frozen() -> None:
    node = parse_source("let x = 1 in x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.name = "y"  # type: ignore[misc]


def test_let_node_has_no_dict_due_to_slots() -> None:
    node = parse_source("let x = 1 in x")
    assert not hasattr(node, "__dict__")


# --------------------------------------------------------------------------- #
# Malformed syntax
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        "let = 1 in x",  # missing identifier
        "let if = 1 in x",  # keyword instead of identifier
        "let true = 1 in x",  # keyword literal instead of identifier
        "let x 1 in x",  # missing '='
        "let x = in x",  # missing value
        "let x = 1 x",  # missing 'in'
        "let x = 1 in",  # missing body
    ],
)
def test_malformed_let_raises_parser_error(source: str) -> None:
    with pytest.raises(ParserError):
        parse_source(source)


# --------------------------------------------------------------------------- #
# Existing non-let parsing is unchanged
# --------------------------------------------------------------------------- #


def test_existing_arithmetic_precedence_is_unchanged() -> None:
    node = parse_source("1 + 2 * 3")

    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.right, BinaryExpr)
    assert node.right.operator is TokenType.STAR


def test_non_let_parsing_unchanged() -> None:
    assert isinstance(parse_source("a if b else c"), ConditionalExpr)
    node = parse_source("(1 + 2) * 3")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.STAR
