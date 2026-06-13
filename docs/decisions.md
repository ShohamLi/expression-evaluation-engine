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

## Parser and AST (Stage 3)

This stage adds a parser and an immutable AST only. No evaluation, `Engine`,
compiled `Expression`, functions, or `let` parsing is included. The AST is a
syntactic representation; it is **not** a compiled expression and does not
implement parse-once compilation. A later stage may wrap it in an immutable
compiled-expression object and reuse it across evaluations.

### Grammar and parser strategy

- A conventional hand-written **recursive-descent** parser, with one small
  method per precedence level. No Pratt parser, parser generator, table-driven
  parser, combinators, or dispatch registry is used.
- Left-associative binary levels are written as iterative loops; recursion is
  used only where it is the natural grammar shape: nested parentheses, repeated
  unary operators, and the right-associative conditional.
- The parser consumes the tokenizer's token sequence (`parse(tokens)`) and does
  not inspect raw source, re-tokenize, or mutate tokens. All mutable state (a
  token reference and an integer cursor) is local to a single-use parser
  instance; no global state and nothing is retained between calls.
- Interface: `parse(tokens: Sequence[Token]) -> Expr` is **internal** and is not
  exported from the package root.

### Precedence and associativity

From lowest binding to highest (one method per level):

1. conditional `value_if_true if condition else value_if_false` — right-assoc;
2. boolean `or` — left-assoc;
3. boolean `and` — left-assoc;
4. comparisons `== != < <= > >=` — non-chaining (at most one);
5. additive `+ -` — left-assoc;
6. multiplicative `* /` — left-assoc;
7. unary `not + -` — binds to the following expression; repeatable;
8. primary — literals, variables, and `( … )` grouping.

`10 - 3 - 2` parses as `(10 - 3) - 2`; `a if b else c if d else e` parses as
`a if b else (c if d else e)`. The `if`-condition and the true-value are parsed
at the `or` level, so a bare conditional in those positions requires
parentheses.

### Chained comparisons

- Chained comparisons such as `a < b < c` are **rejected** with a `ParserError`,
  consistent with the existing "comparisons are non-chaining" decision under
  *Language syntax*. The parser accepts at most one comparison operator and
  raises if a second immediately follows. `1 + + 2` is not a chaining/repeat
  case: it parses as `1 + (+2)` (a unary plus), which is intended.

### AST design and immutability

- Node types: `LiteralExpr`, `VariableExpr`, `UnaryExpr`, `BinaryExpr`,
  `ConditionalExpr`, and `LetExpr` (added in Stage 9), with `Expr` as their
  union. No base class or visitor.
- All nodes are `@dataclass(frozen=True, slots=True)`: immutable after
  construction, no per-instance `__dict__`, and structural equality.
- Nodes reuse existing lexical types instead of duplicating them: operator and
  literal *kinds* are recorded as `TokenType`, and source locations are
  `Position` (from `_tokens`).
- `LiteralExpr.value` stores the tokenizer-provided `Token.value` verbatim as a
  `str` (decoded text for strings, source text for numbers, keyword spelling for
  `true`/`false`/`null`/`undefined`). No conversion to `int`/`float`/`bool`/
  `None`/`UNDEFINED` happens in this stage, consistent with the tokenizer's
  documented deferral of numeric conversion.

### Source-position policy (anchor only)

- Each node stores exactly one **anchor** `Position`, not a full source span:
  - literals and variables: the token's start position;
  - unary nodes: the operator position;
  - binary nodes: the operator position;
  - conditional nodes: the `if` keyword position.
- This is explicitly an anchor policy. A single position cannot reconstruct a
  complete start/end span, especially because redundant parentheses are dropped,
  string tokens hold decoded (not raw) text, and no end offsets are stored. No
  source-span object is introduced in this stage.

### Parentheses

- Parentheses only affect grouping and produce **no** AST node. Redundant
  parentheses are not preserved: `(((1)))` parses to the same node as `1`.

### Error handling

