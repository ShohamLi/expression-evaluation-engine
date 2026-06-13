# Final Technical Hardening

- **Tool:** Codex
- **Project:** Expression Evaluation Engine
- **Transcript type:** English submission copy
- **Editing applied:** Project title added, local paths redacted, and export boilerplate lightly normalized; supplied Codex tool traces and collapsed-history structure preserved.
- **Integrity note:** No prompt, answer, result, decision, or missing conversation was invented.

---

# Audit final hardening

> User context
>
> Attachments:
> -Backend Home Assignment — Expression Evaluation Engine.pdf
> - Perform a focused final-hardening audit and, only where justified by the existi…: `[LOCAL_HOME]/.codex/attachments/059c6a98-e776-4bd7-9f03-88d1b410f767/pasted-text.txt`

<details><summary>19 previous messages</summary>

> I’ll read the attached request and the assignment PDF first, then inspect the repository against those exact requirements before making any justified changes.
>
> <details><summary>Explored a file, a list, ran 2 commands</summary>
>
> <details><summary>Explored a file</summary>
>
> - Read `[LOCAL_HOME]/.codex/attachments/059c6a98-e776-4bd7-9f03-88d1b410f767/pasted-text.txt`
>
> </details>
>
> - Ran `git status --short --branch`
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
> The hardening brief is precise, and the branch is already correct with a clean worktree. `pdftotext` is unavailable here, so I’m switching to the bundled document runtime to extract the assignment before inspecting code; no files have been edited.
>
> <details><summary>Explored a list, ran 2 commands</summary>
>
> <details><summary>Explored a list</summary>
>
> - Listed files in `bin`
>
> </details>
>
> - Ran `'[LOCAL_HOME]/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3' -c "import pypdf; print(pypdf.__version__)"`
>
> - Ran `'[LOCAL_HOME]/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3' -c "from pypdf import PdfReader; p=PdfReader('Backend Home Assignment — Expression Evaluation Engine.pdf'); print('PAGES', len(p.pages)); [print(f'\n--- PAGE {i} ---\n'+(x.extract_text() or '')) for i,x in enumerate(p.pages,1)]"`
>
> </details>
>
> I’ve now read the complete two-page assignment. Next I’m tracing the five concerns through the public API, evaluator, errors, docs, metadata, and tests so the pre-edit audit distinguishes real defects from cosmetic suggestions.
>
> <details><summary>Explored 27 files</summary>
>
> - Read `./src/expression_engine/errors.py`
> - Read `./docs/product-design.md`
> - Read `./src/expression_engine/_values.py`
> - Read `./src/expression_engine/__init__.py`
> - Read `./ai-transcripts/README.md`
> - Read `./src/expression_engine/_evaluator.py`
> - Read `./src/expression_engine/_functions.py`
> - Read `./src/expression_engine/_tokenizer.py`
> - Read `./README.md`
> - Read `./docs/write-up.md`
> - Read `./pyproject.toml`
> - Read `./src/expression_engine/_ast.py`
> - Read `./src/expression_engine/_engine.py`
> - Read `./docs/decisions.md`
> - Read `./src/expression_engine/_tokens.py`
> - Read `./src/expression_engine/_parser.py`
> - Read `./docs/write-up.md`
> - Read `./pyproject.toml`
> - Read `./src/expression_engine/_ast.py`
> - Read `./tests/test_package.py`
> - Read `./docs/decisions.md`
> - Read `./src/expression_engine/errors.py`
> - Read `./tests/test_public_api.py`
> - Read `./docs/decisions.md`
> - Read `./src/expression_engine/_evaluator.py`
> - Read `./README.md`
> - Read `./tests/test_evaluator.py`
>
> </details>
>
> Two issues are already looking substantive: `/` directly returns `left / right` after only the zero check, and invalid variable containers reach `.get()` without a boundary guard. I’m confirming their exact exception behavior and checking whether documentation or metadata already records intentional choices before proposing edits.
>
> <details><summary>Explored a file, 4 searches, ran a command</summary>
>
> <details><summary>Explored a file, 4 searches</summary>
>
> - Read `./docs/write-up.md`
> - Searched for `AI|owner|decision|responsib|selected|corrected|rejected|architecture|scope|semantics` in `write-up.md`
> - Searched for `division|OverflowError|left / right|SLASH|DivisionByZero` in `src`
> - Searched for `variables|Mapping|evaluate\(` in `README.md`
> - Searched for `0\.0\.0|Pre-Alpha|Development Status|version|metadata` in `README.md`
>
> </details>
>
> - Ran `PYTHONPATH=src python -c "from expression_engine import Engine; e=Engine().compile('x'); cases=[[],(),'',1,object()];
> for v in cases:
>  try: print(type(v).__name__, '=>', e.evaluate(v))
>  except BaseException as exc: print(type(v).__name__, type(exc).__name__, repr(str(exc)))
> h=10**400
> for a,b in [(h,1),(10**300,10**299)]:
>  try: print('DIV', len(str(a)), '/', len(str(b)), '=>', Engine().compile('x / y').evaluate({'x':a,'y':b}))
>  except BaseException as exc: print('DIV', type(exc).__name__, repr(str(exc)), 'cause=', repr(exc.__cause__))"`
>
> </details>
>
> **Pre-Edit Audit**
>
> 1. **Division overflow normalization**
>    Relevant path: `Expression.evaluate()` in `src/expression_engine/_engine.py` delegates to `evaluate()` and `_eval_binary()` in `src/expression_engine/_evaluator.py`; `/` checks `right == 0` and then directly executes `left / right`. Current behavior is confirmed: `10**400 / 1` through `Engine.compile("x / y").evaluate(...)` leaks raw `OverflowError("integer division result too large for a float")`, while `10**300 / 10**299` returns `10.0`. A change is justified. Smallest fix: catch only `OverflowError` immediately around the division operation and raise positioned `ExpressionEvaluationError` with chaining. Expected files: `_evaluator.py` and `tests/test_public_api.py`. Risks to preserve: zero remains `DivisionByZeroError`; ordinary int/float division is unchanged; `+`, `-`, and `*` remain untouched.
>
> 2. **Runtime validation of `variables`**
>    Relevant path: public `Expression.evaluate()` delegates unchanged to internal `evaluate()`; the latter converts only `None` to `{}`, then variable lookup calls `variables.get(...)`. Current behavior is confirmed: lists, tuples, strings, integers, and arbitrary objects leak `AttributeError` when a variable is read; expressions without lookup can silently accept them. A change is justified at the internal evaluator boundary so both public and direct internal use are deterministic. Smallest fix: after handling `None`, require `isinstance(variables, Mapping)` and raise plain `TypeError`; do not copy or mutate mappings. Expected files: `_evaluator.py`, `_engine.py` docstring, and `tests/test_public_api.py`. Risks: preserve custom read-only mappings, omitted/`None` behavior, caller identity/state, and programmer-error classification outside the expression error hierarchy.
>
> 3. **`LiteralExpr` docstring**
>    Relevant path: `src/expression_engine/_ast.py`; runtime conversion is in `_eval_literal()`. Current text incorrectly says conversion does not happen “during evaluation,” contradicting both implementation and surrounding documentation. A wording-only fix is justified: conversion is deferred during tokenization, parsing, and AST construction, then occurs during evaluation. Expected file: `_ast.py`. No runtime or compatibility risk.
>
> 4. **Package metadata**
>    Relevant files: `pyproject.toml`, `src/expression_engine/__init__.py`, README, and assignment context. `0.0.0` and `Pre-Alpha` consistently describe an unpublished take-home library with intentionally deferred features; no evidence shows either harms installation, testing, or the submission. No change is justified. Changing them would be cosmetic and could create version inconsistency. Expected files: none; the decision will be recorded in the final report.
>
> 5. **Owner decisions versus AI wording**
>    Relevant files: `docs/write-up.md` lines 11–17 and `docs/decisions.md`’s AI-assisted sections. They already consistently state that AI suggested code, implementation details, tests, and edge cases; the owner reviewed, changed, simplified, selected, or rejected suggestions; and final architecture, semantics, API, scope, implementation responsibility, and decisions remained with the owner. No wording change is justified, especially given the one-page limit. Expected files: none.
>
> I’ll now make only the three justified changes above, add focused public-API regressions, run those tests first, then perform the complete requested validation and diff audit.
>
> <details><summary>Explored a file</summary>
>
> - Read `./src/expression_engine/_functions.py`
>
> </details>
>
> I’m applying a narrowly scoped patch: one exception-normalization block around `/`, one `Mapping` guard at the evaluator boundary, the corrected literal doc wording, and public-API tests that pin those contracts. Metadata, README, decision records, APIs, and unrelated evaluator paths remain untouched.
>
> The first patch did not apply because the test import order differed from the expected context; the patch tool rejected it before changing files. I’m re-reading the small target regions and will apply the same edits with exact context.
>
> <details><summary>Edited 4 files, explored 2 files, ran a command</summary>
>
> <details><summary>Explored 3 files</summary>
>
> - Read `./src/expression_engine/_evaluator.py`
> - Read `./src/expression_engine/_evaluator.py`
> - Read `./tests/test_public_api.py`
>
> </details>
>
> - Ran `git diff -- src/expression_engine/_evaluator.py src/expression_engine/_engine.py src/expression_engine/_ast.py tests/test_public_api.py`
>
> - Wrote `./src/expression_engine/_ast.py` (+2 -1)
> - Wrote `./src/expression_engine/_engine.py` (+1 -0)
> - Wrote `./src/expression_engine/_evaluator.py` (+14 -3)
>
> - Wrote `./tests/test_public_api.py` (+58 -1)
>
> </details>
>
> The scoped edits are in place. I’m running the public-API test file first, which covers the new overflow and variable-boundary regressions plus the existing compile/evaluate, immutability, and concurrency contracts.
>
> <details><summary>Ran a command</summary>
>
> - Ran `PYTHONPATH=src python -m pytest -q tests/test_public_api.py`
>
> </details>
>
> The focused suite passes: `27 passed`. I’m reviewing the complete diff now for scope, API compatibility, exception placement, and test quality before running the full validation matrix.
>
> <details><summary>Ran a command</summary>
>
> - Ran `git diff -- src/expression_engine/_evaluator.py src/expression_engine/_engine.py src/expression_engine/_ast.py tests/test_public_api.py`
>
> </details>
>
> The diff is limited to the three justified items and their tests; there is no metadata, README, AI-wording, API-shape, or unrelated arithmetic churn. I’m running the exact required full-suite, whitespace, forbidden-call, and status commands now; this project defines no separate lint or type-check command.
>
> <details><summary>Explored a search, ran 3 commands</summary>
>
> - Ran `git status --short`
>
> - Ran `git diff --check`
>
> - Ran `PYTHONPATH=src python -m pytest -q`
>
> <details><summary>Explored a search</summary>
>
> - Searched for `\beval\s*\(|\bexec\s*\(` in `src`
>
> </details>
>
> </details>
</details>

