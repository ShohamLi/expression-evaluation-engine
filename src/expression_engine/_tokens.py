"""Immutable token data structures for the expression engine.

This module defines *data only*: the lexical categories (:class:`TokenType`),
the source-position record (:class:`Position`), and the immutable
:class:`Token` value object. The scanning logic that produces these objects
lives in :mod:`expression_engine._tokenizer`.

These types are internal to the engine. They are kept here, separate from the
tokenizer, so that later stages (parser, validator) can depend on the token
*shape* without importing the scanning machinery.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto, unique

__all__ = ["TokenType", "Position", "Token"]


@unique
class TokenType(Enum):
    """The lexical category of a :class:`Token`.

    Each operator, keyword, and punctuation mark has its own member so a later
    parser can match on ``token.type`` without re-inspecting the lexeme.
    """

    # Literals and names.
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords.
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    UNDEFINED = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IF = auto()
    ELSE = auto()
    LET = auto()
    IN = auto()

    # Operators.
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQ = auto()  # ==
    NE = auto()  # !=
    LT = auto()  # <
    LE = auto()  # <=
    GT = auto()  # >
    GE = auto()  # >=
    ASSIGN = auto()  # = (the `let name = expr` binder)

    # Punctuation.
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()

    # End of input.
    EOF = auto()


@dataclass(frozen=True)
class Position:
    """An immutable source position pointing at a single character.

    Attributes:
        offset: Zero-based index of the character in the source string.
        line: One-based line number.
        column: One-based column number within ``line``.
    """

    offset: int
    line: int
    column: int


@dataclass(frozen=True)
class Token:
    """An immutable lexical token.

    Attributes:
        type: The :class:`TokenType` category.
        value: The token's text. For ``STRING`` this is the *decoded* content
            (escapes resolved); for numbers it is the exact source lexeme; for
            identifiers, keywords, operators and punctuation it is the matched
            text. The ``EOF`` token has an empty value.
        position: The :class:`Position` of the token's first character.
    """

    type: TokenType
    value: str
    position: Position
