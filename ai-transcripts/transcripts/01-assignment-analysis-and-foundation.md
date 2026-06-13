# Assignment Analysis and Project Foundation

- **Tool:** Cursor
- **Project:** Expression Evaluation Engine
- **Transcript type:** English submission copy
- **Editing applied:** Project title and speaker headings normalized; meaningful Hebrew fragments translated faithfully; obvious keyboard noise and repeated export boilerplate removed; local paths redacted where present.
- **Integrity note:** No prompt, answer, result, decision, or missing conversation was invented.

---

## User Prompt

Read the attached assignment PDF and inspect the current repository.

This is an analysis-only task. Do not create, edit, delete, rename, or format any files. Do not write implementation code.

Analyze the assignment and propose a focused implementation plan for a Python Expression Evaluation Engine.

Cover:

1. All explicit requirements from the PDF.
2. Ambiguous requirements that require a candidate decision.
3. A minimal and clean public API.
4. Expression syntax and operator precedence.
5. Compilation versus evaluation.
6. Null versus undefined semantics.
7. Boolean, comparison, short-circuit, and conditional semantics.
8. String behavior and supported string operations.
9. The smallest reasonable interpretation of defining and using variables inside expressions.
10. The smallest reasonable interpretation of defining and invoking custom functions.
11. Thread-safety requirements.
12. Error categories and useful error messages.
13. Performance strategy for repeated evaluation.
14. A proposed package and test structure.
15. Features that should remain outside the project scope.
16. A sequence of small implementation stages.

For every ambiguous requirement:

* Present no more than two reasonable alternatives.
* Explain the trade-offs.
* Recommend the smallest production-oriented choice.
* Do not silently assume Python behavior without documenting it.

Important constraints:

* Do not recommend eval() or exec().
* Do not claim unmeasured performance numbers.
* Do not modify any files.
* Do not implement anything.
* Do not commit or push.

End with a concise section titled:


