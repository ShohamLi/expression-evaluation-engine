# Expression Evaluation Engine

A reusable Python library that compiles expression source once and evaluates the
immutable compiled expression repeatedly against named variables.

## Requirements

- Python 3.11 or newer

## Installation

```bash
python -m pip install -e ".[dev]"
```

## Quick start

```python
from expression_engine import Engine

engine = Engine()
expression = engine.compile("2 + 3 * (x - 1)")

assert expression.evaluate({"x": 5}) == 14
assert expression.evaluate({"x": 2}) == 5
```

## Supported expressions

- Integer and floating-point numbers, strings, `true`, `false`, `null`, and
  `undefined`.
- External variables and parentheses.
- Unary `+`, `-`, and `not`.
- Arithmetic `+`, `-`, `*`, and `/`; division is true division.
- String concatenation with `+`, without implicit string conversion.
- Comparisons `==`, `!=`, `<`, `<=`, `>`, and `>=`.
- Strict Boolean `and`, `or`, and `not`; Boolean values are required, booleans
  are not numbers, and `and`/`or` short-circuit.
- Conditional expressions: `value_if_true if condition else value_if_false`.
  Only the selected branch is evaluated.
- Local variables: `let name = value in body`.
- Function calls and local expression functions, such as
  `let add(a, b) = a + b in add(1, 2)`.

A missing external variable evaluates to `UNDEFINED`.

## Functions

Built-ins: `abs`, `min`, `max`, `round`, `floor`, `ceil`, `sqrt`, `pow`, and
`log`. `log` is the natural logarithm; `min` and `max` require at least two
arguments. Numeric arguments accept built-in `int` and `float` values, not
`bool`.

```python
from expression_engine import Engine

def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))

engine = Engine(functions={"clamp": clamp})
expression = engine.compile("clamp(x, 0, 100)")

assert expression.evaluate({"x": 125}) == 100
```

Functions are registered when constructing `Engine`. Built-in names are
reserved. Registered Python functions are responsible for their own thread
safety.

## Null and undefined

`null` evaluates to Python `None`. `undefined` and missing variables evaluate to
the exported `UNDEFINED` singleton. Null and undefined are distinct, neither is
silently converted to `0`, and arithmetic or ordering involving them raises an
engine error.

```python
from expression_engine import Engine, UNDEFINED

engine = Engine()

assert engine.compile("null").evaluate() is None
assert engine.compile("undefined").evaluate() is UNDEFINED
assert engine.compile("missing").evaluate({}) is UNDEFINED
```

## Errors

Public error types are `ExpressionError`, `ExpressionSyntaxError`,
`ExpressionValidationError`, `UnknownFunctionError`, `FunctionArityError`,
`ExpressionEvaluationError`, `ExpressionTypeError`, and `DivisionByZeroError`.
Syntax and function validation errors occur during `compile()`; runtime type,
function-execution, and division errors occur during `evaluate()`.

## Reuse and thread safety

`Engine.compile()` tokenizes, parses, and validates once. `Expression.evaluate()`
does not tokenize or parse again. Compiled expressions are immutable and may be
evaluated repeatedly or concurrently with independent variable mappings, which
the engine does not mutate. Registered Python functions may still contain
mutable or non-thread-safe behavior.

## Benchmark

```bash
PYTHONPATH=src python benchmarks/benchmark_engine.py
```

For a shorter run:

```bash
PYTHONPATH=src python benchmarks/benchmark_engine.py \
  --iterations 1000 \
  --samples 3
```

Compilation and evaluation are measured separately, and evaluation workloads
reuse compiled expressions. Results depend on the machine, interpreter, and
system load.

## Running the tests

```bash
PYTHONPATH=src python -m pytest -q
```

## Limitations

- No recursive local functions.
- No anonymous or higher-order functions.
- No variadic, keyword, or default arguments in local expression functions.
- No chained comparisons.
- No `%` operator.
- No implicit type coercion.
- No arbitrary Python attribute access or code execution.
- No compilation cache.
