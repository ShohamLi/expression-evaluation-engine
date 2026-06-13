# expression-evaluation-engine

A reusable Python library for compiling and evaluating expressions such as
`2 + 3 * (x - 1)` against a set of named variables.

> **Status: under development.** This is an early scaffold. No expression-language
> features (parsing, evaluation, variables, functions, strings, null/undefined
> handling, etc.) are implemented yet. The sections below describe only what
> currently exists.

## Requirements

- Python 3.11 or newer

## Installation (editable, for development)

```bash
python -m pip install -e ".[dev]"
```

This installs the package in editable mode together with the development
dependencies (currently only `pytest`).

## Running the tests

```bash
python -m pytest
```

## What currently exists

- An importable `expression_engine` package.
- A small, documented exception hierarchy rooted at `ExpressionError`.
- The `UNDEFINED` singleton, representing a missing or unavailable value and kept
  distinct from explicit null (Python `None`).

```python
import expression_engine
from expression_engine import UNDEFINED
```

## Not yet implemented

Expression compilation and evaluation, variable lookup, local variables and
functions, built-in math functions, custom function registration, string
operations, boolean/conditional semantics, and the public `Engine` / `Expression`
API are planned for later stages and are **not** available yet.