- A small `ParserError(ExpressionSyntaxError)` is added. It mirrors `LexerError`:
  it stores the offending `Position` on `position` and folds line/column into the
  message. `ExpressionSyntaxError` alone was insufficient because it carries no
  position attribute or constructor, would force ad-hoc message formatting at
  each raise site, and would make parse failures indistinguishable from lexer
  failures.
- `ParserError` is added to `expression_engine.errors.__all__`, consistently with
  how `LexerError` is exposed there. This is an additive extension of the
  errors-module surface; it is **not** added to the package-root
  `expression_engine.__init__` API, which is unchanged.
- Malformed parser input is validated once at the `parse()` boundary: the token
  sequence must be non-empty and terminated by an `EOF` token, otherwise a
  `ParserError` is raised. Because an `EOF` sentinel is then guaranteed and the
  parser never advances past it, internal token access cannot raise
  `IndexError`. No re-tokenizing or synthetic lexical layer is introduced.
- Parser errors identify what was expected, what was found (or end-of-input), and
  the relevant source position. Empty input has no dedicated message; it yields
  the standard "expected an expression but reached end of input".

## Evaluator: arithmetic and variables (Stage 4)

This stage adds a single evaluator module (`_evaluator.py`) that walks the
immutable AST and returns a runtime value. It implements only arithmetic and
external variable lookup; comparisons, `not`/`and`/`or`, conditionals, string
operations, null/undefined propagation, `let`, and functions are out of scope.
No `Engine`, compiled `Expression`, cache, or benchmark is added.

### Interface

- `evaluate(node: Expr, variables: Mapping[str, object] | None = None) -> object`
  is **internal** (not exported from the package root), mirroring `tokenize` and
  `parse`. `None` means an empty variable mapping. The evaluator never
  re-tokenizes or re-parses, holds no global state, and never mutates the AST,
  the caller's mapping, or the caller's values.

### Runtime literal values

- integer literal → `int`; float literal → `float`; string literal → its decoded
  `str`; `true`/`false` → `bool`; `null` → `None`; `undefined` → the existing
  `UNDEFINED` singleton. Conversion (previously deferred from the tokenizer) now
  happens here.

### Variable lookup and the missing-variable rule

- A name absent from the mapping evaluates to `UNDEFINED` (`variables.get(name,
  UNDEFINED)`), consistent with the previously approved "missing variable
  evaluates to `UNDEFINED`" decision. A stored `UNDEFINED` value evaluates to the
  same singleton: a missing variable and an explicit `undefined` have different
  origins but the same approved runtime result. Neither is converted to `None`,
  `False`, or `0`. `null`/`None`, `False`, numeric zero, and `UNDEFINED` remain
  distinct values (note that Python still treats `False == 0` as true; the
  guarantee is about distinct objects and types, not `==`).

### Numeric type rule

- Arithmetic accepts only the **exact** built-in numeric types: a value is
  numeric iff `type(value) in (int, float)`. `bool` is therefore not numeric
  (booleans-are-not-numbers, already documented). `isinstance` is deliberately
  not used, so caller-defined `int`/`float` subclasses are rejected and no
  overloaded arithmetic on caller objects is invoked. `Decimal`, `Fraction`,
  NumPy values, and other custom numeric types are unsupported in this stage.
- Strings are never converted to numbers. String `+` concatenation (eventually
  documented for two strings) is **not** implemented in Stage 4 and currently
  raises `ExpressionTypeError`; it will arrive with string operations later.

### Arithmetic semantics

- Unary `+`/`-` and binary `+`/`-`/`*` follow normal Python numeric promotion
  (any `float` operand yields a `float`); integer-only arithmetic stays `int`.
- `/` always performs true division and returns a `float`; a zero divisor
  (`0` or `0.0`) raises `DivisionByZeroError`.
- Binary operands are evaluated left-to-right, then operand types are validated,
  then the result is computed (so a zero check happens only after both operands
  are confirmed numeric).

### Operations outside Stage 4

- `not`, the six comparisons, `and`, `or`, and conditional expressions raise the
  base `ExpressionEvaluationError` with the node's anchor position and **do not
  evaluate their operands** (no partial evaluation or side effects). No
  `UnsupportedOperationError` class is introduced, since those operators are
  planned for later stages.

