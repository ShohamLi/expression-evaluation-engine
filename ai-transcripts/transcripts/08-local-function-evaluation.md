# Local Function Evaluation and Test Review

- **Tool:** Codex
- **Project:** Expression Evaluation Engine
- **Transcript type:** English submission copy
- **Editing applied:** Project title and explicit partial-status note added; the supplied unstructured excerpt is otherwise preserved.
- **Integrity note:** No prompt, answer, result, decision, or missing conversation was invented.

---

> **Completeness: Partial.** The supplied excerpt truncates the original Stage
> 16 implementation prompt and ends with an incomplete diff fragment. No missing
> prompt, response, or code was reconstructed.

git status --short
git rev-parse --short HEAD
git rev-parse --short origin/main
feat/local-function-evaluation
660cbb3
660cbb3
shoham@MacBookPro expression-evaluation-engine %
6:53 PM

Worked for 6s
Context noted:

Branch: feat/local-function-evaluation
Working tree: clean
HEAD: 660cbb3
origin/main: 660cbb3 (fully aligned)
6:53 PM

Implement Stage 16 only: local-function compile-time validation, lexical resolu…

Worked for 8m 19s
What changed: compile-time lexical resolution, exact arity/parameter validation, recursion rejection, per-evaluation closures, and local-function execution.

Files changed:

_functions.py
_evaluator.py
errors.py
test_local_function_evaluation.py
test_public_api.py
decisions.md
Architecture: calls bind directly to immutable LocalFunctionExpr nodes during compilation. Runtime uses frozen, per-evaluation closures with ChainMap variable/function scopes. No runtime name resolution or shared evaluation state.

Decisions/assumptions: lexical definition-site scope, exact positional parameters, reserved built-ins, local-over-registered resolution, and no recursion follow owner requirements. A visible outer local definition wins before recursion blocking.

Covered edge cases: laziness, skipped branches, argument ordering/failures, duplicate parameters, arity, recursion, registered shadowing, nested captures, null/undefined, repeated calls, state isolation, and concurrency.

Known limitations: no recursion, anonymous/higher-order functions, defaults, variadics, keyword arguments, memoization, or runtime function lookup.

Exact validation commands:

PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q
Requested five-file compatibility command
PYTHONPATH=src python -m pytest -q
python -m compileall -q src
git diff --check
Requested grep -R -nE ... src tests
git status --short
git diff --stat
Results:

Focused: 43 passed in 0.12s
Compatibility: 209 passed in 0.27s
Full suite: 698 passed in 1.05s
compileall: exit 0, no output
git diff --check: exit 0, no output
Prohibited-call grep: exit 1, no matches, expected
Status: five modified files and one untracked test file listed above
Diff stat: 5 files changed, 194 insertions(+), 50 deletions(-); untracked 370-line test file is naturally excluded
During development, one obsolete Stage 15 test and two position assertions initially failed; both causes were corrected before final validation.
No validation warnings. PDF extraction emitted two harmless malformed-object warnings while successfully reading both pages.
No commit, push, merge, publication, or pull request was performed.


decisions.md
Document · MD

Edited 6 files
+564
-50

docs/decisions.md
+29
-0

src/expression_engine/_evaluator.py
+75
-17

src/expression_engine/_functions.py
+77
-18

Show 3 more files
7:01 PM
Review the complete Stage 16 test file before commit.

Context:

* Branch: feat/local-function-evaluation
* Stage 16 implementation is already complete.
* The full suite currently passes with 698 passed.
* The new file is tests/test_local_function_evaluation.py.
* Do not commit, push, merge, or open a pull request.

Task:
Inspect the entire Stage 16 test file and verify that the tests are focused, necessary, and aligned with the existing project conventions.

Check specifically for:

* duplicated or nearly identical tests;
* unnecessary helper functions or excessive setup;
* tests coupled to private implementation details;
* unnecessary private imports, especially:

  * expression_engine._engine as engine_module
  * expression_engine._tokens.Position
* tests that could be written through the public API instead;
* weak concurrency tests that do not actually evaluate the same compiled expression concurrently;
* assertions that overfit exact error wording instead of checking the relevant error type, position, and essential message;
* obsolete Stage 15 expectations;
* tests that accidentally weaken existing behavior;
* missing coverage for important Stage 16 semantics.

Required Stage 16 coverage:

* zero, one, and multiple parameters;
* exact arity validation at compile time;
* duplicate parameter rejection;
* reserved built-in names;
* local-over-registered resolution;
* direct recursion rejection;
* recursion in skipped or nested branches;
* visible outer local function resolution;
* lexical definition-site variable capture;
* nested functions capturing outer parameters;
* parameter shadowing;
* arguments evaluated left-to-right and exactly once;
* function bodies evaluated lazily and once per call;
* null and undefined preservation;
* repeated evaluation of one compiled expression;
* caller input preservation;
* state isolation between evaluations;
* concurrent evaluation of the same compiled expression.

Rules:

* Inspect the full existing implementation and relevant tests before editing.
* Prefer tests through the public Engine.compile() and Expression.evaluate() API.
* Keep private imports only when they verify an important invariant that cannot reasonably be tested publicly.
* Do not remove meaningful edge-case or regression coverage merely to shorten the file.
* Make only the smallest justified changes.
* Do not refactor production code.
* Do not add dependencies or new files.
* Do not use eval() or exec().

Before editing, report:

1. Which tests are duplicated or unnecessary.
2. Which private imports are justified or unjustified.
3. Any meaningful Stage 16 coverage gaps.
4. The exact changes you propose.

