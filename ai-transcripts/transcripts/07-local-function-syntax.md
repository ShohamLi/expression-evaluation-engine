# Local Function Syntax, Evaluation, and Test Review

- **Tool:** Codex
- **Project:** Expression Evaluation Engine
- **Transcript type:** English submission copy
- **Editing applied:** Project title added, local paths redacted, and export boilerplate lightly normalized; supplied Codex tool traces and collapsed-history structure preserved.
- **Integrity note:** No prompt, answer, result, decision, or missing conversation was invented.

---

# Add local function syntax

> User context
>
> Attachments:
> -Backend Home Assignment — Expression Evaluation Engine.pdf
> - Implement Stage 15 only: local-function definition syntax and immutable AST. Wo…: `[LOCAL_HOME]/.codex/attachments/658bca7b-075c-47a3-892e-f6f01a1c600d/pasted-text.txt`

<details><summary>19 previous messages</summary>

> I’ll read the attached request and the assignment PDF first, then inspect the repository’s current stage and tests before making the Stage 15 changes.
>
> <details><summary>Explored a file, a list, ran 2 commands</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `[LOCAL_HOME]/.codex/attachments/658bca7b-075c-47a3-892e-f6f01a1c600d/pasted-text.txt`
>
> </details>
>
> - Ran `git status --short`
>
> - Ran `pdftotext 'Backend Home Assignment — Expression Evaluation Engine.pdf' -`
>
> <details><summary>Explored a list</summary>
>
> - Listed files
>
> </details>
>
> </details>
>
> The request is precise, and the worktree is currently clean. `pdftotext` is not installed here, so I’m switching to an available local PDF library while I inspect the parser, AST, compile validation path, tests, and branch state.
>
> <details><summary>Explored 9 files, 2 searches, a list, ran 5 commands</summary>
>
> <details><summary>Explored 7 files</summary>
>
> - Read `./tests/test_function_calls.py`
> - Read `./docs/decisions.md`
> - Read `./tests/test_parser.py`
> - Read `./src/expression_engine/_parser.py`
> - Read `./src/expression_engine/_ast.py`
> - Read `./src/expression_engine/_functions.py`
> - Read `./tests/test_public_api.py`
>
> </details>
>
> - Ran `python3 -c 'import importlib.util; print({name: bool(importlib.util.find_spec(name)) for name in ("pypdf", "PyPDF2", "fitz", "pdfplumber")})'`
>
> - Ran `git branch --show-current`
>
> <details><summary>Explored a file, 2 searches, a list</summary>
>
> - Read `./tests/test_let_parser.py`
> - Listed files in `bin`
> - Searched for `^## ` in `decisions.md`
> - Searched for `def validate_function_calls|raise TypeError|LetExpr|CallExpr` in `_functions.py`
>
> </details>
>
> - Ran `[LOCAL_HOME]/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c 'import importlib.util; print({name: bool(importlib.util.find_spec(name)) for name in ("pypdf", "PyPDF2", "fitz", "pdfplumber")})'`
>
> <details><summary>Explored 6 files</summary>
>
> - Read `./docs/decisions.md`
> - Read `./tests/test_parser.py`
> - Read `./tests/test_public_api.py`
> - Read `./src/expression_engine/_engine.py`
> - Read `./tests/test_function_calls.py`
> - Read `./tests/test_let_parser.py`
>
> </details>
>
> - Ran `[LOCAL_HOME]/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c 'from pypdf import PdfReader; p=PdfReader("Backend Home Assignment — Expression Evaluation Engine.pdf"); print("\n".join(f"\n=== PAGE {i} ===\n{page.extract_text()}" for i,page in enumerate(p.pages,1)))'`
>
> - Ran `[LOCAL_HOME]/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pdfinfo 'Backend Home Assignment — Expression Evaluation Engine.pdf'`
>
> </details>
>
> **Inspection Report**
>
> - Branch/worktree: `feat/local-functions`; `git status --short` is empty.
> - Assignment PDF: read completely. It is 2 pages and requires local functions among the broader engine features, while leaving syntax and semantics to the implementation.
> - Current AST:
>   - `LetExpr(name, value, body, position)` is a frozen, slotted dataclass; `position` anchors the `let` token.
>   - `CallExpr(name, arguments, position)` is also frozen/slotted; `arguments` is an immutable tuple in source order, and `position` anchors the callee identifier.
>   - `Expr` is a direct union of concrete node types with no base class or visitor.
> - Current `let` parsing:
>   - `_expression()` checks for `LET` first and otherwise enters `_conditional()`.
>   - `_let()` currently consumes `let IDENTIFIER = expression in expression`.
>   - Both value and body are full expressions, so nesting works naturally.
>   - `let` is the lowest-precedence form and only starts where a full expression is permitted; as an arithmetic operand it must be parenthesized.
> - Public compile behavior:
>   - `Engine.compile()` tokenizes, parses, then calls `validate_function_calls()`.
>   - That visitor has an exhaustive concrete-node chain ending in an internal `TypeError`.
>   - A new `LocalFunctionExpr` would therefore leak `TypeError`, so the requested compatibility adjustment is required: `_functions.py` must recognize it and raise existing `ExpressionValidationError`; one focused public API regression test is also required.
> - Expected modifications:
>   - Core: `_ast.py`, `_parser.py`, `tests/test_local_function_parser.py`, `docs/decisions.md`.
>   - Compile compatibility: `_functions.py`, `tests/test_public_api.py`.
>   - No tokenizer, evaluator, engine, errors, or package-root changes.
> - Assumptions:
>   - Parameter parsing will be a small local branch/helper returning `tuple[str, ...]`; no semantic validation is added, including duplicate names.
>   - The compile rejection will be anchored at the local definition’s `let` position and use `ExpressionValidationError` with the requested “not supported until the evaluation stage” meaning.
>   - Calls inside a local function definition are represented syntactically only; compile rejects the definition before Stage 16 resolution.
> - Ambiguity noted: the assignment itself does not prescribe local-function grammar or validation timing; the attached Stage 15 specification resolves both, so I’ll follow it exactly.
>
> I have enough context now. I’ll add the AST node and parser branch first, build the focused syntax/immutability test matrix, then add the compile-boundary rejection and decision log entry before running the targeted and full suites.
>
> <details><summary>Explored 4 files, ran a command</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./tests/test_parser.py`
>
> </details>
>
> - Ran `wc -l tests/test_parser.py tests/test_public_api.py docs/decisions.md`
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./pyproject.toml`
> - Read `./src/expression_engine/__init__.py`
> - Read `./src/expression_engine/errors.py`
>
> </details>
>
> </details>
>
> I’m making the scoped edits now: one new frozen AST node, a `(` discriminator inside `_let()`, a direct validation rejection for compile-time compatibility, the focused Stage 15 tests, and a short decision entry.
>
> <details><summary>Created a file, edited 5 files</summary>
>
> - Wrote `./docs/decisions.md` (+17 -0)
> - Wrote `./src/expression_engine/_ast.py` (+21 -0)
> - Wrote `./src/expression_engine/_functions.py` (+7 -0)
> - Wrote `./src/expression_engine/_parser.py` (+28 -0)
> - Wrote `./tests/test_local_function_parser.py` (+217 -0)
> - Wrote `./tests/test_public_api.py` (+9 -0)
>
> </details>
>
> The implementation is in place. I’m checking the new parser matrix and the public compile rejection first; this should also catch any position arithmetic mistakes in the focused failure cases before the full suite.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `git diff --check`
> - Ran `git diff --stat`
> - Ran `python3 -m pytest tests/test_local_function_parser.py tests/test_public_api.py tests/test_let_parser.py tests/test_function_calls.py`
>
> </details>
>
> The first test command hit the repository’s src-layout setup rather than code failures: the package is not installed in this shell. I’m rerunning with `PYTHONPATH=src`, which matches the project layout, and checking the untracked focused test file plus the exact diff.
>
> <details><summary>Explored a file, ran 3 commands</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./tests/test_local_function_parser.py`
>
> </details>
>
> - Ran `git status --short`
>
> - Ran `git diff -- src/expression_engine/_ast.py src/expression_engine/_parser.py src/expression_engine/_functions.py tests/test_public_api.py docs/decisions.md`
>
> - Ran `PYTHONPATH=src python3 -m pytest tests/test_local_function_parser.py tests/test_public_api.py tests/test_let_parser.py tests/test_function_calls.py`
>
> </details>
>
> The targeted behavior is correct; one test had the EOF offset two characters too far. I’m correcting that expected position, then I’ll run the full suite and inspect the final diff for accidental Stage 16 behavior.
>
> <details><summary>Edited a file, ran 3 commands</summary>
>
> - Wrote `./tests/test_local_function_parser.py` (+1 -1)
> - Ran `git diff --check`
> - Ran `PYTHONPATH=src python3 -m compileall -q src tests`
> - Ran `PYTHONPATH=src python3 -m pytest`
>
> </details>
>
> All 655 tests pass, including the new Stage 15 cases, and byte-compilation plus whitespace checks are clean. I’m doing one last scope audit now to confirm only the six permitted files changed and that the validator rejects rather than resolving or evaluating local functions.
>
> <details><summary>Explored 6 files, ran 2 commands</summary>
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./docs/decisions.md`
> - Read `./tests/test_public_api.py`
> - Read `./src/expression_engine/_parser.py`
>
> </details>
>
> - Ran `git diff --name-only`
>
> <details><summary>Explored a file</summary>
>
> - Read `./src/expression_engine/_ast.py`
>
> </details>
>
> - Ran `git status --short`
>
> <details><summary>Explored 2 files</summary>
>
> - Read `./tests/test_local_function_parser.py`
> - Read `./src/expression_engine/_functions.py`
>
> </details>
>
> </details>
>
> Implemented Stage 15 on `feat/local-functions`.
>
> - Added immutable `LocalFunctionExpr` and parser syntax in [_ast.py](../../src/expression_engine/_ast.py#L155) and [_parser.py](../../src/expression_engine/_parser.py#L133).
> - Added clear compile-time `ExpressionValidationError` without Stage 16 behavior.
> - Added comprehensive parser tests and decision documentation.
> - No tokenizer or evaluator changes.
>
> Verification: `655 passed`; byte-compilation and `git diff --check` clean.
>
> <details><summary>Plan</summary>
>
> - [x] Add LocalFunctionExpr and parser support
> - [x] Add focused parser and compile-boundary tests
> - [x] Document the Stage 15 decisions
> - [x] Run targeted and full verification
>
> </details>
</details>

Implemented Stage 15 on `feat/local-functions`.

- Added immutable `LocalFunctionExpr` and parser syntax in [_ast.py](../../src/expression_engine/_ast.py#L155) and [_parser.py](../../src/expression_engine/_parser.py#L133).
- Added clear compile-time `ExpressionValidationError` without Stage 16 behavior.
- Added comprehensive parser tests and decision documentation.
- No tokenizer or evaluator changes.

Verification: `655 passed`; byte-compilation and `git diff --check` clean.

> Make one documentation-only correction in `docs/decisions.md`.
>
> Context:
>
> Stage 15 implementation is already complete and verified:
>
> ```text
> 29 focused tests passed
> 655 full-suite tests passed
> compileall passed
> git diff --cached --check passed
> no eval() or exec() usage found
> ```
>
> The current Stage 15 decision entry says:
>
> ```markdown
> - The project owner selected the `LocalFunctionExpr` name, fields, and exact
>   representation. AI assistance supplied implementation and test suggestions.
> ```
>
> This attribution is too broad because AI assistance also suggested the
> `LocalFunctionExpr` name and field layout.
>
> Replace only those lines with:
>
> ```markdown
> - The project owner selected the local-function syntax and approved keeping
>   Stage 15 limited to parsing and immutable AST representation. AI assistance
>   suggested the `LocalFunctionExpr` name, field layout, implementation approach,
>   and focused test cases.
> ```
>
> Requirements:
>
> * Modify only `docs/decisions.md`.
> * Do not change source code or tests.
> * Do not rewrite any other decision entries.
> * Do not unstaged or alter the existing staged Stage 15 changes.
> * Keep the wording concise and accurate.
> * Do not commit, push, merge, or open a pull request.
>
> After editing, run:
>
> ```bash
> git add docs/decisions.md
> git diff --cached --check
> git diff --cached -- docs/decisions.md
> PYTHONPATH=src python -m pytest -q
> git status --short
> ```
>
> Report:
>
> 1. The exact documentation change.
> 2. Confirmation that only `docs/decisions.md` was edited.
> 3. Exact command results.
> 4. Confirmation that the full suite still passes.
> 5. Confirmation that no commit or push was performed.

<details><summary>9 previous messages</summary>

> I’ll replace only that Stage 15 attribution, stage the documentation file without disturbing the existing index, then run the exact verification commands and report their outputs.
>
> <details><summary>Explored a file, ran a command</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./docs/decisions.md`
>
> </details>
>
> - Ran `git status --short`
>
> </details>
>
> The existing Stage 15 changes are already staged, including `docs/decisions.md`. I’m applying the requested four-line attribution replacement and will re-stage only that file so the index retains every prior staged change.
>
> <details><summary>Edited a file, ran a command</summary>
>
> - Wrote `./docs/decisions.md` (+4 -2)
> - Ran `git add docs/decisions.md`
>
> </details>
>
> The documentation correction is staged successfully; the sandbox initially blocked the Git index lock, so I used the approved Git staging permission and made no other index changes. I’m running the remaining requested checks in order now.
>
> <details><summary>Ran 4 commands</summary>
>
> - Ran `git diff --cached --check`
> - Ran `git diff --cached -- docs/decisions.md`
> - Ran `PYTHONPATH=src python -m pytest -q`
> - Ran `git status --short`
>
> </details>
>
> The full suite still passes with `655 passed`. I’m making one final read-only check that there are no unstaged changes, which confirms the requested edit was fully staged and no source or test file was touched during this correction.
>
> <details><summary>Explored a file, ran a command</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./docs/decisions.md`
>
> </details>
>
> - Ran `git diff --name-only`
>
> </details>
>
> Updated only `docs/decisions.md` with the exact requested attribution.
>
> Command results:
> - `git add docs/decisions.md`: succeeded
> - `git diff --cached --check`: passed, no output
> - `git diff --cached -- docs/decisions.md`: shows corrected Stage 15 wording
> - `PYTHONPATH=src python -m pytest -q`: `655 passed in 1.26s`
> - `git status --short`: all existing Stage 15 files remain staged
> - No unstaged changes remain
>
> No source code or tests were edited. No commit, push, merge, or PR was performed.
</details>

Updated only `docs/decisions.md` with the exact requested attribution.

Command results:
- `git add docs/decisions.md`: succeeded
- `git diff --cached --check`: passed, no output
- `git diff --cached -- docs/decisions.md`: shows corrected Stage 15 wording
- `PYTHONPATH=src python -m pytest -q`: `655 passed in 1.26s`
- `git status --short`: all existing Stage 15 files remain staged
- No unstaged changes remain

No source code or tests were edited. No commit, push, merge, or PR was performed.

> git status --short
> git rev-parse --short HEAD
> git rev-parse --short origin/main
> feat/local-function-evaluation
> 660cbb3
> 660cbb3
> shoham@MacBookPro expression-evaluation-engine %

<details><summary>1 previous message</summary>

> Context noted:
>
> - Branch: `feat/local-function-evaluation`
> - Working tree: clean
> - `HEAD`: `660cbb3`
> - `origin/main`: `660cbb3` (fully aligned)
</details>

Context noted:

- Branch: `feat/local-function-evaluation`
- Working tree: clean
- `HEAD`: `660cbb3`
- `origin/main`: `660cbb3` (fully aligned)

> User context
>
> Attachments:
> - Implement Stage 16 only: local-function compile-time validation, lexical resolu…: `[LOCAL_HOME]/.codex/attachments/abf28e2d-4649-43ee-a262-30d193898d37/pasted-text.txt`

<details><summary>30 previous messages</summary>

> I’ll read the Stage 16 request first, then inspect the clean branch, current Stage 15 AST/parser, compile validation, evaluator, and relevant tests before making any edits.
>
> <details><summary>Explored a file, a list, ran 3 commands</summary>
>
> - Ran `git branch --show-current`
>
> - Ran `git status --short`
>
> <details><summary>Explored a file</summary>
>
> - Read `[LOCAL_HOME]/.codex/attachments/abf28e2d-4649-43ee-a262-30d193898d37/pasted-text.txt`
>
> </details>
>
> - Ran `git rev-parse --short HEAD`
>
> <details><summary>Explored a list</summary>
>
> - Listed files
>
> </details>
>
> </details>
>
> The branch and clean-tree preconditions match exactly. I’ve reached the architecture section of the request; I’m reading the remainder plus the complete assignment PDF and all required implementation/test files before I summarize the current binding model.
>
> <details><summary>Explored 14 files, ran 2 commands</summary>
>
> <details><summary>Explored 5 files</summary>
>
> - Read `./src/expression_engine/_functions.py`
> - Read `./src/expression_engine/_parser.py`
> - Read `./src/expression_engine/_evaluator.py`
> - Read `./src/expression_engine/_ast.py`
> - Read `./src/expression_engine/_engine.py`
>
> </details>
>
> - Ran `git rev-parse --short origin/main`
>
> <details><summary>Explored a file</summary>
>
> - Read `[LOCAL_HOME]/.codex/attachments/abf28e2d-4649-43ee-a262-30d193898d37/pasted-text.txt`
>
> </details>
>
> - Ran `[LOCAL_HOME]/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c 'from pypdf import PdfReader; p=PdfReader("Backend Home Assignment — Expression Evaluation Engine.pdf"); print("\n".join(f"\n=== PAGE {i} ===\n{page.extract_text()}" for i,page in enumerate(p.pages,1)))'`
>
> <details><summary>Explored 8 files</summary>
>
> - Read `./src/expression_engine/errors.py`
> - Read `./tests/test_built_in_functions.py`
> - Read `./tests/test_registered_functions.py`
> - Read `./tests/test_public_api.py`
> - Read `./tests/test_local_bindings.py`
> - Read `./tests/test_local_function_parser.py`
> - Read `./src/expression_engine/__init__.py`
> - Read `./pyproject.toml`
>
> </details>
>
> </details>
>
> The existing design aligns with the requested minimal path: call nodes already compile to immutable target metadata, and variable scopes already layer with `ChainMap`. I’m checking the precise validation/error conventions and the complete Stage 10/13/14 decision history now, especially how positioned validation errors are represented.
>
> <details><summary>Explored 7 files, a search</summary>
>
> - Read `./docs/decisions.md`
> - Read `./src/expression_engine/_functions.py`
> - Read `./src/expression_engine/_functions.py`
> - Searched for `ExpressionValidationError|FunctionArityError|UnknownFunctionError|position` in `tests`
> - Read `./tests/test_registered_functions.py`
> - Read `./docs/decisions.md`
> - Read `./tests/test_local_bindings.py`
> - Read `./tests/test_registered_functions.py`
>
> </details>
>
> **Inspection Report**
>
> - Preconditions are satisfied: branch `feat/local-function-evaluation`, clean working tree, and `HEAD == origin/main == 660cbb3`.
> - The complete 2-page assignment PDF was read. It requires reusable/thread-safe compiled expressions, local functions, null/undefined preservation, and no arbitrary Python execution; Stage 16’s detailed semantics come from the attached specification.
> - `LocalFunctionExpr` is already a frozen, slotted, data-only AST node with `name`, immutable `parameters: tuple[str, ...]`, `function_body`, outer `body`, and a `position` anchored at `let`. Parser work is complete and should remain unchanged.
> - Registered and built-in calls are currently resolved during `Engine.compile()`:
>   - `validate_function_calls()` walks every AST branch, including skipped runtime branches.
>   - Each `CallExpr` maps to immutable `_RegisteredFunction` or `_BuiltinSpec` metadata.
>   - Registration signatures and arity are checked before evaluation; unknown names and arity errors are positioned at the call.
> - Immutable compiled storage:
>   - `Expression` is frozen/slotted and privately stores `_ast` plus `_function_bindings`.
>   - `FunctionBindings` is a `MappingProxyType` keyed by immutable `CallExpr` nodes.
>   - Repeated evaluation reuses this metadata without tokenizing, parsing, resolving names, or inspecting signatures.
> - Current call evaluation:
>   - Arguments are evaluated via tuple construction, left-to-right and once each.
>   - The prebound target is fetched from `_function_bindings`.
>   - Registered calls use their captured callable metadata and host-return validation; built-ins use fixed internal dispatch.
> - Current variable scope:
>   - `LetExpr` evaluates its value once in the outer scope.
>   - `ChainMap({name: value}, variables)` creates a fresh immutable-by-convention lexical layer for the body without mutating caller data.
> - Minimal Stage 16 architecture:
>   - Extend compile bindings so a call can target its exact `LocalFunctionExpr`.
>   - Validate with a lexical `ChainMap` of local function names to definitions plus a blocked-name set for non-recursion.
>   - Resolve local first, then registered, then built-in; exact local arity is checked at compile time.
>   - Validate a definition’s function body against outer functions only, while blocking fallback of its own name; validate its outer body with the new function added.
>   - At runtime, pass a per-evaluation local-closure mapping keyed by definition nodes. Each frozen private closure captures the definition-site variable mapping and visible local closures.
>   - A local call layers a fresh parameter dict over captured variables, then evaluates the function body with captured function closures. No result memoization or shared mutable state is introduced.
> - Affected files:
>   - Required: `_functions.py`, `_evaluator.py`, new `tests/test_local_function_evaluation.py`, `tests/test_public_api.py`, and `docs/decisions.md`.
>   - One additional minimal change is justified in `errors.py`: plain `ExpressionValidationError` currently cannot carry a `Position`, but Stage 16 requires duplicate-name, reserved-name, and recursion errors to carry definition/call positions. I’ll add the same backward-compatible optional-position behavior already used by evaluation and function-call validation errors.
> - Important edge cases:
>   - The current function is excluded from its own compile/runtime scope, while outer local functions remain visible.
>   - A blocked recursive name cannot fall through to a registered or built-in target.
>   - Nested definitions inherit blocked names, so recursion hidden in nested or skipped code is still rejected.
>   - A genuinely visible outer local function wins before a blocked fallback, preserving lexical shadowing.
>   - Runtime errors in unused bodies remain lazy, while all call names and arities inside those bodies remain compile-time validated.
>   - Definition-site variables are captured separately on every `Expression.evaluate()` call; parameters shadow captures; nested closures can capture outer parameters.
> - No new public API or dependency is needed: `Engine`, `Expression.evaluate`, public errors, parser syntax, AST shape, and package exports remain intact. Closures and local binding targets stay private implementation details.
> - Assumptions:
>   - “No recursion” is enforced for references to the current definition’s name when no outer local definition of that name is lexically visible; it never falls through to registered/built-in functions.
>   - Local language-expression returns use normal evaluator semantics and deliberately bypass host callback return validation.
>   - Anonymous functions, higher-order values, mutual recursion, defaults, variadics, keywords, and caching remain out of scope.
>
> The implementation plan is now fixed: compile-time lexical binding in `_functions.py`, per-evaluation frozen closures in `_evaluator.py`, positioned base validation errors, one focused test file, the public regression replacement, and an appended Stage 16 decision entry. I’ll keep parser, AST, engine, exports, dependencies, and existing tests otherwise untouched.
>
> I’m editing the production path first. The compile visitor will bind local calls directly to definition nodes and reject recursion before registered/built-in fallback; the evaluator will carry closure scopes explicitly through recursive evaluation without storing runtime state on `Expression`.
>
> <details><summary>Edited 3 files</summary>
>
> - Wrote `./src/expression_engine/_evaluator.py` (+75 -17)
> - Wrote `./src/expression_engine/_functions.py` (+77 -18)
> - Wrote `./src/expression_engine/errors.py` (+6 -0)
>
> </details>
>
> The core compile/runtime changes are in. Before adding the larger test matrix, I’m running a fast syntax check and a few representative expressions to catch signature-threading or scope mistakes early.
>
> <details><summary>Ran 3 commands</summary>
>
> - Ran `PYTHONPATH=src python -m compileall -q src`
> - Ran `PYTHONPATH=src python -c 'from expression_engine import Engine; cases=[("let add(a, b) = a + b in add(1, 2)", {}, 3), ("let x = 1 in let get_x() = x in let x = 2 in get_x()", {}, 1), ("let outer(x) = let inner(y) = x + y in inner(2) in outer(3)", {}, 5)]; print([(s, Engine().compile(s).evaluate(v), e) for s,v,e in cases])'`
> - Ran `PYTHONPATH=src python -m pytest tests/test_public_api.py tests/test_registered_functions.py tests/test_built_in_functions.py -q`
>
> </details>
>
> The smoke run confirms lexical capture and nested closures work; the only failing test is the intentionally obsolete Stage 15 public test that still expects compilation to fail. I’m replacing that regression and adding the focused Stage 16 suite covering laziness, lexical capture, validation, ordering, reuse, and concurrency.
>
> <details><summary>Created a file, edited a file, ran a command</summary>
>
> - Wrote `./tests/test_local_function_evaluation.py` (+352 -0)
> - Wrote `./tests/test_public_api.py` (+5 -7)
> - Ran `PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q`
>
> </details>
>
> The focused suite exposed one compatibility detail from making base validation errors position-aware: the two existing subclasses were formatting positions themselves, then the new base constructor reset `.position` to `None`. I’m tightening those constructors to delegate the position once; this preserves their existing messages and restores the position attribute.
>
> <details><summary>Edited a file, ran a command</summary>
>
> - Wrote `./src/expression_engine/errors.py` (+2 -8)
> - Ran `PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q`
>
> </details>
>
> All 42 focused Stage 16 tests now pass. I’m reviewing the implementation diff for subtle scope mistakes before documenting it, with particular attention to blocked recursion propagation, closure lookup failures, and preserving existing registered/built-in behavior.
>
> <details><summary>Explored a search, ran 2 commands</summary>
>
> <details><summary>Explored a search</summary>
>
> - Searched for `_eval\(` in `_evaluator.py`
>
> </details>
>
> - Ran `git diff -- src/expression_engine/_functions.py src/expression_engine/_evaluator.py src/expression_engine/errors.py tests/test_local_function_evaluation.py tests/test_public_api.py`
>
> - Ran `PYTHONPATH=src python -m pytest tests/test_local_function_parser.py tests/test_local_bindings.py tests/test_registered_functions.py tests/test_built_in_functions.py tests/test_public_api.py -q`
>
> </details>
>
> The compatibility suite passes (`209 passed`), and the diff review shows the evaluator threads closure state through every existing branch without changing operator semantics. I’m appending the Stage 16 decision record now, including the explicit owner/AI attribution and limitations.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./docs/decisions.md` (+29 -0)
>
> </details>
>
> One test-coverage refinement from the review: I’m making body-entry ordering observable, adding a no-memoization check, and making the direct-recursion case explicitly unused. These sharpen requirements already implemented without changing production behavior.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./tests/test_local_function_evaluation.py` (+22 -4)
>
> </details>
>
> Implementation and documentation are complete. I’m now running the exact requested validation sequence, in order, and will preserve the command outputs and exit statuses for the final report.
>
> <details><summary>Explored a search, ran 5 commands</summary>
>
> - Ran `PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q`
>
> - Ran `PYTHONPATH=src python -m pytest \
>   tests/test_local_function_parser.py \
>   tests/test_local_bindings.py \
>   tests/test_registered_functions.py \
>   tests/test_built_in_functions.py \
>   tests/test_public_api.py -q`
>
> - Ran `PYTHONPATH=src python -m pytest -q`
>
> - Ran `python -m compileall -q src`
>
> - Ran `git diff --check`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `\beval\s*\(|\bexec\s*\(` in `src`
>
> </details>
>
> </details>
>
> The exact test and compile checks are clean: `43` focused, `209` compatibility, and `698` full-suite tests passed. The prohibited-call grep returned exit status `1` with no output, which is the expected “no matches” result.
>
> <details><summary>Ran 2 commands</summary>
>
> - Ran `git status --short`
> - Ran `git diff --stat`
>
> </details>
>
> I’m doing the required final diff review now, including the untracked new test file that `git diff --stat` does not count. I’ll also verify no prohibited or unrelated files changed and inspect the resulting line-level implementation one last time.
>
> <details><summary>Explored a file, ran 4 commands</summary>
>
> - Ran `wc -l tests/test_local_function_evaluation.py`
>
> <details><summary>Explored a file</summary>
>
> - Read `./tests/test_local_function_evaluation.py`
>
> </details>
>
> - Ran `git diff -- docs/decisions.md src/expression_engine/_evaluator.py src/expression_engine/_functions.py src/expression_engine/errors.py tests/test_public_api.py`
>
> - Ran `git status --porcelain=v1`
>
> - Ran `git diff --name-only`
>
> </details>
>
> 1. **What changed:** compile-time lexical resolution, exact arity/parameter validation, recursion rejection, per-evaluation closures, and local-function execution.
>
> 2. **Files changed:**
>    - [_functions.py](../../src/expression_engine/_functions.py)
>    - [_evaluator.py](../../src/expression_engine/_evaluator.py)
>    - [errors.py](../../src/expression_engine/errors.py)
>    - [test_local_function_evaluation.py](../../tests/test_local_function_evaluation.py)
>    - [test_public_api.py](../../tests/test_public_api.py)
>    - [decisions.md](../../docs/decisions.md)
>
> 3. **Architecture:** calls bind directly to immutable `LocalFunctionExpr` nodes during compilation. Runtime uses frozen, per-evaluation closures with `ChainMap` variable/function scopes. No runtime name resolution or shared evaluation state.
>
> 4. **Decisions/assumptions:** lexical definition-site scope, exact positional parameters, reserved built-ins, local-over-registered resolution, and no recursion follow owner requirements. A visible outer local definition wins before recursion blocking.
>
> 5. **Covered edge cases:** laziness, skipped branches, argument ordering/failures, duplicate parameters, arity, recursion, registered shadowing, nested captures, null/undefined, repeated calls, state isolation, and concurrency.
>
> 6. **Known limitations:** no recursion, anonymous/higher-order functions, defaults, variadics, keyword arguments, memoization, or runtime function lookup.
>
> 7. **Exact validation commands:**
>    - `PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q`
>    - Requested five-file compatibility command
>    - `PYTHONPATH=src python -m pytest -q`
>    - `python -m compileall -q src`
>    - `git diff --check`
>    - Requested `grep -R -nE ... src tests`
>    - `git status --short`
>    - `git diff --stat`
>
> 8. **Results:**
>    - Focused: `43 passed in 0.12s`
>    - Compatibility: `209 passed in 0.27s`
>    - Full suite: `698 passed in 1.05s`
>    - `compileall`: exit `0`, no output
>    - `git diff --check`: exit `0`, no output
>    - Prohibited-call grep: exit `1`, no matches, expected
>    - Status: five modified files and one untracked test file listed above
>    - Diff stat: `5 files changed, 194 insertions(+), 50 deletions(-)`; untracked 370-line test file is naturally excluded
>    - During development, one obsolete Stage 15 test and two position assertions initially failed; both causes were corrected before final validation.
>    - No validation warnings. PDF extraction emitted two harmless malformed-object warnings while successfully reading both pages.
>
> 9. No commit, push, merge, publication, or pull request was performed.
>
> <details><summary>Plan</summary>
>
> - [x] Implement compile-time local-function validation and lexical call binding
> - [x] Implement per-evaluation lexical closures and local call execution
> - [x] Add focused evaluation, validation, reuse, and public API tests
> - [x] Append Stage 16 decision documentation
> - [x] Run exact requested validation commands and review full diff
>
> </details>
</details>

1. **What changed:** compile-time lexical resolution, exact arity/parameter validation, recursion rejection, per-evaluation closures, and local-function execution.

2. **Files changed:**
   - [_functions.py](../../src/expression_engine/_functions.py)
   - [_evaluator.py](../../src/expression_engine/_evaluator.py)
   - [errors.py](../../src/expression_engine/errors.py)
   - [test_local_function_evaluation.py](../../tests/test_local_function_evaluation.py)
   - [test_public_api.py](../../tests/test_public_api.py)
   - [decisions.md](../../docs/decisions.md)

3. **Architecture:** calls bind directly to immutable `LocalFunctionExpr` nodes during compilation. Runtime uses frozen, per-evaluation closures with `ChainMap` variable/function scopes. No runtime name resolution or shared evaluation state.

4. **Decisions/assumptions:** lexical definition-site scope, exact positional parameters, reserved built-ins, local-over-registered resolution, and no recursion follow owner requirements. A visible outer local definition wins before recursion blocking.

5. **Covered edge cases:** laziness, skipped branches, argument ordering/failures, duplicate parameters, arity, recursion, registered shadowing, nested captures, null/undefined, repeated calls, state isolation, and concurrency.

6. **Known limitations:** no recursion, anonymous/higher-order functions, defaults, variadics, keyword arguments, memoization, or runtime function lookup.

7. **Exact validation commands:**
   - `PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q`
   - Requested five-file compatibility command
   - `PYTHONPATH=src python -m pytest -q`
   - `python -m compileall -q src`
   - `git diff --check`
   - Requested `grep -R -nE ... src tests`
   - `git status --short`
   - `git diff --stat`

8. **Results:**
   - Focused: `43 passed in 0.12s`
   - Compatibility: `209 passed in 0.27s`
   - Full suite: `698 passed in 1.05s`
   - `compileall`: exit `0`, no output
   - `git diff --check`: exit `0`, no output
   - Prohibited-call grep: exit `1`, no matches, expected
   - Status: five modified files and one untracked test file listed above
   - Diff stat: `5 files changed, 194 insertions(+), 50 deletions(-)`; untracked 370-line test file is naturally excluded
   - During development, one obsolete Stage 15 test and two position assertions initially failed; both causes were corrected before final validation.
   - No validation warnings. PDF extraction emitted two harmless malformed-object warnings while successfully reading both pages.

9. No commit, push, merge, publication, or pull request was performed.

> Review the complete Stage 16 test file before commit.
>
> Context:
>
> * Branch: `feat/local-function-evaluation`
> * Stage 16 implementation is already complete.
> * The full suite currently passes with `698 passed`.
> * The new file is `tests/test_local_function_evaluation.py`.
> * Do not commit, push, merge, or open a pull request.
>
> Task:
> Inspect the entire Stage 16 test file and verify that the tests are focused, necessary, and aligned with the existing project conventions.
>
> Check specifically for:
>
> * duplicated or nearly identical tests;
> * unnecessary helper functions or excessive setup;
> * tests coupled to private implementation details;
> * unnecessary private imports, especially:
>
>   * `expression_engine._engine as engine_module`
>   * `expression_engine._tokens.Position`
> * tests that could be written through the public API instead;
> * weak concurrency tests that do not actually evaluate the same compiled expression concurrently;
> * assertions that overfit exact error wording instead of checking the relevant error type, position, and essential message;
> * obsolete Stage 15 expectations;
> * tests that accidentally weaken existing behavior;
> * missing coverage for important Stage 16 semantics.
>
> Required Stage 16 coverage:
>
> * zero, one, and multiple parameters;
> * exact arity validation at compile time;
> * duplicate parameter rejection;
> * reserved built-in names;
> * local-over-registered resolution;
> * direct recursion rejection;
> * recursion in skipped or nested branches;
> * visible outer local function resolution;
> * lexical definition-site variable capture;
> * nested functions capturing outer parameters;
> * parameter shadowing;
> * arguments evaluated left-to-right and exactly once;
> * function bodies evaluated lazily and once per call;
> * null and undefined preservation;
> * repeated evaluation of one compiled expression;
> * caller input preservation;
> * state isolation between evaluations;
> * concurrent evaluation of the same compiled expression.
>
> Rules:
>
> * Inspect the full existing implementation and relevant tests before editing.
> * Prefer tests through the public `Engine.compile()` and `Expression.evaluate()` API.
> * Keep private imports only when they verify an important invariant that cannot reasonably be tested publicly.
> * Do not remove meaningful edge-case or regression coverage merely to shorten the file.
> * Make only the smallest justified changes.
> * Do not refactor production code.
> * Do not add dependencies or new files.
> * Do not use `eval()` or `exec()`.
>
> Before editing, report:
>
> 1. Which tests are duplicated or unnecessary.
> 2. Which private imports are justified or unjustified.
> 3. Any meaningful Stage 16 coverage gaps.
> 4. The exact changes you propose.
>
> After editing, run:
>
> ```bash
> PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q
> PYTHONPATH=src python -m pytest tests/test_public_api.py tests/test_local_bindings.py tests/test_local_function_parser.py tests/test_registered_functions.py tests/test_built_in_functions.py -q
> PYTHONPATH=src python -m pytest -q
> python -m compileall -q src
> git diff --check
> git diff --cached --check
> git status --short
> git diff --stat
> ```
>
> At the end, report:
>
> 1. What changed.
> 2. Which files changed.
> 3. Why every removed, combined, or retained test was justified.
> 4. Whether private imports remain and why.
> 5. Coverage preserved or added.
> 6. Exact validation results, including failures and warnings.
> 7. Confirmation that no production code was modified unless an actual bug required it.
> 8. Confirmation that no commit or push was performed.

<details><summary>13 previous messages</summary>

> I’ll review the entire Stage 16 test file alongside the production implementation and neighboring test conventions, then report concrete duplication, private-import justification, gaps, and the smallest proposed edits before touching anything.
>
> <details><summary>Explored 6 files, ran 2 commands</summary>
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./src/expression_engine/_engine.py`
> - Read `./src/expression_engine/_functions.py`
> - Read `./tests/test_public_api.py`
>
> </details>
>
> - Ran `git branch --show-current`
>
> - Ran `git status --short`
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./src/expression_engine/_evaluator.py`
> - Read `./src/expression_engine/errors.py`
> - Read `./tests/test_local_function_evaluation.py`
>
> </details>
>
> </details>
>
> I’ve finished the first pass. The file is generally strong and public-API-driven; I’m comparing its position assertions, concurrency pattern, and compile-once test against neighboring suites now so the pre-edit recommendations are grounded in existing conventions rather than just line count.
>
> <details><summary>Explored 3 files, a search, ran 2 commands</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `./tests/test_local_bindings.py`
>
> </details>
>
> - Ran `git diff -- tests/test_local_function_evaluation.py tests/test_public_api.py`
>
> <details><summary>Explored a file, a search</summary>
>
> - Read `./tests/test_registered_functions.py`
> - Searched for `position|ThreadPoolExecutor|retokenize|reparse|left_to_right|exactly_once|unused|short_circuit` in `test_local_bindings.py`
>
> </details>
>
> - Ran `git diff --cached -- tests/test_local_function_evaluation.py tests/test_public_api.py`
>
> <details><summary>Explored a file</summary>
>
> - Read `./tests/test_built_in_functions.py`
>
> </details>
>
> </details>
>
> **Pre-Edit Review**
>
> 1. **Duplicated or unnecessary tests**
> - `test_arithmetic_function_body` duplicates the one-parameter `double(x)` and multi-parameter `add(a, b)` arithmetic coverage. I propose removing it.
> - `test_local_function_can_be_called_multiple_times` is weaker duplication of `test_function_body_is_evaluated_again_for_each_call`, which proves two calls occur and the body is not memoized. I propose removing the weaker test.
> - `test_repeated_local_function_evaluation_does_not_retokenize_or_reparse` duplicates the existing public API compile-once regression in `tests/test_public_api.py`. The invariant is engine-wide, not local-function-specific, and this duplicate is the only reason for the private `_engine` import and mocking. I propose removing it.
> - The null/undefined tests are structurally identical and can be one parameterized identity-preservation test without losing distinct `is` assertions.
> - The Boolean and conditional laziness tests repeat the same registered probe setup. I propose combining them into one parameterized short-circuit test while retaining both expressions.
>
> The remaining apparently similar tests are meaningfully distinct:
> - definition-time laziness vs an unused body containing a runtime error;
> - repeated evaluation vs closure-state isolation;
> - direct, skipped-branch, nested, and registered-fallback recursion;
> - nested parameter capture vs calling a visible outer local function.
>
> 2. **Private imports**
> - `expression_engine._engine as engine_module`: unjustified here. The same compile-once invariant is already tested in `test_public_api.py`; remove it with the duplicate test.
> - `expression_engine._tokens.Position`: unjustified. Stage 16 should verify public exception `.position` data, but it can assert non-`None` and `(line, column)` without constructing a private token type.
> - `ThreadPoolExecutor` remains justified: it verifies the same compiled `Expression` is evaluated concurrently.
> - The small `evaluate()` helper is justified and matches neighboring test style; it keeps public API tests concise.
>
> 3. **Coverage gaps**
> - No required Stage 16 semantic is missing.
> - The concurrency test is valid: one compiled expression is shared across all worker calls.
> - The public API regression has already replaced the obsolete Stage 15 expectation.
> - Error assertions generally check type, position, and essential phrases rather than exact full wording.
> - I do not propose adding coverage merely to increase count.
>
> 4. **Exact proposed changes**
> - Modify only `tests/test_local_function_evaluation.py`.
> - Remove the three redundant tests listed above.
> - Remove `patch`, `_engine`, and `Position` imports.
> - Replace `Position(...)` equality with public `.position` line/column assertions.
> - Parameterize null/undefined preservation.
> - Parameterize Boolean/conditional short-circuit cases.
> - Keep all other edge-case, validation, scope, reuse, and concurrency tests unchanged.
> - No production code, documentation, public API, dependencies, or additional files will change.
>
> I’m applying only the test-file cleanup described above. The substantive coverage stays intact; this removes duplicate signals and makes position checks depend only on the public error objects.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./tests/test_local_function_evaluation.py` (+25 -54)
>
> </details>
>
> The cleanup is applied: private `_engine` and `_tokens` imports are gone, three redundant tests are removed, and four paired cases are parameterized without dropping behavior. I’m checking the resulting full file once, then I’ll run the exact requested command sequence.
>
> <details><summary>Explored a file, a search, ran 9 commands</summary>
>
> <details><summary>Explored a file, a search</summary>
>
> - Read `./tests/test_local_function_evaluation.py`
> - Searched for `expression_engine\._|Position|patch|engine_module|def test_` in `test_local_function_evaluation.py`
>
> </details>
>
> - Ran `git diff -- tests/test_local_function_evaluation.py`
>
> - Ran `PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q`
>
> - Ran `PYTHONPATH=src python -m pytest tests/test_public_api.py tests/test_local_bindings.py tests/test_local_function_parser.py tests/test_registered_functions.py tests/test_built_in_functions.py -q`
>
> - Ran `PYTHONPATH=src python -m pytest -q`
>
> - Ran `python -m compileall -q src`
>
> - Ran `git diff --check`
>
> - Ran `git diff --cached --check`
>
> - Ran `git status --short`
>
> - Ran `git diff --stat`
>
> </details>
>
> The cleaned suite passes: `40` focused tests, `209` compatibility tests, and `695` total. The three-test reduction is exactly the three redundant tests removed; parameterized pairs still execute both null/undefined and both short-circuit cases. I’m doing a final read-only diff audit to confirm this review changed only the Stage 16 test file and left production code untouched.
>
> <details><summary>Explored a search, ran 3 commands</summary>
>
> <details><summary>Explored a search</summary>
>
> - Searched for `expression_engine\._|from unittest\.mock|Position|engine_module` in `test_local_function_evaluation.py`
>
> </details>
>
> - Ran `git diff --name-only`
>
> - Ran `git diff -- tests/test_local_function_evaluation.py`
>
> - Ran `git diff --numstat`
>
> </details>
>
> 1. **Changed**
> - Removed 3 redundant tests:
>   - duplicate arithmetic-body coverage;
>   - weaker repeated-call coverage;
>   - duplicate compile-once/private-spy coverage.
> - Parameterized null/undefined and short-circuit cases.
> - Replaced private `Position` construction with public error-position assertions.
>
> 2. **Files changed**
> - Only `tests/test_local_function_evaluation.py` during this review.
> - No production or documentation files were edited.
>
> 3. **Test justification**
> - Removed tests were already covered by stronger tests or `test_public_api.py`.
> - Combined tests still execute every original semantic case.
> - Retained distinct coverage for laziness, runtime-error deferral, argument failure, lexical capture, nested functions, recursion variants, resolution, state isolation, and concurrency.
>
> 4. **Private imports**
> - No private imports remain.
> - Removed `_engine`, `_tokens.Position`, and `unittest.mock.patch`.
> - `ThreadPoolExecutor` remains because the test genuinely shares one compiled expression across workers.
> - The public `Engine.compile()`/`Expression.evaluate()` API is used throughout.
>
> 5. **Coverage**
> All required Stage 16 semantics remain covered, including exact arity, recursion variants, lexical capture, argument ordering, per-call evaluation, null/undefined, reuse, input preservation, isolation, and concurrent evaluation.
>
> 6. **Validation**
> - Focused: `40 passed in 0.14s`
> - Compatibility: `209 passed in 0.55s`
> - Full suite: `695 passed in 1.24s`
> - `compileall`: exit `0`, no output
> - `git diff --check`: exit `0`, no output
> - `git diff --cached --check`: exit `0`, no output
> - No failures or warnings
>
> `git status --short`:
> ```text
> M  docs/decisions.md
> M  src/expression_engine/_evaluator.py
> M  src/expression_engine/_functions.py
> M  src/expression_engine/errors.py
> AM tests/test_local_function_evaluation.py
> M  tests/test_public_api.py
> ```
>
> `git diff --stat`:
> ```text
> tests/test_local_function_evaluation.py | 79 +++++++++++----------------------
> 1 file changed, 25 insertions(+), 54 deletions(-)
> ```
>
> 7. No production code was modified during this review.
>
> 8. No commit, push, merge, or pull request was performed. The reviewed test cleanup is currently unstaged, reflected by `AM`.
>
> <details><summary>Plan</summary>
>
> - [x] Remove redundant Stage 16 tests and unjustified private imports
> - [x] Preserve required coverage with focused parameterization and public assertions
> - [x] Run the exact requested validation commands
> - [x] Review final test diff and status
>
> </details>
</details>

1. **Changed**
- Removed 3 redundant tests:
  - duplicate arithmetic-body coverage;
  - weaker repeated-call coverage;
  - duplicate compile-once/private-spy coverage.
- Parameterized null/undefined and short-circuit cases.
- Replaced private `Position` construction with public error-position assertions.

2. **Files changed**
- Only `tests/test_local_function_evaluation.py` during this review.
- No production or documentation files were edited.

3. **Test justification**
- Removed tests were already covered by stronger tests or `test_public_api.py`.
- Combined tests still execute every original semantic case.
- Retained distinct coverage for laziness, runtime-error deferral, argument failure, lexical capture, nested functions, recursion variants, resolution, state isolation, and concurrency.

4. **Private imports**
- No private imports remain.
- Removed `_engine`, `_tokens.Position`, and `unittest.mock.patch`.
- `ThreadPoolExecutor` remains because the test genuinely shares one compiled expression across workers.
- The public `Engine.compile()`/`Expression.evaluate()` API is used throughout.

5. **Coverage**
All required Stage 16 semantics remain covered, including exact arity, recursion variants, lexical capture, argument ordering, per-call evaluation, null/undefined, reuse, input preservation, isolation, and concurrent evaluation.

6. **Validation**
- Focused: `40 passed in 0.14s`
- Compatibility: `209 passed in 0.55s`
- Full suite: `695 passed in 1.24s`
- `compileall`: exit `0`, no output
- `git diff --check`: exit `0`, no output
- `git diff --cached --check`: exit `0`, no output
- No failures or warnings

`git status --short`:
```text
M  docs/decisions.md
M  src/expression_engine/_evaluator.py
M  src/expression_engine/_functions.py
M  src/expression_engine/errors.py
AM tests/test_local_function_evaluation.py
M  tests/test_public_api.py
```

`git diff --stat`:
```text
tests/test_local_function_evaluation.py | 79 +++++++++++----------------------
1 file changed, 25 insertions(+), 54 deletions(-)
```

7. No production code was modified during this review.

8. No commit, push, merge, or pull request was performed. The reviewed test cleanup is currently unstaged, reflected by `AM`.
