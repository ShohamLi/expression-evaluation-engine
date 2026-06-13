# Design Decisions

This document records the design decisions for the expression engine as they are
made. It is a working log, not the final assignment write-up. Each decision notes
the chosen behavior and, where relevant, what was deliberately excluded.

## Language syntax

- Everything is a single expression; there are no statements.
- Local bindings use `let name = expr in body`.
- Local functions use `let name(p1, p2) = expr in body` (named, positional
  parameters only).
- Conditional expressions use Python-style `value_if_true if condition else value_if_false`.
- Boolean operators are the word forms `and`, `or`, `not` only. `&&`, `||`, and
  `!` are not supported in v1.
- Comparisons are non-chaining (`a < b < c` is a syntax error; use parentheses).

## Numeric semantics

- Decimal integer and decimal floating-point literals are supported.
- Scientific notation is supported (`1e3`, `2.5e-4`, `1E6`).
- A decimal point requires digits on both sides: `0.5` is valid; `.5` and `5.`
  are invalid.
- Out of scope for v1: hexadecimal, octal, and binary literals, numeric
  underscores, and `NaN` / `infinity` literals.
- Invalid numeric literals produce a clear syntax error with a source position.
- Integer literals produce `int`; decimal/scientific literals produce `float`.
- `+`, `-`, `*` follow normal numeric promotion (any `float` operand yields a
  `float`).
- `/` always performs true division and returns a `float`.
- Division by zero raises a clear engine-specific error (`DivisionByZeroError`).
- `%` is not part of v1 and may be considered as a future extension.
- Booleans are **not** numbers: `true == 1` is `false`, `false == 0` is `false`,
  ordering between booleans and numbers is a type error, and arithmetic involving
  booleans is a type error.

## Strings

- Single-quoted and double-quoted strings are supported.
- Supported escapes: `\\`, `\"`, `\'`, `\n`, `\t`, `\r`. Unknown escape sequences
  are errors.
- Ordinary Unicode characters are supported in string literals.
- Out of scope for v1: interpolation, f-strings, raw strings, multiline strings.
- `+` concatenates only when both operands are strings; there is no implicit
  stringification (`"value: " + 1` is a type error).
- String ordering is case-sensitive lexicographic by Unicode code point. Locale-
  aware ordering is out of scope for v1.

## Null and undefined

- Two distinct concepts:
  - **null**: a value that is explicitly present but empty. Represented to
    callers by Python `None`. Internally it may later be normalized to a private
    immutable null sentinel so it stays distinct from undefined.
  - **undefined**: a missing or unavailable value. Represented by the exported
    `UNDEFINED` singleton, which is never Python `None` internally.
- `{"x": None}` (x exists and is null) must remain distinguishable from `{}`
  (x is absent and resolves to `UNDEFINED`).
- A missing variable evaluates to `UNDEFINED` by default rather than raising.
- Equality: `null == null` is true, `undefined == undefined` is true,
  `null == undefined` is false.
- Neither null nor undefined is ever silently converted to `0`.
- Arithmetic and ordering involving null or undefined raise a clear type or
  evaluation error, unless a specific built-in explicitly accepts them.
- Inspection helpers planned: `is_defined(value)`, `is_null(value)`.
- There is a single documented behavior; no strict/lenient modes in v1.

## Variables and scope

- External variables are supplied per evaluation as a mapping and are never
  mutated by the engine.
- Local variables (`let name = expr in body`):
  - the bound expression is evaluated once;
  - the binding is visible only within `body`, not within its own right-hand side;
  - locals may shadow external variables;
  - bindings are immutable; nested `let` is supported;
  - no assignment statements or mutable variables.
  - Scope resolution: outside a binding's `body`, the same identifier is resolved
    again through an outer lexical scope, then caller-provided variables, and
    finally `UNDEFINED`. A free identifier is a valid external-variable reference
    and is never rejected merely because it is not a local binding.

## Functions

- Built-in, registered (host), and local functions all use the same call syntax.
- Resolution order: local (lexical) > registered > built-in.
- Built-in function names are **reserved**: registering a host function or
  defining a local function with a built-in name is rejected (a validation
  error). Local functions may shadow only *registered* functions, within their
  lexical scope.
- Local functions (`let name(params) = expr in body`): named only, positional
  immutable parameters, lexical scope, no recursion in v1, no anonymous or
  higher-order functions, no defaults or variadics.
- Built-in math set for v1: `abs`, `min`, `max`, `round`, `floor`, `ceil`,
  `sqrt`, `pow`, `log`. The Python `math` module and arbitrary attributes are not
  exposed.
  - `log(x)`: natural logarithm only; custom base is out of scope for v1.
  - `pow(x, y)`: both numeric and non-boolean; two integers with a non-negative
    exponent return `int`, otherwise `float`; complex results unsupported;
    invalid domains raise a stable engine error.
  - `round(x)` and `round(x, ndigits)`: `x` numeric non-boolean, `ndigits`
    integer non-boolean; documented half-to-even rounding.
  - `min` / `max`: two or more positional arguments (no iterables in v1);
    arguments must be mutually comparable; fewer than two arguments is an
    arity error.
- Unknown functions, argument counts, argument types, returned values, and
  exceptions raised by user functions are validated/wrapped into engine errors.

## Thread safety

- Compiled expressions are immutable after creation and safe to evaluate
  concurrently from multiple threads with different variable contexts.
- No evaluation-specific state (variables, stacks, intermediate values) is stored
  on a shared compiled expression.
- Global mutable state is avoided; caller-supplied dictionaries are never mutated.

## Performance

- Compilation is separated from evaluation: parse and validate once, then reuse
  an immutable compiled representation for repeated evaluations.
- The hot evaluation path does not tokenize, parse, or rebuild the tree.
- No compilation cache is implemented in v1; a bounded, thread-safe cache is a
  possible later stage once correctness and benchmarks justify it.
- No throughput numbers are claimed without a reproducible benchmark.

## AI-assisted decisions

- All language decisions above were proposed as options by the AI assistant and
  explicitly chosen, corrected, or rejected by the project owner. Notable owner
  corrections include: preserving int/float distinction (no blanket float),
  excluding `%` from v1, requiring `let ... in` local bindings and local
  function definitions, treating booleans as non-numbers, the package naming
  (`expression-evaluation-engine` / `expression_engine`), using
  `setuptools.build_meta`, deferring any compilation cache, and representing
  public null as Python `None` rather than a public `NULL` object.
- This log is maintained so the final one-page write-up can distinguish owner
  decisions from AI suggestions. The final write-up is not authored until the
  implementation decisions are stable.
