# Local Bindings, Compilation API, Functions, and Product Design

- **Tool:** Cursor
- **Project:** Expression Evaluation Engine
- **Transcript type:** English submission copy
- **Editing applied:** Project title and speaker headings normalized; meaningful Hebrew fragments translated faithfully; obvious keyboard noise and repeated export boilerplate removed; local paths redacted where present.
- **Integrity note:** No prompt, answer, result, decision, or missing conversation was invented.

---

## User Prompt

Stage 10: Local-variable binding evaluation.

Implement only runtime evaluation for the existing immutable `LetExpr` produced by Stage 9:

```text
let name = value in body
```

Do not implement functions, public compilation APIs, caching, or later project stages.

## Branch preparation

Before inspecting or modifying files, confirm that Stage 9 has been merged into `main`.

Run:

```bash
git status --short
git fetch origin
git switch main
git pull --ff-only origin main
git log --oneline -3
git switch -c feat/local-bindings-evaluation
git branch --show-current
git status --short
```

The working tree must be clean before switching branches.

The new branch must be created from the updated `main` containing the merged Stage 9 changes.

Do not delete any branch.

## Intended behavior

Support:

```text
let x = 2 in x + 3              -> 5
let x = "a" in x + "b"          -> "ab"
let x = null in x               -> null
let x = undefined in x          -> undefined
```

## Scope semantics

The required semantics are:

* evaluate the bound `value` exactly once;
* evaluate the bound `value` in the outer scope;
* the new binding is not visible inside its own `value`;
* make the binding visible only while evaluating `body`;
* local bindings may shadow caller-provided variables;
* nested local bindings may shadow outer local bindings;
* leaving the body restores the outer scope naturally;
* never mutate the caller-provided variables mapping;
* never mutate the AST or store evaluation state on it;
* return the body result unchanged;
* preserve `null` and `undefined` as distinct values;
* propagate existing evaluation errors without converting them to `0`, `False`, `None`, or another value.

Examples:

```text
let x = 1 in x
```

returns `1`.

With external variables `{"x": 10}`:

```text
let x = 1 in x
```

returns `1`, while the caller mapping remains `{"x": 10}`.

With external variables `{"x": 2}`:

```text
let x = x + 1 in x
```

returns `3`. The `x` inside the bound value resolves to the external `x`, because the new local binding is not visible in its own value.

Nested shadowing:

```text
let x = 1 in let x = 2 in x
```

returns `2`.

Outer binding restoration:

```text
let x = 1 in (let x = 2 in x) + x
```

returns `3`.

## Phase 1: inspection only

Do not modify any files during Phase 1.

Inspect the current repository, especially:

* `src/expression_engine/_ast.py`
* `src/expression_engine/_evaluator.py`
* `src/expression_engine/_parser.py`
* `src/expression_engine/_values.py`
* `src/expression_engine/errors.py`
* current evaluator tests
* Stage 9 parser tests
* `docs/decisions.md`
* package exports and public API
* current branch, status, recent commits, and diff

Run the complete test suite before proposing implementation changes.

## Required Phase 1 report

Report:

1. The current behavior when a parsed `LetExpr` is passed to `evaluate()`.

2. The smallest evaluator change required.

3. How the runtime scope should be represented without mutating the caller mapping.

4. Compare only the smallest reasonable alternatives, such as:

   * a standard-library layered mapping;
   * a copied mapping containing the local binding;
   * another approach only if the existing repository already establishes one.

Recommend the smallest approach that:

* preserves arbitrary caller-provided `Mapping` objects;
* does not mutate the caller mapping;
* supports nested bindings and shadowing;
* keeps evaluation-specific state local to one evaluation;
* does not add unnecessary classes or modules.

Do not silently select an implementation before explaining this trade-off.

5. How the implementation guarantees that `value` is evaluated once in the outer scope and `body` is evaluated in the extended scope.

6. Whether any evaluator function signature must change.

Prefer no public or broad internal signature change unless inspection proves it necessary.

7. The exact files expected to change.

8. The focused tests required.

9. Any ambiguity or assumption.

10. Confirmation that no tokenizer, parser, AST, error hierarchy, values module, package export, dependency, or configuration change is needed.

## Expected Phase 2 scope

The expected scope should remain limited to:

* `src/expression_engine/_evaluator.py`
* a focused `tests/test_local_bindings.py`
* `docs/decisions.md` only for a short Stage 10 note

Do not modify Stage 9 parser tests unless an existing test incorrectly asserts that evaluation is unsupported.

Do not add a new runtime environment module, scope class, registry, or abstraction unless the existing evaluator cannot remain clear without it.

## Focused test scope

Propose tests for:

1. basic local binding;
2. arithmetic using the local variable;
3. string concatenation using a local variable;
4. `null` as a local value;
5. `undefined` as a local value;
6. a missing variable bound and returned as `UNDEFINED`;
7. external variables used inside the bound value;
8. the new binding not being visible in its own value;
9. local binding shadowing an external variable;
10. nested bindings;
11. nested shadowing;
12. outer binding visible again after an inner binding;
13. a conditional in the bound value;
14. a conditional in the body;
15. evaluation errors in the bound value propagating;
16. evaluation errors in the body propagating;
17. bound value evaluated exactly once;
18. caller mapping remains unchanged;
19. repeated evaluation of the same AST with different variable mappings;
20. error positions remain anchored at the original failing operator, not at `let`.

Use parametrization where it reduces repetition.

Test through the existing parser and evaluator path where possible.

## Explicitly out of scope

Do not implement:

* mutable assignment;
* multiple bindings in one `let`;
* destructuring;
* local function definitions;
* function calls;
* built-in mathematical functions;
* custom functions;
* recursion;
* public `Engine` or `Expression` classes;
* compilation or validation passes;
* caching;
* benchmarks;
* thread-pool infrastructure;
* public API changes;
* unrelated refactoring.

Do not use `eval()` or `exec()`.

## Phase 1 validation

Run:

```bash
PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
git branch --show-current
git log --oneline -5
```

Report exact results, including failures and warnings.

Confirm that:

* the active branch is `feat/local-bindings-evaluation`;
* the branch contains the merged Stage 9 commit;
* no files were modified;
* no commit or push was performed.

Stop after the Phase 1 report and wait for explicit approval.
the task isBackend Home Assignment — Expression Evaluation Engine
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

I'll start with Phase 1: inspection only. Let me begin with the branch preparation steps, but carefully verify the working tree state first.

The working tree is clean and I'm already on `feat/local-bindings-evaluation`, which already contains the Stage 9 commit (`c31ca2a feat: add local binding syntax and AST`). Let me verify the relationship to `main` and `origin`.

`origin/main` now contains the merged Stage 9 work as `5de6ba8 feat: add local binding syntax and AST (#8)` (a squash-merge of the local `c31ca2a`). I'm already on `feat/local-bindings-evaluation`. Let me verify this branch's content matches the merged Stage 9 on `origin/main`, so I can confirm the base is correct without any destructive branch operations.

The branch content is byte-identical to `origin/main` (the merged Stage 9), so `feat/local-bindings-evaluation` is correctly based on merged Stage 9. No destructive branch operations are needed (and re-creating it would risk losing this state and violate "do not delete any branch"). Now let me inspect all the key files.

Now let me read the parser, package exports, decisions doc, and relevant tests.

Now let me look at the parser's `let` handling, the evaluator tests, and run the full test suite plus the validation commands.

Let me check whether any existing test asserts that `LetExpr` evaluation is unsupported, and check the `test_evaluator.py` section on unsupported operations.

No existing test asserts that `LetExpr` evaluation is unsupported (the `_eval` function would currently fall through to the catch-all error). Now let me run the full test suite and the Phase 1 validation commands.