### Errors and positions

- `ExpressionEvaluationError` gained a backward-compatible constructor: `message`
  is required and `position` is optional. Message-only construction still works;
  when a position is supplied it is stored on `.position` and folded into the
  message (matching `LexerError`/`ParserError`). `ExpressionTypeError` and
  `DivisionByZeroError` inherit this. The package root `expression_engine.__all__`
  is unchanged.
- The evaluator always supplies the relevant AST anchor: the operator position
  for unary, binary, division-by-zero, and unsupported-operation errors, and the
  literal position for literal-conversion errors.
- Numeric literal conversion catches only `ValueError`/`OverflowError` from
  `int()`/`float()` on tokenizer-produced text and reports them as an
  `ExpressionEvaluationError` at the literal position; no broad exception
  handling and no custom numeric parsing.

### Current limitation

- A syntactically valid but extremely large float literal (e.g. `1e400`)
  converts via Python's `float()` to a non-finite value (`inf`); Stage 4 accepts
  that normal Python result rather than adding finite-number validation.

## Comparisons (Stage 5)

This stage adds evaluation for the six comparison operators (`==`, `!=`, `<`,
`<=`, `>`, `>=`) to the existing evaluator. Boolean operators (`and`, `or`,
`not`), conditional expressions, string concatenation, functions, and local
variables remain out of scope. The comparison logic lives inside `_evaluator.py`
(a small `_eval_comparison` reached from `_eval_binary`); no new module, runtime
dependency, or public API surface is added.

- **Result type:** comparisons always return an exact Python `bool`.
- **Evaluation:** the left operand is evaluated before the right, and each
  operand is evaluated exactly once. The caller-provided variables mapping and
  values are never mutated.
- **Numbers:** the exact built-in types `int` and `float` are mutually
  comparable (`1 == 1.0`, `1 < 1.5`, `2.0 >= 2`). Booleans are **not** numbers.
  Ordered comparisons (`<`, `<=`, `>`, `>=`) accept only `int`/`float` operands.
- **Booleans:** equality is defined only within `bool` (`true == true`); a
  boolean is never equal to a number (`true == 1` is `false`, with no coercion).
  Ordered comparison involving a boolean is an `ExpressionTypeError`.
- **Strings:** the exact built-in `str` type supports equality and inequality
  (`"a" == "a"`, `"a" != "b"`). Ordered string comparison (`<`, `<=`, `>`, `>=`)
  is deferred to a later stage and raises `ExpressionTypeError`. There is no
  coercion between strings and numbers.
- **Equality across categories:** equality never coerces between categories.
  Numbers, strings, booleans, `null`, and `undefined` each compare only within
  their own category; any cross-category pair is unequal rather than an error.
- **null / undefined:** `null == null` and `undefined == undefined` are true;
  `null` and `undefined` remain distinct (`null == undefined` is false). A
  missing variable evaluates to `undefined`, so `missing == undefined` is true.
  Ordered comparison involving `null` or `undefined` is an `ExpressionTypeError`.
- **Non-finite floats:** `inf` and `nan` are ordinary floats and follow Python
  IEEE-754 semantics (`nan == nan` is false, `nan < 1` is false, `inf > 1` is
  true). The nan-not-equal-to-itself rule applies only to numbers and does not
  affect `null`/`undefined` equality.
- **Unsupported operands:** caller-provided objects and built-in type subclasses
  (e.g. an `int` or `str` subclass) are rejected with `ExpressionTypeError`
  before any comparison is performed, so their overloaded comparison methods are
  never invoked. This uses exact `type(...)` checks rather than `isinstance`.
- **Errors and positions:** unsupported operand combinations raise
  `ExpressionTypeError` (a subclass of `ExpressionEvaluationError`) anchored at
  the comparison operator's position.
- **Chaining:** chained comparisons remain rejected by the parser (unchanged).

## Boolean operators (Stage 6)

This stage adds evaluation for `not`, `and`, and `or` inside the existing
evaluator. Conditional expressions, string operations, functions, and local
variables remain out of scope; no new module, error class, or public API is
added.

