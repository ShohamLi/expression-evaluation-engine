"""Stage 3 tests: the recursive-descent parser.

These tests exercise the parser through its intended interface
(``expression_engine._parser.parse`` consuming ``expression_engine._tokenizer.
tokenize`` output) and assert on the immutable AST from
``expression_engine._ast`` or on the raised ``ParserError``. They cover AST
shape, precedence, associativity, nesting, complete-input consumption, syntax
failures, error positions, and parser state isolation. No evaluation behavior
is assumed.
"""

from __future__ import annotations

import dataclasses

import pytest

from expression_engine import ExpressionSyntaxError
from expression_engine.errors import LexerError, ParserError
from expression_engine._ast import (
    BinaryExpr,
    ConditionalExpr,
    Expr,
    LiteralExpr,
    UnaryExpr,
    VariableExpr,
)
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize
from expression_engine._tokens import Position, Token, TokenType


def parse_source(source: str) -> Expr:
    """Tokenize ``source`` and parse it into an expression AST."""
    return parse(tokenize(source))


# --------------------------------------------------------------------------- #
# Literals and identifiers
# --------------------------------------------------------------------------- #


def test_integer_literal() -> None:
    node = parse_source("42")
    assert node == LiteralExpr(TokenType.INTEGER, "42", Position(0, 1, 1))


def test_float_literal() -> None:
    node = parse_source("3.14")
    assert isinstance(node, LiteralExpr)
    assert node.kind is TokenType.FLOAT
    assert node.value == "3.14"


def test_string_literal_keeps_decoded_value() -> None:
    node = parse_source(r'"a\nb"')
    assert isinstance(node, LiteralExpr)
    assert node.kind is TokenType.STRING
    assert node.value == "a\nb"


def test_true_literal() -> None:
    assert parse_source("true") == LiteralExpr(TokenType.TRUE, "true", Position(0, 1, 1))


def test_false_literal() -> None:
    assert parse_source("false") == LiteralExpr(
        TokenType.FALSE, "false", Position(0, 1, 1)
    )


def test_null_literal() -> None:
    assert parse_source("null") == LiteralExpr(TokenType.NULL, "null", Position(0, 1, 1))


def test_undefined_literal() -> None:
    assert parse_source("undefined") == LiteralExpr(
        TokenType.UNDEFINED, "undefined", Position(0, 1, 1)
    )


def test_identifier_is_variable() -> None:
    assert parse_source("counter") == VariableExpr("counter", Position(0, 1, 1))


def test_keyword_literals_are_not_identifiers() -> None:
    # Tokenizer keeps these as keyword literals, so they become LiteralExpr,
    # never VariableExpr.
    for source in ("true", "false", "null", "undefined"):
        assert isinstance(parse_source(source), LiteralExpr)


def test_boolean_operator_keywords_are_not_identifiers() -> None:
    # `and`/`or` are operators, never usable as a bare variable reference.
    with pytest.raises(ParserError):
        parse_source("and")
    with pytest.raises(ParserError):
        parse_source("or")


def test_literal_does_not_convert_to_python_value() -> None:
    node = parse_source("42")
    assert isinstance(node, LiteralExpr)
    assert node.value == "42"
    assert isinstance(node.value, str)


# --------------------------------------------------------------------------- #
# AST immutability and equality
# --------------------------------------------------------------------------- #