The test suite passes (415 passed) and there are no `eval(`/`exec(` usages. The output got truncated after the grep (grep's non-zero "no match" exit code interfered with the chain). Let me re-run the remaining status checks cleanly.

Phase 1 inspection is complete. No files were modified, and no commit or push was performed. Here is the full report.

## Phase 1 Report — Stage 10 (Local-variable binding evaluation)

### Branch & repository state

- **Active branch:** `feat/local-bindings-evaluation` ✅
- **Working tree:** clean (`git status --short` is empty) ✅
- **Stage 9 merged into `main`:** Yes. `origin/main` is now at `5de6ba8 feat: add local binding syntax and AST (#8)` — the squash-merge of the Stage 9 PR.
- **Branch contains the merged Stage 9 changes:** Yes, by content. The branch carries local commit `c31ca2a feat: add local binding syntax and AST`, and `git diff --stat HEAD origin/main` is **empty** — the tree is byte-identical to the merged Stage 9. `git rev-list --left-right --count HEAD...origin/main` reports `1  1` only because Stage 9 was squash-merged (different hash, identical content).
- **Important note / decision:** The branch already existed and is already correctly based on merged Stage 9 content. I deliberately did **not** run the literal `git switch main` / `git switch -c …` recreation sequence, because the branch exists, recreating it would require deleting it (the task forbids deleting any branch), and it would discard the already-correct state. No destructive git action was taken.

### Phase 1 validation command results

- `PYTHONPATH=src python -m pytest -q` → **415 passed in 0.41s**, no failures, no warnings.
- `git diff --check` → clean (exit 0).
- `grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests` → **no matches** (no `eval()`/`exec()` anywhere).
- `git status --short` → empty (clean).
- `git branch --show-current` → `feat/local-bindings-evaluation`.
- `git log --oneline -5` → `c31ca2a` (Stage 9) on top of `dc57864`, `309b25b`, `61845a8`, `fd1f8d3`.

---

### 1. Current behavior when a parsed `LetExpr` reaches `evaluate()`

`_eval` dispatches on node type (`LiteralExpr`, `VariableExpr`, `UnaryExpr`, `BinaryExpr`, `ConditionalExpr`) and `LetExpr` matches none of them, so it falls through to the catch-all:

```149:151:src/expression_engine/_evaluator.py
    raise ExpressionEvaluationError(
        "cannot evaluate unsupported expression node", node.position
    )
```

So today a `LetExpr` raises `ExpressionEvaluationError` ("cannot evaluate unsupported expression node") anchored at the `let` keyword. No existing evaluator test asserts this behavior (so removing it breaks nothing).

### 2. Smallest evaluator change

Add one `isinstance(node, LetExpr)` branch in `_eval` (and import `LetExpr` + the chosen scope helper). Conceptually:

```python
if isinstance(node, LetExpr):
    bound = _eval(node.value, variables)          # outer scope, evaluated once
    inner = ChainMap({node.name: bound}, variables)
    return _eval(node.body, inner)
```

Nothing else in the evaluator changes. The catch-all stays for genuinely unknown node types.

### 3. Representing runtime scope without mutating the caller mapping

A new scope layer holding only `{name: bound_value}` is placed *in front of* the caller mapping for the duration of `body` evaluation. Lookups (`VariableExpr` uses `variables.get(name, UNDEFINED)`) resolve the local binding first, then fall through to the caller mapping, then `UNDEFINED`. The caller mapping is only read, never written. Leaving `body` is automatic: outer recursion frames still hold the original `variables`, so no teardown is needed.

### 4. Comparison of the smallest alternatives

| Approach | Mutates caller? | Preserves arbitrary `Mapping`? | Nesting/shadowing | Cost | New class/module? |
|---|---|---|---|---|---|
| **`collections.ChainMap({name: value}, variables)`** | No (only reads underlying maps; writes would hit the new dict) | Yes — references it, no copy, works with any `Mapping` via `__getitem__`/`.get` | Natural: nest another `ChainMap` per `let`; first match wins | O(1) per binding; lookup walks at most the active layers | No (stdlib) |
| Copied dict: `d = dict(variables); d[name] = value` | No | Forces materializing the caller `Mapping` into a `dict` each binding | Works, but copies the whole mapping at every nested `let` | O(n) copy per binding — bad on the hot path / large contexts | No |
| Custom scope/environment class | No | Yes | Yes | Similar to ChainMap | Yes — extra abstraction the task says to avoid |

**Recommendation: `collections.ChainMap`.** It is the smallest approach that preserves arbitrary caller `Mapping` objects (no copy), never mutates the caller mapping, supports nested bindings and shadowing by layering, keeps all evaluation state local to the single recursive call (no shared/global state → thread-safe), and adds **no new class or module**. The copied-dict alternative is correct but copies the entire context on every binding, which is wasteful given the documented "millions of times per second" goal and nested `let`s; the custom class is unnecessary abstraction.

One verified subtlety: `ChainMap` is technically a `MutableMapping`, but we only ever read via `.get`, and any hypothetical write would land in the fresh `{name: value}` dict — never in the caller mapping. The `RecordingMapping` test helper (a plain `Mapping`) works correctly as a `ChainMap` underlying layer.

### 5. Guaranteeing "value once in outer scope, body in extended scope"

`node.value` is evaluated with `variables` (the outer mapping) **before** the `ChainMap` is built, and its result is stored in a local. Because it is evaluated exactly once and bound to a local, the binding cannot be visible in its own value, and the value is not re-evaluated. `node.body` is then evaluated with the `ChainMap` layer in front. (A recording-mapping test will assert single evaluation — test #17.)

### 6. Signature changes

**None.** `evaluate(node, variables: Mapping[str, object] | None = None)` and `_eval(node, variables: Mapping[str, object])` already accept any `Mapping`, and `ChainMap` is a `Mapping`. No public or internal signature change is required.

### 7. Exact files expected to change (Phase 2)

- `src/expression_engine/_evaluator.py` — add `LetExpr` import, `from collections import ChainMap` (or `collections.abc` is already imported for `Mapping`; `ChainMap` lives in `collections`), one dispatch branch, and a short docstring update.
- `tests/test_local_bindings.py` — new focused test file.
- `docs/decisions.md` — a short "Local bindings: evaluation (Stage 10)" note.

### 8. Focused tests required

A new `tests/test_local_bindings.py` driving the real `tokenize -> parse -> evaluate` path (matching `test_evaluator.py`'s `run()` helper), reusing the existing `RecordingMapping` for lookup-order/once-only checks.

### 9. Proposed test list (parametrized where it reduces repetition)

1. basic binding (`let x = 1 in x` → 1)
2. arithmetic with the local (`let x = 2 in x + 3` → 5)
3. string concat with the local (`let x = "a" in x + "b"` → `"ab"`)
4. `null` value (`let x = null in x` → `None`)
5. `undefined` value (`let x = undefined in x` → `UNDEFINED`)
6. missing variable bound and returned (`let x = y in x`, no `y` → `UNDEFINED`)
7. external variable used in the bound value (`{"x":2}`, `let x = x + 1 in x` → 3)
8. binding not visible in its own value (same as #7, verifies inner `x` is the external one)
9. local shadows external (`{"x":10}`, `let x = 1 in x` → 1)
10. nested bindings (`let x = 1 in let y = x + 1 in y` → 2)
11. nested shadowing (`let x = 1 in let x = 2 in x` → 2)
12. outer binding visible after inner (`let x = 1 in (let x = 2 in x) + x` → 3)
13. conditional in the bound value
14. conditional in the body
15. evaluation error in the bound value propagates (e.g. `let x = 1/0 in x` → `DivisionByZeroError`)
16. evaluation error in the body propagates (e.g. `let x = 1 in x + "a"` → `ExpressionTypeError`)
17. bound value evaluated exactly once (via `RecordingMapping`)
18. caller mapping unchanged after evaluation (mapping equals its original contents)
19. repeated evaluation of the same parsed AST with different mappings (no state leakage)
20. error position anchored at the failing operator, not at `let` (assert `.position` matches the operator, not the `let` keyword)

(Items like the `null`/`undefined`/literal-value cases and the error-propagation cases are good candidates for `pytest.mark.parametrize`.)

### 10. Ambiguity / assumptions

- **Branch recreation:** As noted, I treated the existing, content-correct branch as the Stage 9 base rather than deleting/recreating it (the task forbids deleting branches, and recreation is unnecessary). Flag if you'd prefer a different branch handling.
- **Missing-variable binding (test #6):** I assume `let x = y in x` with absent `y` binds `x` to `UNDEFINED` and returns `UNDEFINED` (consistent with the documented missing-variable rule). No special-casing.
- **Error message for the removed catch-all:** the `LetExpr` branch replaces the fall-through for `let`; the catch-all remains for any other unexpected node.

### 11. Confirmation of no changes elsewhere

No changes are needed to the tokenizer, parser, AST, error hierarchy, values module, package exports/public API, dependencies, or configuration. The `LetExpr` node, parser support, `ChainMap` (stdlib), `UNDEFINED`, and the error classes all already exist; Stage 10 is purely additive runtime evaluation inside `_evaluator.py`.

---

**No files were modified; no commit or push was performed.** Stopping here for your explicit approval before starting Phase 2.

---

## User Prompt

Proceed with Phase 2 of Stage 10: local-variable binding evaluation.

Implement only evaluation support for the existing `LetExpr` AST node. Do not implement functions, mathematical built-ins, caching, compilation changes, performance optimizations, or any later project stage.

Before editing:

- Inspect the current evaluator, `LetExpr` AST definition, parser behavior, existing tests, error hierarchy, public API, and project conventions.
- Confirm the current behavior when `LetExpr` reaches evaluation.
- Identify any ambiguity or assumption before changing code.
- List the exact files you expect to modify.
- If the required implementation differs materially from the Phase 1 proposal, stop and explain why before editing.

Required semantics:

- `let name = value in body` evaluates `value` exactly once using the outer scope.
- The new binding must not be visible while evaluating its own value.
- After the value is computed, evaluate `body` using a new local scope.
- The local binding must shadow an external variable with the same name.
- Nested bindings and nested shadowing must work.
- After an inner binding finishes, the outer binding must still be available.
- A missing variable must preserve the existing `UNDEFINED` behavior.
- `null` and `undefined` must remain distinct.
- Errors from the bound value or body must propagate unchanged, including their original source positions.
- Do not mutate or copy the caller-provided variables mapping.
- Do not store evaluation-specific state on the AST or any shared object.
- The same parsed expression must remain safe for repeated and concurrent evaluation.
- Preserve all existing evaluator and public API signatures.

Implementation constraints:

- Make the smallest direct change required.
- Import `ChainMap` from Python’s `collections` standard-library module.
- Import the existing `LetExpr` type into `_evaluator.py`.
- Add one direct `LetExpr` branch to the existing evaluator dispatch.
- Evaluate `node.value` before constructing the local scope.
- Use a fresh dictionary containing only the local binding in front of the existing mapping.
- Keep the current catch-all error for genuinely unsupported AST nodes.
- Do not introduce helper functions for this small operation.
- Do not add a custom scope or environment class.
- Do not add wrappers, factories, callbacks, utility modules, or generic abstractions.
- Do not use unnecessary external function calls.
- Do not add third-party dependencies.
- Do not use `eval()` or `exec()`.
- Do not modify unrelated code or perform unrelated refactoring.
- Add comments only when they explain a non-obvious invariant or security/thread-safety decision.

The intended evaluator logic should remain approximately this small:

    if isinstance(node, LetExpr):
        value = _eval(node.value, variables)
        local_scope = ChainMap({node.name: value}, variables)
        return _eval(node.body, local_scope)

Follow the existing code style rather than copying this snippet blindly.

Expected files:

- `src/expression_engine/_evaluator.py`
- `tests/test_local_bindings.py`
- `docs/decisions.md`

Do not modify the tokenizer, parser, AST definitions, public exports, dependencies, configuration, or unrelated tests unless a strictly necessary issue is discovered. If so, explain it before making that additional change.

Testing requirements:

Test through the real public pipeline where possible: tokenize, parse, and evaluate.

Cover:

1. Basic local binding.
2. Arithmetic using a local variable.
3. String concatenation using a local variable.
4. Binding `null`.
5. Binding `undefined`.
6. Binding a missing variable and receiving `UNDEFINED`.
7. Using an external variable in the bound value.
8. Confirming that a binding is not visible in its own value.
9. Local binding shadowing an external variable.
10. Nested bindings.
11. Nested shadowing.
12. Outer binding remaining available after an inner binding.
13. Conditional expression in the bound value.
14. Conditional expression in the body.
15. Error propagation from the bound value.
16. Error propagation from the body.
17. Bound value evaluated exactly once:
    `let x = source in x + x`
    must read external `source` only once.
18. Caller-provided mapping remains unchanged.
19. Repeated evaluation of the same parsed AST with different mappings.
20. Error position remains anchored to the actual failing operator or expression.

Use parametrization only where it improves clarity and reduces repetition. Do not add excessive or duplicate tests.

Documentation:

Add only a short Stage 10 decision entry explaining:

- the evaluation order;
- why the binding is not recursive;
- why `ChainMap` was selected;
- how caller input preservation and thread safety are maintained;
- that no shared evaluation state is introduced.

After implementation:

- Review the full diff for unnecessary code, helpers, imports, comments, and unrelated changes.
- Run exactly:

    PYTHONPATH=src python -m pytest -q
    git diff --check
    grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
    git status --short

Report:

1. What changed.
2. Which files changed.
3. Why this approach was selected.
4. Assumptions and design decisions.
5. Edge cases covered.
6. Known limitations and out-of-scope items.
7. Exact validation commands executed.
8. Exact test results, including failures and warnings.
9. Confirmation that no commit or push was performed.

Do not commit or push.

---

## Cursor Response

Phase 1 already covered full inspection, and the required implementation matches my Phase 1 proposal exactly (no material difference), so I'll proceed directly. Files I expect to modify: `src/expression_engine/_evaluator.py`, `tests/test_local_bindings.py` (new), `docs/decisions.md`.

Let me make the evaluator change first.

Now let me update the module docstring to reflect the added capability.

Now the test file. Let me check the existing `RecordingMapping` helper so I can reuse the pattern.

I have everything I need. Now let me create the focused test file.

Now the documentation entry in `docs/decisions.md`, inserted after the Stage 9 section.

Let me check for lint issues on the edited files, then run the validation commands.

All 435 tests pass (415 prior + 20 new). Now the remaining validation commands, run separately so grep's exit code doesn't truncate the chain.

No `eval(`/`exec(` matches (grep printed nothing and exited 1, which means no matches). Let me review the final diff to confirm it's minimal and clean.

The diff is minimal and matches the agreed approach. Phase 2 is complete.

## Phase 2 Report — Stage 10 (Local-variable binding evaluation)

The required implementation matched my Phase 1 proposal exactly, so I proceeded without deviation.

### 1. What changed

- Added runtime evaluation for `LetExpr` to the evaluator's `_eval` dispatch as one direct branch: evaluate `node.value` once in the outer scope, build a fresh single-entry local scope with `ChainMap({node.name: value}, variables)`, then evaluate `node.body` in that scope. No helper function, scope/environment class, wrapper, or abstraction was introduced.
- Added two imports to `_evaluator.py`: `from collections import ChainMap` and `LetExpr` into the existing `._ast` import group.
- Extended the module docstring with a one-bullet Stage 10 entry.
- Added a focused test file with 20 tests covering the required scenarios.
- Added a short Stage 10 decision entry to `docs/decisions.md`.

The catch-all `ExpressionEvaluationError` for genuinely unsupported nodes was kept.

### 2. Files changed

- `src/expression_engine/_evaluator.py` (modified)
- `tests/test_local_bindings.py` (new)
- `docs/decisions.md` (modified)

No tokenizer, parser, AST, error hierarchy, public exports, dependencies, configuration, or unrelated tests were touched.

### 3. Why this approach

`ChainMap` layers a fresh `{name: value}` dict in front of the caller mapping. It shadows external/outer-local variables by lookup order, supports nesting/shadowing by stacking layers, and restores the outer scope automatically when `body` returns (outer frames still hold the original mapping). It never copies or mutates the caller mapping. A copied dict was rejected (copies the whole context per binding); a custom scope class was rejected as unnecessary abstraction. This is the smallest correct change.

### 4. Assumptions and design decisions

- A missing bound variable (`let x = y in x`, `y` absent) binds `x` to `UNDEFINED` and returns `UNDEFINED`, preserving the existing missing-variable rule.
- The binding is non-recursive: `value` is evaluated before the local scope exists, so it cannot see its own binding.
- Evaluation state lives only in local variables of a single `_eval` call; the immutable AST stays state-free, so the same parsed expression is safe for repeated and concurrent evaluation.
- No public/internal signatures changed (`evaluate`/`_eval` already accept any `Mapping`, and `ChainMap` is a `Mapping`).

### 5. Edge cases covered (tests)

Basic binding; arithmetic with a local; string concatenation; binding `null` (distinct `None`); binding `undefined` (distinct `UNDEFINED`); missing variable → `UNDEFINED`; external variable used in the bound value; binding not visible in its own value; local shadowing an external; nested bindings; nested shadowing; outer binding still available after an inner binding; conditional in value; conditional in body; error propagation from value (`DivisionByZeroError`); error propagation from body (`ExpressionTypeError`); bound value evaluated exactly once via a recording mapping (`source` read once); caller mapping unchanged; repeated evaluation of one AST with different mappings; error position anchored at the failing `+` operator, not at `let`.

### 6. Known limitations / out of scope

No functions, math built-ins, multiple bindings per `let`, mutable assignment, recursion, caching, compilation changes, performance optimizations, or public API changes — all intentionally out of scope for Stage 10.

### 7. Validation commands executed

```
PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
```

### 8. Exact results

- `pytest -q` → **435 passed in 0.74s** (was 415; +20 new). No failures, no warnings.
- `git diff --check` → clean (exit 0), no whitespace errors.
- `grep … eval/exec` → no output, exit 1 (no matches).
- `git status --short`:
  - ` M docs/decisions.md`
  - ` M src/expression_engine/_evaluator.py`
  - `?? tests/test_local_bindings.py`

### 9. Commit/push confirmation

No commit and no push were performed. The changes remain uncommitted in the working tree on branch `feat/local-bindings-evaluation`.

---

## User Prompt

Before commit, make only these Stage 10 cleanup changes:

1. Update the stale first line of `_evaluator.py` that still says "Stages 4-7"
   to a stage-independent evaluator module description.
2. Shorten the LetExpr evaluator comment to only the two non-obvious invariants:
   the binding is non-recursive, and caller input is not mutated.
3. Condense the Stage 10 entry in `docs/decisions.md` to a genuinely short entry
   while preserving evaluation order, non-recursive scope, ChainMap rationale,
   caller-input preservation, and absence of shared evaluation state.
4. Do not change behavior or tests.

Then show the complete new test file using:

git diff --no-index /dev/null tests/test_local_bindings.py || true

Run again:

PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short

Do not commit or push.

---

## Cursor Response

I'll make the three cleanup changes. First, let me look at the current first line of `_evaluator.py`.

Now shorten the `LetExpr` comment to the two non-obvious invariants.

Now condense the Stage 10 entry in `docs/decisions.md`.

Now let me show the complete new test file and run the validation commands.

Now the validation commands. Let me also confirm no lint issues on the edited evaluator.

All three cleanup changes are done, and the full test file was shown above.

### Cleanup changes made

1. **`_evaluator.py` module docstring first line** — replaced the stale `"Stages 4-7: ..."` header with a stage-independent description: `"The expression evaluator: walks an immutable AST and returns a runtime value."`
2. **`LetExpr` evaluator comment** — condensed to the two non-obvious invariants only:

```245:251:src/expression_engine/_evaluator.py
    if isinstance(node, LetExpr):
        # Evaluating the value before the scope keeps the binding non-recursive;
        # ChainMap layers a fresh dict in front without mutating the caller map.
        value = _eval(node.value, variables)
        local_scope = ChainMap({node.name: value}, variables)
        return _eval(node.body, local_scope)
```

3. **`docs/decisions.md` Stage 10 entry** — condensed to a single short paragraph that still preserves evaluation order, the non-recursive scope rationale, the `ChainMap` rationale (and rejected alternatives), caller-input preservation, and absence of shared evaluation state.

No behavior or tests were changed (the docstring/comment edits are non-functional).

### Validation results

- `PYTHONPATH=src python -m pytest -q` → **435 passed in 0.44s** (no failures, no warnings).
- `git diff --check` → clean (exit 0).
- `grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests` → no output, exit 1 (no matches).
- `git status --short`:
  - ` M docs/decisions.md`
  - ` M src/expression_engine/_evaluator.py`
  - `?? tests/test_local_bindings.py`

No linter errors. No commit or push was performed.

---

## User Prompt

/resolve

---

## Cursor Response

I don't have a `/resolve` command or skill defined in this workspace, so I'm not sure what you'd like me to do. Could you clarify?

> **There's no `/resolve` command available here. Given the completed Stage 10 work with uncommitted changes, what would you like me to do?**
> - Commit the Stage 10 changes on feat/local-bindings-evaluation (no push)
> - Commit, push, and open a PR for Stage 10
> - Show a final review/summary of the staged changes (no commit)
> - Nothing yet — I'll explain what /resolve should do ✔

I'm ready — go ahead and explain what `/resolve` should do, and I'll take it from there.

---

## User Prompt

resolve @docs/decisions.md conflict

---

## Cursor Response

There's a merge in progress with a conflict in `docs/decisions.md`. Let me see what's being merged and read the conflict region.

The conflict is simple: our branch (`HEAD`) added the "Local bindings: evaluation (Stage 10)" section, while `main` added nothing in that spot (the section between `=======` and `>>>>>>> main` is empty). The correct resolution is to keep our Stage 10 section and drop the markers.

Now let me verify no conflict markers remain anywhere, stage the resolution, and confirm the merge state.

The only marker hits are in `.venv` third-party packages (decorative `====` lines, not conflicts) — no real conflict markers remain in the project. The resolved file is staged and git reports "All conflicts fixed". Let me verify the merged result is sound by running the tests.

The conflict in `docs/decisions.md` is resolved.

**What happened:** A merge of `main` (`5de6ba8`, the squash-merged Stage 9 PR #8) into your branch (`18dd676 feat: evaluate local variable bindings`) hit one conflict in `docs/decisions.md`. Your side added the "Local bindings: evaluation (Stage 10)" section; the `main` side added nothing there, so the resolution was simply to keep your Stage 10 section and drop the markers.

**Status:**
- Conflict markers removed; no real conflict markers remain in the project (the `.venv` grep hits are decorative `====` lines in third-party packages).
- `docs/decisions.md` is staged; git reports "All conflicts fixed but you are still merging."
- Tests: **435 passed**.

I have not committed, since concluding a merge creates a commit and I avoid committing unless you ask. To finish the merge, the next step would be `git commit` (it will use the default merge message). Want me to conclude the merge now?

---

## User Prompt

Proceed with Stage 11, Phase 1 only: inspect and design function-call syntax and its immutable AST representation.

Do not modify any files during Phase 1.

First confirm the repository state:

```bash
git branch --show-current
git status --short
git log --oneline -3
```

Expected branch:

```text
feat/function-call-syntax
```

Inspect the current repository before proposing changes, including:

* the assignment PDF
* `docs/decisions.md`
* `src/expression_engine/_tokens.py`
* `src/expression_engine/_tokenizer.py`
* `src/expression_engine/_ast.py`
* `src/expression_engine/_parser.py`
* `src/expression_engine/_evaluator.py`
* `src/expression_engine/errors.py`
* `src/expression_engine/__init__.py`
* all relevant tokenizer, parser, evaluator, conditional, string, and local-binding tests
* project configuration and current conventions

This stage is only for parsing and immutable AST support for function calls such as:

```text
abs(x)
max(a, b)
pow(2, 3)
custom_function(x, y + 1)
```

Do not implement:

* function evaluation
* built-in mathematical functions
* custom-function registration
* local function definitions
* function resolution
* function validation
* public compilation API changes
* caching
* benchmarks
* performance optimizations
* any later project stage

Report without editing:

1. Current tokenizer support relevant to calls:

   * identifiers
   * `(`
   * `)`
   * commas
   * EOF
   * source positions

2. Current parser grammar and the smallest parser change required.

3. The exact precedence level where function calls should be parsed.

4. The smallest immutable AST representation:

   * proposed node name
   * exact fields and types
   * arguments stored as `tuple[Expr, ...]`, not a mutable list
   * source-position anchor
   * integration into the existing `Expr` union

5. Proposed function-call grammar.

6. Expected parsing behavior for:

```text
f
f()
f(1)
f(1, 2 + 3)
f(g(1), h(2))
f(1)(2)
(f)(1)
1(2)
```

7. Present the smallest reasonable alternatives for each ambiguity, then recommend one without implementing it:

* identifier-only calls versus arbitrary callable expressions
* chained calls
* zero-argument calls
* trailing commas
* keywords as function names
* source-position anchor
* whether arguments may contain conditionals and `let`

The preferred minimal v1 direction is:

* only an identifier may be called
* zero-argument calls are supported
* trailing commas are rejected
* chained calls are rejected
* parenthesized or arbitrary expressions are not callable
* keywords cannot be function names
* arguments are full expressions
* the call position is anchored at the function identifier

Do not silently choose a different design. Explain any reason to deviate.

8. Malformed syntax and expected parser-error positions:

```text
f(
f(,1)
f(1,)
f(1 2)
f(1,,2)
f)
```

9. Exact files expected to change in Phase 2.

The expected Phase 2 files should normally be limited to:

```text
src/expression_engine/_ast.py
src/expression_engine/_parser.py
tests/test_function_calls.py
docs/decisions.md
```

Do not modify the tokenizer, evaluator, errors, public exports, dependencies, configuration, or unrelated tests unless a strictly necessary issue is discovered. If so, explain it before editing.

10. Focused tests to add, including:

* zero, one, and multiple arguments
* nested calls
* expression arguments
* conditional and parenthesized `let` arguments
* malformed commas and parentheses
* rejected chained and arbitrary calls
* `f` without parentheses remains `VariableExpr`
* precedence with unary, arithmetic, comparisons, Boolean operators, conditionals, and `let`
* immutable `CallExpr`
* tuple-based arguments
* source-position anchor
* existing parser behavior remains unchanged

Phase 2 implementation constraints:

* make the smallest focused change
* preserve the existing public API
* preserve evaluator behavior
* do not make `CallExpr` evaluatable
* use `@dataclass(frozen=True, slots=True)`
* do not add helper modules, registries, validators, visitors, or generic abstractions
* do not add dependencies
* do not use `eval()` or `exec()`
* do not perform unrelated refactoring
* do not commit or push

Documentation constraints for Phase 2:

* add only a short Stage 11 decision entry
* do not repeat existing tokenizer or parser documentation
* do not add long rationale sections
* do not add comments that restate the code
* keep comments only for non-obvious precedence or immutability decisions
* do not expand unrelated module docstrings

Stop after the Phase 1 inspection report. Do not implement anything yet.


---

## Cursor Response

Let me first confirm the repository state, since we were mid-merge on a different branch.

Repository state confirmed: on a clean `feat/function-call-syntax` branch, Stage 10 merged as `#9`. Now let me inspect the relevant files. Let me start with the parser, tokens, tokenizer, and locate the assignment PDF.

No PDF is present in the repo (the assignment text was provided in the chat). Let me verify the tokenizer emits commas/parens/identifiers and check for any existing function-call tests.

The tokenizer already emits `LPAREN`, `RPAREN`, `COMMA`, and `IDENTIFIER` (with keyword matching via `_KEYWORDS`), each with a source `Position`. Let me confirm no existing `Call`/function AST exists and check the parser test conventions for error-position assertions.

Let me look at the existing parser error tests around parentheses to anchor my error-position predictions.

I now have a complete picture. No assignment PDF exists in the repo (its content was provided in chat). No `CallExpr`/function handling exists yet anywhere. Here is the Phase 1 report — no files were modified.

## Stage 11 — Phase 1 Inspection Report (function-call syntax + immutable AST)

### Repository state
- `git branch --show-current` → `feat/function-call-syntax` ✅ (matches expected)
- `git status --short` → empty (clean working tree)
- `git log --oneline -3` → `d7b8a5a feat: evaluate local variable bindings (#9)`, `5de6ba8 feat: add local binding syntax and AST (#8)`, `dc57864 Add minimal string concatenation (#7)`

Stage 10 is merged; the branch is a clean base for Stage 11. (The earlier `decisions.md` merge conflict was resolved and is now part of merged history.)

---

### 1. Current tokenizer support relevant to calls

Everything needed already exists; **no tokenizer change is required**.

- **Identifiers:** `IDENTIFIER` token, ASCII `[A-Za-z_][A-Za-z0-9_]*`, case-sensitive; keyword matching via `_KEYWORDS` so reserved words (`true`, `if`, `let`, …) lex as their own token types, never as `IDENTIFIER`.
- **`(` / `)` / `,`:** emitted as `LPAREN`, `RPAREN`, `COMMA` (single-char punctuation map in `_tokenizer.py`).
- **EOF:** the tokenizer terminates with an `EOF` token (required by `parse()`).
- **Source positions:** every `Token` carries a `Position(offset, line, column)` at its first character (`Position` is 0-based offset, 1-based line/column).

### 2. Current parser grammar and the smallest parser change

The parser is hand-written recursive descent, one method per precedence level, `primary` being tightest:

```26:26:src/expression_engine/_parser.py
    primary        := literal | identifier | "(" expression ")"
```

```216:229:src/expression_engine/_parser.py
    def _primary(self) -> Expr:
        token = self._current()
        if token.type in _LITERAL_TYPES:
            self._advance()
            return LiteralExpr(token.type, token.value, token.position)
        if token.type is TokenType.IDENTIFIER:
            self._advance()
            return VariableExpr(token.value, token.position)
        if token.type is TokenType.LPAREN:
            self._advance()
            grouped = self._expression()
            self._expect(TokenType.RPAREN, "')'")
            return grouped
        raise self._unexpected(token, "an expression")
```

**Smallest change:** in the `IDENTIFIER` branch of `_primary`, after consuming the identifier, peek for a `LPAREN`; if present, parse a parenthesized, comma-separated argument list and return a `CallExpr`; otherwise return the existing `VariableExpr`. A small private method (e.g. `_call_arguments`) consistent with the existing `_let`/`_conditional` style parses the list. **No new precedence-level method, no postfix loop, and no other parser method changes.** This naturally rejects chained calls, parenthesized-expression calls, and non-identifier callees (they fall through to the existing "unexpected trailing token" check).

### 3. Exact precedence level for calls

At the **primary** level, as a postfix immediately attached to an identifier — i.e. calls bind **tightest**, tighter than unary. So `-f(x)` parses as `-(f(x))` and `f(x) + 1` as `(f(x)) + 1`. This is conventional and requires no new level.

### 4. Smallest immutable AST representation

- **Node name:** `CallExpr`
- **Fields/types:**
  - `name: str` — the function identifier text (not a callee `Expr`, because v1 only allows an identifier to be called)
  - `arguments: tuple[Expr, ...]` — immutable tuple (empty tuple for `f()`)
  - `position: Position` — anchor at the function identifier's first character
- **Decorator:** `@dataclass(frozen=True, slots=True)` (matches every other node)
- **Union integration:** add `| CallExpr` to the `Expr` union in `_ast.py` and add `"CallExpr"` to `__all__`.

```python
@dataclass(frozen=True, slots=True)
class CallExpr:
    name: str
    arguments: tuple[Expr, ...]
    position: Position
```

Storing `name: str` (rather than `callee: Expr`) is the smallest faithful encoding of the v1 "identifier-only call" rule and keeps the node trivially immutable.

### 5. Proposed function-call grammar

```
primary   := literal
           | IDENTIFIER ( "(" arguments? ")" )?      # at most one argument list (no chaining)
           | "(" expression ")"
arguments := expression ( "," expression )*          # no trailing comma
```

Each argument is parsed via the top-level `self._expression()`, so arguments may be full expressions (arithmetic, comparisons, Boolean ops, conditionals, and `let`).

### 6. Expected parsing behavior

| Input | Result |
|---|---|
| `f` | `VariableExpr("f")` — no `(`, unchanged behavior |
| `f()` | `CallExpr("f", ())` — zero-arg call |
| `f(1)` | `CallExpr("f", (LiteralExpr 1,))` |
| `f(1, 2 + 3)` | `CallExpr("f", (Literal 1, BinaryExpr +))` |
| `f(g(1), h(2))` | `CallExpr("f", (CallExpr g, CallExpr h))` — nested calls |
| `f(1)(2)` | **ParserError** — chained call: "unexpected trailing `'('`" at the 2nd `(` (offset 4, col 5) |
| `(f)(1)` | **ParserError** — parenthesized expr not callable: trailing `'('` at offset 3, col 4 |
| `1(2)` | **ParserError** — literal not callable: trailing `'('` at offset 1, col 2 |

### 7. Ambiguities — alternatives and recommendations

For each, I follow the preferred minimal v1 direction; no deviations are needed.

1. **Identifier-only vs arbitrary callable** — (A) only `IDENTIFIER` callable, store `name: str`; (B) any expression callable, store `callee: Expr` + postfix loop. **Recommend A** — matches the assignment's named-function examples and `decisions.md` ("no higher-order functions in v1"); smallest node.
2. **Chained calls `f(1)(2)`** — (A) reject (single optional arg list); (B) allow (loop). **Recommend A** — no currying/higher-order in v1; falls out as a trailing-token error for free.
3. **Zero-argument calls `f()`** — (A) support; (B) reject. **Recommend A** — natural, harmless syntactically, matches v1 direction.
4. **Trailing commas `f(1,)`** — (A) reject; (B) allow Python-style. **Recommend A** — simpler; rejected as "expected an expression but found `')'`".
5. **Keywords as names `if(...)`/`true(...)`** — (A) reject. **Recommend A** — free: keywords lex as distinct token types, so only `IDENTIFIER` is treated as a callee; `true(1)` etc. become trailing-token errors.
6. **Source-position anchor** — (A) anchor at the function identifier; (B) anchor at `(`. **Recommend A** — consistent with the existing anchor policy (literals/variables anchored at their start) and points error messages at the function name.
7. **Conditionals / `let` in arguments** — (A) parse each argument with `self._expression()` → conditionals and `let` allowed (bare `let` permitted because each argument starts a fresh expression inside the call parens; parenthesized `let` also works); (B) parse at `self._conditional()` → bare `let` rejected, must be parenthesized. **Recommend A** — matches the "arguments are full expressions" direction and is the smallest (reuses the existing entry point). I note that A consequently accepts a bare `let` argument such as `f(let x = 1 in x, 2)`; if you specifically want `let` arguments to require parentheses, that is option B — please flag it, otherwise I will implement A.

### 8. Malformed syntax and expected parser-error positions

All reuse the existing `_expect` / `_unexpected` / trailing-token machinery — **no new error class**. Positions are `Position(offset, line, column)`:

| Input | Error | Position |
|---|---|---|
| `f(` | "expected an expression but reached end of input" | EOF, `(2,1,3)` |
| `f(,1)` | "expected an expression but found `','`" | `,` at `(2,1,3)` |
| `f(1,)` | "expected an expression but found `')'`" | `)` at `(4,1,5)` |
| `f(1 2)` | "expected `')'` but found `'2'`" | `2` at `(4,1,5)` |
| `f(1,,2)` | "expected an expression but found `','`" | 2nd `,` at `(4,1,5)` |
| `f)` | "unexpected trailing `')'` after a complete expression" | `)` at `(1,1,2)` (`f` parses as `VariableExpr`) |

### 9. Exact files expected to change in Phase 2

- `src/expression_engine/_ast.py` — add `CallExpr`, union, `__all__`.
- `src/expression_engine/_parser.py` — call parsing in `_primary` + a small private argument-list method; update the grammar docstring's `primary` line only.
- `tests/test_function_calls.py` — new focused tests.
- `docs/decisions.md` — short Stage 11 entry.

**No changes** to the tokenizer, evaluator, `errors.py`, public exports (`__init__.py`), dependencies, or configuration. Note on the evaluator: `CallExpr` is deliberately **not** added to `_eval` dispatch, so a `CallExpr` reaching `evaluate()` hits the existing catch-all `ExpressionEvaluationError("cannot evaluate unsupported expression node")` — consistent with "do not make `CallExpr` evaluatable" and requiring no evaluator edit.

### 10. Focused tests to add (`tests/test_function_calls.py`)

Driven through the real `tokenize -> parse` pipeline (no evaluation):

- **Arity:** zero (`f()`), one (`f(1)`), multiple (`f(1, 2 + 3)`) arguments.
- **Nested calls:** `f(g(1), h(2))`.
- **Expression arguments:** arithmetic/comparison/Boolean argument (`f(a + 1, b == 2, c and d)`).
- **Conditional & parenthesized-`let` arguments:** `f(a if b else c)`, `f((let x = 1 in x))` (and, per decision 7A, a bare-`let` argument).
- **Malformed commas/parens:** the six cases in §8, asserting `ParserError` and exact `.position`.
- **Rejected chained/arbitrary calls:** `f(1)(2)`, `(f)(1)`, `1(2)` raise `ParserError`.
- **`f` without parens stays `VariableExpr`.**
- **Precedence:** `-f(2)` → `UnaryExpr(MINUS, CallExpr)`; `f(2) + 1`, `f(2) == 4`, `f(a) and g(b)`, `f(1) if c else g(2)`, `let x = f(1) in x` — call binds tightest.
- **Immutability:** `CallExpr` is frozen (`FrozenInstanceError` on assignment) and has no `__dict__` (slots).
- **Tuple arguments:** `type(node.arguments) is tuple`.
- **Source-position anchor:** `node.position` equals the function identifier position (e.g. `  f(1)` → `Position(2,1,3)`).
- **Existing behavior unchanged:** a couple of regression assertions (e.g. grouped expressions, bare identifiers).

Use parametrization for the arity and malformed-syntax groups; keep the rest explicit.

---

**Assumptions / notes:**
- No assignment PDF is in the repo; I relied on the assignment text provided in chat plus `docs/decisions.md` (which already documents the intended function model for later stages).
- The only genuine open decision is §7.7 (bare vs parenthesized `let` arguments); I recommend allowing full expressions (bare `let` permitted). Flag if you prefer requiring parentheses.

Stopping here per instructions — no implementation performed, no files modified.

---

## User Prompt

Proceed with Stage 11, Phase 2: implement function-call parsing and the immutable `CallExpr` AST only.

Phase 1 is approved with these explicit decisions:

* only identifiers may be called;
* zero-argument calls are supported;
* chained calls are rejected;
* arbitrary expressions are not callable;
* trailing commas are rejected;
* keywords cannot be function names;
* arguments are full expressions;
* bare `let` expressions are allowed as arguments;
* `CallExpr.position` is anchored at the function identifier;
* function evaluation remains out of scope.

Make only the smallest focused implementation.

Expected AST:

```python
@dataclass(frozen=True, slots=True)
class CallExpr:
    name: str
    arguments: tuple[Expr, ...]
    position: Position
```

Add `CallExpr` to `__all__` and the `Expr` union.

Parser behavior:

```text
f
```

remains a `VariableExpr`.

These parse as `CallExpr`:

```text
f()
f(1)
f(1, 2 + 3)
f(g(1), h(2))
f(a if b else c)
f(let x = 1 in x, 2)
```

These must raise `ParserError`:

```text
f(1)(2)
(f)(1)
1(2)
f(
f(,1)
f(1,)
f(1 2)
f(1,,2)
f)
```

Implementation constraints:

* parse calls only in the existing identifier branch of `_primary`;
* do not add a generic postfix-expression layer or arbitrary-callee support;
* a small private argument-list parser is acceptable if it keeps `_primary` clear;
* parse each argument through `_expression()`;
* store arguments as an immutable tuple;
* do not modify evaluator behavior;
* do not add function resolution, validation, built-ins, registries, local functions, caching, or compilation changes;
* do not add dependencies;
* do not modify the public API;
* do not perform unrelated refactoring;
* do not use `eval()` or `exec()`.

Expected files:

```text
src/expression_engine/_ast.py
src/expression_engine/_parser.py
tests/test_function_calls.py
docs/decisions.md
```

Do not modify other files unless a strictly necessary issue is discovered. Stop and report the reason before doing so.

Tests must cover:

* zero, one, and multiple arguments;
* nested calls;
* arithmetic, comparison, Boolean, conditional, and `let` arguments;
* bare `let` as an argument;
* malformed commas and parentheses;
* rejection of chained and arbitrary calls;
* a bare identifier remains `VariableExpr`;
* call precedence under unary, arithmetic, comparison, Boolean, conditional, and `let`;
* `CallExpr` is frozen and uses slots;
* `arguments` is exactly a tuple;
* source position is anchored at the identifier.

Important source-position correction:

```text
f(1)
```

must produce:

```python
Position(0, 1, 1)
```

To test a non-zero offset, use:

```text
"  f(1)"
```

which should produce:

```python
Position(2, 1, 3)
```

Documentation constraints:

* add only a short Stage 11 entry;
* document identifier-only calls, immutable tuple arguments, full-expression arguments, and rejected chaining/trailing commas;
* do not repeat tokenizer documentation;
* do not add long rationale sections;
* do not expand unrelated module docstrings;
* comments should explain only non-obvious parser decisions.

After implementation, review the complete diff and run:

```bash
PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
```

Also run focused tests separately:

```bash
PYTHONPATH=src python -m pytest tests/test_function_calls.py -q
PYTHONPATH=src python -m pytest tests/test_parser.py tests/test_let_parser.py -q
```

Report:

1. what changed;
2. files changed;
3. why the approach was selected;
4. assumptions and decisions;
5. edge cases covered;
6. known limitations and out-of-scope items;
7. exact validation commands;
8. exact results, failures, and warnings;
9. confirmation that no commit or push was performed.

Do not commit or push.


---

## Cursor Response

I'll implement Phase 2. Let me start with the AST node.

Now the parser. Update the import, the grammar docstring's `primary` line, and the `IDENTIFIER` branch in `_primary` plus a small argument-list method.

Now add the `_call` argument-list method. I'll place it right after `_primary`.

Now the test file.

Now the short Stage 11 doc entry, inserted after the Stage 9 section and before the Stage 10 section.

Let me check lints on the edited files, then run the full and focused test suites.

The implementation is correct; my expected offset in the bare-`let` test was off by one (I forgot the space after the comma — `2` is at offset 18, not 17). Let me fix the test assertion.

All 466 pass. Now the focused suites and the remaining validation commands.

Let me do a final review of the source diff to confirm it's minimal and clean.

The diff is minimal and matches the approved design. Stage 11 Phase 2 is complete.

## Stage 11 — Phase 2 Report (function-call parsing + `CallExpr` AST)

### 1. What changed
- **AST:** Added the immutable `CallExpr` node (`@dataclass(frozen=True, slots=True)`) with `name: str`, `arguments: tuple["Expr", ...]`, `position: Position`; added it to `__all__` and the `Expr` union.
- **Parser:** In the existing `IDENTIFIER` branch of `_primary`, a `(` immediately after an identifier now begins a call, delegating to a small private `_call` method that parses a comma-separated list of full expressions (`_expression()`), supports the empty list (zero-arg), rejects trailing commas, and stores arguments as an immutable tuple anchored at the identifier. Updated the grammar docstring's `primary` line only. No generic postfix layer, no arbitrary-callee support.
- **Tests:** New `tests/test_function_calls.py` (31 tests).
- **Docs:** Short Stage 11 entry in `docs/decisions.md`.

### 2. Files changed
- `src/expression_engine/_ast.py`
- `src/expression_engine/_parser.py`
- `tests/test_function_calls.py` (new)
- `docs/decisions.md`

No other files were touched (no tokenizer, evaluator, errors, public exports, dependencies, or config changes).

### 3. Why this approach
Parsing the call directly in the identifier branch of `_primary` is the smallest change that satisfies all approved decisions: identifier-only callees, no chaining, and arbitrary/parenthesized expressions not callable all fall out for free (a second `(`, `(f)(...)`, or `1(...)` simply become "unexpected trailing token" errors via existing machinery). A tiny `_call` method mirrors the existing `_let`/`_conditional` style and keeps `_primary` readable, without introducing a postfix precedence level or any abstraction.

### 4. Assumptions and decisions
- Implemented exactly the approved Phase 1 decisions, including bare `let` allowed as an argument (arguments parse via `_expression()`).
- `CallExpr` is intentionally **not** added to the evaluator dispatch, so a `CallExpr` reaching `evaluate()` hits the existing unsupported-node error — function evaluation stays out of scope.
- Corrected the source-position test as instructed: `f(1)` → `Position(0, 1, 1)`, `"  f(1)"` → `Position(2, 1, 3)`. (I also fixed an off-by-one in my own `f(let x = 1 in x, 2)` test: the `2` is at `Position(18, 1, 19)`; the parser was already correct.)

### 5. Edge cases covered
Zero/one/multiple args; nested calls `f(g(1), h(2))`; arithmetic/comparison/Boolean/conditional/bare-`let` arguments; bare identifier stays `VariableExpr`; precedence under unary, arithmetic, comparison, Boolean, conditional, and `let` (call binds tightest); `CallExpr` frozen + slots (no `__dict__`); `arguments` is exactly a `tuple`; identifier-anchored positions (zero and non-zero offset); rejection of chained/arbitrary calls (`f(1)(2)`, `(f)(1)`, `1(2)`); malformed commas/parens with exact error positions (`f(`→`(2,1,3)`, `f(,1)`→`(2,1,3)`, `f(1,)`→`(4,1,5)`, `f(1 2)`→`(4,1,5)`, `f(1,,2)`→`(4,1,5)`, `f)`→`(1,1,2)`).

### 6. Known limitations / out of scope
No function evaluation, resolution, validation, built-ins, registries, local function definitions, caching, or compilation changes. Only an identifier is callable; no chaining or higher-order/parenthesized callees. `CallExpr` is not evaluatable.

### 7. Exact validation commands
```
PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
PYTHONPATH=src python -m pytest tests/test_function_calls.py -q
PYTHONPATH=src python -m pytest tests/test_parser.py tests/test_let_parser.py -q
```

### 8. Exact results, failures, warnings
- Full suite: **466 passed** in 0.51s (no failures, no warnings). *(An initial run had 1 failure from my off-by-one test assertion; after the test fix it is 466 passed.)*
- `tests/test_function_calls.py`: **31 passed**.
- `tests/test_parser.py tests/test_let_parser.py`: **125 passed** (existing parser behavior unchanged).
- `git diff --check`: clean (exit 0).
- `grep … eval/exec`: no matches (exit 1).
- `git status --short`:
  - ` M docs/decisions.md`
  - ` M src/expression_engine/_ast.py`
  - ` M src/expression_engine/_parser.py`
  - `?? tests/test_function_calls.py`
- No linter errors.

### 9. Commit/push confirmation
No commit and no push were performed. All changes remain uncommitted in the working tree on `feat/function-call-syntax`.

---

## User Prompt

Before committing Stage 11, make only these final cleanup checks:

1. Ensure the Stage 11 decision entry in `docs/decisions.md` appears after
   the Stage 10 entry, so the stage order remains chronological.

2. Verify the non-zero source-position test:
   - `"  f(1)"` with exactly two leading spaces must produce
     `Position(2, 1, 3)`.
   - Do not use one leading space with that expected position.

3. Do not claim that lint passed unless an actual configured lint command
   was executed.

Do not change parser behavior, AST design, or test coverage.

Then run:

PYTHONPATH=src python -m pytest tests/test_function_calls.py -q
PYTHONPATH=src python -m pytest tests/test_parser.py tests/test_let_parser.py -q
PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short

Show the complete diff, including the new untracked test file.

Do not commit or push.

---

## Cursor Response

I'll verify the Stage 11 doc order, the two-space position test, and run the validation commands.


Stage 11 is currently before Stage 10 in the docs — I'll reorder that. The position test already uses exactly two leading spaces.


Now running validation commands and gathering the complete diff.


Cleanup checks are done. Only the Stage 11 doc order needed a change; parser behavior, AST design, and tests were left as-is.

### Cleanup changes
1. **`docs/decisions.md` stage order** — Moved the Stage 11 entry to after Stage 10. Order is now chronological: Stage 9 → Stage 10 → Stage 11 → AI-assisted decisions.
2. **Non-zero source-position test** — Already correct: `test_position_anchored_at_identifier_nonzero_offset` uses exactly two leading spaces (`"  f(1)"`) and expects `Position(2, 1, 3)`.
3. **Lint** — No configured lint command was run; no lint claim is made.

### Validation results

```
PYTHONPATH=src python -m pytest tests/test_function_calls.py -q
→ 31 passed in 0.06s

PYTHONPATH=src python -m pytest tests/test_parser.py tests/test_let_parser.py -q
→ 125 passed in 0.18s

PYTHONPATH=src python -m pytest -q
→ 466 passed in 0.57s

git diff --check
→ clean (exit 0)

grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
→ no matches (exit 1)

git status --short
 M docs/decisions.md
 M src/expression_engine/_ast.py
 M src/expression_engine/_parser.py
?? tests/test_function_calls.py
```

No failures, no warnings. No commit or push was performed.

### Complete diff

**Tracked changes:**

```diff
diff --git a/docs/decisions.md b/docs/decisions.md
index f2e4eff..bbf73e1 100644
--- a/docs/decisions.md
+++ b/docs/decisions.md
@@ -425,6 +425,24 @@ never copied or mutated, and all scope state is local to one `_eval` call, so th
 immutable AST holds no shared evaluation state and stays safe for repeated and
 concurrent evaluation.

+## Function calls: syntax and AST (Stage 11)
+
+- Call syntax is `name(arg0, arg1, ...)`. Only an identifier may be called:
+  parenthesized or arbitrary expressions are not callable (`(f)(1)`, `1(2)`),
+  and calls do not chain (`f(1)(2)` is a `ParserError`). Keywords are not
+  identifiers, so they cannot be function names.
+- Calls are parsed in the identifier branch of `_primary` (tightest binding); a
+  `(` immediately following an identifier begins the call. No generic
+  postfix-expression layer is introduced.
+- Arguments are full expressions (parsed via `_expression()`), so arithmetic,
+  comparisons, Boolean operators, conditionals, and bare `let` are all valid
+  argument forms. Zero-argument calls are allowed; trailing commas are rejected.
+- `CallExpr` is immutable (`frozen=True, slots=True`); `arguments` is a
+  `tuple[Expr, ...]` (never a mutable list) and `position` is anchored at the
+  function identifier. This stage adds syntax and AST only; evaluation stays out
+  of scope, so a `CallExpr` reaching the evaluator hits the existing
+  unsupported-node error.
+
 ## AI-assisted decisions
 ...
diff --git a/src/expression_engine/_ast.py b/src/expression_engine/_ast.py
--- a/src/expression_engine/_ast.py
+++ b/src/expression_engine/_ast.py
@@ -35,6 +35,7 @@ __all__ = [
     "BinaryExpr",
     "ConditionalExpr",
     "LetExpr",
+    "CallExpr",
     "Expr",
 ]
 ...
+@dataclass(frozen=True, slots=True)
+class CallExpr:
+    """A function call ``name(arg0, arg1, ...)``.
+    ...
+    name: str
+    arguments: tuple["Expr", ...]
+    position: Position
+
 Expr = (
     ...
     | LetExpr
+    | CallExpr
 )
diff --git a/src/expression_engine/_parser.py b/src/expression_engine/_parser.py
--- a/src/expression_engine/_parser.py
+++ b/src/expression_engine/_parser.py
@@ -23,7 +23,9 @@ Grammar and precedence ...
-    primary        := literal | identifier | "(" expression ")"
+    primary        := literal
+                    | IDENTIFIER ( "(" ( expression ("," expression)* )? ")" )?
+                    | "(" expression ")"
 ...
         if token.type is TokenType.IDENTIFIER:
             self._advance()
+            if self._current().type is TokenType.LPAREN:
+                return self._call(token)
             return VariableExpr(token.value, token.position)
+
+    def _call(self, name: Token) -> Expr:
+        ...
+        return CallExpr(name.value, tuple(arguments), name.position)
```

**New file `tests/test_function_calls.py`** (252 lines) — full content shown in the command output above, including:

- `test_position_anchored_at_identifier_zero_offset`: `"f(1)"` → `Position(0, 1, 1)`
- `test_position_anchored_at_identifier_nonzero_offset`: `"  f(1)"` → `Position(2, 1, 3)` (exactly two leading spaces)

---

## User Prompt

Proceed with Stage 12, Phase 1 only: inspect and design the minimal public compilation and repeated-evaluation API.

Do not modify any files during Phase 1.

First confirm the repository state:

```bash
git branch --show-current
git status --short
git log --oneline -3
git log main --oneline -5
git diff --stat main...HEAD
```

Expected branch:

```text
feat/compiled-expression-api
```

The working tree must be clean.

The branch must be based on the current `main`, and Stage 11 function-call syntax and immutable `CallExpr` support must already be present in `main`.

Verify this from the Git history and the Stage 11 implementation and tests. Do not rely only on the current branch contents.

If any of these conditions is not true, stop and report the exact problem without changing files:

* the current branch is not `feat/compiled-expression-api`;
* the working tree is not clean;
* the branch is not based on the current `main`;
* Stage 11 is not already present in `main`.

## Goal

Design the smallest clean public Python-library API that:

* compiles a source expression once;
* stores and reuses the existing immutable parsed representation;
* evaluates the same compiled expression repeatedly with different variable mappings;
* never tokenizes or parses again during evaluation;
* is safe for concurrent evaluation;
* does not store evaluation-specific state on shared objects;
* does not mutate caller-provided mappings;
* hides tokenizer, parser, AST, and evaluator implementation details from library users.

This stage is about the public compiled-expression API only.

Do not implement:

* built-in function evaluation;
* custom-function registration;
* local function definitions or evaluation;
* function validation or resolution;
* caching;
* global registries;
* benchmarks or performance optimization;
* a web API, CLI, database, or service;
* new expression-language syntax;
* unrelated documentation cleanup;
* any later project stage.

## Required inspection

Read the assignment PDF completely and inspect the current repository, including:

* `pyproject.toml`;
* `src/expression_engine/__init__.py`;
* `src/expression_engine/_tokenizer.py`;
* `src/expression_engine/_parser.py`;
* `src/expression_engine/_ast.py`;
* `src/expression_engine/_evaluator.py`;
* `src/expression_engine/errors.py`;
* `docs/decisions.md`;
* the current README, if present;
* all package and public-import tests;
* parser tests;
* evaluator tests;
* local-binding tests;
* function-call tests;
* current naming, typing, docstring, and module conventions.

Inspect the actual call sites of the tokenizer, parser, and evaluator. Determine whether any test or public code currently depends on their exact function names or signatures.

Do not rely on a generic design from another project. Base the proposal on the current implementation and public exports.

## Phase 1 report

Report the following without editing any files.

### 1. Current state

Explain:

* the current public package exports;
* the current internal pipeline from source text to runtime value;
* which steps currently happen once and which happen on every call;
* whether any public compiled-expression abstraction already exists;
* how syntax and evaluation errors currently propagate;
* what immutable structures can already be reused;
* whether current evaluator calls keep all evaluation-specific state local to each call.

### 2. Smallest public API alternatives

Compare only the smallest reasonable alternatives.

#### Alternative A

```python
engine = Engine()
expression = engine.compile("2 + x")
result = expression.evaluate({"x": 3})
```

#### Alternative B

```python
expression = compile_expression("2 + x")
result = expression.evaluate({"x": 3})
```

For each alternative, explain:

* public surface size;
* future compatibility with built-in and registered functions;
* whether it introduces unnecessary abstraction now;
* thread-safety implications;
* how well it matches the assignment and current repository.

Recommend one alternative, but do not implement it.

The preferred direction is:

```python
from expression_engine import Engine

engine = Engine()
expression = engine.compile("2 + x")

expression.evaluate({"x": 3})
expression.evaluate({"x": 10})
```

Do not silently choose a different public API. Explain any reason to deviate.

### 3. Proposed exact interfaces

Propose exact minimal signatures and type hints for:

* `Engine`;
* `Engine.compile(...)`;
* the compiled-expression class;
* its `evaluate(...)` method.

Address these decisions explicitly:

* `CompiledExpression` versus `Expression` as the public class name;
* whether `Engine` is stateless in this stage;
* whether the compiled object should use `@dataclass(frozen=True, slots=True)` or another project-consistent immutable design;
* whether the stored AST field should be private;
* whether the original source string needs to be stored;
* whether the AST should be exposed publicly;
* whether `variables` should accept `Mapping[str, object] | None`;
* whether omitted variables should behave as an empty mapping;
* whether any helper function or top-level compile alias is genuinely necessary.

Prefer the smallest public surface. Do not propose duplicate ways to perform the same operation without a concrete need.

Do not add speculative constructor arguments for functions, registries, caching, validation, or configuration.

### 4. Compilation and evaluation boundary

Define exactly what happens during:

```text
Engine.compile(source)
```

and exactly what happens during:

```text
CompiledExpression.evaluate(variables)
```

The intended separation is:

```text
compile:
source -> tokenize -> parse -> immutable compiled representation

evaluate:
compiled representation + variables -> result
```

Evaluation must not tokenize or parse again.

Explain how this can be tested without adding artificial instrumentation, counters, hooks, or test-only behavior to production code.

Prefer patching or spying on the existing tokenizer/parser entry points from the test, if compatible with the current import structure.

### 5. Errors

Explain expected public behavior for:

* invalid syntax during `compile`;
* missing variables during `evaluate`;
* type errors during `evaluate`;
* division by zero during `evaluate`;
* compiling a syntactically valid `CallExpr`;
* evaluating that `CallExpr` before function evaluation is implemented.

Distinguish compile-time syntax errors from runtime evaluation errors.

Do not add a validation pass or new errors in this stage unless the current architecture strictly requires it.

Preserve existing engine-specific error classes, messages where reasonably stable, and source positions.

### 6. Immutability and thread safety

Explain how the proposed design guarantees:

* the same compiled expression can be evaluated repeatedly;
* different evaluations do not share variable state;
* concurrent calls on the same compiled expression are safe;
* caller mappings are not changed;
* the AST remains immutable;
* no global mutable state is introduced.

Identify any mutable field, shared object, module-level state, default mutable argument, or evaluator-side mutation risk in the current code, if one exists.

Do not claim thread safety merely because the AST is frozen. Verify that evaluation itself stores no state on the engine, compiled object, AST, or caller mapping.

### 7. Future function support without premature implementation

Explain how the proposed API can later support:

* built-in functions;
* registered custom functions;
* local functions;

without implementing registries, function resolution, or function evaluation in Stage 12.

Do not add placeholder registries, unused constructor parameters, configuration objects, protocols, factories, builders, generic contexts, or future-only abstractions.

Clearly separate what Stage 12 needs now from what a later function stage may add.

### 8. Expected files for Phase 2

List the exact files that would need to change.

The expected change should normally remain limited to something similar to:

```text
src/expression_engine/<one small public API implementation module>
src/expression_engine/__init__.py
tests/test_public_api.py
docs/decisions.md
```

A different file list is acceptable only if the current repository structure clearly requires it. Explain why before implementation.

Do not modify tokenizer, parser, AST, evaluator, errors, dependencies, project configuration, or unrelated tests unless a strictly necessary issue is discovered during inspection.

### 9. Focused Phase 2 tests

Propose focused tests through the public API for:

* importing the public classes from `expression_engine`;
* compiling and evaluating a basic expression;
* repeated evaluation of the same compiled object with different mappings;
* proving tokenizer and parser are not rerun during evaluation, using the smallest technique that does not modify production code solely for testing;
* omitted variables mapping;
* caller mapping preservation;
* syntax errors raised during compile;
* evaluation errors raised only during evaluate;
* `null` and `UNDEFINED` preservation;
* local bindings through the public API;
* immutable compiled representation;
* no publicly exposed mutable AST state;
* concurrent evaluation of the same compiled expression with independent mappings;
* current behavior for parsed-but-unsupported function calls;
* regression coverage for the existing internal pipeline.

Do not duplicate broad language-semantic tests already covered by tokenizer, parser, evaluator, binding, or function-call test modules.

For every proposed test, state briefly what Stage 12 requirement it proves.

### 10. Documentation limits

For Phase 2, propose only:

* short public docstrings for public interfaces;
* a short Stage 12 entry in `docs/decisions.md`;
* no README rewrite;
* no long architecture document;
* no repeated explanation of tokenizer, parser, AST, or evaluator internals;
* no comments that merely restate the code.

## Constraints

* preserve the existing public API;
* add only the smallest necessary public API;
* separate compilation from evaluation;
* parse each source only once;
* reuse an immutable compiled representation;
* do not tokenize or parse during repeated evaluation;
* do not mutate caller-provided mappings;
* keep `null` and `UNDEFINED` distinct;
* preserve current short-circuit and conditional behavior;
* keep the compiled expression safe for concurrent evaluation;
* avoid global mutable state;
* use clear names and type hints;
* add docstrings to public interfaces;
* add helpers only when they remove genuine duplication or keep a public interface clear;
* do not add unnecessary functions, wrappers, aliases, modules, classes, or dependencies;
* do not use `eval()` or `exec()`;
* do not perform unrelated refactoring;
* do not commit or push.

Stop after the Phase 1 inspection and design report.

Do not modify any files and do not implement anything yet.


---

## Cursor Response

Starting Phase 1 inspection only — I'll confirm repository state and read the relevant files.


Repository state checks out. Next I'll inspect the internal pipeline, public exports, and how tests call tokenizer/parser/evaluator.


## Stage 12 — Phase 1 Inspection & Design Report (public compiled-expression API)

### Repository preconditions

All required conditions are satisfied:

| Check | Result |
|---|---|
| Branch | `feat/compiled-expression-api` ✅ |
| Working tree | clean (`git status --short` empty) ✅ |
| Based on current `main` | `HEAD` and `main` both at `7d14155`; `git diff --stat main...HEAD` empty ✅ |
| Stage 11 in `main` | `7d14155 feat: add function call syntax and AST (#10)`; `CallExpr` and `tests/test_function_calls.py` present on `main` ✅ |

No assignment PDF is in the repo; design is based on the assignment text from chat and `docs/decisions.md`.

---

### 1. Current state

**Public package exports (`__init__.py`)**

Currently exported: `UNDEFINED`, the exception hierarchy (`ExpressionError`, `ExpressionSyntaxError`, `ExpressionValidationError`, `ExpressionEvaluationError`, `ExpressionTypeError`, `DivisionByZeroError`, `UnknownFunctionError`, `FunctionArityError`), and `__version__`.

Not exported: `Engine`, `Expression`, internal modules (`_tokenizer`, `_parser`, `_ast`, `_evaluator`), `LexerError`, `ParserError` (they exist in `errors.py` but are not re-exported from the package root).

The package docstring and README explicitly state that `Engine` / `Expression` are planned but **not yet implemented**.

**Internal pipeline (source → value)**

Today, tests and internal callers use:

```text
source → tokenize(source) → parse(tokens) → evaluate(ast, variables) → result
```

Each internal stage is a module-level function on a private module:

- `_tokenizer.tokenize(source: str) -> list[Token]`
- `_parser.parse(tokens: Sequence[Token]) -> Expr`
- `_evaluator.evaluate(node: Expr, variables: Mapping[str, object] | None = None) -> object`

**What happens once vs every call**

| Step | When it runs today |
|---|---|
| Tokenize | Every time a test/helper calls `run(source, …)` |
| Parse | Every time |
| Evaluate | Every time |
| AST construction | Every time (via parse) |

There is **no** public compiled-expression wrapper; every evaluation repeats the full compile path.

**Existing compiled-expression abstraction**

None. The immutable AST (`Expr` union) exists and is reusable, but nothing public stores it between calls. `docs/decisions.md` explicitly deferred a compiled-expression object to a later stage.

**Error propagation**

- **Lex/parse:** `LexerError` / `ParserError` (subclasses of `ExpressionSyntaxError`), each carrying `.position` and a formatted message.
- **Evaluate:** `ExpressionEvaluationError` subclasses (`ExpressionTypeError`, `DivisionByZeroError`), with optional `.position`.
- **Unsupported nodes:** `CallExpr` reaching `_eval` raises `ExpressionEvaluationError("cannot evaluate unsupported expression node", node.position)`.
- **Missing variables:** no error — `variables.get(name, UNDEFINED)`.

**Reusable immutable structures**

All AST nodes are `@dataclass(frozen=True, slots=True)`. Tokens and `Position` are frozen. `UNDEFINED` is an immutable singleton. These are safe to store and share.

**Evaluator state locality**

Verified in `_evaluator.py`:

- `evaluate()` delegates to `_eval()` with only local recursion frames.
- `variables is None` is normalized to a fresh `{}` (does not mutate caller input).
- `LetExpr` uses a per-call `ChainMap({name: value}, variables)` — no shared scope object.
- No module-level mutable evaluation state; `_OPERATOR_SYMBOL` and operator frozensets are read-only constants.
- Tokenizer/parser likewise use per-call instance state (`_Tokenizer`, `_Parser`), no retained global mutable state.

**Test / public dependency on internal names**

All language-semantics tests import internal modules directly (`expression_engine._tokenizer`, `._parser`, `._evaluator`, `._ast`). Only `tests/test_package.py` uses the public package surface. **No public code depends on internal function signatures** — Stage 12 can wrap internals without breaking existing public consumers (only additive exports).

---

### 2. Smallest public API alternatives

#### Alternative A — `Engine` instance

```python
engine = Engine()
expression = engine.compile("2 + x")
result = expression.evaluate({"x": 3})
```

| Aspect | Assessment |
|---|---|
| Public surface | Two types (`Engine`, compiled object) + one method each — minimal and namespaced |
| Future functions | Natural extension point: later `Engine` can hold registered functions or a compile-time validation context without changing `Expression.evaluate(...)` |
| Unnecessary abstraction now? | `Engine` is stateless in Stage 12, but it matches documented/planned API and avoids a orphan top-level compile function |
| Thread safety | Stateless `Engine`; immutable `Expression`; evaluate is stateless per call — safe |
| Assignment / repo fit | Matches README, `__init__.py`, and `docs/decisions.md` references to `Engine` / `Expression` |

#### Alternative B — module-level `compile_expression`

```python
expression = compile_expression("2 + x")
result = expression.evaluate({"x": 3})
```

| Aspect | Assessment |
|---|---|
| Public surface | One function + one type — slightly smaller count, but adds a second entry point |
| Future functions | Would need either global registry, extra parameters on `compile_expression(...)`, or moving to an `Engine` later — likely a breaking or awkward migration |
| Unnecessary abstraction now? | The free function adds a parallel compile path with no benefit in Stage 12 |
| Thread safety | Same as A if the compiled object is immutable |
| Assignment / repo fit | Deviates from documented `Engine` / `Expression` plan |

**Recommendation: Alternative A (`Engine.compile` → `Expression.evaluate`).**

This matches the preferred direction and existing project documentation. No deviation warranted: a stateless `Engine` costs almost nothing now and is the documented home for later function registration and validation context.

---

### 3. Proposed exact interfaces

```python
# src/expression_engine/engine.py (new public implementation module, re-exported from __init__.py)

from collections.abc import Mapping

class Engine:
    """Compiles expression source text into reusable :class:`Expression` objects."""

    def compile(self, source: str) -> Expression:
        """Compile ``source`` to an immutable expression.

        Raises:
            ExpressionSyntaxError: If tokenization or parsing fails.
        """

@dataclass(frozen=True, slots=True)
class Expression:
    """An immutable compiled expression safe for repeated and concurrent evaluation."""

    _ast: Expr  # private; not part of public documented surface

    def evaluate(self, variables: Mapping[str, object] | None = None) -> object:
        """Evaluate this compiled expression.

        Raises:
            ExpressionEvaluationError: On runtime evaluation failure.
        """
```

**Decisions**

| Decision | Choice | Rationale |
|---|---|---|
| Class name | **`Expression`** | Already documented in `__init__.py` and README as the planned public type; `CompiledExpression` would diverge |
| `Engine` stateless? | **Yes, in Stage 12** | No instance fields; `compile()` is a pure wrapper over tokenize+parse. Later stages may add optional constructor args without changing `Expression` |
| Compiled object design | **`@dataclass(frozen=True, slots=True)`** | Matches every AST node and project immutability convention |
| AST field visibility | **Private `_ast: Expr`** | Hides tokenizer/parser/AST types from library users |
| Store original source? | **No** | Not needed for evaluation, thread safety, or current API; avoids extra mutable-adjacent surface (`repr` can stay minimal) |
| Expose AST publicly? | **No** | Requirement is to hide implementation details |
| `variables` type | **`Mapping[str, object] \| None`** | Matches existing `evaluate()` |
| Omitted variables | **Empty mapping** | Same as current evaluator (`None` → `{}`) |
| Top-level compile alias | **No** | `Engine.compile` is sufficient; duplicate entry points violate “smallest surface” |

**`__init__.py` additive exports**

Add `Engine` and `Expression` to `__all__`. Preserve all existing exports unchanged.

---

### 4. Compilation and evaluation boundary

**`Engine.compile(source)`**

```text
source: str
  → tokenize(source)          # may raise LexerError
  → parse(tokens)             # may raise ParserError
  → Expression(_ast=ast)      # immutable wrapper, no evaluation
```

No evaluation, no variable context, no validation pass, no caching.

**`Expression.evaluate(variables)`**

```text
variables: Mapping[str, object] | None
  → evaluate(self._ast, variables)   # existing internal evaluator only
  → runtime value
```

No tokenize, no parse, no AST rebuild.

**Testing compile/evaluate separation (no production instrumentation)**

Use `unittest.mock.patch` on the symbols as imported by the new public module:

```python
with patch("expression_engine.engine.tokenize") as mock_tokenize, \
     patch("expression_engine.engine.parse") as mock_parse:
    expr = Engine().compile("1 + 2")
    mock_tokenize.assert_called_once()
    mock_parse.assert_called_once()

    mock_tokenize.reset_mock()
    mock_parse.reset_mock()

    expr.evaluate({"x": 1})
    mock_tokenize.assert_not_called()
    mock_parse.assert_not_called()
```

Patch **`expression_engine.engine.tokenize`** / **`.parse`** (where-used), not only the underlying `_tokenizer` module, so the test proves the public layer does not re-invoke compile steps. No counters, hooks, or test-only code in production.

---

### 5. Errors

| Scenario | When | Expected exception |
|---|---|---|
| Invalid source syntax | `compile()` | `LexerError` or `ParserError` (both `ExpressionSyntaxError`) with `.position` |
| Missing variable | `evaluate()` | No exception; returns `UNDEFINED` |
| Type error (e.g. `"a" + 1`) | `evaluate()` | `ExpressionTypeError` (`ExpressionEvaluationError`) |
| Division by zero | `evaluate()` | `DivisionByZeroError` |
| Valid `CallExpr` compiled | `compile("f(1)")` | **Succeeds** — syntax only |
| `CallExpr` evaluated | `evaluate()` | `ExpressionEvaluationError("cannot evaluate unsupported expression node", …)` — existing evaluator behavior |

**Compile-time vs runtime:** syntax errors only during `compile()`; evaluation errors only during `evaluate()`. No new validation pass or error types in Stage 12. Existing messages and positions preserved via unchanged internal calls.

---

### 6. Immutability and thread safety

**Guarantees from the proposed design**

- **Repeated evaluation:** `Expression` holds a fixed `_ast`; each `evaluate()` call is independent.
- **No shared variable state:** variables are passed per call; evaluator uses local frames and per-`let` `ChainMap` layers.
- **Concurrent safety:** no writes to `Engine`, `Expression`, AST, or caller mapping during evaluation; multiple threads may call `expression.evaluate(different_mapping)` concurrently.
- **Caller mapping preserved:** evaluator only reads mappings (`get` / `ChainMap` read path); existing tests already prove this for the internal path.
- **AST immutability:** frozen dataclass nodes; wrapper is also frozen.
- **No new global mutable state:** new module adds only types and compile wrapper.

**Current mutation / shared-state risks (none blocking Stage 12)**

- `evaluate(..., variables=None)` allocates a new `{}` locally — safe.
- No evaluator fields on nodes; no caches; no registries.
- Frozen AST alone is insufficient for thread safety, but **evaluation is also stateless on shared objects** — the combination satisfies the requirement.

---

### 7. Future function support (without implementing now)

Stage 12 needs only: compile once → store AST → evaluate with variables.

Later stages can extend without breaking the public shape:

- **Built-ins:** resolved inside evaluator or a later validation pass; `Expression` still wraps AST; `evaluate()` signature unchanged.
- **Registered functions:** optional `Engine(functions=...)` or `engine.register(...)` added later; compile may gain a validation pass producing richer compiled state — still hideable inside `Expression`.
- **Local functions:** parser/AST/evaluator changes; public `compile` / `evaluate` boundary unchanged.

No placeholder registries, unused constructor kwargs, protocols, or config objects in Stage 12.

---

### 8. Expected Phase 2 files

```text
src/expression_engine/engine.py      # new: Engine + Expression (only public API implementation)
src/expression_engine/__init__.py  # export Engine, Expression; update short package docstring
tests/test_public_api.py           # new: focused public API tests
docs/decisions.md                  # short Stage 12 entry
```

**No changes expected** to tokenizer, parser, AST, evaluator, errors, `pyproject.toml`, README, or existing test modules — unless inspection during implementation reveals a strictly necessary issue (none found in Phase 1).

Putting `Engine`/`Expression` in `engine.py` (no leading underscore) matches the fact that this is the intentional public surface, while internals remain `_`-prefixed.

---

### 9. Focused Phase 2 tests (`tests/test_public_api.py`)

| Test | Stage 12 requirement proved |
|---|---|
| Import `Engine`, `Expression` from `expression_engine` | Public exports work |
| `Engine().compile("2 + 3").evaluate()` → `5` | Basic compile + evaluate |
| Same `Expression` with `{"x": 3}` and `{"x": 10}` | Repeated evaluation, different mappings |
| Patch `engine.tokenize` / `engine.parse`: called on compile, not on evaluate | Parse-once boundary |
| `evaluate()` with no variables / `None` | Omitted mapping → empty context |
| Caller dict unchanged after evaluate | No mapping mutation |
| `compile("1 +")` raises `ExpressionSyntaxError` | Syntax errors at compile time |
| `compile("1/0").evaluate()` raises `DivisionByZeroError` | Runtime errors only at evaluate |
| `compile("null").evaluate()` → `None`; missing var → `UNDEFINED` | Distinct null/undefined |
| `compile("let x = 1 in x").evaluate()` → `1` | Local bindings through public API |
| `Expression` is frozen; slots; no public AST attribute | Immutable compiled representation |
| `threading` / `concurrent.futures`: same expression, concurrent evaluates with different mappings | Concurrent safety |
| `compile("f(1)").evaluate()` raises `ExpressionEvaluationError` | Parsed-but-unsupported calls |
| One smoke assertion that internal `evaluate(parse(tokenize(...)))` still works | Regression for internal pipeline (not re-testing full language semantics) |

Parametrize where it reduces repetition (e.g. compile-time syntax errors vs evaluate-time errors). Do **not** duplicate broad semantics already covered in `test_evaluator.py`, `test_local_bindings.py`, `test_function_calls.py`, etc.

---

### 10. Documentation limits (Phase 2)

- Short docstrings on `Engine`, `Engine.compile`, `Expression`, `Expression.evaluate`.
- Short Stage 12 entry in `docs/decisions.md`: compile/evaluate split, immutable wrapper, thread safety, no caching, no function support yet.
- No README rewrite, no long architecture doc, no repetition of tokenizer/parser/AST internals.
- Comments only for non-obvious choices (e.g. why `_ast` is private).

---

**Phase 1 complete. No files were modified. No implementation performed. No commit or push.**

---

## User Prompt

Before proceeding to Stage 12 Phase 2, amend the Phase 1 design report only.

Do not modify any files.

Read the complete attached assignment PDF and confirm whether it changes any Stage 12 conclusion. The PDF is the primary source of truth even though it is not stored in the repository.

Apply these corrections to the proposed design:

1. Use a private implementation module:

```text
src/expression_engine/_engine.py
```

Export the public classes only from `expression_engine.__init__`.

Explain why this avoids introducing `expression_engine.engine` as an additional public import path and matches the repository's existing private-module convention.

2. Keep the public compiled-object class name `Expression`, because the current README and package documentation already use that planned name.

3. Define its stored representation as a private field conceptually equivalent to:

```python
_ast: Expr = field(repr=False)
```

The class should remain `@dataclass(frozen=True, slots=True)`.

Do not claim that `_ast` is technically inaccessible in Python. State instead that:

* there is no public `ast` property;
* AST types are not exported;
* `_ast` is an implementation detail;
* the AST is immutable;
* the AST should not appear in the compiled object's repr.

4. Correct the tokenize/parse reuse test proposal.

Use spies with `wraps` around the actual functions imported in `_engine.py`, rather than replacing them with plain mocks. The test must compile a real expression, record that tokenize and parse were each called once, perform repeated evaluations, and verify that their call counts do not increase.

Do not add counters, hooks, or test-only production behavior.

5. Do not make a concrete Stage 12 decision about how future registered functions are stored.

State only that later stages may add private immutable function-related state to `Engine`, `Expression`, or the evaluator without changing the current compile/evaluate public workflow. Do not introduce that state now.

6. Remove the proposed new internal-pipeline smoke test from `tests/test_public_api.py`.

Existing internal tests already provide regression coverage. Phase 2 should add focused public-API tests and then run the complete existing suite.

Confirm the final recommended interfaces, final expected Phase 2 file list, and corrected focused test list.

Stop after the amended report. Do not implement, commit, or push.
Backend Home Assignment — Expression Evaluation Engine
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

## Stage 12 — Amended Phase 1 Design Report (public compiled-expression API)

This amends the prior Phase 1 report only. **No files were modified, implemented, committed, or pushed.**

---

### Assignment PDF review — does it change Stage 12?

The assignment PDF (provided in chat; not stored in the repo) is the primary source of truth. Relevant requirements:

| Assignment requirement | Stage 12 scope | Effect on design |
|---|---|---|
| Evaluate expressions like `2 + 3 * (x - 1)` against named variables | ✅ Core goal of compile + evaluate | Confirms compile-once / evaluate-many API |
| Run millions of times per second, usually similar expressions | ✅ Strong motivation for parse-once | Confirms separation; **does not** require caching in Stage 12 |
| Open-source library for other teams | ✅ Clean public API, hide internals | Confirms `_engine.py` + `__init__` exports only |
| Booleans, conditionals, strings, variables | Already implemented internally | Public API wraps existing evaluator; no new semantics in Stage 12 |
| `+`, `-`, `*`, `/`, parentheses, variable lookup, common math | Math built-ins **not** in Stage 12 | No change — function evaluation deferred |
| Define and use functions inside expressions | Later stages | Stage 12 compiles `CallExpr` syntactically; evaluation of calls stays unsupported |
| Thread-safe | ✅ Required | Confirms immutable compiled object + stateless evaluation |
| Null and undefined throughout | Already implemented | Public API inherits existing behavior |

**Conclusion:** The PDF **does not change** the Stage 12 scope or the recommended Alternative A (`Engine` + `Expression`). It reinforces:

- compile-once / evaluate-many as the right shape for production reuse;
- a small, dependency-friendly public surface;
- thread safety and immutability as first-class design constraints.

Stage 12 remains **public compilation and repeated evaluation only** — not functions, caching, or performance optimization.

---

### 1. Current state (unchanged summary)

- **Public exports today:** `UNDEFINED`, exception hierarchy, `__version__`. No `Engine` / `Expression` yet.
- **Internal pipeline:** `source → tokenize → parse → evaluate → result`, repeated on every internal test `run()` call.
- **No compiled-expression abstraction** exists publicly; the immutable AST is reusable but not wrapped.
- **Evaluator state** is local per call; no shared mutable evaluation state on AST, modules, or caller mappings.
- **Internal modules** use `_`-prefixed names; public surface is `expression_engine.__init__` only.

---

### 2. Public API alternative (unchanged recommendation)

**Alternative A — `Engine.compile` → `Expression.evaluate`** remains recommended:

```python
from expression_engine import Engine

engine = Engine()
expression = engine.compile("2 + x")

expression.evaluate({"x": 3})
expression.evaluate({"x": 10})
```

Alternative B (module-level `compile_expression`) is rejected: duplicates entry points, diverges from documented `Engine` / `Expression` plan, and offers no benefit in Stage 12.

---

### 3. Final recommended interfaces

**Module layout:** implementation in `src/expression_engine/_engine.py`; public classes exported **only** from `expression_engine.__init__`.

**Why `_engine.py`, not `engine.py`?**

- Matches the repository convention: all implementation lives in `_`-prefixed modules (`_tokenizer`, `_parser`, `_evaluator`, `_ast`).
- Avoids introducing `expression_engine.engine` as a second public import path (`from expression_engine.engine import Engine` would become possible and diverge from the single-package-root API).
- Keeps the public contract exactly at `from expression_engine import Engine, Expression`, consistent with how `UNDEFINED` and exceptions are exported today.

```python
# src/expression_engine/_engine.py  (private implementation module)

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ._ast import Expr
from ._evaluator import evaluate
from ._parser import parse
from ._tokenizer import tokenize


class Engine:
    """Compiles expression source text into reusable :class:`Expression` objects."""

    def compile(self, source: str) -> Expression:
        """Compile ``source`` to an immutable :class:`Expression`.

        Raises:
            ExpressionSyntaxError: If tokenization or parsing fails.
        """
        return Expression(_ast=parse(tokenize(source)))


@dataclass(frozen=True, slots=True)
class Expression:
    """An immutable compiled expression safe for repeated and concurrent evaluation."""

    _ast: Expr = field(repr=False)

    def evaluate(self, variables: Mapping[str, object] | None = None) -> object:
        """Evaluate this compiled expression against ``variables``.

        Raises:
            ExpressionEvaluationError: On runtime evaluation failure.
        """
        return evaluate(self._ast, variables)
```

**`Expression` naming:** kept as **`Expression`** — matches README and `__init__.py` documentation that already plan this name (not `CompiledExpression`).

**Stored representation:**

```python
_ast: Expr = field(repr=False)
```

- `@dataclass(frozen=True, slots=True)` preserved.
- `_ast` is an **implementation detail**, not a hidden-in-Python sense: Python does not enforce private fields.
- Explicit design guarantees instead:
  - **No public `ast` property**
  - **AST types are not exported** from the package root
  - **`_ast` is an implementation detail** consumers should not depend on
  - **The AST is immutable** (frozen dataclass nodes)
  - **The AST must not appear in the compiled object's repr** (`field(repr=False)`)

**Other decisions (unchanged):**

| Decision | Choice |
|---|---|
| `Engine` stateless in Stage 12 | Yes — no instance fields |
| Store original source string | No |
| Expose AST publicly | No |
| `variables: Mapping[str, object] \| None` | Yes; `None` → empty mapping (matches evaluator) |
| Top-level `compile_expression` alias | No |

**`__init__.py` additive exports:** add `Engine` and `Expression` to `__all__`; preserve all existing exports.

---

### 4. Compilation and evaluation boundary (unchanged logic)

**`Engine.compile(source)`**

```text
source → tokenize(source) → parse(tokens) → Expression(_ast=ast)
```

**`Expression.evaluate(variables)`**

```text
variables → evaluate(self._ast, variables) → result
```

Evaluation must not tokenize or parse again.

---

### 5. Corrected tokenize/parse reuse test proposal

Use **`unittest.mock.patch` with `wraps`** on the functions as imported in `_engine.py` — not plain mocks that replace behavior:

```python
from unittest.mock import patch

import expression_engine._engine as engine_module
from expression_engine import Engine


def test_compile_once_evaluate_many_does_not_retokenize_or_reparse() -> None:
    with patch.object(engine_module, "tokenize", wraps=engine_module.tokenize) as spy_tokenize, \
         patch.object(engine_module, "parse", wraps=engine_module.parse) as spy_parse:
        expression = Engine().compile("2 + x")

        assert spy_tokenize.call_count == 1
        assert spy_parse.call_count == 1

        assert expression.evaluate({"x": 3}) == 5
        assert expression.evaluate({"x": 10}) == 12

        assert spy_tokenize.call_count == 1
        assert spy_parse.call_count == 1
```

This compiles a **real** expression through the actual tokenizer and parser, records one call each, performs repeated evaluations, and verifies counts do not increase. No counters, hooks, or test-only production code.

---

### 6. Errors (unchanged)

| Scenario | When | Exception |
|---|---|---|
| Invalid syntax | `compile()` | `LexerError` / `ParserError` (`ExpressionSyntaxError`) |
| Missing variable | `evaluate()` | Returns `UNDEFINED` (no exception) |
| Type error | `evaluate()` | `ExpressionTypeError` |
| Division by zero | `evaluate()` | `DivisionByZeroError` |
| Valid `CallExpr` | `compile("f(1)")` | Succeeds |
| `CallExpr` evaluated | `evaluate()` | `ExpressionEvaluationError` (existing unsupported-node path) |

No new validation pass or error types in Stage 12.

---

### 7. Immutability and thread safety (unchanged)

- Immutable `Expression` wrapping immutable AST
- Stateless `Engine` and stateless per-call evaluation
- No shared variable state between evaluations
- Caller mappings read-only (never mutated)
- No new global mutable state

---

### 8. Future function support — no concrete Stage 12 decision

Stage 12 does **not** decide how registered functions will be stored.

It is sufficient to note: **later stages may add private, immutable function-related state to `Engine`, `Expression`, or the evaluator** without changing the current public compile/evaluate workflow (`engine.compile(source)` → `expression.evaluate(variables)`).

No placeholder registries, constructor parameters, protocols, or configuration objects in Stage 12.

---

### 9. Final expected Phase 2 file list

```text
src/expression_engine/_engine.py   # private: Engine + Expression implementation
src/expression_engine/__init__.py  # re-export Engine, Expression only
tests/test_public_api.py           # new focused public-API tests
docs/decisions.md                  # short Stage 12 entry
```

**No changes** to tokenizer, parser, AST, evaluator, errors, `pyproject.toml`, README, or existing test modules unless a strictly necessary issue appears during implementation (none identified).

---

### 10. Final corrected focused test list (`tests/test_public_api.py`)

| Test | Stage 12 requirement |
|---|---|
| Import `Engine`, `Expression` from `expression_engine` | Public exports |
| `Engine().compile("2 + 3").evaluate()` → `5` | Basic compile + evaluate |
| Same `Expression`, different mappings (`{"x": 3}` / `{"x": 10}`) | Repeated evaluation |
| **`wraps` spies** on `_engine.tokenize` / `_engine.parse`: one call each at compile; counts unchanged after repeated `evaluate()` | Parse-once boundary (real compile, no production instrumentation) |
| `evaluate()` with `None` / omitted variables | Empty mapping behavior |
| Caller dict unchanged after `evaluate()` | Mapping preservation |
| `compile("1 +")` raises `ExpressionSyntaxError` | Syntax errors at compile time |
| `compile("1/0").evaluate()` raises `DivisionByZeroError` | Runtime errors at evaluate time |
| `compile("null").evaluate()` → `None`; missing var → `UNDEFINED` | Null/undefined distinct |
| `compile("let x = 1 in x").evaluate()` → `1` | Local bindings through public API |
| `Expression` frozen, slots, no public `ast` attribute; repr omits `_ast` | Immutable compiled representation |
| Concurrent evaluation (e.g. `threading` or `concurrent.futures`) of same `Expression` with independent mappings | Thread safety |
| `compile("f(1)").evaluate()` raises `ExpressionEvaluationError` | Parsed-but-unsupported calls |

**Removed:** internal-pipeline smoke test (`evaluate(parse(tokenize(...)))`). Existing internal test modules already provide regression coverage; Phase 2 runs the **complete existing suite** after adding focused public-API tests.

Parametrize where it reduces repetition (compile-time vs evaluate-time errors). Do not duplicate broad language semantics already covered in evaluator, binding, parser, or function-call tests.

---

### 11. Documentation limits (Phase 2, unchanged)

- Short docstrings on public interfaces
- Short Stage 12 entry in `docs/decisions.md`
- No README rewrite, no long architecture doc, no repetition of tokenizer/parser/AST internals

---

**Amended Phase 1 complete. No files modified. No implementation. No commit or push.**

---

## User Prompt

Before proceeding to Stage 12 Phase 2, amend the Phase 1 design report only.

Do not modify any files.

Read the complete attached assignment PDF and confirm whether it changes any Stage 12 conclusion. The PDF is the primary source of truth even though it is not stored in the repository.

Apply these corrections to the proposed design:

1. Use a private implementation module:

```text
src/expression_engine/_engine.py
```

Export the public classes only from `expression_engine.__init__`.

Explain why this avoids introducing `expression_engine.engine` as an additional public import path and matches the repository's existing private-module convention.

2. Keep the public compiled-object class name `Expression`, because the current README and package documentation already use that planned name.

3. Define its stored representation as a private field conceptually equivalent to:

```python
_ast: Expr = field(repr=False)
```

The class should remain `@dataclass(frozen=True, slots=True)`.

Do not claim that `_ast` is technically inaccessible in Python. State instead that:

* there is no public `ast` property;
* AST types are not exported;
* `_ast` is an implementation detail;
* the AST is immutable;
* the AST should not appear in the compiled object's repr.

4. Correct the tokenize/parse reuse test proposal.

Use spies with `wraps` around the actual functions imported in `_engine.py`, rather than replacing them with plain mocks. The test must compile a real expression, record that tokenize and parse were each called once, perform repeated evaluations, and verify that their call counts do not increase.

Do not add counters, hooks, or test-only production behavior.

5. Do not make a concrete Stage 12 decision about how future registered functions are stored.

State only that later stages may add private immutable function-related state to `Engine`, `Expression`, or the evaluator without changing the current compile/evaluate public workflow. Do not introduce that state now.

6. Remove the proposed new internal-pipeline smoke test from `tests/test_public_api.py`.

Existing internal tests already provide regression coverage. Phase 2 should add focused public-API tests and then run the complete existing suite.

Confirm the final recommended interfaces, final expected Phase 2 file list, and corrected focused test list.

Stop after the amended report. Do not implement, commit, or push.


---

## Cursor Response

## Stage 12 — Amended Phase 1 Design Report (public compiled-expression API)

This amends the prior Phase 1 report only. **No files were modified, implemented, committed, or pushed.**

---

### Assignment PDF review — does it change Stage 12?

The assignment PDF (provided in chat; not stored in the repo) is the primary source of truth.

| PDF requirement | Stage 12 impact |
|---|---|
| Evaluate expressions like `2 + 3 * (x - 1)` against named variables | Core goal: compile once, evaluate many with different mappings |
| Run millions of times per second, usually similar expressions | Reinforces compile/evaluate separation; **does not** require caching in Stage 12 |
| Open-source library for other backend teams | Clean public API; hide tokenizer, parser, AST, evaluator |
| Booleans, conditionals, strings, variables | Already implemented internally; public API wraps existing evaluator |
| `+`, `-`, `*`, `/`, parentheses, variable lookup, common math | Math built-ins deferred; Stage 12 does not add function evaluation |
| Define and use functions inside expressions | Later stages; Stage 12 compiles `CallExpr` syntactically only |
| Thread-safe | Immutable compiled object + stateless per-call evaluation |
| Null and undefined throughout | Inherited from existing evaluator behavior |

**Conclusion:** The PDF **does not change** Stage 12 scope or the recommended API shape. It reinforces compile-once / evaluate-many, a minimal public surface, and thread safety. Stage 12 remains **public compilation and repeated evaluation only** — not functions, caching, or performance work.

---

### 1. Current state (summary)

- **Public exports today:** `UNDEFINED`, exception hierarchy, `__version__`. No `Engine` / `Expression` yet.
- **Internal pipeline:** `source → tokenize → parse → evaluate → result`, repeated on every internal `run()` call.
- **No public compiled-expression wrapper** exists; the immutable AST is reusable but not stored between calls.
- **Evaluator state** is local per call; no shared mutable state on AST, engine, or caller mappings.
- **Convention:** implementation in `_`-prefixed modules; public surface via `expression_engine.__init__` only.

---

### 2. Public API recommendation (unchanged)

**Alternative A** remains recommended:

```python
from expression_engine import Engine

engine = Engine()
expression = engine.compile("2 + x")

expression.evaluate({"x": 3})
expression.evaluate({"x": 10})
```

Alternative B (module-level `compile_expression`) is rejected: extra entry point, diverges from documented plan, no Stage 12 benefit.

---

### 3. Final recommended interfaces

#### Module layout

```text
src/expression_engine/_engine.py   ← private implementation
src/expression_engine/__init__.py  ← re-export Engine, Expression only
```

**Why `_engine.py`, not `engine.py`?**

- Matches the repository convention: all implementation lives in `_`-prefixed modules (`_tokenizer`, `_parser`, `_evaluator`, `_ast`).
- Avoids introducing `expression_engine.engine` as a second public import path (`from expression_engine.engine import Engine` would become possible and fragment the API).
- Keeps the public contract at a single entry point: `from expression_engine import Engine, Expression`, consistent with how `UNDEFINED` and exceptions are exported today.

#### `Engine`

```python
class Engine:
    """Compiles expression source text into reusable Expression objects."""

    def compile(self, source: str) -> Expression:
        """Compile source to an immutable Expression.

        Raises:
            ExpressionSyntaxError: If tokenization or parsing fails.
        """
```

- **Stateless in Stage 12:** no instance fields.
- **`compile`:** `tokenize(source)` → `parse(tokens)` → `Expression(_ast=ast)`.

#### `Expression`

```python
@dataclass(frozen=True, slots=True)
class Expression:
    """An immutable compiled expression safe for repeated and concurrent evaluation."""

    _ast: Expr = field(repr=False)

    def evaluate(self, variables: Mapping[str, object] | None = None) -> object:
        """Evaluate this compiled expression.

        Raises:
            ExpressionEvaluationError: On runtime evaluation failure.
        """
```

- **Class name:** **`Expression`** — matches README and `__init__.py` documentation (not `CompiledExpression`).
- **Stored representation:** `_ast: Expr = field(repr=False)`.
- **`@dataclass(frozen=True, slots=True)`** preserved.

**Encapsulation (not Python-enforced privacy):**

- There is **no public `ast` property**.
- **AST types are not exported** from the package root.
- **`_ast` is an implementation detail** — consumers should not depend on it.
- **The AST is immutable** (frozen dataclass nodes).
- **The AST must not appear in the compiled object's repr** (`field(repr=False)`).

Python does not make `_ast` technically inaccessible; the design simply does not expose it as public API.

#### Other decisions

| Decision | Choice |
|---|---|
| Store original source string | No |
| Top-level `compile_expression` alias | No |
| `variables: Mapping[str, object] \| None` | Yes; `None` → empty mapping (matches evaluator) |
| New validation pass | No |

**`__init__.py`:** add `Engine` and `Expression` to `__all__`; preserve all existing exports.

---

### 4. Compilation and evaluation boundary

**`Engine.compile(source)`**

```text
source → tokenize(source) → parse(tokens) → Expression(_ast=ast)
```

**`Expression.evaluate(variables)`**

```text
variables → evaluate(self._ast, variables) → result
```

Evaluation must **not** tokenize or parse again.

---

### 5. Corrected tokenize/parse reuse test

Use **`unittest.mock.patch` with `wraps`** on the functions as imported in `_engine.py` — not plain mocks that replace behavior:

```python
from unittest.mock import patch

import expression_engine._engine as engine_module
from expression_engine import Engine


def test_compile_once_evaluate_many_does_not_retokenize_or_reparse() -> None:
    with patch.object(engine_module, "tokenize", wraps=engine_module.tokenize) as spy_tokenize, \
         patch.object(engine_module, "parse", wraps=engine_module.parse) as spy_parse:
        expression = Engine().compile("2 + x")

        assert spy_tokenize.call_count == 1
        assert spy_parse.call_count == 1

        assert expression.evaluate({"x": 3}) == 5
        assert expression.evaluate({"x": 10}) == 12

        assert spy_tokenize.call_count == 1
        assert spy_parse.call_count == 1
```

- Compiles a **real** expression through actual tokenizer and parser.
- Records one call each at compile time.
- Repeated evaluations must not increase call counts.
- No counters, hooks, or test-only production code.

---

### 6. Errors (unchanged)

| Scenario | When | Exception |
|---|---|---|
| Invalid syntax | `compile()` | `LexerError` / `ParserError` (`ExpressionSyntaxError`) |
| Missing variable | `evaluate()` | Returns `UNDEFINED` |
| Type error | `evaluate()` | `ExpressionTypeError` |
| Division by zero | `evaluate()` | `DivisionByZeroError` |
| Valid `CallExpr` | `compile("f(1)")` | Succeeds |
| `CallExpr` evaluated | `evaluate()` | `ExpressionEvaluationError` (existing unsupported-node path) |

---

### 7. Immutability and thread safety (unchanged)

- Immutable `Expression` wrapping immutable AST.
- Stateless `Engine`; stateless per-call evaluation.
- No shared variable state between evaluations.
- Caller mappings read-only, never mutated.
- No new global mutable state.

---

### 8. Future function support — no concrete Stage 12 decision

Stage 12 does **not** decide how registered functions will be stored.

**Later stages may add private, immutable function-related state to `Engine`, `Expression`, or the evaluator** without changing the current public workflow:

```text
engine.compile(source) → expression.evaluate(variables)
```

No placeholder registries, constructor parameters, or configuration objects in Stage 12.

---

### 9. Final expected Phase 2 file list

```text
src/expression_engine/_engine.py   # private: Engine + Expression
src/expression_engine/__init__.py  # re-export Engine, Expression only
tests/test_public_api.py           # new focused public-API tests
docs/decisions.md                  # short Stage 12 entry
```

**No changes** to tokenizer, parser, AST, evaluator, errors, `pyproject.toml`, README, or existing test modules unless a strictly necessary issue appears during implementation.

---

### 10. Final corrected focused test list (`tests/test_public_api.py`)

| Test | Stage 12 requirement |
|---|---|
| Import `Engine`, `Expression` from `expression_engine` | Public exports |
| `Engine().compile("2 + 3").evaluate()` → `5` | Basic compile + evaluate |
| Same `Expression`, different mappings | Repeated evaluation |
| **`wraps` spies** on `_engine.tokenize` / `_engine.parse`: one call each at compile; counts unchanged after repeated `evaluate()` | Parse-once boundary |
| `evaluate()` with `None` / omitted variables | Empty mapping behavior |
| Caller dict unchanged after `evaluate()` | Mapping preservation |
| `compile("1 +")` raises `ExpressionSyntaxError` | Syntax errors at compile time |
| `compile("1/0").evaluate()` raises `DivisionByZeroError` | Runtime errors at evaluate time |
| `compile("null").evaluate()` → `None`; missing var → `UNDEFINED` | Null/undefined distinct |
| `compile("let x = 1 in x").evaluate()` → `1` | Local bindings through public API |
| `Expression` frozen, slots, no public `ast` attribute; repr omits `_ast` | Immutable compiled representation |
| Concurrent evaluation of same `Expression` with independent mappings | Thread safety |
| `compile("f(1)").evaluate()` raises `ExpressionEvaluationError` | Parsed-but-unsupported calls |

**Removed:** internal-pipeline smoke test. Existing internal tests provide regression coverage; Phase 2 runs the **complete existing suite** after adding focused public-API tests.

Parametrize where it reduces repetition. Do not duplicate broad language semantics already covered elsewhere.

---

### 11. Documentation limits (Phase 2)

- Short docstrings on public interfaces.
- Short Stage 12 entry in `docs/decisions.md`.
- No README rewrite, no long architecture doc, no repetition of tokenizer/parser/AST internals.

---

**Amended Phase 1 complete. No files modified. No implementation. No commit or push.**

---

## User Prompt

Proceed with Stage 12, Phase 2 only: implement the approved minimal public compilation and repeated-evaluation API.

Before editing, reconfirm:

```bash
git branch --show-current
git status --short
git log --oneline -3
```

Expected branch:

```text
feat/compiled-expression-api
```

The working tree must be clean. If the branch is incorrect or the tree is not clean, stop and report without modifying files.

Use the amended Phase 1 design as the implementation plan.

## Scope

Implement only:

```python
from expression_engine import Engine, Expression

engine = Engine()
expression = engine.compile("2 + x")

expression.evaluate({"x": 3})
expression.evaluate({"x": 10})
```

Compilation must tokenize and parse once.

Repeated evaluation must reuse the stored immutable AST and must not tokenize or parse again.

Do not implement any later stage.

## Expected files

Limit changes to:

```text
src/expression_engine/_engine.py
src/expression_engine/__init__.py
tests/test_public_api.py
docs/decisions.md
```

Do not modify tokenizer, parser, AST, evaluator, errors, existing semantic tests, dependencies, project configuration, or README unless a strictly necessary problem is discovered.

If another file appears necessary, stop before modifying it and explain why.

## Required implementation

### `src/expression_engine/_engine.py`

Implement `Expression` and `Engine`.

Use the existing tokenizer, parser, evaluator, AST types, errors, and project conventions. Do not duplicate their behavior.

The intended design is conceptually:

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from expression_engine._ast import Expr
from expression_engine._evaluator import evaluate
from expression_engine._parser import parse
from expression_engine._tokenizer import tokenize


@dataclass(frozen=True, slots=True)
class Expression:
    """An immutable compiled expression reusable across evaluations."""

    _ast: Expr = field(repr=False)

    def evaluate(
        self,
        variables: Mapping[str, object] | None = None,
    ) -> object:
        """Evaluate the compiled expression with the supplied variables."""
        return evaluate(self._ast, variables)


class Engine:
    """Compiles source expressions into reusable Expression objects."""

    __slots__ = ()

    def compile(self, source: str) -> Expression:
        """Compile source text into an immutable Expression."""
        return Expression(parse(tokenize(source)))
```

This is the approved behavior, not necessarily a demand to copy formatting verbatim. Follow the repository's existing import and docstring conventions.

Important requirements:

* `Engine` remains stateless.
* `Expression` is `@dataclass(frozen=True, slots=True)`.
* `_ast` uses `field(repr=False)`.
* Do not store the original source string.
* Do not expose an `ast` property.
* Do not export AST, tokenizer, parser, or evaluator details.
* Do not add a top-level `compile_expression` alias.
* Do not add caching.
* Do not add validation.
* Do not add registries, constructor options, or function-related state.
* Do not catch and rewrap existing engine errors.
* Preserve exact existing syntax and evaluation error propagation.
* Do not mutate caller-provided mappings.
* Do not use `eval()` or `exec()`.

### `src/expression_engine/__init__.py`

Add `Engine` and `Expression` to the public package exports.

Preserve every existing public export.

Keep the package docstring short and accurate. Do not rewrite unrelated documentation.

The supported public import must be:

```python
from expression_engine import Engine, Expression
```

Do not create another public implementation module.

### `tests/test_public_api.py`

Add focused public-API tests only.

Test through:

```python
from expression_engine import ...
```

except for the tokenize/parse spy test, which may inspect the private `_engine` module solely to verify the compile/evaluate boundary.

Cover:

1. `Engine` and `Expression` are importable from `expression_engine`.
2. A basic expression compiles and evaluates.
3. The same `Expression` evaluates repeatedly with different mappings.
4. Tokenization and parsing happen once during compilation and are not repeated during evaluation.
5. Omitted variables and explicit `None` use an empty variable mapping.
6. A caller-provided dictionary remains unchanged.
7. Invalid syntax raises the existing syntax error during `compile()`.
8. Division by zero and type errors are delayed until `evaluate()`.
9. `null` evaluates to `None`.
10. A missing variable evaluates to the existing `UNDEFINED` singleton.
11. Local variable bindings work through the public API.
12. The compiled object is immutable.
13. There is no public `ast` attribute.
14. `_ast` does not appear in `repr(expression)`.
15. The same compiled expression can be evaluated concurrently with independent mappings.
16. A valid function call expression compiles successfully but raises the current existing evaluation error when evaluated.

Do not duplicate broad arithmetic, precedence, Boolean, conditional, string, binding, or parser tests already covered elsewhere.

For the tokenize/parse reuse test, use spies with `wraps` around the symbols imported in `_engine.py`.

The test should:

* compile a real expression;
* confirm `tokenize` and `parse` were each called exactly once;
* perform more than one evaluation;
* confirm their call counts remain exactly one.

Do not add instrumentation or test-only behavior to production code.

For concurrency, keep the test small and deterministic. Use the standard library only. Verify returned values rather than attempting to benchmark performance.

For immutability, verify an attempted field assignment fails with the appropriate dataclass immutability error. Do not depend on mutating the internal AST.

### `docs/decisions.md`

Add one concise Stage 12 decision entry covering only:

* the `Engine.compile()` / `Expression.evaluate()` boundary;
* compilation once and repeated AST reuse;
* private immutable `_ast`;
* stateless evaluation and concurrent safety;
* no input mapping mutation;
* no cache or function support in this stage;
* why no top-level compile alias was added.

Clearly record that this design followed the candidate-approved Phase 1 decision.

Do not write a long architecture section and do not repeat tokenizer/parser/evaluator documentation.

## Validation

After implementation:

1. Review the complete diff.
2. Run focused Stage 12 tests.
3. Run the complete existing test suite.
4. Run the project's existing lint and type-check commands only if they are already configured.
5. Run:

```bash
git diff --check
git status --short
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
```

Do not install or introduce new tools merely to run lint or type checking.

Do not claim a check passed unless it was actually executed.

## Final report

Report:

1. What changed.
2. Which files changed.
3. Why this approach was selected.
4. Assumptions and design decisions.
5. Edge cases covered.
6. Known limitations and out-of-scope items.
7. Exact validation commands executed.
8. Exact test, lint, type-check, and warning results.
9. The final `git status --short`.
10. Confirmation that no commit or push was performed.

Do not commit, push, merge, publish, or open a pull request.

Stop after Stage 12 Phase 2 implementation and verification.


---

## Cursor Response

I'll reconfirm git state, then implement the approved Stage 12 public API.


Branch and working tree look good. Implementing the four expected files next.


Stage 12 Phase 2 is complete. No commit or push was performed.

## Final Report — Stage 12 Phase 2

### 1. What changed

- Added private module `_engine.py` with stateless `Engine.compile()` and immutable `Expression.evaluate()`.
- `Engine.compile(source)` runs `tokenize` → `parse` once and stores the AST in `Expression(_ast=...)`.
- `Expression.evaluate(variables)` calls the existing evaluator only; no re-tokenize or re-parse.
- Updated `__init__.py` to export `Engine` and `Expression` alongside all existing public exports.
- Added focused public-API tests (`tests/test_public_api.py`, 18 tests).
- Added a short Stage 12 entry in `docs/decisions.md`.

### 2. Files changed

- `src/expression_engine/_engine.py` (new)
- `src/expression_engine/__init__.py` (modified)
- `tests/test_public_api.py` (new)
- `docs/decisions.md` (modified)

No other files were touched.

### 3. Why this approach

The amended Phase 1 design wraps existing internals behind a minimal public surface:

- `_engine.py` follows the `_`-prefixed private-module convention.
- Public import stays at `from expression_engine import Engine, Expression` — no `expression_engine.engine` path.
- `Expression` stores a private immutable `_ast` with `field(repr=False)`.
- No caching, validation, registries, or function state — smallest change that satisfies compile-once / evaluate-many and thread safety.

### 4. Assumptions and design decisions

- **`Expression`** name kept (matches README / package docs).
- **`Engine`** is stateless (`__slots__ = ()`, no instance fields).
- **`_ast`** is an implementation detail: no public `ast` property, AST types not exported, repr omits `_ast`.
- **`variables=None`** → empty mapping (matches evaluator).
- Existing errors propagate unchanged (no catch/re-wrap).
- **`CallExpr`** compiles successfully; evaluation hits existing unsupported-node error.

### 5. Edge cases covered (tests)

Importability; basic compile/evaluate; repeated evaluation with different mappings; compile-once boundary via `wraps` spies; omitted/`None` variables; caller mapping preservation; syntax error at compile; division-by-zero and type error at evaluate; `null` → `None`; missing var → `UNDEFINED`; local bindings; immutability; no public `ast`; repr omits `_ast`; concurrent evaluation; valid `f(1)` compiles but fails on evaluate.

### 6. Known limitations / out of scope

No function evaluation, built-ins, registries, local functions, validation pass, compilation cache, performance work, README update, or top-level `compile_expression` alias.

### 7. Exact validation commands executed

```bash
git branch --show-current
git status --short
git log --oneline -3

PYTHONPATH=src python -m pytest tests/test_public_api.py -q
PYTHONPATH=src python -m pytest -q
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
```

### 8. Exact results

| Command | Result |
|---|---|
| Branch | `feat/compiled-expression-api` ✅ |
| Pre-edit status | clean ✅ |
| `pytest tests/test_public_api.py -q` | **18 passed** in 0.08s |
| `pytest -q` (full suite) | **484 passed** in 0.52s |
| `git diff --check` | clean (exit 0) |
| `grep … eval/exec` | no matches (exit 1) |
| Lint / type-check | **Not run** — none configured in `pyproject.toml` |

No failures, no warnings.

### 9. Final `git status --short`

```
 M docs/decisions.md
 M src/expression_engine/__init__.py
?? src/expression_engine/_engine.py
?? tests/test_public_api.py
```

### 10. Commit/push confirmation

No commit, push, merge, publish, or pull request was performed. Changes remain uncommitted on `feat/compiled-expression-api`.

---

## User Prompt

Make one focused test correction before commit.

Do not modify production code or documentation.

In tests/test_public_api.py, change:

- test_evaluate_with_none_uses_empty_mapping
- test_evaluate_with_omitted_variables_uses_empty_mapping

Both tests currently use the constant expression "1 + 2", which does not access the variables mapping and therefore does not prove empty-mapping behavior.

Use a missing-variable expression and assert the existing UNDEFINED singleton:

def test_evaluate_with_none_uses_empty_mapping() -> None:
    expression = Engine().compile("missing")
    assert expression.evaluate(None) is UNDEFINED

def test_evaluate_with_omitted_variables_uses_empty_mapping() -> None:
    expression = Engine().compile("missing")
    assert expression.evaluate() is UNDEFINED

Do not make any other changes.

Then run:

PYTHONPATH=src python -m pytest tests/test_public_api.py -q
PYTHONPATH=src python -m pytest -q
git diff --cached --check
git status --short

Report exact results. Do not commit or push.

Make one focused test correction before commit.

Do not modify production code or documentation.

In tests/test_public_api.py, change:

- test_evaluate_with_none_uses_empty_mapping
- test_evaluate_with_omitted_variables_uses_empty_mapping

Both tests currently use the constant expression "1 + 2", which does not access the variables mapping and therefore does not prove empty-mapping behavior.

Use a missing-variable expression and assert the existing UNDEFINED singleton:

def test_evaluate_with_none_uses_empty_mapping() -> None:
    expression = Engine().compile("missing")
    assert expression.evaluate(None) is UNDEFINED

def test_evaluate_with_omitted_variables_uses_empty_mapping() -> None:
    expression = Engine().compile("missing")
    assert expression.evaluate() is UNDEFINED

Do not make any other changes.

Then run:

PYTHONPATH=src python -m pytest tests/test_public_api.py -q
PYTHONPATH=src python -m pytest -q
git diff --cached --check
git status --short

Report exact results. Do not commit or push.

---

## Cursor Response

Updated only the two requested tests in `tests/test_public_api.py`. No production code or documentation was changed.

### Validation results

```
PYTHONPATH=src python -m pytest tests/test_public_api.py -q
→ 18 passed in 0.06s

PYTHONPATH=src python -m pytest -q
→ 484 passed in 0.44s

git diff --cached --check
→ clean (exit 0)

git status --short
M  docs/decisions.md
M  src/expression_engine/__init__.py
A  src/expression_engine/_engine.py
AM tests/test_public_api.py
```

No failures, no warnings. No commit or push was performed.

Note: `tests/test_public_api.py` shows `AM` because earlier staged content exists plus the new unstaged test correction. Stage the file again before commit if you want the updated tests included.

---

## User Prompt

Implement Stage 13 and Stage 14 together on the current branch, but execute them sequentially and keep the changes focused.

Stage 13: built-in mathematical functions.
Stage 14: safely registered host functions.

Do not implement local function definitions, local-function AST nodes, recursion, a cache, a web API, a CLI, benchmarks, README finalization, or the product-design feature from page 2 of the assignment.

Do not commit, push, merge, or open a pull request.

## Mandatory inspection before editing

Read the entire assignment PDF and inspect the current repository, including at least:

* `src/expression_engine/_engine.py`
* `src/expression_engine/_evaluator.py`
* `src/expression_engine/_ast.py`
* `src/expression_engine/_parser.py`
* `src/expression_engine/errors.py`
* `src/expression_engine/__init__.py`
* `tests/test_public_api.py`
* `tests/test_function_calls.py`
* relevant evaluator and error tests
* `docs/decisions.md`
* `pyproject.toml`

Before changing code, provide a concise inspection report containing:

1. Current function-call parsing and AST behavior.
2. Current public `Engine` and `Expression` API.
3. Current unsupported `CallExpr` evaluation behavior.
4. Existing function-related error classes.
5. Proposed minimal architecture.
6. Exact files expected to change.
7. Assumptions and important edge cases.

Then continue with implementation using the decisions below. Do not pause for confirmation unless the repository directly contradicts one of these decisions.

## Public API

Extend the existing API without breaking current callers:

```python
engine = Engine(
    functions={
        "double": lambda value: value * 2,
    }
)

expression = engine.compile("double(x) + sqrt(9)")
result = expression.evaluate({"x": 4})
```

Required constructor shape:

```python
Engine(
    functions: Mapping[str, Callable[..., object]] | None = None
)
```

`Engine()` with no arguments must behave exactly as it does today.

Do not add a top-level compile helper or a second registration API.

## Architecture requirements

* Keep compilation separate from evaluation.
* Parse once and validate function calls once during `Engine.compile()`.
* Do not resolve names, inspect signatures, tokenize, or parse again during evaluation.
* Keep `Expression` immutable and safe for concurrent evaluation.
* Do not store evaluation-specific state on `Engine` or `Expression`.
* Snapshot the caller-provided function mapping. Never mutate it or retain a mutable reference to it.
* Function metadata stored by the engine must be immutable.
* Avoid global mutable state.
* A static immutable built-in registry is acceptable.
* Do not create a generic visitor framework or unnecessary abstraction hierarchy.
* Prefer exactly one focused private module, such as `_functions.py`, if separating function metadata, validation, and invocation keeps `_engine.py` and `_evaluator.py` small. Do not create several new modules.
* Do not use `eval()`, `exec()`, dynamic imports, attribute lookup on `math`, or arbitrary Python expression execution.

## Stage 13: built-in functions

Implement exactly these built-ins:

* `abs`
* `min`
* `max`
* `round`
* `floor`
* `ceil`
* `sqrt`
* `pow`
* `log`

Only expose these exact names. Do not expose the `math` module or other Python built-ins.

### Common rules

* Numeric arguments accept only exact built-in `int` and `float`.
* `bool` is not numeric.
* `None`, `UNDEFINED`, strings, containers, subclasses, and arbitrary objects are rejected unless explicitly allowed below.
* Arguments are evaluated left-to-right and exactly once.
* Wrong arity raises `FunctionArityError` during compilation.
* Unknown function names raise `UnknownFunctionError` during compilation.
* Domain and runtime calculation failures raise a stable engine-specific evaluation error at the call position.
* Never silently convert missing variables, `null`, `undefined`, type errors, or function failures to `0`.

### Exact built-in behavior

`abs(x)`

* exactly one numeric argument;
* preserve normal `int` or `float` result type.

`floor(x)` and `ceil(x)`

* exactly one numeric argument;
* return an exact `int`.

`sqrt(x)`

* exactly one numeric argument;
* return `float`;
* reject negative values with an engine-specific evaluation error.

`log(x)`

* exactly one numeric argument;
* natural logarithm only;
* reject zero and negative values with an engine-specific evaluation error;
* custom logarithm bases are out of scope.

`pow(x, y)`

* exactly two numeric arguments;
* two integers with a non-negative integer exponent return `int`;
* all other valid numeric combinations return `float`;
* complex results are unsupported and must raise an engine-specific evaluation error.

`round(x)` and `round(x, ndigits)`

* one or two arguments;
* `x` must be numeric and non-boolean;
* `ndigits` must be an exact `int`, not `bool`;
* use documented Python half-to-even rounding behavior;
* do not expose keyword arguments.

`min(...)` and `max(...)`

* require at least two arguments;
* for this stage accept numeric arguments only;
* allow mixed `int` and `float`;
* reject booleans, strings, `None`, `UNDEFINED`, subclasses, and arbitrary objects;
* string ordering remains out of scope.

## Stage 14: registered host functions

Registered functions use the same call syntax as built-ins.

### Registration rules

* The `functions` argument must be a mapping or `None`.
* Copy it once during `Engine` construction.
* Never mutate the supplied mapping.
* Registered names must follow the existing language identifier rules.
* Keywords are invalid registered names.
* Built-in names are reserved and cannot be overridden.
* Each registered value must be callable.
* Invalid registration raises a clear existing engine error where appropriate. Add a new small engine-specific error class only if the existing hierarchy cannot represent the failure clearly.

### Callable signature rules

Inspect each callable signature once during `Engine` construction, not during evaluation.

Support:

* positional-only parameters;
* positional-or-keyword parameters;
* trailing positional parameters with defaults.

Reject as unsupported registration shapes:

* `*args`;
* keyword-only parameters;
* `**kwargs`;
* signatures that cannot be inspected.

Record immutable minimum and maximum positional arity.

During compilation:

* validate every registered call against its recorded arity;
* raise `FunctionArityError` for too few or too many arguments;
* raise `UnknownFunctionError` for unresolved names.

Do not validate argument value types during compilation.

### Invocation rules

* Evaluate all arguments left-to-right and exactly once.
* Invoke the stored callable directly with positional arguments.
* Do not pass the variables mapping, engine, expression, AST, or internal state to the callable.
* If the callable raises an existing `ExpressionError`, propagate it.
* If it raises another normal `Exception`, wrap it in `ExpressionEvaluationError`, include the function name and call position, and preserve the original exception as the cause.
* Do not catch `BaseException`.

Allowed return values are only:

* exact `int`
* exact `float`
* exact `str`
* exact `bool`
* `None`
* the exported `UNDEFINED` singleton

Reject all other return values with a clear engine-specific type or evaluation error at the call position.

The library guarantees that its compiled representation and function registry are immutable. It does not guarantee that user-provided callable implementations are internally thread-safe; document this distinction in `docs/decisions.md`.

## Function resolution

For this combined stage, resolution order is:

1. registered host function;
2. built-in function.

Built-in names are reserved, so there is no ambiguity between the two.

Local functions are not implemented in this task. Do not add placeholder local-function resolution.

## Compile-time validation

Add only the smallest validation pass needed for built-in and registered function calls.

It must recursively inspect all existing AST node types and validate `CallExpr` names and arities.

Requirements:

* validation runs once during `Engine.compile()`;
* it must inspect calls inside arithmetic, comparisons, Boolean expressions, conditional branches, call arguments, and local variable bindings;
* do not introduce a generic visitor class;
* do not mutate the AST;
* do not reject free variable names;
* short-circuiting and selected-branch evaluation remain runtime behavior, but unknown function names and invalid arity are compile-time errors even inside branches that may not execute.

## Expected file scope

Prefer the following focused file set:

* add `src/expression_engine/_functions.py`
* modify `src/expression_engine/_engine.py`
* modify `src/expression_engine/_evaluator.py`
* modify `tests/test_public_api.py`
* add `tests/test_built_in_functions.py`
* add `tests/test_registered_functions.py`
* modify `docs/decisions.md`

Modify `src/expression_engine/errors.py` or `src/expression_engine/__init__.py` only if a clearly necessary public error or export change is justified.

Do not modify the tokenizer, parser, token types, or AST unless inspection proves a correctness issue. `CallExpr` syntax and AST already exist and should be reused unchanged.

Do not update the README in this task.

## Required tests

Test mainly through the public API.

### Built-in tests

Cover:

* every built-in success path;
* integer and float behavior;
* boolean rejection;
* `null` and `undefined` rejection;
* missing variable arguments;
* exact arity failures during compile;
* unknown functions during compile;
* domain failures for `sqrt`, `log`, and `pow`;
* `round` with one and two arguments;
* `min` and `max` with two and more arguments;
* mixed integer and float arguments;
* nested function calls;
* function calls inside conditionals, Boolean expressions, and local bindings;
* argument evaluation order;
* arguments evaluated exactly once;
* repeated evaluation of one compiled expression.

### Registered-function tests

Cover:

* successful one-argument and multi-argument functions;
* zero-argument functions;
* positional parameters with defaults;
* too few and too many arguments during compile;
* unknown registered function during compile;
* invalid function names;
* keyword names;
* attempts to override built-ins;
* non-callable values;
* unsupported callable signatures;
* mapping snapshot behavior;
* caller mapping preservation;
* allowed return values;
* unsupported return values;
* wrapping callable exceptions with the original cause;
* propagation of existing engine errors;
* nested registered and built-in calls;
* repeated evaluation;
* concurrent evaluation of the same compiled expression using a pure registered function.

Update the existing public API test that currently expects `f(1)` to compile and fail only during evaluation. After this stage, an unresolved call must fail during `Engine.compile()` with `UnknownFunctionError`.

Do not weaken or delete valid existing tests.

## Documentation

Add a concise `docs/decisions.md` entry covering:

* the public registration API;
* built-in list and semantics;
* compile-time name and arity validation;
* immutable registry snapshots;
* allowed custom return values;
* exception wrapping;
* thread-safety boundary for user callables;
* rejected alternatives, including global registration, dynamic attribute access, and runtime signature inspection.

Clearly distinguish project-owner decisions from AI suggestions.

## Validation commands

Run exactly:

```bash
PYTHONPATH=src python -m pytest tests/test_built_in_functions.py -q
PYTHONPATH=src python -m pytest tests/test_registered_functions.py -q
PYTHONPATH=src python -m pytest tests/test_public_api.py -q
PYTHONPATH=src python -m pytest -q
python -m compileall -q src
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
git diff --stat
```

The grep command is expected to return no matches. Report its exit code accurately.

Do not claim linting, type checking, or benchmark results unless those tools were actually configured and run.

## Final report

At the end, report:

1. What changed.
2. Which files changed.
3. Why the approach was selected.
4. Assumptions and design decisions.
5. Edge cases covered.
6. Known limitations and out-of-scope items.
7. Exact validation commands executed.
8. Exact test, compile, grep, and diff results, including failures and warnings.
9. Confirmation that no commit, push, merge, or pull request was performed.


Implement Stage 13 and Stage 14 together on the current branch, but execute them sequentially and keep the changes focused.

Stage 13: built-in mathematical functions.
Stage 14: safely registered host functions.

Do not implement local function definitions, local-function AST nodes, recursion, a cache, a web API, a CLI, benchmarks, README finalization, or the product-design feature from page 2 of the assignment.

Do not commit, push, merge, or open a pull request.

## Mandatory inspection before editing

Read the entire assignment PDF and inspect the current repository, including at least:

* `src/expression_engine/_engine.py`
* `src/expression_engine/_evaluator.py`
* `src/expression_engine/_ast.py`
* `src/expression_engine/_parser.py`
* `src/expression_engine/errors.py`
* `src/expression_engine/__init__.py`
* `tests/test_public_api.py`
* `tests/test_function_calls.py`
* relevant evaluator and error tests
* `docs/decisions.md`
* `pyproject.toml`

Before changing code, provide a concise inspection report containing:

1. Current function-call parsing and AST behavior.
2. Current public `Engine` and `Expression` API.
3. Current unsupported `CallExpr` evaluation behavior.
4. Existing function-related error classes.
5. Proposed minimal architecture.
6. Exact files expected to change.
7. Assumptions and important edge cases.

Then continue with implementation using the decisions below. Do not pause for confirmation unless the repository directly contradicts one of these decisions.

## Public API

Extend the existing API without breaking current callers:

```python
engine = Engine(
    functions={
        "double": lambda value: value * 2,
    }
)

expression = engine.compile("double(x) + sqrt(9)")
result = expression.evaluate({"x": 4})
```

Required constructor shape:

```python
Engine(
    functions: Mapping[str, Callable[..., object]] | None = None
)
```

`Engine()` with no arguments must behave exactly as it does today.

Do not add a top-level compile helper or a second registration API.

## Architecture requirements

* Keep compilation separate from evaluation.
* Parse once and validate function calls once during `Engine.compile()`.
* Do not resolve names, inspect signatures, tokenize, or parse again during evaluation.
* Keep `Expression` immutable and safe for concurrent evaluation.
* Do not store evaluation-specific state on `Engine` or `Expression`.
* Snapshot the caller-provided function mapping. Never mutate it or retain a mutable reference to it.
* Function metadata stored by the engine must be immutable.
* Avoid global mutable state.
* A static immutable built-in registry is acceptable.
* Do not create a generic visitor framework or unnecessary abstraction hierarchy.
* Prefer exactly one focused private module, such as `_functions.py`, if separating function metadata, validation, and invocation keeps `_engine.py` and `_evaluator.py` small. Do not create several new modules.
* Do not use `eval()`, `exec()`, dynamic imports, attribute lookup on `math`, or arbitrary Python expression execution.

## Stage 13: built-in functions

Implement exactly these built-ins:

* `abs`
* `min`
* `max`
* `round`
* `floor`
* `ceil`
* `sqrt`
* `pow`
* `log`

Only expose these exact names. Do not expose the `math` module or other Python built-ins.

### Common rules

* Numeric arguments accept only exact built-in `int` and `float`.
* `bool` is not numeric.
* `None`, `UNDEFINED`, strings, containers, subclasses, and arbitrary objects are rejected unless explicitly allowed below.
* Arguments are evaluated left-to-right and exactly once.
* Wrong arity raises `FunctionArityError` during compilation.
* Unknown function names raise `UnknownFunctionError` during compilation.
* Domain and runtime calculation failures raise a stable engine-specific evaluation error at the call position.
* Never silently convert missing variables, `null`, `undefined`, type errors, or function failures to `0`.

### Exact built-in behavior

`abs(x)`

* exactly one numeric argument;
* preserve normal `int` or `float` result type.

`floor(x)` and `ceil(x)`

* exactly one numeric argument;
* return an exact `int`.

`sqrt(x)`

* exactly one numeric argument;
* return `float`;
* reject negative values with an engine-specific evaluation error.

`log(x)`

* exactly one numeric argument;
* natural logarithm only;
* reject zero and negative values with an engine-specific evaluation error;
* custom logarithm bases are out of scope.

`pow(x, y)`

* exactly two numeric arguments;
* two integers with a non-negative integer exponent return `int`;
* all other valid numeric combinations return `float`;
* complex results are unsupported and must raise an engine-specific evaluation error.

`round(x)` and `round(x, ndigits)`

* one or two arguments;
* `x` must be numeric and non-boolean;
* `ndigits` must be an exact `int`, not `bool`;
* use documented Python half-to-even rounding behavior;
* do not expose keyword arguments.

`min(...)` and `max(...)`

* require at least two arguments;
* for this stage accept numeric arguments only;
* allow mixed `int` and `float`;
* reject booleans, strings, `None`, `UNDEFINED`, subclasses, and arbitrary objects;
* string ordering remains out of scope.

## Stage 14: registered host functions

Registered functions use the same call syntax as built-ins.

### Registration rules

* The `functions` argument must be a mapping or `None`.
* Copy it once during `Engine` construction.
* Never mutate the supplied mapping.
* Registered names must follow the existing language identifier rules.
* Keywords are invalid registered names.
* Built-in names are reserved and cannot be overridden.
* Each registered value must be callable.
* Invalid registration raises a clear existing engine error where appropriate. Add a new small engine-specific error class only if the existing hierarchy cannot represent the failure clearly.

### Callable signature rules

Inspect each callable signature once during `Engine` construction, not during evaluation.

Support:

* positional-only parameters;
* positional-or-keyword parameters;
* trailing positional parameters with defaults.

Reject as unsupported registration shapes:

* `*args`;
* keyword-only parameters;
* `**kwargs`;
* signatures that cannot be inspected.

Record immutable minimum and maximum positional arity.

During compilation:

* validate every registered call against its recorded arity;
* raise `FunctionArityError` for too few or too many arguments;
* raise `UnknownFunctionError` for unresolved names.

Do not validate argument value types during compilation.

### Invocation rules

* Evaluate all arguments left-to-right and exactly once.
* Invoke the stored callable directly with positional arguments.
* Do not pass the variables mapping, engine, expression, AST, or internal state to the callable.
* If the callable raises an existing `ExpressionError`, propagate it.
* If it raises another normal `Exception`, wrap it in `ExpressionEvaluationError`, include the function name and call position, and preserve the original exception as the cause.
* Do not catch `BaseException`.

Allowed return values are only:

* exact `int`
* exact `float`
* exact `str`
* exact `bool`
* `None`
* the exported `UNDEFINED` singleton

Reject all other return values with a clear engine-specific type or evaluation error at the call position.

The library guarantees that its compiled representation and function registry are immutable. It does not guarantee that user-provided callable implementations are internally thread-safe; document this distinction in `docs/decisions.md`.

## Function resolution

For this combined stage, resolution order is:

1. registered host function;
2. built-in function.

Built-in names are reserved, so there is no ambiguity between the two.

Local functions are not implemented in this task. Do not add placeholder local-function resolution.

## Compile-time validation

Add only the smallest validation pass needed for built-in and registered function calls.

It must recursively inspect all existing AST node types and validate `CallExpr` names and arities.

Requirements:

* validation runs once during `Engine.compile()`;
* it must inspect calls inside arithmetic, comparisons, Boolean expressions, conditional branches, call arguments, and local variable bindings;
* do not introduce a generic visitor class;
* do not mutate the AST;
* do not reject free variable names;
* short-circuiting and selected-branch evaluation remain runtime behavior, but unknown function names and invalid arity are compile-time errors even inside branches that may not execute.

## Expected file scope

Prefer the following focused file set:

* add `src/expression_engine/_functions.py`
* modify `src/expression_engine/_engine.py`
* modify `src/expression_engine/_evaluator.py`
* modify `tests/test_public_api.py`
* add `tests/test_built_in_functions.py`
* add `tests/test_registered_functions.py`
* modify `docs/decisions.md`

Modify `src/expression_engine/errors.py` or `src/expression_engine/__init__.py` only if a clearly necessary public error or export change is justified.

Do not modify the tokenizer, parser, token types, or AST unless inspection proves a correctness issue. `CallExpr` syntax and AST already exist and should be reused unchanged.

Do not update the README in this task.

## Required tests

Test mainly through the public API.

### Built-in tests

Cover:

* every built-in success path;
* integer and float behavior;
* boolean rejection;
* `null` and `undefined` rejection;
* missing variable arguments;
* exact arity failures during compile;
* unknown functions during compile;
* domain failures for `sqrt`, `log`, and `pow`;
* `round` with one and two arguments;
* `min` and `max` with two and more arguments;
* mixed integer and float arguments;
* nested function calls;
* function calls inside conditionals, Boolean expressions, and local bindings;
* argument evaluation order;
* arguments evaluated exactly once;
* repeated evaluation of one compiled expression.

### Registered-function tests

Cover:

* successful one-argument and multi-argument functions;
* zero-argument functions;
* positional parameters with defaults;
* too few and too many arguments during compile;
* unknown registered function during compile;
* invalid function names;
* keyword names;
* attempts to override built-ins;
* non-callable values;
* unsupported callable signatures;
* mapping snapshot behavior;
* caller mapping preservation;
* allowed return values;
* unsupported return values;
* wrapping callable exceptions with the original cause;
* propagation of existing engine errors;
* nested registered and built-in calls;
* repeated evaluation;
* concurrent evaluation of the same compiled expression using a pure registered function.

Update the existing public API test that currently expects `f(1)` to compile and fail only during evaluation. After this stage, an unresolved call must fail during `Engine.compile()` with `UnknownFunctionError`.

Do not weaken or delete valid existing tests.

## Documentation

Add a concise `docs/decisions.md` entry covering:

* the public registration API;
* built-in list and semantics;
* compile-time name and arity validation;
* immutable registry snapshots;
* allowed custom return values;
* exception wrapping;
* thread-safety boundary for user callables;
* rejected alternatives, including global registration, dynamic attribute access, and runtime signature inspection.

Clearly distinguish project-owner decisions from AI suggestions.

## Validation commands

Run exactly:

```bash
PYTHONPATH=src python -m pytest tests/test_built_in_functions.py -q
PYTHONPATH=src python -m pytest tests/test_registered_functions.py -q
PYTHONPATH=src python -m pytest tests/test_public_api.py -q
PYTHONPATH=src python -m pytest -q
python -m compileall -q src
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
git diff --stat
```

The grep command is expected to return no matches. Report its exit code accurately.

Do not claim linting, type checking, or benchmark results unless those tools were actually configured and run.

## Final report

At the end, report:

1. What changed.
2. Which files changed.
3. Why the approach was selected.
4. Assumptions and design decisions.
5. Edge cases covered.
6. Known limitations and out-of-scope items.
7. Exact validation commands executed.
8. Exact test, compile, grep, and diff results, including failures and warnings.
9. Confirmation that no commit, push, merge, or pull request was performed.


---

## Cursor Response

Starting with mandatory inspection, then implementing Stage 13 and Stage 14 sequentially.


Inspection complete. Implementing Stage 13 first, then Stage 14.


Inspection summary: `CallExpr` parses but `_evaluator` rejects it; `Engine`/`Expression` compile once with no validation; `UnknownFunctionError`/`FunctionArityError` exist without positions. Implementing `_functions.py` with built-ins, validation, and invocation.


Updating `test_public_api.py` and adding the built-in and registered function test files.


## Inspection report (pre-implementation)

1. **Call parsing/AST:** `CallExpr(name, arguments: tuple[Expr, ...], position)` parsed at primary level; identifier-only, no chaining.
2. **Public API:** Stateless `Engine.compile()` → immutable `Expression.evaluate()`; no function support yet.
3. **CallExpr evaluation:** Fell through to `ExpressionEvaluationError("cannot evaluate unsupported expression node")`.
4. **Function errors:** `UnknownFunctionError`, `FunctionArityError` (validation); no `.position` before this change.
5. **Architecture:** Single `_functions.py` for registry, compile-time validation, built-in dispatch, registered invocation; `Engine` holds immutable registry; `Expression` stores registry snapshot; validate at compile, invoke at evaluate.
6. **Files changed:** `_functions.py` (new), `_engine.py`, `_evaluator.py`, `errors.py`, `test_public_api.py`, `test_built_in_functions.py` (new), `test_registered_functions.py` (new), `docs/decisions.md`.
7. **Assumptions:** Resolution order registered → built-in; compile-time validation for all calls including dead branches; `Engine()` unchanged except unknown calls now fail at compile.

---

## Final report

### 1. What changed

**Stage 13 — built-ins:** Added static registry and implementations for `abs`, `min`, `max`, `round`, `floor`, `ceil`, `sqrt`, `pow`, `log` with documented numeric rules and domain errors.

**Stage 14 — registered functions:** Extended `Engine(functions=...)` to snapshot and validate host callables at construction; compile-time name/arity validation; runtime invocation with return-type checks and exception wrapping.

**Pipeline:** `Engine.compile()` → tokenize → parse → **validate function calls** → `Expression(_ast, _registry)`. `Expression.evaluate()` → `evaluate(ast, variables, registry)` with `CallExpr` support.

### 2. Files changed

- `src/expression_engine/_functions.py` (new)
- `src/expression_engine/_engine.py`
- `src/expression_engine/_evaluator.py`
- `src/expression_engine/errors.py` (optional `.position` on function validation errors)
- `tests/test_public_api.py`
- `tests/test_built_in_functions.py` (new)
- `tests/test_registered_functions.py` (new)
- `docs/decisions.md`

### 3. Why this approach

One focused `_functions.py` keeps registry, validation, and invocation together without a visitor framework or global registration. Immutable `FunctionRegistry` snapshots preserve thread safety; compile-time validation matches the error hierarchy (`UnknownFunctionError` / `FunctionArityError` at compile; domain failures at evaluate). Explicit built-in dispatch avoids `getattr(math, name)`.

### 4. Design decisions

- `Engine(functions=None)` — `Engine()` behavior preserved for non-call expressions; unknown calls fail at compile.
- `Expression` stores `_registry` (immutable, `repr=False`) alongside `_ast`.
- Registered names: identifier rules, no keywords, no built-in override.
- Signature inspection once at `Engine` construction via `inspect.signature`.
- Callable exceptions: `ExpressionError` propagates; other `Exception` wrapped with cause.
- No local functions, cache, or README changes.

### 5. Edge cases covered

Built-in success/domain/arity/type paths; registered registration validation; snapshot; allowed/disallowed returns; exception wrapping; nested calls; conditionals/bindings; argument order; repeated/concurrent evaluation; public API unknown-call-at-compile update.

### 6. Out of scope

Local functions, recursion, cache, CLI/web API, benchmarks, README, product-design feature.

### 7. Validation commands executed

```bash
PYTHONPATH=src python -m pytest tests/test_built_in_functions.py -q
PYTHONPATH=src python -m pytest tests/test_registered_functions.py -q
PYTHONPATH=src python -m pytest tests/test_public_api.py -q
PYTHONPATH=src python -m pytest -q
python -m compileall -q src
git diff --check
grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
git status --short
git diff --stat
```

### 8. Exact results

| Command | Result |
|---|---|
| `test_built_in_functions.py` | **39 passed** |
| `test_registered_functions.py` | **30 passed** |
| `test_public_api.py` | **18 passed** |
| Full suite | **553 passed** in 0.74s |
| `compileall -q src` | exit **0** |
| `git diff --check` | exit **0** |
| `grep … eval/exec` | no output, exit **1** (expected) |
| Lint/type-check | **Not run** — none configured in `pyproject.toml` |

No failures, no warnings.

### 9. `git status --short`

```
 M docs/decisions.md
 M src/expression_engine/_engine.py
 M src/expression_engine/_evaluator.py
 M src/expression_engine/errors.py
 M tests/test_public_api.py
?? src/expression_engine/_functions.py
?? tests/test_built_in_functions.py
?? tests/test_registered_functions.py
```

### 10. Commit/push confirmation

No commit, push, merge, or pull request was performed.

---

## User Prompt

Write a concise product-design answer, no longer than half a page, for this assignment question:

A data scientist says: “For some reason my expressions always evaluate to 0, but it does not make any sense. What’s going on?”

Propose one product feature that would help them understand the result.

Focus only on the user problem and the proposed solution. Describe:

* what the feature is;
* what information it would show;
* how it would help identify why the result is 0;
* one short example;
* one important usability or performance consideration.

A suitable direction is an “Expression Explain Mode” that shows resolved variables, important intermediate values, selected conditional branches, skipped branches, function results, and the exact sub-expression that produced 0.

Write from a product-manager perspective, not as an implementation plan.

Do not:

* implement the feature;
* add code or tests;
* describe APIs or architecture;
* claim the feature already exists;
* exceed half a page.

Return only the final English product-design answer.
Product design, up to half a page.

Write a concise product-design answer, no longer than half a page, for this assignment question:

A data scientist says: “For some reason my expressions always evaluate to 0, but it does not make any sense. What’s going on?”

Propose one product feature that would help them understand the result.

Focus only on the user problem and the proposed solution. Describe:

* what the feature is;
* what information it would show;
* how it would help identify why the result is 0;
* one short example;
* one important usability or performance consideration.

A suitable direction is an “Expression Explain Mode” that shows resolved variables, important intermediate values, selected conditional branches, skipped branches, function results, and the exact sub-expression that produced 0.

Write from a product-manager perspective, not as an implementation plan.

Do not:

* implement the feature;
* add code or tests;
* describe APIs or architecture;
* claim the feature already exists;
* exceed half a page.

Return only the final English product-design answer.


Write a concise product-design answer, no longer than half a page, for this assignment question:

A data scientist says: “For some reason my expressions always evaluate to 0, but it does not make any sense. What’s going on?”

Propose one product feature that would help them understand the result.

Focus only on the user problem and the proposed solution. Describe:

* what the feature is;
* what information it would show;
* how it would help identify why the result is 0;
* one short example;
* one important usability or performance consideration.

A suitable direction is an “Expression Explain Mode” that shows resolved variables, important intermediate values, selected conditional branches, skipped branches, function results, and the exact sub-expression that produced 0.

Write from a product-manager perspective, not as an implementation plan.

Do not:

* implement the feature;
* add code or tests;
* describe APIs or architecture;
* claim the feature already exists;
* exceed half a page.

Return only the final English product-design answer.


---

## Cursor Response

**Expression Explain Mode**

When a computed variable returns `0`, the data scientist often cannot tell whether that is the intended result, a side effect of missing data, or a logic mistake. The expression may look reasonable on paper, but the actual values feeding it are invisible at evaluation time.

**Expression Explain Mode** is an on-demand debugging view for a single expression and one variable context. Instead of showing only the final result, it shows how the expression was evaluated step by step. For each run, it would display: the resolved values of input variables (including `null`, `undefined`, and missing variables); intermediate results for arithmetic, comparisons, and function calls; which branch was taken in conditionals and which branch was skipped; and the exact sub-expression that produced `0`.

This helps because `0` is often not the “answer” to the whole expression, but the result of one small part of it. A scientist may expect a positive score, but Explain Mode might reveal that a missing variable became `undefined`, a conditional chose the fallback branch, or a function returned `0` before the rest of the expression ran. Highlighting the first sub-expression that evaluates to `0` turns a confusing final number into a concrete logic clue.

**Example:** For `bonus if revenue > target else 0`, Explain Mode might show `revenue = undefined`, `revenue > target = false`, selected branch: `else 0`, final result: `0`. The user immediately sees the issue is missing input data, not the bonus formula itself.

**Consideration:** Explain Mode should be optional and scoped to one expression at a time, so it helps debugging without slowing normal high-volume evaluation across millions of rows.
