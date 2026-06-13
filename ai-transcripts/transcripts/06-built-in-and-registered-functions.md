# Built-in and Registered Functions

- **Tool:** Codex
- **Project:** Expression Evaluation Engine
- **Transcript type:** English submission copy
- **Editing applied:** Project title added, local paths redacted, and export boilerplate lightly normalized; supplied Codex tool traces and collapsed-history structure preserved.
- **Integrity note:** No prompt, answer, result, decision, or missing conversation was invented.

---

# Implement stages 13 and 14

> User context
>
> Attachments:
> - Implement Stage 13 and Stage 14 together on the current branch, but execute the…: `[LOCAL_HOME]/.codex/attachments/65386e46-1739-4327-887f-7649f92f3940/pasted-text.txt`

<details><summary>22 previous messages</summary>

> I’ll read the attached specification first, then map it onto the current branch and carry the implementation through verification.
>
> I’ve got the stage requirements. I’m now locating the assignment PDF and auditing the existing call pipeline, API, tests, decisions, and repository state; I’ll give the requested inspection report before touching code.
>
> The working tree already contains uncommitted Stage 13/14-shaped changes, including the proposed `_functions.py` and new tests. I’m treating them as existing user work: I’ll inspect and preserve what is sound, identify gaps against the full assignment and requested contract, then make only necessary edits.
>
> [REDACTED FOR PRIVACY]
>
> Meanwhile, the existing implementation has the right overall shape, but I’m auditing details such as mapping validation, signature edge cases, numeric overflow/domain behavior, immutability, and compile-time traversal before deciding what needs correction.
>
> <details><summary>Searched the web</summary>
>
> <details><summary>Searched the web</summary>
>
> - Searched the web for `site:github.com/ShohamLi/expression-evaluation-engine assignment PDF`
>
> </details>
>
> </details>
>
> **Inspection Report**
>
> 1. **Function-call syntax/AST:** The parser already accepts identifier-only calls (`name(...)`), zero or more positional arguments, nesting, and full expressions as arguments. Calls bind at primary-expression precedence; chained or arbitrary callees are rejected. `CallExpr` is frozen/slotted and stores `name`, an immutable argument tuple, and the identifier position.
> 2. **Public API:** The committed API is `Engine()` → `compile(source)` → immutable `Expression.evaluate(variables=None)`. Compilation tokenizes/parses once; evaluation reuses the AST and holds no per-evaluation state. The current dirty tree already extends `Engine(functions=...)` and stores an immutable registry snapshot on each `Expression`.
> 3. **Unsupported evaluation baseline:** At committed `HEAD`, `_evaluator.py` has no `CallExpr` branch, so a parsed call falls through to `ExpressionEvaluationError("cannot evaluate unsupported expression node", position)`. The existing dirty implementation now evaluates arguments left-to-right into a tuple and dispatches through `_functions.invoke_call`.
> 4. **Function errors:** `UnknownFunctionError` and `FunctionArityError` already exist under `ExpressionValidationError` and are publicly exported. Runtime function type/domain/failure cases can use existing `ExpressionTypeError` and `ExpressionEvaluationError`; no new public error is necessary.
> 5. **Minimal architecture:** Keep parser/AST/tokenizer untouched. Use one `_functions.py` for immutable metadata, constructor-time registration/signature inspection, recursive compile-time call validation, built-in implementations, registered invocation, return validation, and exception wrapping. `_engine.py` owns registry construction and one-time validation; `_evaluator.py` only evaluates arguments and invokes resolved metadata.
> 6. **Expected changed files:** `src/expression_engine/_functions.py`, `_engine.py`, `_evaluator.py`, `errors.py` (documentation only), `tests/test_public_api.py`, new `tests/test_built_in_functions.py`, new `tests/test_registered_functions.py`, and `docs/decisions.md`. I do not expect parser, tokenizer, AST, README, or package exports to change.
> 7. **Assumptions/edge cases:** Exact built-in types only; `bool` and subclasses rejected; all call names/arities validated even in skipped branches; mapping copied once; built-ins reserved; defaults must be trailing; non-mapping inputs and non-string keys need clean engine errors; `NaN`/infinity and overflow/domain behavior must never leak raw Python exceptions; registered return subclasses are rejected; `ExpressionError` propagates unchanged; normal callable exceptions preserve `__cause__`; user callable thread safety remains outside the engine guarantee.
>
> The assignment PDF itself is not present in the repository, attachment store, common local document folders, repository history, or discoverable public results. I’ll use the attached specification as authoritative and will explicitly note that limitation in the final report. I’m proceeding to run the focused Stage 13 tests against the existing dirty implementation, then I’ll correct gaps before moving to Stage 14.
>
> Stage 13’s visible tests pass, but the implementation still leaks raw Python exceptions for cases like `floor(inf)`, `round(nan)`, and overflowing/zero-to-negative `pow`. I also found a contract-level issue shared with Stage 14: evaluation currently looks functions up by name again, while the request requires resolution during compilation. I’m tightening Stage 13 around stable runtime errors and changing compile validation to produce immutable per-call bindings, then I’ll validate Stage 13 before addressing registration-specific input/signature cases.
>
> I’m editing the function layer now. The key change is to make `Engine.compile()` return immutable bindings from each `CallExpr` to already-resolved metadata, so evaluation only evaluates arguments and invokes that binding. I’m also normalizing built-in calculation failures into positioned engine errors without changing parser or AST behavior.
>
> <details><summary>Edited 3 files</summary>
>
> - Wrote `./src/expression_engine/_engine.py` (+13 -5)
> - Wrote `./src/expression_engine/_evaluator.py` (+44 -29)
> - Wrote `./src/expression_engine/_functions.py` (+119 -67)
>
> </details>
>
> The first Stage 13 rerun exposed a dataclass constraint: Python rejects a `mappingproxy` as a direct field default even though it is immutable. I’m switching that field to a factory returning the shared immutable empty binding map, then rerunning the focused suite.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./src/expression_engine/_engine.py` (+1 -1)
>
> </details>
>
> Stage 13 dispatch now satisfies compile-time resolution and the original focused tests. I’m adding coverage for the edge cases the specification calls out but the existing tests missed: every arity boundary, exact-type rejection (including subclasses), validation inside non-executed branches and bindings, result types, and wrapped arithmetic failures.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./tests/test_built_in_functions.py` (+90 -0)
>
> </details>
>
> Stage 13 is now green with 84 focused tests. Moving to Stage 14, I’m validating constructor-time registration behavior: strict mapping input, exact language names, positional-only/default signatures, one-time signature inspection, immutable snapshots, allowed exact return types, and exception boundaries.
>
> The existing Stage 14 tests pass after compile-time binding. I’m expanding them around the registration boundary, where hidden failures are most likely: iterable-but-not-mapping inputs, non-string keys, positional-only callables, uninspectable signatures, all reserved built-ins, exact return-type subclasses, `BaseException`, argument order, and proof that signature inspection happens only at engine construction.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./tests/test_registered_functions.py` (+55 -3)
> - Wrote `./tests/test_registered_functions.py` (+75 -9)
>
> </details>
>
> Stage 14 is green with 57 focused tests. Before the full suite, I’m doing a code-level pass for contract wording and defensive registration behavior, then I’ll update the decision log to explicitly separate owner-mandated choices from implementation suggestions and record the compile-time binding design.
>
> I found two small refinements worth making before the full run: accept any actual string key while normalizing it to a plain `str`, and wrap any normal signature-inspection failure consistently rather than only `TypeError`/`ValueError`. I’m also replacing the terse decisions entry with the requested concrete semantics and an explicit owner-decision versus AI-suggestion split.
>
> <details><summary>Edited 4 files</summary>
>
> - Wrote `./docs/decisions.md` (+38 -19)
> - Wrote `./src/expression_engine/_evaluator.py` (+2 -0)
> - Wrote `./src/expression_engine/_functions.py` (+13 -23)
> - Wrote `./tests/test_registered_functions.py` (+1 -1)
>
> </details>
>
> The implementation and decision log are aligned now. I’m running the public API and full suite to catch regressions across arithmetic, comparisons, Boolean short-circuiting, conditionals, local bindings, parser behavior, and package exports before the final prescribed validation sequence.
>
> All 625 tests pass in the preflight run. I’m starting the exact validation sequence requested, in the listed order, and I’ll record each command’s exit code, output, and any warnings without claiming tools that were not run.
>
> The three focused suites and full suite are clean: 84, 57, 18, and 625 tests respectively. I’m finishing the non-test checks now: bytecode compilation, whitespace validation, prohibited `eval`/`exec` search, and final worktree/diff summaries.
</details>

Implemented Stages 13 then 14, completing and tightening the existing uncommitted work.

**Changes**
- Added nine mathematical built-ins with strict types, arities, result types, and positioned runtime errors.
- Added safe `Engine(functions=...)` registration, immutable snapshots, constructor-time signature inspection, and return validation.
- Function names and arities are resolved once during compilation into immutable per-call bindings.
- Added comprehensive built-in, registered-function, concurrency, exception, and edge-case tests.
- Updated the decision log and validation-error positioning.

**Files**
- [\_functions.py](../../src/expression_engine/_functions.py)
- [\_engine.py](../../src/expression_engine/_engine.py)
- [\_evaluator.py](../../src/expression_engine/_evaluator.py)
- [errors.py](../../src/expression_engine/errors.py)
- [test_built_in_functions.py](../../tests/test_built_in_functions.py)
- [test_registered_functions.py](../../tests/test_registered_functions.py)
- [test_public_api.py](../../tests/test_public_api.py)
- [decisions.md](../../docs/decisions.md)

No parser, tokenizer, AST, README, CLI, cache, local functions, or unrelated features were changed.

**Validation**
```text
PYTHONPATH=src python -m pytest tests/test_built_in_functions.py -q
84 passed in 0.12s; exit 0

