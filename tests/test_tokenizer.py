"""Tokenizer tests.

These tests exercise the tokenizer through its intended interface
(``expression_engine._tokenizer.tokenize`` plus the ``Token`` / ``TokenType``
types). They cover valid tokens, whitespace handling, source positions,
operators, keywords versus identifiers, strings and escapes, and the
engine-specific lexer errors for malformed input. No parser/evaluator behavior
is assumed.
"""

from __future__ import annotations

import pytest

from expression_engine import ExpressionSyntaxError
from expression_engine.errors import LexerError
from expression_engine._tokens import Position, Token, TokenType
from expression_engine._tokenizer import tokenize


def types_of(source: str) -> list[TokenType]:
    """Token types for ``source`` excluding the trailing EOF."""
    return [tok.type for tok in tokenize(source)[:-1]]


def kinds_and_values(source: str) -> list[tuple[TokenType, str]]:
    return [(tok.type, tok.value) for tok in tokenize(source)[:-1]]


# --------------------------------------------------------------------------- #
# EOF / empty input
# --------------------------------------------------------------------------- #


def test_empty_source_yields_only_eof() -> None:
    tokens = tokenize("")
    assert len(tokens) == 1
    assert tokens[0].type is TokenType.EOF
    assert tokens[0].value == ""


def test_whitespace_only_yields_only_eof() -> None:
    tokens = tokenize("   \t\n  ")
    assert [tok.type for tok in tokens] == [TokenType.EOF]


def test_stream_always_ends_with_eof() -> None:
    tokens = tokenize("1 + 2")
    assert tokens[-1].type is TokenType.EOF


# --------------------------------------------------------------------------- #
# Tokens are immutable
# --------------------------------------------------------------------------- #


def test_tokens_are_immutable() -> None:
    token = tokenize("x")[0]
    with pytest.raises(AttributeError):
        token.value = "y"  # type: ignore[misc]


def test_tokens_support_value_equality() -> None:
    assert Token(TokenType.PLUS, "+", Position(0, 1, 1)) == Token(
        TokenType.PLUS, "+", Position(0, 1, 1)
    )


def test_positions_are_immutable() -> None:
    position = tokenize("x")[0].position
    with pytest.raises(AttributeError):
        position.offset = 5  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Numbers
# --------------------------------------------------------------------------- #


def test_integer_literal() -> None:
    (token,) = tokenize("42")[:-1]
    assert token.type is TokenType.INTEGER
    assert token.value == "42"


def test_float_literal() -> None:
    (token,) = tokenize("3.14")[:-1]
    assert token.type is TokenType.FLOAT
    assert token.value == "3.14"


@pytest.mark.parametrize("source", ["1e3", "2.5e-4", "1E6", "10e+2", "0.5E0"])
def test_scientific_notation_is_float(source: str) -> None:
    (token,) = tokenize(source)[:-1]
    assert token.type is TokenType.FLOAT
    assert token.value == source


def test_zero_and_multidigit_integers() -> None:
    assert kinds_and_values("0 1000 007") == [
        (TokenType.INTEGER, "0"),
        (TokenType.INTEGER, "1000"),
        (TokenType.INTEGER, "007"),
    ]


@pytest.mark.parametrize(
    "source",
    [".5", "5.", "1e", "1e+", "1.2.3", "123abc", "1_000"],
)
def test_malformed_numbers_raise(source: str) -> None:
    with pytest.raises(ExpressionSyntaxError):
        tokenize(source)


# --------------------------------------------------------------------------- #
# Identifiers and keywords
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "word,expected",
    [
        ("true", TokenType.TRUE),
        ("false", TokenType.FALSE),
        ("null", TokenType.NULL),
        ("undefined", TokenType.UNDEFINED),
        ("and", TokenType.AND),
        ("or", TokenType.OR),
        ("not", TokenType.NOT),
        ("if", TokenType.IF),
        ("else", TokenType.ELSE),
        ("let", TokenType.LET),
        ("in", TokenType.IN),
    ],
)
def test_keywords_are_recognized(word: str, expected: TokenType) -> None:
    (token,) = tokenize(word)[:-1]
    assert token.type is expected
    assert token.value == word


@pytest.mark.parametrize(
    "name",
    ["x", "_x", "x1", "value", "True", "TRUE", "trueish", "and_", "ifx", "let_in"],
)
def test_identifiers_are_recognized(name: str) -> None:
    (token,) = tokenize(name)[:-1]
    assert token.type is TokenType.IDENTIFIER
    assert token.value == name


def test_keyword_matching_is_case_sensitive() -> None:
    assert tokenize("True")[0].type is TokenType.IDENTIFIER
    assert tokenize("true")[0].type is TokenType.TRUE


# --------------------------------------------------------------------------- #
# Operators and punctuation
# --------------------------------------------------------------------------- #


def test_arithmetic_operators() -> None:
    assert types_of("+ - * /") == [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
    ]


def test_comparison_operators() -> None:
    assert types_of("== != < <= > >=") == [
        TokenType.EQ,
        TokenType.NE,
        TokenType.LT,
        TokenType.LE,
        TokenType.GT,
        TokenType.GE,
    ]


def test_assign_versus_equality() -> None:
    assert types_of("=") == [TokenType.ASSIGN]
    assert types_of("==") == [TokenType.EQ]
    assert types_of("= ==") == [TokenType.ASSIGN, TokenType.EQ]