After editing, run:
bash
PYTHONPATH=src python -m pytest tests/test_local_function_evaluation.py -q
PYTHONPATH=src python -m pytest tests/test_public_api.py tests/test_local_bindings.py tests/test_local_function_parser.py tests/test_registered_functions.py tests/test_built_in_functions.py -q
PYTHONPATH=src python -m pytest -q
python -m compileall -q src
git diff --check
git diff --cached --check
git status --short
git diff --stat

At the end, report:

1. What changed.
2. Which files changed.
3. Why every removed, combined, or retained test was justified.
4. Whether private imports remain and why.
5. Coverage preserved or added.
6. Exact validation results, including failures and warnings.
7. Confirmation that no production code was modified unless an actual bug required it.
8. Confirmation that no commit or push was performed.

Show more
7:07 PM

Worked for 2m 59s
Changed
Removed 3 redundant tests:
duplicate arithmetic-body coverage;
weaker repeated-call coverage;
duplicate compile-once/private-spy coverage.
Parameterized null/undefined and short-circuit cases.
Replaced private Position construction with public error-position assertions.
Files changed
Only tests/test_local_function_evaluation.py during this review.
No production or documentation files were edited.
Test justification
Removed tests were already covered by stronger tests or test_public_api.py.
Combined tests still execute every original semantic case.
Retained distinct coverage for laziness, runtime-error deferral, argument failure, lexical capture, nested functions, recursion variants, resolution, state isolation, and concurrency.
Private imports
No private imports remain.
Removed _engine, _tokens.Position, and unittest.mock.patch.
ThreadPoolExecutor remains because the test genuinely shares one compiled expression across workers.
The public Engine.compile()/Expression.evaluate() API is used throughout.
Coverage
All required Stage 16 semantics remain covered, including exact arity, recursion variants, lexical capture, argument ordering, per-call evaluation, null/undefined, reuse, input preservation, isolation, and concurrent evaluation.

Validation

Focused: 40 passed in 0.14s
Compatibility: 209 passed in 0.55s
Full suite: 695 passed in 1.24s
compileall: exit 0, no output
git diff --check: exit 0, no output
git diff --cached --check: exit 0, no output
No failures or warnings
git status --short:

M  docs/decisions.md
M  src/expression_engine/_evaluator.py
M  src/expression_engine/_functions.py
M  src/expression_engine/errors.py
AM tests/test_local_function_evaluation.py
M  tests/test_public_api.py
git diff --stat:

tests/test_local_function_evaluation.py | 79 +++++++++++----------------------
1 file changed, 25 insertions(+), 54 deletions(-)
No production code was modified during this review.

No commit, push, merge, or pull request was performed. The reviewed test cleanup is currently unstaged, reflected by AM.


Edited test_local_function_evaluation.py
+25
-54
7:10 PM


tests/test_local_function_evaluation.py
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

import expression_engine._engine as engine_module
from expression_engine import (
    UNDEFINED,
    Engine,
    FunctionArityError,
    UnknownFunctionError,
)
from expression_engine._tokens import Position


def evaluate(source: str, variables: dict[str, object] | None = None) -> object:

def test_multiple_parameter_function() -> None:
    assert evaluate("let add(a, b) = a + b in add(1, 2)") == 3


def test_arithmetic_function_body() -> None:
    assert evaluate("let calculate(x) = x * 2 + 1 in calculate(4)") == 9


def test_string_result() -> None:
    assert evaluate("let positive(x) = x > 0 in positive(2)") is True


def test_null_is_preserved() -> None:
    assert evaluate("let identity(x) = x in identity(null)") is None


def test_undefined_is_preserved() -> None:
    assert evaluate("let identity(x) = x in identity(undefined)") is UNDEFINED
@pytest.mark.parametrize(
    ("argument", "expected"),
    [("null", None), ("undefined", UNDEFINED)],
)
def test_null_and_undefined_are_preserved(
    argument: str, expected: object
) -> None:
    assert evaluate(f"let identity(x) = x in identity({argument})") is expected


def test_builtin_call_from_local_function() -> None:
def test_registered_call_from_local_function() -> None:
    engine = Engine(functions={"triple": lambda value: value * 3})
    assert engine.compile("let apply(x) = triple(x) in apply(4)").evaluate() == 12


def test_local_function_can_be_called_multiple_times() -> None:
    assert evaluate("let increment(x) = x + 1 in increment(1) + increment(2)") == 5


def test_function_body_is_evaluated_again_for_each_call() -> None:
    assert events == ["argument"]


def test_boolean_short_circuit_remains_lazy_inside_function_body() -> None:
@pytest.mark.parametrize(
    ("function_body", "expected"),
    [("true or fail()", True), ("1 if true else fail()", 1)],
)
def test_short_circuit_remains_lazy_inside_function_body(
    function_body: str, expected: object
) -> None:
    events: list[str] = []

    def fail() -> bool:
        events.append("fail")
        return False

    engine = Engine(functions={"fail": fail})
    expression = engine.compile("let check() = true or fail() in check()")

    assert expression.evaluate() is True
    assert events == []


def test_conditional_remains_lazy_inside_function_body() -> None:
    events: list[str] = []

    def fail() -> int:
        events.append("fail")
        return 0

    engine = Engine(functions={"fail": fail})
    expression = engine.compile(
        "let choose() = 1 if true else fail() in choose()"
        f"let check() = {function_body} in check()"
    )

    assert expression.evaluate() == 1
    assert expression.evaluate() == expected
    assert events == []