PYTHONPATH=src python -m pytest tests/test_registered_functions.py -q
57 passed in 0.13s; exit 0

PYTHONPATH=src python -m pytest tests/test_public_api.py -q
18 passed in 0.05s; exit 0

PYTHONPATH=src python -m pytest -q
625 passed in 1.02s; exit 0

python -m compileall -q src
No output; exit 0

git diff --check
No output; exit 0

grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
No matches; expected exit 1

git status --short
5 modified files and 3 untracked new files; exit 0

git diff --stat
143 insertions, 38 deletions across tracked files; exit 0
```

No warnings or failures occurred. `git diff --stat` does not include the three untracked new files.

The referenced assignment PDF could not be found locally, in repository history, attachments, or public search results; the attached detailed specification was treated as authoritative.

No commit, push, merge, or pull request was performed.

> Make one type-hint correction only in `src/expression_engine/_functions.py`.
>
> `_raise_calculation_error()` is currently typed with `error: ArithmeticError`,
> but it is also called with `ValueError`. The function always raises.
>
> Change it to:
>
> * import `NoReturn` from `typing`;
> * accept `error: Exception`;
> * return `NoReturn`.
>
> Do not change runtime behavior, function semantics, architecture, tests,
> documentation, or any other file. Do not refactor.
>
> Then run:
>
> ```bash
> PYTHONPATH=src python -m pytest tests/test_built_in_functions.py -q
> PYTHONPATH=src python -m pytest tests/test_registered_functions.py -q
> PYTHONPATH=src python -m pytest tests/test_public_api.py -q
> PYTHONPATH=src python -m pytest -q
> python -m compileall -q src
> git diff --check
> git status --short
> ```
>
> Do not commit or push. Report exact results.

<details><summary>4 previous messages</summary>

> I’ll make exactly the requested annotation/import change in `_functions.py`, inspect the diff to confirm no other edits, then run the commands in the specified order.
>
> The mismatch is exactly as described. I’m applying only the `NoReturn` import and the helper’s parameter/return annotations.
>
> <details><summary>Edited a file</summary>
>
> - Wrote `./src/expression_engine/_functions.py` (+3 -2)
>
> </details>
>
> The diff contains only the three requested type-hint changes. I’m running the seven validation commands now in the exact order provided.
</details>

Updated only `_functions.py`:

- Imported `NoReturn`.
- Changed `error` to `Exception`.
- Changed return type to `NoReturn`.

Validation:

```text
Built-ins: 84 passed in 0.19s
Registered: 57 passed in 0.32s
Public API: 18 passed in 0.06s
Full suite: 625 passed in 1.13s
compileall: exit 0
git diff --check: exit 0
```

`git status --short`:

```text
M  docs/decisions.md
M  src/expression_engine/_engine.py
M  src/expression_engine/_evaluator.py
AM src/expression_engine/_functions.py
M  src/expression_engine/errors.py
A  tests/test_built_in_functions.py
M  tests/test_public_api.py
A  tests/test_registered_functions.py
```

No commit or push performed.

> git add src/expression_engine/_functions.py
> git diff --cached --check
> PYTHONPATH=src python -m pytest -q
> shoham@MacBookPro expression-evaluation-engine % git add src/expression_engine/_functions.py
> git diff --cached --check
> PYTHONPATH=src python -m pytest -q
> ............................................................................ [ 12%]
> ............................................................................ [ 24%]
> ............................................................................ [ 36%]
> ............................................................................ [ 48%]
> ............................................................................ [ 60%]
> ............................................................................ [ 72%]
> ............................................................................ [ 85%]
> ............................................................................ [ 97%]
> .................                                                            [100%]
> 625 passed in 1.20s
> shoham@MacBookPro expression-evaluation-engine %

Confirmed:

- `_functions.py` staged successfully.
- `git diff --cached --check` passed with no output.
- Full suite passed: **625 tests in 1.20s**.