def test_two_char_operators_take_priority_over_one_char() -> None:
    # `<=` must lex as one LE token, not LT then ASSIGN.
    assert types_of("<=") == [TokenType.LE]
    assert types_of("< =") == [TokenType.LT, TokenType.ASSIGN]


def test_parentheses_and_comma() -> None:
    assert types_of("( , )") == [
        TokenType.LPAREN,
        TokenType.COMMA,
        TokenType.RPAREN,
    ]


def test_operators_without_surrounding_whitespace() -> None:
    assert types_of("1+2") == [TokenType.INTEGER, TokenType.PLUS, TokenType.INTEGER]


def test_minus_is_not_part_of_number() -> None:
    # Unary minus is a parser concern; the lexer emits MINUS then INTEGER.
    assert types_of("-5") == [TokenType.MINUS, TokenType.INTEGER]


@pytest.mark.parametrize("source", ["#", "@", "!", "?", ".", "&", "|", "$"])
def test_invalid_characters_raise(source: str) -> None:
    with pytest.raises(ExpressionSyntaxError):
        tokenize(source)


# --------------------------------------------------------------------------- #
# Strings and escapes
# --------------------------------------------------------------------------- #


def test_double_quoted_string() -> None:
    (token,) = tokenize('"hello"')[:-1]
    assert token.type is TokenType.STRING
    assert token.value == "hello"


def test_single_quoted_string() -> None:
    (token,) = tokenize("'hello'")[:-1]
    assert token.type is TokenType.STRING
    assert token.value == "hello"


def test_empty_string() -> None:
    (token,) = tokenize('""')[:-1]
    assert token.type is TokenType.STRING
    assert token.value == ""


def test_all_supported_escapes_are_decoded() -> None:
    (token,) = tokenize(r'"a\\b\"c\'d\ne\tf\rg"')[:-1]
    assert token.value == "a\\b\"c'd\ne\tf\rg"


def test_quote_of_other_kind_is_literal_inside_string() -> None:
    assert tokenize("'he said \"hi\"'")[0].value == 'he said "hi"'
    assert tokenize('"it\'s ok"')[0].value == "it's ok"


def test_unicode_inside_string_is_preserved() -> None:
    assert tokenize('"caf\u00e9 \u2603"')[0].value == "caf\u00e9 \u2603"


@pytest.mark.parametrize("source", [r'"\x"', r'"\d"', r'"\0"', r'"bad\q"'])
def test_invalid_escapes_raise(source: str) -> None:
    with pytest.raises(ExpressionSyntaxError):
        tokenize(source)


@pytest.mark.parametrize("source", ['"unterminated', "'unterminated", '"ends with backslash\\'])
def test_unterminated_strings_raise(source: str) -> None:
    with pytest.raises(ExpressionSyntaxError):
        tokenize(source)


def test_newline_in_string_is_unterminated() -> None:
    with pytest.raises(ExpressionSyntaxError):
        tokenize('"line one\nline two"')


# --------------------------------------------------------------------------- #
# Source positions
# --------------------------------------------------------------------------- #


def test_positions_are_one_based_on_first_line() -> None:
    plus, ident = tokenize("+ ab")[:-1]
    assert (plus.position.offset, plus.position.line, plus.position.column) == (0, 1, 1)
    assert (ident.position.offset, ident.position.line, ident.position.column) == (2, 1, 3)


def test_positions_track_across_newlines() -> None:
    # "a\n  bc" -> 'a' at line 1 col 1; 'bc' at line 2 col 3.
    a, bc = tokenize("a\n  bc")[:-1]
    assert (a.position.line, a.position.column) == (1, 1)
    assert (bc.position.line, bc.position.column, bc.position.offset) == (2, 3, 4)


def test_eof_position_is_end_of_input() -> None:
    tokens = tokenize("ab")
    eof = tokens[-1]
    assert eof.type is TokenType.EOF
    assert eof.position.offset == 2
    assert eof.position.column == 3


def test_error_message_includes_position() -> None:
    with pytest.raises(ExpressionSyntaxError) as info:
        tokenize("a + #")
    message = str(info.value)
    assert "line 1" in message
    assert "column 5" in message


def test_lexer_error_is_a_syntax_error_with_position() -> None:
    with pytest.raises(LexerError) as info:
        tokenize("a + #")
    assert isinstance(info.value, ExpressionSyntaxError)
    assert info.value.position == Position(4, 1, 5)


# --------------------------------------------------------------------------- #
# A representative composite expression
# --------------------------------------------------------------------------- #


def test_composite_expression_from_decision_log() -> None:
    source = 'let x = 2 + 3 * (y - 1) in x > 0 and name == "hi"'
    assert types_of(source) == [
        TokenType.LET,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.INTEGER,
        TokenType.PLUS,
        TokenType.INTEGER,
        TokenType.STAR,
        TokenType.LPAREN,
        TokenType.IDENTIFIER,
        TokenType.MINUS,
        TokenType.INTEGER,
        TokenType.RPAREN,
        TokenType.IN,
        TokenType.IDENTIFIER,
        TokenType.GT,
        TokenType.INTEGER,
        TokenType.AND,
        TokenType.IDENTIFIER,
        TokenType.EQ,
        TokenType.STRING,
    ]


def test_type_input_validation() -> None:
    with pytest.raises(TypeError):
        tokenize(123)  # type: ignore[arg-type]
