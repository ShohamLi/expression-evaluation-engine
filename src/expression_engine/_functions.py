"""Built-in and registered function metadata, validation, and invocation."""

from __future__ import annotations

import inspect
import math
import re
from collections import ChainMap
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import NoReturn

from .errors import (
    ExpressionError,
    ExpressionEvaluationError,
    ExpressionTypeError,
    ExpressionValidationError,
    FunctionArityError,
    UnknownFunctionError,
)
from ._ast import (
    BinaryExpr,
    CallExpr,
    ConditionalExpr,
    Expr,
    LetExpr,
    LiteralExpr,
    LocalFunctionExpr,
    UnaryExpr,
    VariableExpr,
)
from ._tokens import Position
from ._values import UNDEFINED

__all__ = [
    "FunctionBindings",
    "FunctionRegistry",
    "EMPTY_FUNCTION_BINDINGS",
    "build_registry",
    "validate_function_calls",
    "invoke_call",
]

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_KEYWORD_NAMES: frozenset[str] = frozenset(
    {
        "true",
        "false",
        "null",
        "undefined",
        "and",
        "or",
        "not",
        "if",
        "else",
        "let",
        "in",
    }
)

BUILTIN_NAMES: frozenset[str] = frozenset(
    {"abs", "min", "max", "round", "floor", "ceil", "sqrt", "pow", "log"}
)


def _is_number(value: object) -> bool:
    return type(value) in (int, float)


def _require_number(value: object, function: str, position: Position) -> int | float:
    if not _is_number(value):
        raise ExpressionTypeError(
            f"{function}() requires numeric arguments, "
            f"got {type(value).__name__}",
            position,
        )
    return value


def _require_numbers(
    values: tuple[object, ...], function: str, position: Position
) -> list[int | float]:
    return [_require_number(value, function, position) for value in values]


def _validate_return_value(value: object, function: str, position: Position) -> object:
    if type(value) in (int, float, str, bool) or value is None or value is UNDEFINED:
        return value
    raise ExpressionTypeError(
        f"{function}() returned unsupported type {type(value).__name__}",
        position,
    )


@dataclass(frozen=True, slots=True)
class _RegisteredFunction:
    name: str
    callable: Callable[..., object]
    min_args: int
    max_args: int


@dataclass(frozen=True, slots=True)
class _BuiltinSpec:
    name: str
    min_args: int
    max_args: int | None  # ``None`` means no upper limit (``min`` / ``max``).


_BUILTIN_SPECS: Mapping[str, _BuiltinSpec] = MappingProxyType(
    {
        "abs": _BuiltinSpec("abs", 1, 1),
        "floor": _BuiltinSpec("floor", 1, 1),
        "ceil": _BuiltinSpec("ceil", 1, 1),
        "sqrt": _BuiltinSpec("sqrt", 1, 1),
        "log": _BuiltinSpec("log", 1, 1),
        "pow": _BuiltinSpec("pow", 2, 2),
        "round": _BuiltinSpec("round", 1, 2),
        "min": _BuiltinSpec("min", 2, None),
        "max": _BuiltinSpec("max", 2, None),
    }
)

_ResolvedFunction = _RegisteredFunction | _BuiltinSpec | LocalFunctionExpr
FunctionBindings = Mapping[CallExpr, _ResolvedFunction]
EMPTY_FUNCTION_BINDINGS: FunctionBindings = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class FunctionRegistry:
    """Immutable snapshot of registered host functions."""

    _registered: Mapping[str, _RegisteredFunction]

    @staticmethod
    def empty() -> FunctionRegistry:
        return FunctionRegistry(MappingProxyType({}))

    def get_registered(self, name: str) -> _RegisteredFunction | None:
        return self._registered.get(name)


def _validate_registration_name(name: object) -> str:
    if not isinstance(name, str):
        raise ExpressionValidationError(
            f"function names must be str, got {type(name).__name__}"
        )
    name = str(name)
    if not _IDENTIFIER_PATTERN.fullmatch(name):
        raise ExpressionValidationError(
            f"invalid function name {name!r}; names must match "
            r"[A-Za-z_][A-Za-z0-9_]*"
        )
    if name in _KEYWORD_NAMES:
        raise ExpressionValidationError(f"invalid function name {name!r}; keyword")
    return name


