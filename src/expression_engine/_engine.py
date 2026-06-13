"""Stage 12: the public compilation and evaluation API.

This module wraps the internal tokenizer, parser, and evaluator behind
:class:`Engine` and :class:`Expression`. Compilation tokenizes and parses once;
repeated :meth:`Expression.evaluate` calls reuse the stored immutable AST and
never re-tokenize or re-parse.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ._ast import Expr
from ._evaluator import evaluate
from ._parser import parse
from ._tokenizer import tokenize


@dataclass(frozen=True, slots=True)
class Expression:
    """An immutable compiled expression reusable across evaluations."""

    _ast: Expr = field(repr=False)

    def evaluate(
        self,
        variables: Mapping[str, object] | None = None,
    ) -> object:
        """Evaluate the compiled expression with the supplied variables.

        Args:
            variables: External variables as a read-only mapping from name to
                value. ``None`` means an empty mapping. A name that is absent
                evaluates to :data:`~expression_engine.UNDEFINED`.

        Returns:
            The evaluated value.

        Raises:
            ExpressionEvaluationError: If evaluation fails.
        """
        return evaluate(self._ast, variables)


class Engine:
    """Compiles source expressions into reusable :class:`Expression` objects."""

    __slots__ = ()

    def compile(self, source: str) -> Expression:
        """Compile source text into an immutable :class:`Expression`.

        Args:
            source: The expression source text.

        Returns:
            A compiled expression that can be evaluated repeatedly.

        Raises:
            ExpressionSyntaxError: If tokenization or parsing fails.
        """
        return Expression(parse(tokenize(source)))