- **Strict Boolean operands:** operands must be the exact built-in `bool` type;
  there is no implicit truthiness. Numbers, strings, `null`, `undefined`, and
  missing variables are never converted to a Boolean and raise
  `ExpressionTypeError` at the operator position when evaluated as an operand.
- **Exact results:** `not`, `and`, and `or` return an exact Python `bool`.
- **Left-to-right, real short-circuit:** the left operand is evaluated first and
  exactly once. `and` returns `False` immediately when the left operand is
  `False`; `or` returns `True` immediately when the left operand is `True`. The
  right operand (and its validation) is skipped entirely when short-circuited,
  so errors inside a skipped operand never occur; when the right operand is
  required, its evaluation errors propagate normally.
- **null / undefined:** never converted to `False`.

## Conditional expressions (Stage 7)

This stage adds evaluation for `value_if_true if condition else value_if_false`
inside the existing evaluator. No new module, error class, or public API is
added.

- **Strict Boolean condition:** the condition must be the exact built-in `bool`
  type; there is no implicit truthiness. Numbers, strings, `null`, `undefined`,
  and missing variables are invalid conditions and raise `ExpressionTypeError`
  at the `if` anchor position.
- **Condition evaluated once.**
- **Selected branch only:** when the condition is `True` only `value_if_true` is
  evaluated; when `False` only `value_if_false` is evaluated. The unselected
  branch is never evaluated or validated.
- **Result returned unchanged:** the selected branch's value (any supported
  type, including `null` and `undefined`) is returned without coercion.

## String concatenation (Stage 8)

- `+` concatenates two exact built-in `str` operands and returns an exact `str`.
- There is no implicit string conversion.
- Mixed string and non-string operands raise `ExpressionTypeError`.
- All other string operations remain unsupported.

## Local bindings: syntax and AST (Stage 9)

- Local binding syntax is `let name = value in body`.
- `let` has the lowest precedence; a `let` used as an operand must be
  parenthesized (`1 + (let x = 2 in x)`; `1 + let x = 2 in x` is a `ParserError`).
- `LetExpr` is immutable (`frozen=True, slots=True`) and anchored at the `let`
  token; `value` and `body` are full expressions, so nested `let` and
  conditionals are allowed in both.
- This stage adds syntax and AST only; evaluation and runtime scope are deferred
  to Stage 10.

## Local bindings: evaluation (Stage 10)

Runtime evaluation for `LetExpr` is one direct branch in `_eval`. `value` is
evaluated first, exactly once, in the outer scope; `body` is then evaluated in a
local scope. Evaluating `value` before building the scope makes the binding
non-recursive (it is invisible inside its own `value`). The scope is
`collections.ChainMap({name: value}, variables)` — a fresh dict layered in front
of the caller mapping; it shadows by lookup order, supports nested
bindings/shadowing by stacking, and restores the outer scope when `body` returns.
A copied dict (copies the whole context per binding) and a custom scope class
(unnecessary abstraction) were both rejected. The caller mapping is only read,
never copied or mutated, and all scope state is local to one `_eval` call, so the
immutable AST holds no shared evaluation state and stays safe for repeated and
concurrent evaluation.

## Function calls: syntax and AST (Stage 11)

- Call syntax is `name(arg0, arg1, ...)`. Only an identifier may be called:
  parenthesized or arbitrary expressions are not callable (`(f)(1)`, `1(2)`),
  and calls do not chain (`f(1)(2)` is a `ParserError`). Keywords are not
  identifiers, so they cannot be function names.
- Calls are parsed in the identifier branch of `_primary` (tightest binding); a
  `(` immediately following an identifier begins the call. No generic
  postfix-expression layer is introduced.
- Arguments are full expressions (parsed via `_expression()`), so arithmetic,
  comparisons, Boolean operators, conditionals, and bare `let` are all valid
  argument forms. Zero-argument calls are allowed; trailing commas are rejected.