def _inspect_callable(fn: Callable[..., object]) -> tuple[int, int]:
    try:
        signature = inspect.signature(fn)
    except Exception as error:
        raise ExpressionValidationError(
            "callable signature cannot be inspected"
        ) from error

    min_args = 0
    max_args = 0
    optional_parameter_seen = False
    for parameter in signature.parameters.values():
        kind = parameter.kind
        if kind is inspect.Parameter.VAR_POSITIONAL:
            raise ExpressionValidationError(
                "callable signature with *args is not supported"
            )
        if kind is inspect.Parameter.VAR_KEYWORD:
            raise ExpressionValidationError(
                "callable signature with **kwargs is not supported"
            )
        if kind is inspect.Parameter.KEYWORD_ONLY:
            raise ExpressionValidationError(
                "callable signature with keyword-only parameters is not supported"
            )
        max_args += 1
        if parameter.default is inspect.Parameter.empty:
            if optional_parameter_seen:
                raise ExpressionValidationError(
                    "callable positional defaults must be trailing"
                )
            min_args += 1
        else:
            optional_parameter_seen = True
    return min_args, max_args


def build_registry(
    functions: Mapping[str, Callable[..., object]] | None,
) -> FunctionRegistry:
    if functions is None:
        return FunctionRegistry.empty()

    if not isinstance(functions, Mapping):
        raise ExpressionValidationError(
            f"functions must be a mapping or None, got {type(functions).__name__}"
        )

    snapshot = dict(functions)
    registered: dict[str, _RegisteredFunction] = {}
    for raw_name, fn in snapshot.items():
        name = _validate_registration_name(raw_name)
        if name in BUILTIN_NAMES:
            raise ExpressionValidationError(
                f"cannot register built-in function name {name!r}"
            )
        if not callable(fn):
            raise ExpressionValidationError(
                f"registered function {name!r} is not callable"
            )
        min_args, max_args = _inspect_callable(fn)
        registered[name] = _RegisteredFunction(name, fn, min_args, max_args)
    return FunctionRegistry(MappingProxyType(registered))


def _check_arity(
    name: str,
    argument_count: int,
    min_args: int,
    max_args: int | None,
    position: Position,
) -> None:
    if argument_count < min_args:
        raise FunctionArityError(
            f"{name}() expected at least {min_args} argument(s), "
            f"got {argument_count}",
            position,
        )
    if max_args is not None and argument_count > max_args:
        raise FunctionArityError(
            f"{name}() expected at most {max_args} argument(s), "
            f"got {argument_count}",
            position,
        )


def _resolve_call(node: CallExpr, registry: FunctionRegistry) -> _ResolvedFunction:
    name = node.name
    count = len(node.arguments)
    registered = registry.get_registered(name)
    if registered is not None:
        _check_arity(
            name, count, registered.min_args, registered.max_args, node.position
        )
        return registered
    if name in _BUILTIN_SPECS:
        spec = _BUILTIN_SPECS[name]
        _check_arity(name, count, spec.min_args, spec.max_args, node.position)
        return spec
    raise UnknownFunctionError(f"unknown function {name!r}", node.position)


def validate_function_calls(node: Expr, registry: FunctionRegistry) -> FunctionBindings:
    """Validate and lexically resolve every call in ``node`` exactly once."""
    bindings: dict[CallExpr, _ResolvedFunction] = {}

    def resolve_call(
        call: CallExpr,
        local_functions: Mapping[str, LocalFunctionExpr],
        blocked_names: frozenset[str],
    ) -> _ResolvedFunction:
        local_function = local_functions.get(call.name)
        if local_function is not None:
            expected = len(local_function.parameters)
            actual = len(call.arguments)
            if actual != expected:
                raise FunctionArityError(
                    f"{call.name}() expected exactly {expected} argument(s), "
                    f"got {actual}",
                    call.position,
                )
            return local_function
        if call.name in blocked_names:
            raise ExpressionValidationError(
                f"recursion is not supported for local function {call.name!r}",
                call.position,
            )
        return _resolve_call(call, registry)

    def validate_definition(definition: LocalFunctionExpr) -> None:
        if definition.name in BUILTIN_NAMES:
            raise ExpressionValidationError(
                f"cannot define local function using built-in name "
                f"{definition.name!r}",
                definition.position,
            )
        seen: set[str] = set()
        for parameter in definition.parameters:
            if parameter in seen:
                raise ExpressionValidationError(
                    f"duplicate parameter {parameter!r} in local function "
                    f"{definition.name!r}",
                    definition.position,
                )
            seen.add(parameter)

    def visit(
        current: Expr,
        local_functions: Mapping[str, LocalFunctionExpr],
        blocked_names: frozenset[str],
    ) -> None:
        if isinstance(current, CallExpr):
            bindings[current] = resolve_call(
                current, local_functions, blocked_names
            )
            for argument in current.arguments:
                visit(argument, local_functions, blocked_names)
            return
        if isinstance(current, BinaryExpr):
            visit(current.left, local_functions, blocked_names)
            visit(current.right, local_functions, blocked_names)
            return
        if isinstance(current, UnaryExpr):
            visit(current.operand, local_functions, blocked_names)
            return
        if isinstance(current, ConditionalExpr):
            visit(current.condition, local_functions, blocked_names)
            visit(current.if_true, local_functions, blocked_names)
            visit(current.if_false, local_functions, blocked_names)
            return
        if isinstance(current, LetExpr):
            visit(current.value, local_functions, blocked_names)
            visit(current.body, local_functions, blocked_names)
            return
        if isinstance(current, LocalFunctionExpr):
            validate_definition(current)
            visit(
                current.function_body,
                local_functions,
                blocked_names | {current.name},
            )
            body_functions = ChainMap({current.name: current}, local_functions)
            visit(
                current.body,
                body_functions,
                blocked_names,
            )
            return
        if isinstance(current, (LiteralExpr, VariableExpr)):
            return
        raise TypeError(f"unsupported expression node {type(current).__name__}")

    visit(node, {}, frozenset())
    return MappingProxyType(bindings)


