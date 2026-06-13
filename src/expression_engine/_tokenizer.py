"""Stage 2: the tokenizer (lexer) for the expression engine.

This module turns expression source text into a flat sequence of immutable
:class:`~expression_engine._tokens.Token` objects (defined in
:mod:`expression_engine._tokens`). It performs *only* lexical analysis: it
recognizes the literals, identifiers, keywords, operators, and punctuation of
the language described in ``docs/decisions.md`` and records a source position
for every token. Parsing, an AST, evaluation, functions, and the public
``Engine`` / ``Expression`` API are intentionally **not** part of this stage.

The intended interface is the module-level :func:`tokenize` function, which
returns the token objects defined in :mod:`expression_engine._tokens`. Lexical
problems are reported by raising
:class:`~expression_engine.errors.LexerError` with the offending source
position attached, so a later parser or a library consumer can locate the
error.

Design notes (smallest reasonable semantics, consistent with the decision log):

* Integer literals produce :attr:`~._tokens.TokenType.INTEGER`; literals with a
  fraction or an exponent produce :attr:`~._tokens.TokenType.FLOAT`. Conversion
  of the lexeme to a Python ``int`` / ``float`` is deliberately deferred to a
  later stage; a number token stores its exact source lexeme as its value.
* A decimal point requires digits on both sides (``0.5`` is valid; ``.5`` and
  ``5.`` are malformed). Scientific notation (``1e3``, ``2.5e-4``, ``1E6``) is
  supported and always yields a float.
* String literals may be single- or double-quoted. The escapes ``\\\\``,
  ``\\"``, ``\\'``, ``\\n``, ``\\t`` and ``\\r`` are decoded; any other escape
  is an error. A string token's value is the decoded text. A raw newline before
  the closing quote is an unterminated string (no multiline strings in v1).
* Identifiers are ASCII ``[A-Za-z_][A-Za-z0-9_]*`` and keyword matching is
  case-sensitive. Unicode is supported only inside string literals.
* Unary minus is not handled here: ``-5`` lexes as ``MINUS`` then ``INTEGER``.
  Boolean negation is the word ``not``; a lone ``!`` is an invalid character
  (only ``!=`` is valid).
"""

from __future__ import annotations

from .errors import LexerError
from ._tokens import Position, Token, TokenType

__all__ = ["tokenize"]


_KEYWORDS: dict[str, TokenType] = {
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "undefined": TokenType.UNDEFINED,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "let": TokenType.LET,
    "in": TokenType.IN,
}

_ESCAPES: dict[str, str] = {
    "\\": "\\",
    '"': '"',
    "'": "'",
    "n": "\n",
    "t": "\t",
    "r": "\r",
}

_TWO_CHAR_OPS: dict[str, TokenType] = {
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
}

_ONE_CHAR_OPS: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "=": TokenType.ASSIGN,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
}

_DIGITS = "0123456789"
_WHITESPACE = " \t\r\n"


def _is_digit(char: str) -> bool:
    # Guards against the empty string returned at end-of-input, for which
    # ``"" in _DIGITS`` would be (misleadingly) true.
    return len(char) == 1 and char in _DIGITS


def _is_ident_start(char: str) -> bool:
    return char == "_" or ("a" <= char <= "z") or ("A" <= char <= "Z")


def _is_ident_continue(char: str) -> bool:
    return _is_ident_start(char) or _is_digit(char)