def test_literal_node_is_immutable() -> None:
    node = parse_source("1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.value = "2"  # type: ignore[misc]


def test_binary_node_is_immutable() -> None:
    node = parse_source("1 + 2")
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.operator = TokenType.MINUS  # type: ignore[misc]


def test_node_has_no_dict_due_to_slots() -> None:
    # slots=True means instances carry no __dict__, so no ad-hoc attributes can
    # be attached. Immutability of declared fields is covered above.
    node = parse_source("1")
    assert not hasattr(node, "__dict__")


def test_equal_expressions_produce_equal_asts() -> None:
    assert parse_source("a + b") == parse_source("a + b")


def test_different_expressions_produce_unequal_asts() -> None:
    assert parse_source("a + b") != parse_source("a - b")


# --------------------------------------------------------------------------- #
# Unary nodes
# --------------------------------------------------------------------------- #


def test_unary_minus() -> None:
    node = parse_source("-x")
    assert node == UnaryExpr(
        TokenType.MINUS, VariableExpr("x", Position(1, 1, 2)), Position(0, 1, 1)
    )


def test_unary_plus() -> None:
    node = parse_source("+x")
    assert isinstance(node, UnaryExpr)
    assert node.operator is TokenType.PLUS


def test_unary_not() -> None:
    node = parse_source("not enabled")
    assert isinstance(node, UnaryExpr)
    assert node.operator is TokenType.NOT
    assert node.operand == VariableExpr("enabled", Position(4, 1, 5))


def test_repeated_unary_operators_are_allowed() -> None:
    node = parse_source("- - x")
    assert isinstance(node, UnaryExpr)
    assert node.operator is TokenType.MINUS
    assert isinstance(node.operand, UnaryExpr)
    assert node.operand.operator is TokenType.MINUS


def test_repeated_not_is_allowed() -> None:
    node = parse_source("not not flag")
    assert isinstance(node, UnaryExpr)
    assert isinstance(node.operand, UnaryExpr)


# --------------------------------------------------------------------------- #
# Binary nodes
# --------------------------------------------------------------------------- #


def test_simple_addition() -> None:
    node = parse_source("1 + 2")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert node.left == LiteralExpr(TokenType.INTEGER, "1", Position(0, 1, 1))
    assert node.right == LiteralExpr(TokenType.INTEGER, "2", Position(4, 1, 5))


@pytest.mark.parametrize(
    "source,operator",
    [
        ("a == b", TokenType.EQ),
        ("a != b", TokenType.NE),
        ("a < b", TokenType.LT),
        ("a <= b", TokenType.LE),
        ("a > b", TokenType.GT),
        ("a >= b", TokenType.GE),
    ],
)
def test_comparison_operators(source: str, operator: TokenType) -> None:
    node = parse_source(source)
    assert isinstance(node, BinaryExpr)
    assert node.operator is operator


def test_boolean_and() -> None:
    node = parse_source("a and b")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.AND


def test_boolean_or() -> None:
    node = parse_source("a or b")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.OR


# --------------------------------------------------------------------------- #
# Conditional nodes
# --------------------------------------------------------------------------- #


def test_conditional_shape() -> None:
    node = parse_source('"yes" if cond else "no"')
    assert isinstance(node, ConditionalExpr)
    assert node.if_true == LiteralExpr(TokenType.STRING, "yes", Position(0, 1, 1))
    assert node.condition == VariableExpr("cond", Position(9, 1, 10))
    assert node.if_false == LiteralExpr(TokenType.STRING, "no", Position(19, 1, 20))


def test_conditional_anchor_is_the_if_token() -> None:
    node = parse_source("a if b else c")
    assert isinstance(node, ConditionalExpr)
    assert node.position == Position(2, 1, 3)  # the `if` keyword


# --------------------------------------------------------------------------- #
# Source positions
# --------------------------------------------------------------------------- #


def test_binary_anchor_is_operator_position() -> None:
    node = parse_source("12 + 3")
    assert isinstance(node, BinaryExpr)
    assert node.position == Position(3, 1, 4)  # the `+`


def test_unary_anchor_is_operator_position() -> None:
    node = parse_source("  -x")
    assert isinstance(node, UnaryExpr)
    assert node.position == Position(2, 1, 3)  # the `-`


def test_variable_anchor_is_token_position() -> None:
    node = parse_source("   value")
    assert isinstance(node, VariableExpr)
    assert node.position == Position(3, 1, 4)


# --------------------------------------------------------------------------- #
# Precedence between adjacent levels
# --------------------------------------------------------------------------- #


def test_parentheses_bind_tighter_than_unary() -> None:
    # -(x + 1): unary minus wraps the parenthesized sum.
    node = parse_source("-(x + 1)")
    assert isinstance(node, UnaryExpr)
    assert isinstance(node.operand, BinaryExpr)
    assert node.operand.operator is TokenType.PLUS


def test_unary_binds_tighter_than_multiplication() -> None:
    # -a * b parses as (-a) * b.
    node = parse_source("-a * b")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.STAR
    assert isinstance(node.left, UnaryExpr)


def test_multiplication_binds_tighter_than_addition() -> None:
    # a + b * c parses as a + (b * c).
    node = parse_source("a + b * c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.right, BinaryExpr)
    assert node.right.operator is TokenType.STAR


def test_division_binds_tighter_than_subtraction() -> None:
    node = parse_source("a - b / c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.MINUS
    assert isinstance(node.right, BinaryExpr)
    assert node.right.operator is TokenType.SLASH


def test_addition_binds_tighter_than_comparison() -> None:
    # a + b < c parses as (a + b) < c.
    node = parse_source("a + b < c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.LT
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.PLUS


def test_comparison_binds_tighter_than_and() -> None:
    # a < b and c parses as (a < b) and c.
    node = parse_source("a < b and c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.AND
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.LT


def test_and_binds_tighter_than_or() -> None:
    # a or b and c parses as a or (b and c).
    node = parse_source("a or b and c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.OR
    assert isinstance(node.right, BinaryExpr)
    assert node.right.operator is TokenType.AND


def test_or_binds_tighter_than_conditional() -> None:
    # a or b if c else d parses as (a or b) if c else d.
    node = parse_source("a or b if c else d")
    assert isinstance(node, ConditionalExpr)
    assert isinstance(node.if_true, BinaryExpr)
    assert node.if_true.operator is TokenType.OR


def test_mixed_precedence_expression() -> None:
    # x >= 10 and enabled or "n" if ready else "y"
    node = parse_source('x >= 10 and enabled or fallback if ready else "y"')
    assert isinstance(node, ConditionalExpr)
    assert isinstance(node.if_true, BinaryExpr)
    assert node.if_true.operator is TokenType.OR
    assert isinstance(node.if_true.left, BinaryExpr)
    assert node.if_true.left.operator is TokenType.AND


# --------------------------------------------------------------------------- #
# Associativity
# --------------------------------------------------------------------------- #


def test_subtraction_is_left_associative() -> None:
    # 10 - 3 - 2 parses as (10 - 3) - 2.
    node = parse_source("10 - 3 - 2")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.MINUS
    assert node.right == LiteralExpr(TokenType.INTEGER, "2", Position(9, 1, 10))
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.MINUS


def test_division_is_left_associative() -> None:
    node = parse_source("a / b / c")
    assert isinstance(node, BinaryExpr)
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.SLASH


def test_mixed_multiplication_and_division_is_left_associative() -> None:
    # a * b / c parses as (a * b) / c.
    node = parse_source("a * b / c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.SLASH
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.STAR


def test_mixed_addition_and_subtraction_is_left_associative() -> None:
    # a - b + c parses as (a - b) + c.
    node = parse_source("a - b + c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.MINUS


def test_and_is_left_associative() -> None:
    node = parse_source("a and b and c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.AND
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.AND


def test_or_is_left_associative() -> None:
    node = parse_source("a or b or c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.OR
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.OR


def test_conditional_is_right_associative() -> None:
    # a if b else c if d else e parses as a if b else (c if d else e).
    node = parse_source("a if b else c if d else e")
    assert isinstance(node, ConditionalExpr)
    assert node.if_true == VariableExpr("a", Position(0, 1, 1))
    assert isinstance(node.if_false, ConditionalExpr)
    assert node.if_false.if_true == VariableExpr("c", Position(12, 1, 13))


# --------------------------------------------------------------------------- #
# Nesting
# --------------------------------------------------------------------------- #


def test_redundant_parentheses_are_not_preserved() -> None:
    assert parse_source("(((1)))") == LiteralExpr(
        TokenType.INTEGER, "1", Position(3, 1, 4)
    )


def test_parentheses_override_precedence() -> None:
    # (a + b) * c parses with multiplication on top.
    node = parse_source("(a + b) * c")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.STAR
    assert isinstance(node.left, BinaryExpr)
    assert node.left.operator is TokenType.PLUS


def test_deeply_nested_parentheses() -> None:
    node = parse_source("((((1 + 2))))")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS


def test_unary_around_parenthesized_expression() -> None:
    node = parse_source("not (a and b)")
    assert isinstance(node, UnaryExpr)
    assert node.operator is TokenType.NOT
    assert isinstance(node.operand, BinaryExpr)
    assert node.operand.operator is TokenType.AND


def test_conditional_inside_parentheses() -> None:
    # The condition slot only accepts a bare conditional via parentheses.
    node = parse_source("x if (a if b else c) else y")
    assert isinstance(node, ConditionalExpr)
    assert isinstance(node.condition, ConditionalExpr)


def test_conditional_in_false_branch() -> None:
    node = parse_source("a if b else (c if d else e)")
    assert isinstance(node, ConditionalExpr)
    assert isinstance(node.if_false, ConditionalExpr)


def test_conditional_in_true_branch_via_parentheses() -> None:
    node = parse_source("(a if b else c) if d else e")
    assert isinstance(node, ConditionalExpr)
    assert isinstance(node.if_true, ConditionalExpr)


# --------------------------------------------------------------------------- #
# Complete input consumption (trailing tokens rejected)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "source",
    [
        "1 2",  # trailing literal
        "a b",  # trailing identifier
        "1, 2",  # unsupported comma
        "x = 1",  # unsupported assignment token
        "1 == 2 == 3",  # handled as chaining, but still rejected
        "1 )",  # unmatched closing parenthesis
        "(1) )",  # extra closing parenthesis
    ],
)
def test_trailing_tokens_are_rejected(source: str) -> None:
    with pytest.raises(ParserError):
        parse_source(source)


def test_trailing_literal_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("1 2")
    assert info.value.position == Position(2, 1, 3)


def test_unsupported_comma_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("1, 2")
    assert info.value.position == Position(1, 1, 2)


def test_unsupported_assignment_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("x = 1")
    assert info.value.position == Position(2, 1, 3)


# --------------------------------------------------------------------------- #
# Syntax failures
# --------------------------------------------------------------------------- #


def test_empty_input_raises() -> None:
    with pytest.raises(ParserError):
        parse_source("")


def test_unexpected_eof_message() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("1 +")
    assert "end of input" in str(info.value)


def test_missing_left_operand() -> None:
    with pytest.raises(ParserError):
        parse_source("* 2")


def test_missing_right_operand() -> None:
    with pytest.raises(ParserError):
        parse_source("1 +")


def test_missing_unary_operand() -> None:
    with pytest.raises(ParserError):
        parse_source("not")


def test_missing_closing_parenthesis() -> None:
    with pytest.raises(ParserError):
        parse_source("(1 + 2")


def test_unexpected_closing_parenthesis() -> None:
    with pytest.raises(ParserError):
        parse_source(")")


def test_empty_parentheses() -> None:
    with pytest.raises(ParserError):
        parse_source("()")


def test_incomplete_conditional_missing_else_and_branch() -> None:
    with pytest.raises(ParserError):
        parse_source("a if b")


def test_missing_condition_after_if() -> None:
    with pytest.raises(ParserError):
        parse_source("a if else c")


def test_missing_else() -> None:
    with pytest.raises(ParserError):
        parse_source("a if b c")


def test_missing_false_branch() -> None:
    with pytest.raises(ParserError):
        parse_source("a if b else")


def test_standalone_else() -> None:
    with pytest.raises(ParserError):
        parse_source("else")


@pytest.mark.parametrize("source", ["and", "or", "and b", "or b"])
def test_standalone_boolean_operators(source: str) -> None:
    with pytest.raises(ParserError):
        parse_source(source)


def test_misplaced_comparison_operator() -> None:
    with pytest.raises(ParserError):
        parse_source("< 2")


def test_repeated_multiplication_operator_is_rejected() -> None:
    with pytest.raises(ParserError):
        parse_source("1 * * 2")


def test_plus_after_plus_is_unary_not_error() -> None:
    # `1 + + 2` is legitimately `1 + (+2)`, not a repeated binary operator.
    node = parse_source("1 + + 2")
    assert isinstance(node, BinaryExpr)
    assert node.operator is TokenType.PLUS
    assert isinstance(node.right, UnaryExpr)
    assert node.right.operator is TokenType.PLUS


def test_chained_comparison_is_rejected() -> None:
    with pytest.raises(ParserError):
        parse_source("a < b < c")


def test_multiple_comparison_operators_without_operands() -> None:
    with pytest.raises(ParserError):
        parse_source("< >")


# --------------------------------------------------------------------------- #
# Error positions
# --------------------------------------------------------------------------- #


def test_unexpected_token_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("* 2")
    assert info.value.position == Position(0, 1, 1)


def test_missing_operand_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("1 +")
    # Anchored at the trailing EOF position (end of input).
    assert info.value.position == Position(3, 1, 4)


def test_missing_closing_parenthesis_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("(1 + 2")
    assert info.value.position == Position(6, 1, 7)  # EOF after "2"


def test_incomplete_conditional_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("a if b")
    assert info.value.position == Position(6, 1, 7)  # EOF where `else` expected


def test_chained_comparison_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("a < b < c")
    assert info.value.position == Position(6, 1, 7)  # the second `<`


def test_unexpected_closing_parenthesis_position() -> None:
    with pytest.raises(ParserError) as info:
        parse_source(")")
    assert info.value.position == Position(0, 1, 1)


def test_parser_error_is_a_syntax_error() -> None:
    with pytest.raises(ExpressionSyntaxError):
        parse_source("1 +")


def test_parser_error_is_not_a_lexer_error() -> None:
    with pytest.raises(ParserError) as info:
        parse_source("1 +")
    assert not isinstance(info.value, LexerError)


# --------------------------------------------------------------------------- #
# Malformed token-sequence input (boundary validation, no IndexError leak)
# --------------------------------------------------------------------------- #


def test_empty_token_sequence_raises_parser_error() -> None:
    with pytest.raises(ParserError):
        parse([])


def test_token_sequence_without_eof_raises_parser_error() -> None:
    tokens = [Token(TokenType.INTEGER, "1", Position(0, 1, 1))]
    with pytest.raises(ParserError):
        parse(tokens)


# --------------------------------------------------------------------------- #
# State isolation
# --------------------------------------------------------------------------- #


def test_repeated_parsing_of_same_tokens_is_stable() -> None:
    tokens = tokenize("a + b * c")
    first = parse(tokens)
    second = parse(tokens)
    assert first == second


def test_repeated_parsing_does_not_mutate_tokens() -> None:
    tokens = tokenize("a + b")
    before = list(tokens)
    parse(tokens)
    parse(tokens)
    assert tokens == before


def test_failed_parse_followed_by_successful_parse() -> None:
    with pytest.raises(ParserError):
        parse_source("1 +")
    assert parse_source("1 + 2") == BinaryExpr(
        TokenType.PLUS,
        LiteralExpr(TokenType.INTEGER, "1", Position(0, 1, 1)),
        LiteralExpr(TokenType.INTEGER, "2", Position(4, 1, 5)),
        Position(2, 1, 3),
    )


def test_parsing_different_expressions_does_not_share_state() -> None:
    assert parse_source("1 + 2") != parse_source("3 * 4")
    assert isinstance(parse_source("a and b"), BinaryExpr)
    assert isinstance(parse_source("a if b else c"), ConditionalExpr)
