"""Special runtime values for the expression engine.

This module defines the ``UNDEFINED`` singleton, which represents a missing or
unavailable value (for example, a variable that was never provided). It is a
distinct concept from explicit *null*:

* explicit null is represented to callers by Python ``None``;
* a missing value is represented by ``UNDEFINED``.

Keeping these distinct lets the engine tell ``{"x": None}`` (``x`` exists and is
null) apart from ``{}`` (``x`` is absent and resolves to ``UNDEFINED``).

The evaluator never coerces ``UNDEFINED`` to zero or a Boolean. Arithmetic and
ordering reject it, while equality keeps it distinct from explicit null.
"""

from __future__ import annotations

from typing import Any

__all__ = ["UNDEFINED"]


class _UndefinedType:
    """Type of the unique ``UNDEFINED`` sentinel.

    The class enforces a single instance: every attempt to construct it returns
    the same object, so callers cannot create independent "undefined" values
    through the public API. The instance is immutable (no instance attributes)
    and survives copying and pickling as the same singleton.
    """

    __slots__ = ()

    _instance: "_UndefinedType | None" = None

    def __new__(cls) -> "_UndefinedType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNDEFINED"

    def __reduce__(self) -> tuple[type, tuple[()]]:
        # Reconstruct via the class so unpickling yields the same singleton.
        return (self.__class__, ())

    def __copy__(self) -> "_UndefinedType":
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> "_UndefinedType":
        return self


UNDEFINED: _UndefinedType = _UndefinedType()
"""The unique sentinel representing a missing or unavailable value."""