1. **Audit conclusions**
   1. Division overflow: confirmed and fixed.
   2. Invalid `variables`: confirmed and fixed with `TypeError`.
   3. `LiteralExpr` docstring: inaccurate and corrected.
   4. Package metadata: unchanged; appropriate for an unpublished pre-alpha submission.
   5. AI/owner wording: already clear and consistent; unchanged.

2. **Changes**
   Normalized division `OverflowError`, validated `variables`, corrected AST documentation, and added focused public-API tests.

3. **Files changed**
   - [\_evaluator.py](../../src/expression_engine/_evaluator.py)
   - [\_engine.py](../../src/expression_engine/_engine.py)
   - [\_ast.py](../../src/expression_engine/_ast.py)
   - [test_public_api.py](../../tests/test_public_api.py)

4. **Why selected**
   Both runtime changes prevent raw internal exceptions while preserving existing API and language semantics. The documentation correction resolves a direct contradiction.

5. **Rejected suggestions**
   Version/classifier, README, and AI-assistance wording changes were rejected as cosmetic or unnecessary.

6. **Design decisions**
   Invalid containers raise plain deterministic `TypeError`. Only division’s expected `OverflowError` is translated, preserving its cause and operator position.

7. **Edge cases covered**
   Huge and ordinary large integers, int/float division, division by zero, omitted/`None` variables, dictionaries, custom mappings, five non-mapping types, and input preservation.

8. **Out of scope**
   No key/value validation, new language features, dependencies, abstractions, or metadata changes.

9. **Commands executed**
   ```text
   PYTHONPATH=src python -m pytest -q tests/test_public_api.py
   git diff --check
   PYTHONPATH=src python -m pytest -q
   grep -R -nE '\beval\s*\(|\bexec\s*\(' src tests
   git status --short
   ```

10. **Results**
    Focused: `27 passed in 0.11s`. Full: `731 passed in 1.68s`. Diff check passed. Grep returned exit 1 with no matches, meaning no forbidden calls. No lint/type-check commands are configured. No warnings or failures.

11. **Git status**
    ```text
     M src/expression_engine/_ast.py
     M src/expression_engine/_engine.py
     M src/expression_engine/_evaluator.py
     M tests/test_public_api.py
    ```

12. **Repository actions**
    No commit, push, merge, branch publication, or pull request was performed.