- `CallExpr` is immutable (`frozen=True, slots=True`); `arguments` is a
  `tuple[Expr, ...]` (never a mutable list) and `position` is anchored at the
  function identifier. This stage adds syntax and AST only; evaluation stays out
  of scope, so a `CallExpr` reaching the evaluator hits the existing
  unsupported-node error.

## Public compilation API (Stage 12)

This stage adds the public compile-once / evaluate-many API approved in Phase 1.
:meth:`Engine.compile` tokenizes and parses source text once into an immutable
:class:`Expression` that stores a private ``_ast`` field (``field(repr=False)``);
:meth:`Expression.evaluate` calls the existing evaluator only and never
re-tokenizes or re-parses. ``Engine`` is stateless; evaluation keeps all
variable state local to each call, so the same compiled expression is safe for
repeated and concurrent evaluation and caller mappings are never mutated. No
compilation cache, top-level compile alias, validation pass, or function support
is added in this stage. Later stages may add private immutable function-related
state without changing this public workflow.

## Built-in and registered functions (Stages 13–14)

Project-owner decisions for these stages:

- The only registration API is ``Engine(functions=...)``. ``Engine()`` remains
  valid, and the supplied mapping is copied once without being mutated or kept
  by reference. Built-in names are reserved.
- The exact built-in set is ``abs``, ``min``, ``max``, ``round``, ``floor``,
  ``ceil``, ``sqrt``, ``pow``, and natural-log ``log``. Numeric inputs are exact
  built-in ``int``/``float`` values, never ``bool`` or subclasses. ``floor`` and
  ``ceil`` return ``int``; ``sqrt`` and ``log`` return ``float``; non-negative
  integer ``pow`` returns ``int`` and every other supported ``pow`` returns
  ``float``. ``round`` uses Python half-to-even behavior, and ``min``/``max``
  require at least two numeric arguments.
- Function names and positional arity are checked during ``Engine.compile`` in
  every AST branch, including branches that runtime short-circuiting will skip.
  Unknown names raise ``UnknownFunctionError`` and wrong arity raises
  ``FunctionArityError``. Free variable names remain valid.
- Registered callables may have positional-only or positional-or-keyword
  parameters plus trailing defaults. ``*args``, keyword-only parameters,
  ``**kwargs``, and uninspectable signatures are rejected at engine
  construction. Evaluation passes only evaluated positional arguments.
- Registered return values are restricted to exact ``int``, ``float``, ``str``,
  ``bool``, ``None``, and the exported ``UNDEFINED`` singleton. An existing
  ``ExpressionError`` propagates; every other normal callable exception is
  wrapped in a positioned ``ExpressionEvaluationError`` with its cause kept.
- Compiled expressions and registry metadata are immutable and safe to share
  between evaluations. A caller-provided function can still contain mutable or
  non-thread-safe behavior; the library does not make that callable thread-safe.

AI implementation suggestion adopted by the project owner: keep the work in one
focused ``_functions.py`` module. The engine stores an immutable registry
snapshot, and compilation creates an immutable mapping from each ``CallExpr``
to resolved function metadata. Evaluation therefore performs no name lookup,
signature inspection, tokenization, or parsing.

Alternatives explicitly rejected by the project owner: global registration,
dynamic attribute access such as ``getattr(math, name)``, runtime signature
inspection, arbitrary Python execution, and local-function resolution in these
stages.

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
- Stage 3 (parser and AST): the owner directly required the recursive-descent
  strategy, the precedence/associativity table, rejecting chained comparisons,
  the five-node AST, frozen `slots=True` dataclasses, the anchor-position policy
  (and the correction that anchors are not full spans), parentheses as grouping
  only, deferring literal conversion, the conditional `ParserError` (only if
  justified), keeping it out of the package root, and boundary validation of
  malformed token input. The AI proposed the concrete grammar wording, the reuse
  of `TokenType`/`Position` on nodes, naming the literal field `value` to match
  `Token.value`, and the specific error messages; the owner approved these.
  Parsing `+ - * /`, parentheses, variables, booleans, `and`/`or`, the ternary
  conditional, and strings is required directly by the assignment; the comparison
  operator set, precedence details, and non-chaining behavior are
  repository-specific decisions since the assignment leaves them unspecified.