def _raise_calculation_error(
    function: str, position: Position, error: Exception
) -> NoReturn:
    raise ExpressionEvaluationError(
        f"{function}() calculation failed", position
    ) from error


def _call_builtin(name: str, args: tuple[object, ...], position: Position) -> object:
    if name == "abs":
        value = _require_number(args[0], name, position)
        return abs(value)
    if name == "floor":
        value = _require_number(args[0], name, position)
        try:
            return math.floor(value)
        except (ValueError, OverflowError) as error:
            _raise_calculation_error(name, position, error)
    if name == "ceil":
        value = _require_number(args[0], name, position)
        try:
            return math.ceil(value)
        except (ValueError, OverflowError) as error:
            _raise_calculation_error(name, position, error)
    if name == "sqrt":
        value = _require_number(args[0], name, position)
        if value < 0:
            raise ExpressionEvaluationError(
                "sqrt() argument must be non-negative", position
            )
        try:
            return float(math.sqrt(value))
        except (ValueError, OverflowError) as error:
            _raise_calculation_error(name, position, error)
    if name == "log":
        value = _require_number(args[0], name, position)
        if value <= 0:
            raise ExpressionEvaluationError(
                "log() argument must be positive", position
            )
        try:
            return float(math.log(value))
        except (ValueError, OverflowError) as error:
            _raise_calculation_error(name, position, error)
    if name == "pow":
        base = _require_number(args[0], name, position)
        exponent = _require_number(args[1], name, position)
        if type(base) is int and type(exponent) is int and exponent >= 0:
            try:
                return pow(base, exponent)
            except ArithmeticError as error:
                _raise_calculation_error(name, position, error)
        try:
            result = pow(base, exponent)
        except ArithmeticError as error:
            _raise_calculation_error(name, position, error)
        if type(result) is complex:
            raise ExpressionEvaluationError(
                "pow() result is not supported", position
            )
        return float(result)
    if name == "round":
        value = _require_number(args[0], name, position)
        if len(args) == 1:
            try:
                return round(value)
            except (ValueError, OverflowError) as error:
                _raise_calculation_error(name, position, error)
        ndigits = args[1]
        if type(ndigits) is not int:
            raise ExpressionTypeError(
                f"round() ndigits must be int, got {type(ndigits).__name__}",
                position,
            )
        try:
            return round(value, ndigits)
        except (ValueError, OverflowError) as error:
            _raise_calculation_error(name, position, error)
    if name in ("min", "max"):
        numbers = _require_numbers(args, name, position)
        return min(numbers) if name == "min" else max(numbers)
    raise ExpressionEvaluationError(f"unknown function {name!r}", position)


def _call_registered(
    registered: _RegisteredFunction,
    args: tuple[object, ...],
    position: Position,
) -> object:
    try:
        result = registered.callable(*args)
    except ExpressionError:
        raise
    except Exception as error:
        raise ExpressionEvaluationError(
            f"registered function {registered.name}() failed: {error}",
            position,
        ) from error
    return _validate_return_value(result, registered.name, position)


def invoke_call(
    function: _ResolvedFunction,
    args: tuple[object, ...],
    position: Position,
) -> object:
    if isinstance(function, _RegisteredFunction):
        return _call_registered(function, args, position)
    if isinstance(function, LocalFunctionExpr):
        raise ExpressionEvaluationError(
            "local function call requires a lexical closure", position
        )
    return _call_builtin(function.name, args, position)