“Decisions requiring candidate approval”
this is the assigment attcedBackend Home Assignment — Expression Evaluation Engine
The task: Build a library that evaluates expressions like 2 + 3 * (x - 1) against a
provided set of named variables. Picture our product letting data scientists define
computed variables and logics using these expressions. Feel more than free to use
claude and/or other ai tools for this assignment.
Context — please read carefully:
This engine is going to run millions of times per second in production, usually for
similar expressions.
We plan to open-source it once it’s mature.
Other backend teams in the company will pull it as a dependency.
Make sure we support booleans and conditional operators like: ternary if,and, or, etc ..
Make sure expressions can also handle strings.
Allow to define and use variables inside expressions.
Support +, -, *, /, parentheses, and variable lookup. We’d also like common math
operations available.
Support defining and using functions inside expressions.
It should be thread-safe
Null and undefined values are handled throughout evaluation.
What to submit:
Working code. Choose from either python or go.
A short write-up (max 1 page (.
How did you approach this? What did you decide vs. what did the AI decide? Some
instructions are vague by design, tell us what you decided and why.
Describe the library. How to use it, and what kind of features and expressions it
supports.
Your AI chat transcripts. Whatever you used. If your tool stores them locally (e.g., a
CLI agent), share whatever you have.
Design answer (½ page max). A data scientist complains: “for some reason my
expressions always evaluates to 0 but it does not make any sense, what’s going on?”
Put on a product manager hat. What feature would you propose to help them? Don’t
build it — just write the proposal.

---

## Cursor Response

I'll start by inspecting the repository to understand the current state.

I've inspected the repository. Here's what's there:

- A clean Git repo on `main` with a single commit that only adds `.gitignore`.
- A `.venv` with **Python 3.11.13** (only `pip` installed — no project deps, no test framework yet despite a `.pytest_cache` directory existing).
- No source code, no `pyproject.toml`, no PDF file in the tree. The assignment content lives only in your message, so I'm analyzing against that text.

Below is the analysis-only implementation plan. **No files were created or changed.**

---

# Expression Evaluation Engine — Implementation Plan

## 1. Explicit requirements (from the assignment text)

These are stated directly and are non-negotiable:

| # | Requirement | Source phrasing |
|---|---|---|
| R1 | Evaluate infix expressions like `2 + 3 * (x - 1)` | "evaluates expressions like 2 + 3 * (x - 1)" |
| R2 | Evaluate against a **provided set of named variables** | "against a provided set of named variables" |
| R3 | Arithmetic operators `+ - * /` and **parentheses** | "Support +, -, *, /, parentheses" |
| R4 | **Variable lookup** | "and variable lookup" |
| R5 | **Common math operations** available | "We'd also like common math operations available" |
| R6 | **Booleans** and conditional operators: **ternary if, `and`, `or`**, etc. | "support booleans and conditional operators like: ternary if, and, or" |
| R7 | **Strings** in expressions | "expressions can also handle strings" |
| R8 | **Define and use variables inside expressions** | "Allow to define and use variables inside expressions" |
| R9 | **Define and use functions inside expressions** | "Support defining and using functions inside expressions" |
| R10 | **Thread-safe** | "It should be thread-safe" |
| R11 | **Null and undefined** handled throughout evaluation | "Null and undefined values are handled throughout" |
| R12 | Optimized for **millions of evals/sec, similar expressions repeated** | "run millions of times per second... usually for similar expressions" |
| R13 | Library quality: open-sourceable, consumable as a dependency by other teams | "open-source it once it's mature... pull it as a dependency" |
| R14 | Python or Go — **Python chosen** | "Choose from either python or go" |
| R15 | Deliverables: working code, ≤1-page write-up, AI transcripts, ½-page design answer | "What to submit" |

The implied non-functional consequence of R12 + R13 is the single most important design driver: **separate one-time parse/compile cost from per-evaluation cost**, and keep compiled artifacts immutable so they are safely shareable across threads (ties to R10).

## 2. Ambiguous requirements requiring a candidate decision

Each is expanded with options/trade-offs/recommendation in the relevant section below, and summarized at the end. The genuinely ambiguous points:

- **A1.** Division semantics (`/`): float vs integer vs decimal; division by zero behavior.
- **A2.** Number model: Python `float`/`int` duality, or unify to float, or expose `Decimal`.
- **A3.** What "define variables inside expressions" means (the vaguest requirement).
- **A4.** What "define functions inside expressions" means (also very vague).
- **A5.** Null vs undefined: how to model two distinct concepts in Python, which has only `None`.
- **A6.** Truthiness rules for `and`/`or`/ternary — Python-native vs strict-boolean.
- **A7.** Equality/comparison across mixed types (e.g. `1 == "1"`, `null == undefined`).
- **A8.** String operation surface (concatenation, comparison, indexing, methods?).
- **A9.** Scope of "common math operations".
- **A10.** Error behavior on unknown variable: raise vs treat as `undefined`.

## 3. Minimal, clean public API

The smallest API that satisfies R1–R13 while making the compile/eval split explicit:

```python
from expreval import Engine, Expression, EvalError, ParseError

engine = Engine()  # holds registered functions + config; immutable after build

# Compile once (parse + validate). Returns an immutable, thread-safe object.
expr: Expression = engine.compile("2 + 3 * (x - 1)")

# Evaluate many times with different variable bindings.
result = expr.evaluate({"x": 5})        # -> 14

# Convenience one-shot (compiles internally; not for hot paths).
result = engine.evaluate("x > 0 ? 'pos' : 'neg'", {"x": 3})
```

Design points:
- `Engine` is a **builder/registry** (custom functions, config such as division mode). Once constructed it is read-only; this is what other teams import and share.
- `Expression` is the **compiled artifact**: immutable AST + metadata. `evaluate(variables: Mapping)` is pure and reentrant — the core of thread-safety (R10) and the repeat-eval performance story (R12).
- Variables are passed **per evaluation** as a plain mapping. The compiled expression carries no mutable per-call state.
- Errors are a small, documented exception hierarchy (Section 12).
- Keep the public surface to ~4 names. Everything else (lexer, parser, AST nodes) is private (`expreval._internal`).

Recommended smallest choice: **two public types (`Engine`, `Expression`) plus the exception classes.** Avoid exposing the AST publicly in v1 — it is the largest future-compatibility liability.

## 4. Expression syntax and operator precedence

Grammar (recursive-descent / Pratt parser — **not** `eval`/`exec`):

- **Literals:** integers, floats, strings (single and/or double quotes), `true`, `false`, `null`. (`undefined` arises from missing variables rather than a literal — see Section 6.)
- **Identifiers:** variable names and function names (`[A-Za-z_][A-Za-z0-9_]*`).
- **Calls:** `name(arg, arg, ...)`.
- **Grouping:** `( ... )`.

Proposed precedence (high → low), a conventional and least-surprising ordering:

| Level | Operators | Assoc |
|---|---|---|
| 1 | unary `-`, unary `!`/`not` | right |
| 2 | `*`, `/`, `%` | left |
| 3 | `+`, `-` | left |
| 4 | `<`, `<=`, `>`, `>=` | left |
| 5 | `==`, `!=` | left |
| 6 | `and` / `&&` | left |
| 7 | `or` / `\|\|` | left |
| 8 | `?:` ternary | right |

Ambiguity to flag: support **word operators (`and`/`or`/`not`)**, **symbol operators (`&&`/`\|\|`/`!`)**, or both. Word operators read naturally for data scientists and match the assignment's wording; symbols are familiar to backend engineers. Recommendation: **accept word forms as canonical and symbol forms as aliases** — small lexer cost, broad familiarity. (Document explicitly; this is a deviation from "pure Python syntax.")

## 5. Compilation vs evaluation

This is the central performance design (R12) and must be explicit:

- **Compile phase** (`engine.compile`): tokenize → parse to AST → validate (arity of known functions, syntax). Done once per unique expression string. Produces an immutable `Expression`.
- **Evaluate phase** (`expr.evaluate(vars)`): a tree-walk over the prebuilt AST. No string work, no re-parsing.

Two reasonable interpretations:
- **(a) Tree-walking interpreter** over an immutable AST.
- **(b) Compile-to-Python-closures** ("closure compilation"): each node returns a `lambda vars: ...`, composed bottom-up so evaluation is a chain of native calls with no per-node dispatch branching.

Trade-off: (a) is simpler to write, debug, and reason about; (b) typically reduces per-eval overhead by removing the `isinstance`/dispatch on every node, at the cost of more complex code and harder debugging. Both keep the compiled artifact immutable and thread-safe.

Recommendation: **Ship (a) first (correct, simple, clearly thread-safe). Keep the AST behind the public API so (b) can be added later without an API break.** Do not assert any speedup number until measured (Section 13). Pair the compile step with a **bounded `compile` cache** keyed by expression string so repeated identical expressions skip parsing entirely — this directly serves "usually for similar expressions."

## 6. Null vs undefined semantics

Python has only `None`, but the assignment names **both** "null and undefined" (R11), so they must be distinguished deliberately.

- **null** = an explicit, known absent value (literal `null` in source, or a variable explicitly bound to it).
- **undefined** = a variable that was **referenced but not provided** in the bindings map.

Two options:
- **(a) Collapse both to a single sentinel** (one "missing" value). Simplest, but loses the distinction the assignment explicitly calls out.
- **(b) Two distinct singleton sentinels** (`NULL`, `UNDEFINED`), both falsy, with documented propagation rules.

Recommendation: **(b)** — it is the smallest design that honors R11's explicit wording. Use module-level singletons (cheap identity checks, naturally immutable → thread-safe). Map Python `None` passed in bindings to `null`. Propagation rule to document: arithmetic/string ops on `null`/`undefined` produce a **typed error** by default (not silent 0/empty) — this is directly relevant to the "always evaluates to 0" design question in the assignment, and "silently coercing missing values to 0" is exactly the anti-pattern that causes it.

Must document explicitly (do not silently assume): whether `null == undefined` is `true`. Recommendation: **`false`** (they are different concepts), but `x == null` is the supported "is it absent-explicit" check. Flag for approval.

## 7. Boolean, comparison, short-circuit, conditional semantics

- **Booleans:** `true`/`false` literals; `and`, `or`, `not`.
- **Short-circuit:** `and`/`or` must short-circuit (left operand decides whether right is evaluated) — important for both performance and avoiding errors (`x != null and x > 0`).
- **Ternary:** `cond ? a : b`, only the taken branch is evaluated.
- **Comparison:** `< <= > >= == !=`.

Ambiguity — **truthiness** (A6):
- **(a) Python-native truthiness:** `0`, `""`, `null`, `undefined` are falsy; everything else truthy.
- **(b) Strict booleans:** non-boolean condition in `and`/`or`/`?:` is a type error.

Trade-off: (a) is permissive and convenient but is precisely the class of behavior that produces silent surprises (e.g., empty string treated as false). (b) is safer and more predictable for a shared library but more verbose for users.

Recommendation: **(b) strict-ish with a narrow, documented exception** — booleans required for logical operators and ternary conditions, but `null`/`undefined` are treated as falsy *only* in the conditional position so guard patterns work. Document this precisely. Flag for approval.

Ambiguity — **cross-type comparison** (A7): `1 == "1"`. Recommendation: **no implicit cross-type equality** (different types ⇒ `==` is `false`, `!=` is `true`); ordering comparisons across incompatible types raise a type error. Avoids Python 2-style surprises. Flag for approval.

## 8. String behavior and supported operations

- **Literals:** quoted strings; document escape handling (at minimum `\\`, `\"`/`\'`, `\n`, `\t`).
- **Operations (smallest useful set):**
  - `+` = concatenation **only when both operands are strings** (no implicit number↔string coercion — that coercion is another classic source of silent bugs).
  - Comparisons `==`/`!=` and ordering `< <= > >=` (lexicographic).
  - Membership/length/case via **functions**, not operators: `len(s)`, `lower(s)`, `upper(s)`, `contains(s, sub)`, `startswith`, `concat(...)`. Keeping string ops as named functions keeps the operator grammar tiny.

Ambiguity (A8): expose rich string methods/indexing/slicing vs a minimal function set. Recommendation: **minimal function set above**; defer slicing/regex. Explicitly document that `1 + "x"` is an error, not `"1x"`.

## 9. "Define and use variables inside expressions" — smallest reasonable interpretation

This is the vaguest requirement (A3). The phrase could mean anything from "read provided variables" to "a full `let` binding sub-language."

Three readings, narrowing:
- **(i) Maximal:** assignment statements / multi-statement programs with mutable state. → Turns the library into a mini-language; large scope, mutable state fights thread-safety. **Reject.**
- **(ii) Middle:** `let`-style local bindings within a single expression: `let y = x - 1 in 2 + 3 * y`. Pure, no external mutation, composes with everything, stays a single expression.
- **(iii) Minimal:** "use variables" = variable **lookup** from the provided bindings (R2/R4), and "define variables" is satisfied by the caller supplying the bindings map plus, optionally, named sub-expressions registered on the `Engine`.

Recommendation: **(iii) as the v1 baseline, with (ii) `let ... in ...` as the smallest in-expression "define" if reviewers expect literal in-expression definition.** Both are pure and immutable-friendly. Lead with (iii); call out (ii) as a clearly-scoped add. Flag which interpretation is expected — this is the biggest scope swing in the assignment.

## 10. "Define and invoke custom functions" — smallest reasonable interpretation

Also vague (A4). Two distinct meanings:
- **(a) Host-registered functions:** Python callables registered on the `Engine` (`engine.register("max", fn, arity=...)`) and **invoked** from expressions: `max(x, 0)`. This covers "common math operations" (R5) too — they're just preregistered builtins.
- **(b) In-expression function definitions:** user defines a function within the expression language itself (lambda/`def`-like).

Trade-off: (a) is small, safe (host controls exactly what's callable — important for an open-source dependency), and immutable once the engine is built (thread-safe). (b) requires closures, the language's own scoping, and substantially more surface and risk, with weaker safety guarantees.

Recommendation: **(a) registration + invocation as the primary, production-oriented interpretation.** Treat "common math" as a default registry (`abs, min, max, floor, ceil, round, sqrt, pow, log, ...`). Optionally allow lightweight **named expression aliases** (`engine.define("disc", "b*b - 4*a*c")`) as the "define a function" gesture without a full closure system. Flag (b) as out of v1 unless reviewers require true in-language definitions.

Security note: registered functions must be **explicit and host-controlled**; never expose arbitrary Python attribute access or import. (Reinforces the no-`eval`/no-`exec` constraint.)

## 11. Thread-safety requirements (R10)

Strategy — achieve safety by **immutability**, not locks:
- `Expression` (compiled AST) is immutable; `evaluate` is a pure function of `(ast, vars)` with no shared mutable state → safe to call concurrently from any number of threads.
- `Engine` is frozen after construction (function registry is read-only post-build). Registration happens at setup time, not during evaluation.
- The only shared mutable structure is the optional **compile cache**; guard it with a lock or use a lock-free/`functools.lru_cache`-style structure. The cache must never leak per-evaluation state.
- Per-call data (the variables map, intermediate values, the recursion stack) lives only on the calling thread's stack.

Document explicitly: the **caller's `variables` mapping** must not be mutated by the engine, and the engine assumes the caller doesn't mutate it mid-evaluation. Note GIL caveat honestly: the GIL serializes bytecode but does **not** make arbitrary multi-step state updates atomic — so the immutability design stands on its own and is not relying on the GIL.

## 12. Error categories and useful messages

A small, documented exception hierarchy (consumable by dependent teams):

```
ExprError (base)
├── ParseError      # lexing/parsing/syntax problems (compile time)
│     └── carries position (column/offset) + offending token
├── ValidationError # known-function arity/name errors (compile time)
└── EvalError       # runtime
      ├── UndefinedVariableError  # referenced var not in bindings
      ├── TypeMismatchError       # e.g. 1 + "x", ordering null
      ├── DivisionByZeroError
      └── UnknownFunctionError / ArityError
```

Message quality (matters for the "always 0" design answer and for an OSS library):
- Include the **expression text**, a **caret/position** pointer for parse errors, the **offending symbol**, and for runtime errors the **operand types** involved.
- Example: `TypeMismatchError: cannot apply '+' to number and string at column 5 in "x + 'a'"`.
- Distinguish "undefined variable" from "null value" in messages so the absent-vs-empty distinction is visible to users.

Decision to flag (A10): on referencing a missing variable — **raise `UndefinedVariableError`** vs **return `undefined`**. Recommendation: **raise by default**, with an optional engine flag `on_missing="undefined"` for users who want lenient propagation. Defaulting to raising directly prevents the silent "evaluates to 0" failure mode.

## 13. Performance strategy for repeated evaluation (R12)

Concrete, **measured-later** strategy (no unquantified claims):
- **Compile once / evaluate many** is the primary lever (Section 5).
- **Bounded compile cache** keyed on expression string (+ engine identity) so "similar/repeated expressions" skip parse entirely.
- Keep `evaluate` allocation-light: avoid building new dicts/lists per node; resolve variable lookups directly against the passed mapping.
- Consider **closure-compilation** (Section 5b) as a later optimization, gated behind benchmarks.
- Provide a **`benchmarks/` harness** (e.g. `pytest-benchmark` or a simple timing script) so any performance claim in the write-up is backed by numbers on a stated machine/Python version. **Do not state throughput figures until this harness produces them.**
- Micro-choices to validate, not assume: `__slots__` on AST nodes, precomputing constant subtrees (constant folding at compile time), interning operator dispatch.

I will not claim any specific ops/sec; the assignment's "millions/sec" is the target to verify, not a result to assert.

## 14. Proposed package and test structure

```
expression-evaluation-engine/
├── pyproject.toml              # packaging, deps, ruff/mypy/pytest config
├── README.md                   # usage + supported features (R13/R15 deliverable)
├── WRITEUP.md                  # ≤1 page: approach, human-vs-AI decisions
├── DESIGN_ANSWER.md            # ≤½ page: "always evaluates to 0" PM proposal
├── src/expreval/
│   ├── __init__.py             # public API: Engine, Expression, errors
│   ├── engine.py               # Engine (registry/config/compile + cache)
│   ├── expression.py           # Expression (immutable compiled artifact)
│   ├── errors.py               # exception hierarchy
│   ├── _lexer.py               # tokenizer (private)
│   ├── _parser.py              # Pratt/recursive-descent parser (private)
│   ├── _ast.py                 # immutable node types (private)
│   ├── _eval.py                # tree-walk evaluator (private)
│   └── _builtins.py            # default math/string functions, null/undefined
├── tests/
│   ├── test_arithmetic.py
│   ├── test_precedence.py
│   ├── test_booleans_ternary.py
│   ├── test_strings.py
│   ├── test_null_undefined.py
│   ├── test_variables.py
│   ├── test_functions.py
│   ├── test_errors.py
│   ├── test_thread_safety.py   # concurrent evaluate() of shared Expression
│   └── test_api.py
└── benchmarks/
    └── bench_eval.py
```

(Listing only — **not** creating these.) Note: the repo already has a `.pytest_cache` and `.venv`; `pyproject.toml`, `src/`, and `tests/` do not yet exist.

## 15. Out of scope (explicitly excluded for v1)

- `eval`/`exec` or any dynamic Python execution (hard constraint).
- Arbitrary attribute access, imports, or filesystem/network from expressions.
- A full statement language / loops / mutable assignment / multi-statement programs.
- User-defined closures/recursion in-language (Section 10b) unless reviewers require it.
- Regex, slicing, rich string method surface, date/time types.
- Decimal/BigInt configurability beyond one documented number model.
- Async evaluation, distributed/JIT compilation, bytecode emission.
- Pluggable grammars / custom operator definition by users.

## 16. Sequenced implementation stages (small, shippable steps)

1. **Skeleton + packaging:** `pyproject.toml`, package layout, error hierarchy stubs, `Engine`/`Expression` signatures. Tests run green-empty.
2. **Lexer:** numbers, strings, identifiers, operators, parens; position tracking. Unit tests.
3. **Parser → AST:** arithmetic + parentheses with the precedence table; `ParseError` with carets.
4. **Tree-walk evaluator (numeric):** `+ - * /`, unary minus, division-by-zero policy. Decide number/division model (A1/A2) here.
5. **Variables:** lookup against bindings; `UndefinedVariableError` and the `on_missing` flag.
6. **Booleans/comparison/short-circuit/ternary:** truthiness policy (A6), cross-type policy (A7).
7. **Null & undefined:** singletons, propagation/error rules, `== null` semantics (A5).
8. **Strings:** literals/escapes, concatenation rule, comparisons.
9. **Function registry + builtins:** registration, arity validation, default math/string functions (R5, Section 10a).
10. **Compile cache:** bounded cache keyed on source.
11. **Thread-safety tests:** concurrent evaluation of a shared compiled `Expression`.
12. **Benchmarks:** harness + record numbers for the write-up (no claims before this).
13. **Docs/deliverables:** `README`, `WRITEUP`, `DESIGN_ANSWER`.
14. *(Optional, gated)* closure-compilation backend; `let ... in`; in-language function defs — only if reviewers want them.

---

## Decisions requiring candidate approval

These are the ambiguous points where I need your sign-off before implementation; for each I list the two reasonable options and my recommended smallest production choice:

1. **Division & numbers (A1/A2):** float-based arithmetic (`/` always float, `%` for modulo, `DivisionByZeroError` on `/0`) **[recommended]** vs preserve Python int/float duality. *Approve: float model + raise on `/0`.*
2. **"Define variables in expressions" scope (A3):** variable **lookup from provided bindings** as v1 **[recommended]** vs add `let x = ... in ...` local bindings. *Approve which interpretation reviewers expect.*
3. **"Define functions in expressions" scope (A4):** **host-registered** Python functions invoked from expressions (+ optional named expression aliases) **[recommended]** vs true in-language function/closure definitions. *Approve registration-only for v1.*
4. **Null vs undefined (A5):** two distinct falsy singletons with `null != undefined` **[recommended]** vs a single "missing" sentinel. *Approve two-sentinel model.*
5. **Missing-variable behavior (A10):** **raise `UndefinedVariableError` by default**, opt-in lenient `undefined` **[recommended]** vs default-lenient. *Approve raise-by-default (prevents the silent "always 0" failure).*
6. **Truthiness (A6):** strict-ish — booleans required for logic/ternary, with `null`/`undefined` allowed as falsy in conditional position **[recommended]** vs full Python truthiness. *Approve strict-ish.*
7. **Cross-type comparison (A7):** no implicit coercion (`1 == "1"` → `false`; cross-type ordering errors) **[recommended]** vs Python-style coercive comparison. *Approve no-coercion.*
8. **String `+` (A8):** concatenation only when both operands are strings; `1 + "x"` is an error **[recommended]** vs implicit stringification. *Approve no-implicit-coercion.*
9. **Operator spelling (Section 4):** accept both word (`and/or/not`) and symbol (`&&/||/!`) forms **[recommended]** vs words-only. *Approve dual spelling.*
10. **"Common math operations" surface (A9):** a fixed default set (`abs, min, max, round, floor, ceil, sqrt, pow, log`) **[recommended]** — please confirm the list, or extend it.

I have not written, created, edited, or committed anything — this is purely the analysis and plan. Tell me which of the above to lock in (or adjust), and I can proceed to implementation in the staged order when you're ready.

---

## User Prompt

Lock in the following design decisions. Do not implement anything yet. First update the proposed design and implementation plan according to these decisions.

1. Numeric model

Do not convert every numeric value to float.

Preserve integer and floating-point literals as separate numeric types:

* integer literals produce int values;
* decimal literals produce float values;
* mixed int/float arithmetic follows normal numeric promotion;
* `/` always performs true division and returns a float;
* division by zero raises a clear engine-specific evaluation error;
* booleans must not be treated as numbers, even though Python bool is a subclass of int.

Do not add `%` in the initial language version because it is not explicitly required by the assignment. It may be documented as a possible future extension.

2. Variables defined inside expressions

External variable lookup alone is not sufficient because the assignment separately asks to define and use variables inside expressions.

Support minimal immutable local bindings using one documented syntax:

`let name = expression in expression`

Example:

`let total = price * quantity in total + shipping`

Required semantics:

* the bound expression is evaluated once;
* the local variable is available only in the expression after `in`;
* local variables may shadow external variables;
* local bindings never mutate the caller-provided variable dictionary;
* bindings are immutable;
* nested `let` expressions are supported;
* using a local variable outside its scope is invalid;
* assignment statements and mutable variables are not supported.

3. Functions defined inside expressions

Host-side function registration alone is not sufficient to satisfy the wording of the assignment.

Support a minimal local named-function definition using syntax consistent with local bindings:

`let function_name(parameter1, parameter2) = expression in expression`

Example:

`let discount(price, rate) = price * (1 - rate) in discount(total, 0.1)`

Keep the feature intentionally limited:

* named functions only;
* positional parameters only;
* immutable parameters;
* lexical scope;
* no anonymous functions;
* no higher-order functions;
* no mutation;
* no recursion in the initial version;
* no default or variadic parameters.

Also support host-registered functions through the public engine API. Built-in, registered, and local functions should use the same call syntax, but their precedence and name-collision rules must be documented.

Local functions should shadow registered functions only within their lexical scope. Overriding built-in functions should be rejected.

4. Null and undefined

Use two distinct concepts:

* `null` represents an explicitly present value with no value;
* `undefined` represents a missing variable or unavailable value.

Internally, undefined should use a dedicated singleton and must not be represented by Python `None`.

Define the following equality semantics:

* `null == null` is true;
* `undefined == undefined` is true;
* `null == undefined` is false.

Do not silently convert either value to 0.

Arithmetic and ordering operations involving null or undefined should raise a clear type or evaluation error unless a specific built-in function explicitly accepts them.

5. Missing-variable behavior

A missing variable should evaluate to the `undefined` singleton by default rather than immediately raising `UndefinedVariableError`.

This is necessary so undefined is a real first-class value that can be inspected with functions such as:

* `is_defined(value)`
* `is_null(value)`

Examples:

* `is_defined(missing_variable)` should return false;
* `missing_variable == undefined` should return true;
* `missing_variable + 1` should raise a clear evaluation error.

Do not add strict and lenient modes in the initial version unless there is a strong implementation reason. One clear, documented behavior is preferable to multiple modes.

6. Boolean and conditional semantics

Use strict, explicitly documented boolean semantics.

Boolean positions accept only:

* boolean values;
* null;
* undefined.

Treat null and undefined as false in boolean and conditional positions.

Numbers and strings are not implicitly truthy or falsy. Using them directly as conditions should raise a type error.

Required behavior:

* `and`, `or`, and `not` return boolean values;
* `and` and `or` use real short-circuit evaluation;
* a conditional expression evaluates only the selected branch;
* the unselected branch must not produce side effects or errors.

7. Comparisons

Use no implicit coercion between unrelated types.

Required behavior:

* int and float values may be compared numerically;
* strings may be compared with strings;
* booleans may be compared with booleans;
* equality between unrelated types returns false;
* ordering between unrelated types raises a type error;
* `1 == "1"` is false;
* `"1" < 2` is an error;
* null and undefined follow the explicit equality rules above;
* ordering involving null or undefined is an error.

8. String addition

Use `+` for string concatenation only when both operands are strings.

Examples:

* `"hello " + name` is valid when name is a string;
* `"value: " + 1` raises a type error.

Do not perform implicit stringification.

9. Operator spelling and conditional syntax

Use one small, consistent syntax.

Support only the word forms:

* `and`
* `or`
* `not`

Do not support `&&`, `||`, or `!` in the initial version.

Use Python-style conditional-expression syntax:

`value_if_true if condition else value_if_false`

This keeps the language familiar to data scientists and avoids unnecessary duplicate syntax.

10. Common mathematical functions

Use the following fixed built-in set for the initial version:

* `abs`
* `min`
* `max`
* `round`
* `floor`
* `ceil`
* `sqrt`
* `pow`
* `log`

Do not expose the Python `math` module or arbitrary attributes.

Validate argument counts and types explicitly and convert underlying Python errors into clear engine-specific errors.

Do not add additional mathematical functions until the required set is implemented, tested, and documented.

11. General scope constraints

Do not silently inherit Python behavior merely because the implementation is written in Python.

The expression language must explicitly document:

* grammar;
* precedence;
* associativity;
* supported types;
* local-variable scope;
* local-function scope;
* built-in and registered function resolution;
* null and undefined behavior;
* type errors;
* syntax errors;
* short-circuit behavior.

Do not implement code yet.

First return:

1. The updated language decisions.
2. The proposed grammar.
3. The precedence table.
4. The public API proposal.
5. The exact scope of local variables and functions.
6. The updated staged implementation order.
7. Any remaining decisions that still require my approval.

Do not create, edit, rename, or delete files.
Do not commit or push.


---

## Cursor Response

Locked in. No files created, edited, or committed — this is the updated plan reflecting your 10 decisions, organized into the seven sections you asked for.

---

# Expression Evaluation Engine — Updated Design (Decisions Locked)

## 1. Updated language decisions

**Numeric model**
- Integer literals → `int`; decimal literals → `float`. No blanket float conversion.
- Mixed `int`/`float` arithmetic follows normal numeric promotion (result is `float` when any operand is `float`).
- `+ - *` preserve type per promotion; `/` is **always true division → `float`** (even `4 / 2` → `2.0`).
- Division by zero (`/` with a `0`/`0.0` divisor) raises `DivisionByZeroError`.
- `bool` is **not** a number: even though Python `bool` subclasses `int`, `true`/`false` are rejected in arithmetic and numeric comparison positions.
- `%` is **excluded** from v1; documented as a possible future extension.

**Local variables (`let … in`)**
- Syntax: `let name = expr in body`.
- The bound expression is evaluated **once**; `name` is visible only inside `body`.
- Locals may shadow caller-provided (external) variables.
- Bindings are immutable; the caller's variable dict is never mutated.
- Nested `let` supported; using a local outside its `body` scope is a parse/scope error.
- No assignment statements, no mutable variables.

**Local functions (`let name(params) = expr in …`)**
- Syntax: `let f(a, b) = expr in body`.
- Named functions only; positional, immutable parameters; lexical scope.
- No anonymous functions, no higher-order functions, no mutation, **no recursion** in v1, no default/variadic params.
- Host-registered functions supported via the public API; built-in, registered, and local functions share the **same call syntax**.
- Resolution & collision rules: **local (lexical) > registered > built-in**. Local functions shadow registered functions only within their lexical scope. **Registering or locally redefining a built-in name is rejected** (see open item 7.3 for the local-vs-builtin nuance).

**Null vs undefined**
- Two distinct, immutable singletons.
- `undefined` uses a dedicated sentinel and is **never** Python `None` internally.
- Equality: `null == null` → true; `undefined == undefined` → true; `null == undefined` → false.
- Neither is silently coerced to `0`.
- Arithmetic/ordering involving `null`/`undefined` raises a clear type/eval error unless a specific built-in explicitly accepts them.

**Missing-variable behavior**
- A missing variable evaluates to the `undefined` singleton (no immediate raise).
- First-class inspection via `is_defined(value)` and `is_null(value)`.
- `is_defined(missing)` → false; `missing == undefined` → true; `missing + 1` → clear `EvalError`.
- **Single documented behavior** — no strict/lenient modes in v1.

**Boolean & conditional semantics (strict)**
- Boolean positions accept only `bool`, `null`, `undefined`. `null` and `undefined` are treated as **false** in boolean/conditional positions.
- Numbers and strings are **not** implicitly truthy/falsy; using them as a condition is a type error.
- `and`, `or`, `not` return booleans; `and`/`or` short-circuit; conditional evaluates only the selected branch (unselected branch produces no error/side effect).

**Comparisons (no implicit coercion)**
- `int`↔`float` compared numerically; `string`↔`string`; `bool`↔`bool`.
- Equality between unrelated types → false (`1 == "1"` → false); ordering between unrelated types → type error (`"1" < 2` → error).
- `null`/`undefined` follow the explicit equality rules; **ordering** involving them is an error.
- Comparisons are **non-associative / non-chaining** in v1 (`a < b < c` is a parse error; use parentheses) — chosen explicitly rather than inheriting Python's chaining.

**String addition**
- `+` concatenates only when **both** operands are strings. `"value: " + 1` → type error. No implicit stringification.

**Operator spelling & conditional syntax**
- Word forms only: `and`, `or`, `not`. No `&&`, `||`, `!`.
- Python-style conditional: `value_if_true if condition else value_if_false`.

**Built-in math functions (fixed v1 set)**
- `abs, min, max, round, floor, ceil, sqrt, pow, log`.
- No exposure of Python's `math` module or arbitrary attributes.
- Argument counts/types validated explicitly; underlying Python errors converted to engine-specific errors.
- No additional math functions until this set is implemented, tested, documented.

**General scope constraint**
- Nothing is silently inherited from Python. Grammar, precedence, associativity, types, local-variable scope, local-function scope, function resolution, null/undefined behavior, type errors, syntax errors, and short-circuit behavior are all explicitly documented.

## 2. Proposed grammar (EBNF)

```
expression      := let_expr | conditional

let_expr        := "let" binding "in" expression
binding         := func_binding | var_binding
var_binding     := IDENT "=" expression
func_binding    := IDENT "(" [ params ] ")" "=" expression
params          := IDENT ( "," IDENT )*

conditional     := or_expr [ "if" or_expr "else" expression ]

or_expr         := and_expr ( "or" and_expr )*
and_expr        := not_expr ( "and" not_expr )*
not_expr        := "not" not_expr | comparison

comparison      := additive [ comp_op additive ]          # non-associative
comp_op         := "==" | "!=" | "<" | "<=" | ">" | ">="

additive        := multiplicative ( ( "+" | "-" ) multiplicative )*
multiplicative  := unary ( ( "*" | "/" ) unary )*
unary           := "-" unary | primary

primary         := NUMBER | STRING
                 | "true" | "false" | "null" | "undefined"
                 | call
                 | IDENT
                 | "(" expression ")"
call            := IDENT "(" [ args ] ")"
args            := expression ( "," expression )*

IDENT           := [A-Za-z_][A-Za-z0-9_]*
NUMBER          := INT | FLOAT          # INT: digits; FLOAT: digits "." digits (see open item 7.1 re: exponent)
STRING          := quoted, with documented escapes (see open item 7.2)
```

Notes baked into the grammar:
- `let` is an expression form (everything is an expression; no statements).
- The conditional's *condition* is parsed as `or_expr`, so `a if b else c` reads naturally and `b` cannot itself be a bare conditional without parentheses.
- `comparison` is single/non-chaining by design.
- Both `let name = …` and `let name(params) = …` share the `let … in` frame.

## 3. Precedence table

Loosest binding (top) → tightest binding (bottom):

| Level | Construct | Form | Associativity |
|------:|-----------|------|---------------|
| 1 | local binding | `let … in …` | prefix, body extends right |
| 2 | conditional | `A if C else B` | right (nesting via `else`) |
| 3 | logical or | `or` | left, short-circuit |
| 4 | logical and | `and` | left, short-circuit |
| 5 | logical not | `not` (unary) | right |
| 6 | comparison | `== != < <= > >=` | **non-associative** |
| 7 | additive | `+ -` | left |
| 8 | multiplicative | `* /` | left |
| 9 | unary minus | `-` | right |
| 10 | call / grouping / atoms | `f(...)`, `( … )`, literals, identifiers | — |

This intentionally follows Python's relative ordering for `or < and < not < comparison`, with comparison non-chaining as the one documented deviation.

## 4. Public API proposal

```python
from expreval import Engine, Expression, NULL, UNDEFINED
from expreval.errors import (
    ExprError, ParseError, ValidationError, EvalError,
    TypeMismatchError, DivisionByZeroError,
    UnknownFunctionError, ArityError,
)

engine = Engine()                      # registry + config; frozen after setup

# Register host functions. Rejects collisions with built-ins (ValidationError).
engine.register("clamp", lambda lo, hi, x: max(lo, min(hi, x)), arity=3)

# Compile once: tokenize -> parse -> validate. Immutable, thread-safe.
expr: Expression = engine.compile("let total = price * qty in total + shipping")

# Evaluate many times; pure function of (compiled AST, variables).
expr.evaluate({"price": 10, "qty": 3, "shipping": 5})   # -> 35

# Convenience one-shot (compiles internally; not for hot paths).
engine.evaluate("x + 1 if is_defined(x) else 0", {"x": 41})   # -> 42
```

Surface:
- **`Engine`** — function registry + config; immutable after construction. `register(name, fn, *, arity)`; `compile(source) -> Expression`; `evaluate(source, variables)` convenience. Holds the bounded compile cache.
- **`Expression`** — immutable compiled artifact. `evaluate(variables: Mapping) -> value`. Reentrant/thread-safe; never mutates `variables`.
- **`NULL`, `UNDEFINED`** — exported singletons so callers can construct/inspect these values in bindings and results.
- **Exception hierarchy** under `expreval.errors` (see below).
- Built-in functions (`abs … log`, plus `is_defined`, `is_null`) are preregistered and **cannot** be overridden via `register`.

Error hierarchy:

```
ExprError
├── ParseError        # lexing/syntax/scope-at-parse (carries position + token)
├── ValidationError   # arity/name issues at compile, builtin-override rejection
└── EvalError         # runtime
      ├── TypeMismatchError       # 1 + "x", "1" < 2, arithmetic on null/undefined,
      │                           # non-bool in boolean position
      ├── DivisionByZeroError
      ├── UnknownFunctionError
      └── ArityError
```

(Missing variables do **not** raise here — they produce `UNDEFINED`.)

## 5. Exact scope of local variables and functions

**Local variables (`let x = e in body`)**
- `x` is in scope **only** within `body`, not within `e` (the binding's own right-hand side).
- Lexical/static scope: visibility determined by nesting, resolved at parse time.
- Shadowing: an inner `let x = …` or a local `x` shadows an outer local or an external (caller) variable named `x`, only within its `body`.
- Resolution order for an identifier used as a **value**: innermost local binding → … → outer local binding → caller-provided variable → otherwise `UNDEFINED`.
- Immutable: no rebinding/assignment; each `let` introduces a fresh, read-only binding.
- The bound value is computed exactly once, before `body` is evaluated.

**Local functions (`let f(a, b) = fexpr in body`)**
- `f` is callable **only** within `body`. In v1, `f` is **not** visible inside its own `fexpr` (no recursion).
- Parameters `a, b` are in scope only inside `fexpr`, are positional and immutable, and shadow outer variables/locals of the same name within `fexpr`.
- Lexical capture: `fexpr` may reference variables/functions visible at the function's **definition** site (lexical scope), not the call site.
- Function-name resolution for a call `g(...)`: innermost local function `g` → outer local function `g` → registered function `g` → built-in `g` → else `UnknownFunctionError`.
- Local functions may shadow **registered** functions within their lexical scope. Built-ins cannot be overridden (open item 7.3 clarifies whether a *local* `let abs(...)` is rejected outright or merely shadows within scope).
- Arity is fixed by the parameter list; calling with the wrong count → `ArityError`. No defaults, no variadics.

## 6. Updated staged implementation order

1. **Skeleton + packaging:** `pyproject.toml`, `src/expreval/` layout, error hierarchy, `Engine`/`Expression` signatures, `NULL`/`UNDEFINED` singletons.
2. **Lexer:** numbers (int vs float), strings + escapes, identifiers, keywords (`let in if else and or not true false null undefined`), operators, parens, commas; position tracking.
3. **Parser → immutable AST:** full grammar incl. `let` var/func bindings, Python conditional, non-chaining comparison; `ParseError` with carets; static scope checks (use-before-scope, unknown local).
4. **Evaluator core — numeric:** int/float preservation, promotion, true-division → float, `DivisionByZeroError`, unary minus, bool-is-not-number guard.
5. **Variables & external lookup:** resolution chain ending in `UNDEFINED`; never mutate caller dict.
6. **Null/undefined model:** singletons, equality rules, arithmetic/ordering errors, `is_defined`/`is_null`.
7. **Booleans/comparison/conditional (strict):** boolean-position type checks, null/undefined-as-false rule, short-circuit `and`/`or`/`not`, `A if C else B` single-branch evaluation; comparison rules + no-coercion + ordering errors.
8. **Strings:** literals/escapes, string-only `+`, string comparisons.
9. **`let` local variables:** binding evaluation-once, scoping, shadowing, nesting, immutability.
10. **Functions:** registry + arity validation; built-in set (`abs, min, max, round, floor, ceil, sqrt, pow, log`) with explicit type/arity checks and error wrapping; local `let f(...) = …`; resolution/collision/override rules.
11. **Compile cache:** bounded cache keyed on source (+ engine identity).
12. **Thread-safety tests:** concurrent `evaluate` of a shared `Expression`.
13. **Benchmarks harness:** `benchmarks/` for later, measured claims (no numbers asserted before this).
14. **Docs/deliverables:** `README`, `WRITEUP` (≤1 page), `DESIGN_ANSWER` (≤½ page).

## 7. Remaining decisions requiring your approval

These are not yet pinned and would otherwise force me to silently inherit Python behavior:

**7.1 Numeric literal forms.** Allow exponent/scientific notation (`1e3`, `2.5e-4`) and a leading-dot/trailing-dot form (`.5`, `5.`)? Recommendation: **support exponent notation; require a digit on both sides of `.` (`0.5`, not `.5`); decimal base only (no hex/octal/binary, no underscores).** Approve or restrict further.

**7.2 String literal details.** Which quotes and escapes? Recommendation: **both `'…'` and `"…"`; escapes `\\ \" \' \n \t \r`; no f-strings/interpolation, no multiline.** Approve or adjust the escape set.

**7.3 Local redefinition of a built-in name.** "Overriding built-ins is rejected" clearly covers `engine.register`. For a **local** `let abs(x) = … in …`: (a) reject at parse time, or (b) allow it to shadow `abs` only within that lexical scope (consistent with how locals shadow registered functions)? Recommendation: **(a) reject** — keeps built-in semantics globally stable and predictable. Approve (a) or (b).

**7.4 `log` signature.** `log(x)` natural log only, or also `log(x, base)`? Recommendation: **`log(x)` = natural log (base e) only in v1**; base variant deferred. Approve or request two-arg form.

**7.5 `pow` and `round` semantics.** (a) `pow(x, y)` — return type by promotion (`pow(2, 3)` → int `8`, `pow(2.0, 3)` → float)? (b) `round(x)` vs `round(x, ndigits)`, and half-to-even (Python banker's rounding) vs half-away-from-zero? Recommendation: **`pow` by numeric promotion; `round(x)` and `round(x, ndigits)` both supported; document Python's banker's rounding rather than changing it.** Approve or specify half-up.

**7.6 `min`/`max` arity.** Fixed 2-arg, or variadic (`min(a, b, c, …)`, ≥2 args)? No iterables exist in the language. Recommendation: **variadic with ≥2 args.** Approve or fix at 2.

**7.7 String ordering.** "Strings may be compared with strings" — confirm this includes **ordering** (`<`, `<=`, …) via lexicographic (Unicode code-point) order, not just equality. Recommendation: **yes, lexicographic ordering allowed.** Approve.

**7.8 `bool` vs number comparison.** Given "booleans compared only with booleans" and "no coercion": `true == 1` → false (unrelated types), and `true < 2` → type error. Confirm this is the intended consequence (it is internally consistent with your rules).

Tell me which of 7.1–7.8 to lock (or how to adjust), and I'll fold them into the final spec before any implementation begins.

---

## User Prompt

I am attaching the original PDF for a backend take-home assignment:
“Backend Home Assignment — Expression Evaluation Engine”.

Read the entire PDF carefully before proposing or changing any code.

Your role is to help me implement the assignment in Python while preserving my
ownership of the design and decisions. The final submission should look like a
focused, production-oriented open-source Python library, not a demo script and
not a web service.

General project rules:

1. Treat the attached PDF as the primary source of truth.
2. Before every implementation task, inspect the existing repository,
   architecture, public API, tests, documentation, and coding conventions.
3. Do not begin coding before explaining:
   - what the task requires;
   - which files are likely to change;
   - the smallest reasonable implementation approach;
   - important assumptions or ambiguities.
4. Make focused and minimal changes.
5. Do not rewrite unrelated files.
6. Do not add unnecessary abstractions, classes, helper functions,
   configuration, dependencies, or design patterns.
7. Do not overengineer the solution.
8. Do not add FastAPI, a REST API, a database, Docker infrastructure,
   a user interface, or external services unless explicitly required.
9. This project must be a reusable Python library with a clean public API.
10. Do not use eval(), exec(), or any mechanism that can execute arbitrary
    Python code from an expression.
11. Preserve backward compatibility with the existing public API unless the
    current task explicitly requires a change.
12. Do not commit, push, merge, or open a pull request unless I explicitly ask.
13. Do not modify unrelated configuration, generated files, lock files, or
    formatting across the whole project.
14. Do not hide implementation problems with broad try/except blocks.
15. Do not silently ignore errors or automatically convert missing values to 0.

Architecture and performance requirements:

1. Optimize for the use case described in the PDF: the same or similar
   expressions are evaluated repeatedly at very high throughput.
2. Separate expression compilation from expression evaluation.
3. Parse and validate an expression once, then reuse an immutable compiled
   representation for repeated evaluations.
4. Do not tokenize, parse, or rebuild the expression tree during every
   evaluation.
5. Keep the hot evaluation path small and avoid unnecessary allocations,
   copies, recursion, and temporary data structures where practical.
6. Do not claim “millions of evaluations per second” without a reproducible
   benchmark.
7. Measure compilation and repeated compiled evaluation separately.
8. Any expression cache must have clear ownership, bounded growth, and
   thread-safe behavior.
9. Do not optimize prematurely at the expense of correctness, clarity,
   security, or maintainability.

Thread-safety requirements:

1. The same compiled expression must be safe to evaluate concurrently from
   multiple threads with different variable contexts.
2. Compiled expressions should be immutable after creation.
3. Never store evaluation-specific variables, stacks, intermediate values,
   or mutable state on a shared compiled expression.
4. Avoid global mutable state.
5. Do not mutate the dictionary or objects supplied by the caller.
6. Function registries, caches, and other shared structures must either be
   immutable during evaluation or protected appropriately.
7. Add focused concurrent tests where thread safety is relevant.

Expression-language requirements:

The implementation should support the requirements from the PDF, including:

- numeric values;
- +, -, *, and /;
- unary operators where appropriate;
- parentheses;
- named-variable lookup;
- booleans;
- boolean operators such as and, or, and not;
- comparison operators needed for conditional expressions;
- conditional or ternary expressions;
- strings and documented string operations;
- defining and using variables inside expressions;
- common mathematical functions;
- registering and invoking custom functions;
- null values;
- undefined values;
- repeated evaluation;
- thread-safe execution.

Do not assume Python semantics automatically. The expression language must have
explicit and documented behavior.

For every language feature, define and test:

1. Syntax.
2. Operator precedence.
3. Associativity.
4. Supported operand types.
5. Return type.
6. Invalid input behavior.
7. Interaction with null.
8. Interaction with undefined.
9. Interaction with short-circuit evaluation.
10. Clear error behavior.

Correctness requirements:

1. Implement correct operator precedence and associativity.
2. Implement lazy short-circuit behavior:
   - false and <expression> must not evaluate the right side;
   - true or <expression> must not evaluate the right side.
3. Conditional expressions must evaluate only the selected branch.
4. Do not perform undocumented implicit conversions between unrelated types.
5. Arithmetic between incompatible types should produce a clear engine error.
6. Invalid expressions must not leak internal exceptions such as IndexError,
   KeyError, AttributeError, or parser implementation errors.
7. Error messages should contain useful information and source positions where
   practical.
8. Do not return a default numeric value when evaluation fails unless such
   behavior is explicitly designed, documented, and requested.

Null and undefined requirements:

1. Treat null and undefined as separate concepts.
2. A variable that exists with a null value must be distinguishable from a
   variable that does not exist.
3. Centralize null and undefined semantics instead of scattering checks
   throughout the evaluator.
4. Explicitly define and test their behavior in:
   - variable lookup;
   - equality and inequality;
   - arithmetic;
   - boolean conditions;
   - and/or/not;
   - conditional expressions;
   - built-in functions;
   - custom functions;
   - local variable definitions;
   - returned results.
5. Do not silently convert null or undefined to 0.
6. Any propagation or error behavior must be consistent and documented.

Variables and functions:

1. Clearly distinguish external variables from variables defined locally
   inside an expression.
2. Local definitions must not mutate the caller’s variable dictionary.
3. Define variable scope, shadowing, redefinition, and use-before-definition
   behavior.
4. Detect or reject invalid and circular definitions if the selected syntax
   allows them.
5. Keep the syntax for local definitions focused and documented.
6. Prefer a clear registration API for custom functions rather than building
   a full programming language unless the PDF or an explicit decision requires
   otherwise.
7. Define whether custom functions may override built-in functions.
8. Validate unknown functions, argument counts, invalid argument types,
   returned values, and exceptions raised by user functions.
9. Do not expose unsafe Python objects or arbitrary attributes to expressions.

Code-quality requirements:

1. Use clear names and small, focused functions.
2. Add type hints to new interfaces and meaningful internal code.
3. Add docstrings to public classes, functions, methods, exceptions, and
   important public values.
4. Add comments only when explaining a non-obvious decision, invariant,
   security restriction, performance consideration, or edge case.
5. Do not add comments that merely repeat what the code already says.
6. Follow the existing code style.
7. Prefer standard-library solutions where they are sufficient.
8. Keep internal parser and evaluator details private where possible.
9. Expose a small, stable, and intuitive public API.
10. Use a small and useful exception hierarchy rather than generic Exception
    everywhere.

Testing requirements:

1. Use pytest unless the existing project uses another testing framework.
2. Test through the public API whenever possible.
3. Do not modify existing tests merely to make an incorrect implementation pass.
4. Do not delete or weaken tests.
5. Every bug fix should include a regression test.
6. Cover both successful behavior and failure behavior.
7. Include tests for:
   - arithmetic precedence and associativity;
   - parentheses;
   - unary operators;
   - numeric edge cases;
   - division by zero;
   - variables;
   - missing variables;
   - strings;
   - escaping and Unicode where supported;
   - booleans;
   - comparisons;
   - and/or/not;
   - short-circuit evaluation;
   - conditional expressions;
   - evaluation of only the selected branch;
   - local variable definitions;
   - null;
   - undefined;
   - built-in math functions;
   - custom functions;
   - invalid function arguments;
   - invalid syntax;
   - useful error messages;
   - repeated evaluation of one compiled expression;
   - concurrent evaluation of one compiled expression;
   - input objects remaining unchanged.
8. Keep performance benchmarks separate from normal correctness tests.
9. Avoid flaky tests and timing assumptions.

Documentation requirements:

The README should eventually explain:

- what the library does;
- installation;
- a minimal usage example;
- the public API;
- compilation and repeated evaluation;
- supported syntax;
- operator precedence;
- supported types;
- strings;
- booleans and conditionals;
- external and local variables;
- built-in math functions;
- custom functions;
- null and undefined semantics;
- exceptions and error examples;
- thread-safety guarantees;
- performance design;
- benchmark instructions;
- known limitations;
- how to run tests.

Submission requirements:

1. Preserve material needed for the required AI transcripts.
2. Clearly distinguish:
   - decisions I made;
   - suggestions produced by AI;
   - suggestions I rejected or modified;
   - code and behavior I manually verified.
3. Help maintain concise notes during development so they can later be used in
   the maximum one-page write-up.
4. Do not write the final one-page document until the implementation decisions
   are stable.
5. Do not implement the product-design feature requested on page 2 of the PDF.
   It requires only a written proposal of up to half a page.
6. The product proposal should focus on helping a data scientist understand why
   an expression evaluates to 0, for example through an opt-in expression
   explanation or evaluation trace, without affecting the production hot path.

Before completing every task:

1. Review the diff for unrelated or unnecessary changes.
2. Check that the implementation matches the attached PDF.
3. Check whether the behavior introduces an undocumented language decision.
4. Check security, thread safety, null/undefined behavior, and repeated
   evaluation.
5. Run the relevant tests.
6. Run formatting, linting, and type checking only if those tools are already
   configured or were intentionally selected for the project.
7. Do not conceal failed validation.

At the end of every task, report:

1. What was implemented.
2. Which files changed.
3. Why this approach was selected.
4. Which decisions were mine and which suggestions came from AI.
5. Which edge cases are covered.
6. Which assumptions were made.
7. What remains unsupported or outside the current scope.
8. The exact validation commands that were run.
9. The exact results, including failures or warnings.
10. Do not commit or push.

---

## Cursor Response

I'll re-inspect the repository state before anything else, per your operating rules.

Repository re-inspected — unchanged since last turn and effectively a clean slate:

- Only `.gitignore`, `.venv` (Python 3.11.13, just `pip`), `.pytest_cache`, and a `.DS_Store`.
- No `pyproject.toml` / `setup.*`, no `src/`, no `tests/`, no `README.md`.
- Git: clean working tree, single commit (`ce0a325 Create .gitignore`), branch `main` tracking `origin/main`.

So there is **no existing public API, tests, or conventions to preserve yet** — the backward-compatibility and "follow existing style" rules become binding from the first commit onward, not retroactively.

## Operating contract — acknowledged

I've absorbed the full ruleset and will treat the PDF as source of truth. Concretely, for this project I will:

- Keep it a **reusable library with a small public API** (`Engine`, `Expression`, `NULL`, `UNDEFINED`, a focused exception hierarchy) — no FastAPI/REST/DB/Docker/UI, no `eval`/`exec`.
- **Separate compile from evaluate**; immutable compiled `Expression`; no re-parsing on the hot path; thread-safety via immutability; bounded, owned, thread-safe compile cache.
- Centralize **null/undefined** semantics in one place; never coerce missing values to `0`; never mutate the caller's dict.
- Explicitly document every language feature (syntax, precedence, associativity, operand/return types, invalid-input behavior, null/undefined/short-circuit interaction, errors) and test it through the public API.
- Wrap internal failures so invalid expressions never leak `IndexError`/`KeyError`/`AttributeError`; no broad `try/except` masking; no swallowed errors.
- Keep development notes distinguishing **my decisions vs. AI suggestions vs. rejected/modified vs. manually verified**, for the transcript and the ≤1-page write-up (written only once decisions are stable).
- **Not** implement the page-2 product feature — only a ≤½-page proposal (opt-in evaluation trace / "why is this 0?" explanation, off the production hot path).
- Not commit, push, merge, or open PRs unless you explicitly ask.

## Status before I write any code

Two things gate the start of implementation:

1. **No explicit "begin coding" instruction in this message.** This message established the working agreement; it didn't name a task. Per your rule "do not begin coding before explaining," I've prepared the explanation for the natural first task (Stage 1) below and am asking for your go-ahead rather than assuming it.
2. **Open language items 7.1–7.8 from my previous message are still unanswered.** They don't block Stage 1 (packaging/skeleton), but they must be resolved before Stages 2–10. My recommended defaults, restated compactly so you can approve in one shot:
   - **7.1** Numbers: decimal base only; exponent notation allowed (`1e3`); require digits on both sides of `.`; no hex/underscores.
   - **7.2** Strings: both `'…'` and `"…"`; escapes `\\ \" \' \n \t \r`; no interpolation/multiline; full Unicode in literals.
   - **7.3** A local `let abs(x)=…` that shadows a **built-in** is **rejected** (built-ins globally stable); locals may shadow only *registered* functions.
   - **7.4** `log(x)` = natural log only in v1.
   - **7.5** `pow` by numeric promotion; `round(x)` and `round(x, ndigits)`; document Python banker's rounding (don't change it).
   - **7.6** `min`/`max` variadic, ≥2 args.
   - **7.7** String ordering allowed, lexicographic by Unicode code point.
   - **7.8** `bool` vs number: `true == 1` → false (unrelated types); `true < 2` → type error.

## Pre-implementation explanation — Stage 1 (skeleton + packaging)

Per your rule 3, before coding I'll explain the first task:

- **What it requires:** a minimal installable library skeleton: `pyproject.toml` (build backend, project metadata, pinned dev tooling — `pytest`, and since style must be "followed," I'd select `ruff` + `mypy` now so the convention exists from commit one), a `src/expreval/` package exposing the public names as typed stubs/docstrings (no logic yet), the exception hierarchy, the `NULL`/`UNDEFINED` singletons, and an empty `tests/` + `benchmarks/` layout.
- **Files likely to be created:** `pyproject.toml`, `README.md` (stub), `src/expreval/__init__.py`, `src/expreval/errors.py`, `src/expreval/engine.py`, `src/expreval/expression.py`, `src/expreval/_values.py` (the null/undefined singletons — centralized), and placeholder `tests/`. No existing files modified except possibly adding entries the `.gitignore` already covers (it already covers `dist/`, `build/`, caches — so likely **no** `.gitignore` change needed).
- **Smallest reasonable approach:** `src/`-layout, standard-library + `pytest`/`ruff`/`mypy` only; signatures and docstrings first so the public API is locked and importable before any evaluator logic lands. No abstractions beyond the four public types + exceptions.
- **Assumptions/ambiguities:** I'll choose package name `expreval`, build backend `hatchling`, and target Python ≥3.11 (matching your venv) unless you prefer otherwise — these are reversible naming/tooling defaults, flagging rather than silently assuming.

## What I need from you to proceed

- Approve (or amend) the **7.1–7.8** defaults above.
- Confirm the **tooling/naming defaults** (package name `expreval`, `hatchling`, `ruff`+`mypy`+`pytest`, Python ≥3.11).
- Say **"start Stage 1"** (or tell me a different first task), since no implementation instruction was included in this message.

I have not created, edited, renamed, deleted, committed, or pushed anything.

---

## User Prompt

The remaining language decisions are approved as follows, and you may now start Stage 1 after applying the corrections below.

## Approved decisions

### 7.1 Numeric literals

* Decimal integers and decimal floating-point literals are supported.
* Scientific notation such as `1e3`, `2.5e-4`, and `1E6` is supported.
* Decimal points require digits on both sides: `0.5` is valid; `.5` and `5.` are invalid.
* Hexadecimal, octal, binary, numeric underscores, NaN, and infinity literals are outside v1.
* Invalid numeric literals must produce a clear parse error with a source position.

### 7.2 Strings

* Support both single-quoted and double-quoted strings.
* Support `\\`, `\"`, `\'`, `\n`, `\t`, and `\r`.
* Ordinary Unicode characters are supported.
* Unknown escape sequences are errors.
* No interpolation, f-strings, raw strings, or multiline strings in v1.

### 7.3 Built-in function names

Built-in function names are reserved.

Reject both:

* host-function registration using a built-in name;
* local function definitions using a built-in name.

The rejection should eventually be a clear compile-time validation error.

### 7.4 `log`

Support `log(x)` only, as the natural logarithm.

A custom logarithm base is outside v1.

### 7.5 `pow` and `round`

For `pow(x, y)`:

* both arguments must be numeric and not boolean;
* two integer arguments with a non-negative exponent return an integer;
* otherwise, the result is a float;
* complex results are not supported;
* invalid domains produce a stable engine-specific error.

For `round`:

* support `round(x)` and `round(x, ndigits)`;
* `x` must be numeric and not boolean;
* `ndigits` must be an integer and not boolean;
* use documented half-to-even rounding.

### 7.6 `min` and `max`

* Support two or more positional arguments.
* Do not support iterable arguments in v1.
* Arguments must be mutually comparable under the engine's explicit type rules.
* Fewer than two arguments eventually produce `ArityError`.

### 7.7 String ordering

Support case-sensitive lexicographic ordering by Unicode code point between two strings.

Locale-aware ordering is outside v1.

### 7.8 Booleans versus numbers

* Booleans are not numbers.
* `true == 1` is false.
* `false == 0` is false.
* Ordering between booleans and numbers is a type error.
* Arithmetic involving booleans is a type error.

## Corrections to your Stage 1 proposal

### Package naming

Use:

* distribution/project name: `expression-evaluation-engine`;
* Python import package: `expression_engine`.

Do not use `expreval`.

Future imports should resemble:

```python
from expression_engine import Engine, Expression, UNDEFINED
```

### Build tooling

Use a standard `src` layout and `setuptools.build_meta`.

Target Python 3.11 or newer.

For Stage 1, add only `pytest` as an optional development dependency.

Do not add Ruff, mypy, Hatchling, parser libraries, or runtime dependencies in this stage. They may be considered later only when justified.

### Compilation cache

Do not implement or advertise a compilation cache in Stage 1.

The required performance model is initially:

```python
compiled = engine.compile(source)
result = compiled.evaluate(variables)
```

A bounded thread-safe cache is a possible later stage, after correctness and benchmarks justify it.

### Public null representation

Python `None` is the caller-facing representation of explicit null.

Internally, the evaluator may later convert `None` to a private immutable null sentinel so it remains distinct from undefined.

Missing values use the exported `UNDEFINED` singleton.

The following inputs must remain distinguishable:

```python
{"x": None}  # x exists and is null
{}           # x is absent and resolves to UNDEFINED
```

Do not require callers to construct or import a public `NULL` object.

### Do not create fake public APIs

Do not create placeholder `Engine` or `Expression` classes whose methods only raise `NotImplementedError`.

Public APIs should be introduced when their first real behavior is implemented and tested.

Stage 1 should create a valid, installable, importable package without pretending that expression compilation already works.

## Start Stage 1 now: package bootstrap only

Implement only the initial project structure.

Create:

* `pyproject.toml`
* `README.md`
* `src/expression_engine/__init__.py`
* `src/expression_engine/errors.py`
* `src/expression_engine/_values.py`
* `tests/test_package.py`
* `docs/decisions.md`
* `ai-transcripts/README.md`

Do not create files merely to hold future placeholders.

Do not create the lexer, parser, AST, evaluator, engine, expression class, function registry, cache, or benchmark implementation yet.

## Stage 1 requirements

### `pyproject.toml`

Configure:

* `setuptools.build_meta`;
* `src` package discovery;
* Python `>=3.11`;
* project metadata;
* an optional `dev` dependency containing only pytest;
* pytest configuration if useful.

Do not add runtime dependencies.

### Package

The package must import successfully:

```python
import expression_engine
```

Expose only functionality that is genuinely implemented in this stage.

### Error hierarchy

Add a small documented exception hierarchy that later stages can use:

* `ExpressionError`
* `ExpressionSyntaxError`
* `ExpressionValidationError`
* `ExpressionEvaluationError`
* `ExpressionTypeError`
* `DivisionByZeroError`
* `UnknownFunctionError`
* `FunctionArityError`

Keep it simple. Do not add unused behavior beyond the exception definitions.

### Values

Implement the immutable `UNDEFINED` singleton.

Requirements:

* it must be distinguishable from Python `None`;
* it must have a clear `repr`;
* callers must not be able to create multiple independent undefined values through the public API;
* do not implement arithmetic or truthiness semantics yet;
* do not expose a public `NULL` singleton.

### README

Add a concise initial README that accurately states:

* this is a reusable Python expression-evaluation library under development;
* Python 3.11 or newer is required;
* how to install it in editable mode;
* how to run tests;
* no expression-language features should be claimed as implemented yet.

### Decisions document

Create headings for recording:

* language syntax;
* numeric semantics;
* null and undefined;
* variables and scope;
* functions;
* thread safety;
* performance;
* AI-assisted decisions.

Record the approved decisions concisely. Do not write the final one-page assignment write-up yet.

### AI transcripts

Explain where raw AI conversations or exported transcripts will be stored for submission.

Do not copy or fabricate transcripts in this stage.

### Tests

Add focused tests verifying:

* the package imports successfully;
* `UNDEFINED` is a singleton;
* `UNDEFINED` is distinct from `None`;
* its representation is stable;
* the documented exception classes inherit from the intended base classes.

## Validation

After implementation, run:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -c "import expression_engine; print(expression_engine.__file__)"
git diff --check
git status
```

Do not commit or push.

At the end report:

1. Every created or modified file.
2. What was implemented.
3. What was deliberately left out.
4. Exact commands executed.
5. Exact results, including warnings or failures.
6. Confirmation that no parser, evaluator, cache, Engine, or Expression implementation was added.
7. Confirmation that no commit or push was performed.

Start Stage 1 now and do not continue to Stage 2.


---

## Cursor Response

Decisions approved and corrections noted. Starting Stage 1 (package bootstrap only). Let me set up a task list and create the files.

Now creating the files.

I included an unused import. Fixing that.

Now let me check for lint issues on the new files, then run validation.

Now running the validation commands. The editable install needs PyPI access for `pytest`.

Install succeeded. Now the remaining validation commands.

All validation passed.

Stage 1 complete. Stopping here as instructed (not continuing to Stage 2).

## 1. Files created or modified

All **created** (no existing files modified):

- `pyproject.toml`
- `README.md`
- `src/expression_engine/__init__.py`
- `src/expression_engine/errors.py`
- `src/expression_engine/_values.py`
- `tests/test_package.py`
- `docs/decisions.md`
- `ai-transcripts/README.md`

## 2. What was implemented

- **`pyproject.toml`**: `setuptools.build_meta` backend, `src` package discovery (`[tool.setuptools.packages.find] where = ["src"]`), `requires-python = ">=3.11"`, project metadata, an optional `dev` extra containing **only** `pytest`, no runtime dependencies, and a small `[tool.pytest.ini_options]` (`testpaths = ["tests"]`).
- **Error hierarchy** (`errors.py`): `ExpressionError` base; `ExpressionSyntaxError`, `ExpressionValidationError`, `ExpressionEvaluationError` under it; `ExpressionTypeError` and `DivisionByZeroError` under `ExpressionEvaluationError`; `UnknownFunctionError` and `FunctionArityError` under `ExpressionValidationError`. Definitions only, no extra behavior. The validation-vs-evaluation classification is documented in the module docstring.
- **`UNDEFINED`** (`_values.py`): a single immutable sentinel (`__slots__ = ()`, enforced singleton via `__new__`), `repr` == `"UNDEFINED"`, distinct from `None`, and preserved as the same object across copy/deepcopy/pickle. No arithmetic or truthiness defined. No public `NULL`.
- **Public API** (`__init__.py`): exports only `UNDEFINED`, the eight exception classes, and `__version__`. `Engine`/`Expression` are deliberately **not** exported.
- **README / decisions.md / ai-transcripts/README.md**: accurate status (nothing claimed as working beyond this stage), all approved language decisions recorded concisely, and the transcript-collection location/process documented without fabricating transcripts.
- **Tests**: import success, `UNDEFINED` singleton/`None`-distinctness/stable repr/immutability/copy-pickle identity, and the full error-inheritance relationships.

## 3. What was deliberately left out

No lexer, parser, AST, evaluator, `Engine`, `Expression`, function registry, compilation cache, or benchmarks. No placeholder classes raising `NotImplementedError`. No Ruff/mypy/Hatchling/parser libraries/runtime deps. No `NULL` object. No `.gitignore` change (it already covers build/dist/caches).

## 4. Exact commands executed

```bash
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -c "import expression_engine; print(expression_engine.__file__)"
git diff --check
git status
```

(Run via the project venv's interpreter, i.e. `python -m pip` / `python -m pytest`.)

## 5. Exact results

- **Editable install**: `Successfully built expression-evaluation-engine` and `Successfully installed expression-evaluation-engine-0.0.0 ... pytest-9.0.3`. One non-fatal notice: pip 24.0 → upgrade available (informational only).
- **pytest**: `9 passed in 0.04s` (Python 3.11.13, pytest 9.0.3, configfile `pyproject.toml`, testpaths `tests`).
- **import**: `[PROJECT_ROOT]/src/expression_engine/__init__.py`.
- **`git diff --check`**: clean, exit 0 (no whitespace errors).
- **`git status`**: working tree has only the new untracked files (`README.md`, `ai-transcripts/`, `docs/`, `pyproject.toml`, `src/`, `tests/`); nothing staged or committed.
- Linter check on `src/` and `tests/`: no errors.

## 6. Confirmation — no engine internals added

Confirmed: no parser, lexer, AST, evaluator, compilation cache, `Engine`, or `Expression` implementation was added. Only packaging, the exception hierarchy, the `UNDEFINED` sentinel, docs, and tests exist.

## 7. Confirmation — no commit or push

Confirmed: nothing was committed, pushed, merged, or opened as a PR. The working tree is untracked-only on `main`.

Stage 1 is ready for your review. I will not proceed to Stage 2 until you say so.

---

## User Prompt

Make only the following Stage 1 cleanup changes. Do not begin Stage 2.

1. Remove premature claims that thread safety is already implemented.

In `pyproject.toml`, change the project description to:

`A reusable Python library for compiling and evaluating expressions.`

In `src/expression_engine/__init__.py`, change the module docstring so it accurately states that the package is under development and that only the currently exported values and exceptions are implemented. Do not claim that expression evaluation is already thread-safe.

2. Correct the local-variable scope documentation in `docs/decisions.md`.

Do not say that using an identifier outside a local binding's body is automatically invalid.

Document that:

* the local binding is visible only inside its body;
* outside that body, the same identifier is resolved again through an outer lexical scope, caller-provided variables, or UNDEFINED;
* free identifiers are valid external-variable references and must not be rejected solely because they are not local bindings.

3. Simplify `tests/test_package.py`.

Remove the redundant assertion:

`assert UNDEFINED != None`

Keep only the identity check:

`assert UNDEFINED is not None`

Move the `pytest` import to the normal top-level import section.

4. Confirm that the exception module is named:

`src/expression_engine/errors.py`

Do not rename it if it is already correct.

After the cleanup, run:

```bash
python -m pytest
python -c "import expression_engine; print(expression_engine.__file__)"
git diff --check
git status
```

Report the exact results.

Do not add new files or features.
Do not implement Engine, Expression, lexer, parser, evaluator, functions, caching, or benchmarks.
Do not commit or push.


---

## Cursor Response

I'll make the four cleanup changes. Let me start with the description and docstring.

Now the decisions.md scope correction.

Now simplify the test file: move `pytest` import to top and remove the redundant assertion.

Item 4: the exception module is already named `src/expression_engine/errors.py` — no rename needed. Let me verify lints and run the validation commands.

Stage 1 cleanup complete. All four changes applied; no new files or features, no Stage 2 work.

## Changes made

1. **Removed premature thread-safety claims.**
   - `pyproject.toml` description → `A reusable Python library for compiling and evaluating expressions.`
   - `src/expression_engine/__init__.py` docstring rewritten to state the package is under development and that only the exported `UNDEFINED` sentinel and the `ExpressionError` hierarchy are implemented. No thread-safety claim.

2. **Corrected local-variable scope docs** in `docs/decisions.md`: removed the "use outside scope is invalid" wording. It now states the binding is visible only inside its `body`; outside it the identifier resolves again via outer lexical scope → caller-provided variables → `UNDEFINED`; and a free identifier is a valid external-variable reference that is never rejected just for not being a local binding.

3. **Simplified `tests/test_package.py`**: removed the redundant `assert UNDEFINED != None` (kept only `assert UNDEFINED is not None`); moved the `pytest` import to the top-level import section (removed the in-function import).

4. **Exception module name confirmed**: already `src/expression_engine/errors.py` — not renamed.

No linter errors in the edited files.

## Validation results (exact)

Commands run via the project venv:

```bash
.venv/bin/python -m pytest
.venv/bin/python -c "import expression_engine; print(expression_engine.__file__)"
git diff --check
git status
```

- **pytest**: `9 passed in 0.04s` (Python 3.11.13, pytest 9.0.3, configfile `pyproject.toml`, testpaths `tests`).
- **import**: `[PROJECT_ROOT]/src/expression_engine/__init__.py`.
- **`git diff --check`**: clean, exit 0.
- **`git status`**: untracked-only on `main` (`README.md`, `ai-transcripts/`, `docs/`, `pyproject.toml`, `src/`, `tests/`); nothing staged or committed.

No new files or features were added; no `Engine`, `Expression`, lexer, parser, evaluator, functions, caching, or benchmarks were implemented. Nothing was committed or pushed. Stopping here — not starting Stage 2.
