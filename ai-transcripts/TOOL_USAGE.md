# AI Tool Usage

I used AI tools as assistants throughout the project while keeping final design
and implementation responsibility.

## Cursor

Cursor supported the staged implementation workflow. I used it to inspect the
existing repository, propose small changes, implement one stage at a time, add
focused tests, and report validation results. Each implementation request
required an inspection phase before editing and explicitly limited the work to
the current stage.

## Codex

Codex was used mainly for deeper repository audits, function semantics,
local-function behavior, error normalization, test review, final hardening,
and submission documentation. I reviewed its proposals against the assignment,
the current codebase, and the project decision log.

## My review and decisions

I did not accept AI output automatically. I selected the language semantics,
public API, scope, and architecture. I corrected proposals that exceeded the
approved stage, rejected unnecessary metadata and documentation changes,
removed redundant tests, and required focused validation before each commit.

The repository history, tests, and decision log remain the source of truth for
the final implementation.