class _Tokenizer:
    """Single-use scanner over one source string.

    The instance holds the scan cursor (``_pos``) and the human-readable
    ``_line`` / ``_column`` that track it. Create one per call to
    :func:`tokenize`; it is not reusable or thread-safe by itself.
    """

    def __init__(self, source: str) -> None:
        self._src = source
        self._len = len(source)
        self._pos = 0
        self._line = 1
        self._column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        src = self._src
        while self._pos < self._len:
            char = src[self._pos]

            if char in _WHITESPACE:
                self._advance()
                continue

            start = self._mark()

            if char in _DIGITS:
                tokens.append(self._read_number(start))
            elif char == ".":
                # A dot is never a valid standalone token in v1. Give a more
                # specific message when it looks like a misformed number.
                if _is_digit(self._peek(1)):
                    raise self._error(
                        "malformed number: a digit is required before the decimal point",
                        start,
                    )
                raise self._error("invalid character '.'", start)
            elif _is_ident_start(char):
                tokens.append(self._read_identifier(start))
            elif char == "'" or char == '"':
                tokens.append(self._read_string(start))
            else:
                tokens.append(self._read_operator(start))

        tokens.append(Token(TokenType.EOF, "", self._mark()))
        return tokens

    def _read_number(self, start: Position) -> Token:
        src = self._src
        is_float = False

        self._consume_digits()

        # Optional fractional part: a decimal point must have digits on both
        # sides, so `.` is only part of the number when a digit follows it.
        if self._current() == ".":
            if _is_digit(self._peek(1)):
                is_float = True
                self._advance()  # consume '.'
                self._consume_digits()
            else:
                raise self._error(
                    "malformed number: a decimal point must be followed by a digit",
                    start,
                )

        # Optional exponent; scientific notation always yields a float.
        if self._current() in ("e", "E"):
            is_float = True
            self._advance()  # consume 'e' / 'E'
            if self._current() in ("+", "-"):
                self._advance()
            if not _is_digit(self._current()):
                raise self._error("malformed number: the exponent has no digits", start)
            self._consume_digits()

        # Reject trailing junk such as `123abc` or `1.2.3` instead of silently
        # splitting it into two tokens.
        trailing = self._current()
        if trailing == "." or _is_ident_start(trailing):
            raise self._error(
                f"malformed number: unexpected character {trailing!r} after numeric literal",
                start,
            )

        lexeme = src[start.offset:self._pos]
        token_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(token_type, lexeme, start)

    def _read_identifier(self, start: Position) -> Token:
        src = self._src
        while self._pos < self._len and _is_ident_continue(src[self._pos]):
            self._advance()
        lexeme = src[start.offset:self._pos]
        token_type = _KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        return Token(token_type, lexeme, start)

    def _read_string(self, start: Position) -> Token:
        src = self._src
        quote = src[self._pos]
        self._advance()  # consume opening quote
        parts: list[str] = []

        while True:
            if self._pos >= self._len:
                raise self._error("unterminated string literal", start)

            char = src[self._pos]

            if char == quote:
                self._advance()  # consume closing quote
                break

            if char == "\n":
                # No multiline strings in v1; a raw newline means the closing
                # quote was never reached on this line.
                raise self._error("unterminated string literal", start)

            if char == "\\":
                escape_at = self._mark()
                self._advance()  # consume backslash
                if self._pos >= self._len:
                    raise self._error("unterminated string literal", start)
                escaped = src[self._pos]
                if escaped not in _ESCAPES:
                    raise self._error(f"invalid escape sequence '\\{escaped}'", escape_at)
                parts.append(_ESCAPES[escaped])
                self._advance()
                continue

            parts.append(char)
            self._advance()

        return Token(TokenType.STRING, "".join(parts), start)

    def _read_operator(self, start: Position) -> Token:
        src = self._src
        char = src[self._pos]
        two = src[self._pos:self._pos + 2]

        if two in _TWO_CHAR_OPS:
            self._advance()
            self._advance()
            return Token(_TWO_CHAR_OPS[two], two, start)

        if char == "!":
            raise self._error("invalid character '!' (did you mean '!='?)", start)

        if char in _ONE_CHAR_OPS:
            self._advance()
            return Token(_ONE_CHAR_OPS[char], char, start)

        raise self._error(f"invalid character {char!r}", start)

    def _consume_digits(self) -> None:
        src = self._src
        while self._pos < self._len and src[self._pos] in _DIGITS:
            self._advance()

    def _current(self) -> str:
        if self._pos < self._len:
            return self._src[self._pos]
        return ""

    def _peek(self, ahead: int) -> str:
        index = self._pos + ahead
        if index < self._len:
            return self._src[index]
        return ""

    def _mark(self) -> Position:
        return Position(self._pos, self._line, self._column)

    def _advance(self) -> str:
        char = self._src[self._pos]
        self._pos += 1
        if char == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return char

    def _error(self, message: str, position: Position) -> LexerError:
        return LexerError(message, position)


def tokenize(source: str) -> list[Token]:
    """Tokenize ``source`` into a list of tokens ending with an ``EOF`` token.

    Args:
        source: The expression source text.

    Returns:
        A list of immutable :class:`~._tokens.Token` objects. The list always
        ends with a single :attr:`~._tokens.TokenType.EOF` token positioned at
        the end of the input.

    Raises:
        LexerError: If the source contains an invalid character, a malformed
            number, an invalid string escape, or an unterminated string. The
            error carries the offending :class:`~._tokens.Position`.
        TypeError: If ``source`` is not a ``str``.
    """

    if not isinstance(source, str):
        raise TypeError(f"source must be a str, not {type(source).__name__}")
    return _Tokenizer(source).tokenize()
