"""Local-function definition syntax and immutable AST tests."""

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
    LocalFunctionExpr,
    VariableExpr,
)
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize
from expression_engine._tokens import Position, TokenType


def parse_source(source: str) -> Expr:
    return parse(tokenize(source))


def test_zero_parameters_and_exact_ast_fields() -> None:
    node = parse_source("let constant() = 5 in constant()")

    assert node == LocalFunctionExpr(
        "constant",
        (),
        LiteralExpr(TokenType.INTEGER, "5", Position(17, 1, 18)),
        CallExpr("constant", (), Position(22, 1, 23)),
        Position(0, 1, 1),
    )


def test_one_parameter_and_exact_ast_fields() -> None:
    node = parse_source("let double(x) = x * 2 in double(4)")

    assert node == LocalFunctionExpr(
        "double",
        ("x",),
        BinaryExpr(
            TokenType.STAR,
            VariableExpr("x", Position(16, 1, 17)),
            LiteralExpr(TokenType.INTEGER, "2", Position(20, 1, 21)),
            Position(18, 1, 19),
        ),
        CallExpr(
            "double",
            (LiteralExpr(TokenType.INTEGER, "4", Position(32, 1, 33)),),
            Position(25, 1, 26),
        ),
        Position(0, 1, 1),
    )


def test_multiple_parameters_preserve_source_order_in_tuple() -> None:
    node = parse_source("let add(a, b) = a + b in add(1, 2)")

    assert isinstance(node, LocalFunctionExpr)
    assert node.name == "add"
    assert node.parameters == ("a", "b")
    assert type(node.parameters) is tuple
    assert isinstance(node.function_body, BinaryExpr)
    assert node.function_body.operator is TokenType.PLUS
    assert isinstance(node.body, CallExpr)
    assert len(node.body.arguments) == 2


def test_arithmetic_and_calls_in_function_body() -> None:
    node = parse_source("let adjusted(x) = abs(x) + 1 in adjusted(2)")

    assert isinstance(node, LocalFunctionExpr)
    assert isinstance(node.function_body, BinaryExpr)
    assert node.function_body.operator is TokenType.PLUS
    assert isinstance(node.function_body.left, CallExpr)
    assert node.function_body.left.name == "abs"


def test_conditional_and_local_binding_in_function_body() -> None:
    node = parse_source(
        "let choose(x) = let y = x in y if true else 0 in choose(1)"
    )

    assert isinstance(node, LocalFunctionExpr)
    assert isinstance(node.function_body, LetExpr)
    assert isinstance(node.function_body.body, ConditionalExpr)


def test_outer_body_accepts_a_full_expression() -> None:
    node = parse_source("let id(x) = x in id(1) + 2 if true else 0")

    assert isinstance(node, LocalFunctionExpr)
    assert isinstance(node.body, ConditionalExpr)
    assert isinstance(node.body.if_true, BinaryExpr)
    assert isinstance(node.body.if_true.left, CallExpr)


def test_nested_local_function_definitions() -> None:
    node = parse_source(
        "let outer(x) = x in let inner(y) = y in outer(inner(1))"
    )

    assert isinstance(node, LocalFunctionExpr)
    assert node.name == "outer"
    assert isinstance(node.body, LocalFunctionExpr)
    assert node.body.name == "inner"
    assert isinstance(node.body.body, CallExpr)
    assert isinstance(node.body.body.arguments[0], CallExpr)


def test_duplicate_parameter_names_are_preserved_syntactically() -> None:
    node = parse_source("let f(x, x) = x in f(1, 2)")

    assert isinstance(node, LocalFunctionExpr)
    assert node.parameters == ("x", "x")


def test_existing_variable_let_syntax_is_unchanged() -> None:
    assert parse_source("let x = 1 in x") == LetExpr(
        "x",
        LiteralExpr(TokenType.INTEGER, "1", Position(8, 1, 9)),
        VariableExpr("x", Position(13, 1, 14)),
        Position(0, 1, 1),
    )


def test_existing_call_parsing_is_unchanged() -> None:
    assert parse_source("f(1, 2)") == CallExpr(
        "f",
        (
            LiteralExpr(TokenType.INTEGER, "1", Position(2, 1, 3)),
            LiteralExpr(TokenType.INTEGER, "2", Position(5, 1, 6)),
        ),
        Position(0, 1, 1),
    )


def test_local_function_definition_inside_parentheses() -> None:
    node = parse_source("(let double(x) = x * 2 in double(3)) + 1")

    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.left, LocalFunctionExpr)


def test_operator_precedence_in_function_body_is_unchanged() -> None:
    node = parse_source("let f(x) = x + 2 * 3 in f(1)")

    assert isinstance(node, LocalFunctionExpr)
    assert isinstance(node.function_body, BinaryExpr)
    assert node.function_body.operator is TokenType.PLUS
    assert isinstance(node.function_body.right, BinaryExpr)
    assert node.function_body.right.operator is TokenType.STAR


def test_bare_local_function_definition_as_operand_is_rejected() -> None:
    with pytest.raises(ParserError):
        parse_source("1 + let f(x) = x in f(1)")


def test_position_is_anchored_at_let_keyword() -> None:
    node = parse_source("  let f() = 1 in f()")

    assert isinstance(node, LocalFunctionExpr)
    assert node.position == Position(2, 1, 3)


def test_local_function_node_is_frozen() -> None:
    node = parse_source("let f(x) = x in f(1)")

    with pytest.raises(dataclasses.FrozenInstanceError):
        node.name = "g"  # type: ignore[misc]


def test_local_function_node_has_no_dict_due_to_slots() -> None:
    node = parse_source("let f(x) = x in f(1)")
    assert not hasattr(node, "__dict__")


def test_parameters_are_an_immutable_tuple() -> None:
    node = parse_source("let f(a, b) = a in f(1, 2)")

    assert isinstance(node, LocalFunctionExpr)
    assert type(node.parameters) is tuple
    with pytest.raises(TypeError):
        node.parameters[0] = "x"  # type: ignore[index]


@pytest.mark.parametrize(
    ("source", "position"),
    [
        ("let () = 1 in 1", Position(4, 1, 5)),
        ("let if(x) = x in x", Position(4, 1, 5)),
        ("let f(x = x in x", Position(8, 1, 9)),
        ("let f(x) x in x", Position(9, 1, 10)),
        ("let f(x) = in x", Position(11, 1, 12)),
        ("let f(x) = x x", Position(13, 1, 14)),
        ("let f(x) = x in", Position(15, 1, 16)),
        ("let f(,x) = x in x", Position(6, 1, 7)),
        ("let f(x,) = x in x", Position(8, 1, 9)),
        ("let f(x,,y) = x in x", Position(8, 1, 9)),
        ("let f(x y) = x in x", Position(8, 1, 9)),
        ("let f(if) = 1 in 1", Position(6, 1, 7)),
    ],
)
def test_malformed_local_function_syntax(
    source: str, position: Position
) -> None:
    with pytest.raises(ParserError) as exc_info:
        parse_source(source)
    assert exc_info.value.position == position
