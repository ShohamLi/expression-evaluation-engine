# Project Write-up

## Approach

I first read the assignment and divided it into small stages. I implemented one main feature at a time, using a separate branch for each stage.

Before each change, I checked the existing code and tests, defined the expected behavior, and listed the important edge cases. I tried to keep every change small and consistent with the code that was already implemented.

Because the same expression may be evaluated many times, I separated compilation from evaluation. An expression is tokenized, parsed, and validated once, and can then be reused with different input values. I built the tokenizer and parser myself and did not use eval() or execute arbitrary Python code.

## My decisions and AI usage

I decided the architecture, public API, syntax, type rules, error behavior, and scope of the first version.

I used Cursor to help with implementation and Codex to review changes. AI suggested code, tests, and edge cases, but I reviewed the output myself. I changed, simplified, or rejected suggestions that did not fit the project.

I only merged a stage after checking the code and running the tests. The final decisions and responsibility for the implementation were mine.

## Vague requirements

The assignment did not define all language behavior, so I made several decisions.

null is represented by Python None. A missing variable or the undefined literal returns a separate UNDEFINED value. None of these values are converted to zero.

Booleans are separate from numbers. The engine does not automatically convert between numbers, strings, and booleans. and and or use short-circuit evaluation, and a conditional evaluates only the selected branch.

I chose the syntax let name = value in expression for local variables and similar syntax for local functions. Recursion and automatic caching are not included in the first version because they would add complexity and were not required.

## Library usage and features

The library is installed as a Python package and used like this:

```python
from expression_engine import Engine

engine = Engine()
expression = engine.compile("revenue - cost if active else 0")

result = expression.evaluate(
    {"revenue": 120, "cost": 75, "active": True}
)
```

The library supports numbers, strings, booleans, variables, arithmetic, comparisons, parentheses, Boolean operators, conditional expressions, local variables, mathematical functions, registered Python functions, local functions, null, and undefined.

Engine.compile() performs tokenization, parsing, and validation once. The returned expression can be evaluated many times with different variables. It does not modify the input mapping and can be evaluated concurrently, as long as registered Python functions are also thread-safe.
