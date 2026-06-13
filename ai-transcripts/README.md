# AI Transcripts - Expression Evaluation Engine

This directory contains the available AI-assisted conversations used during
the Expression Evaluation Engine assignment. Cursor supported staged
implementation and focused testing; Codex supported deeper audits, validation,
hardening, and documentation review.

The files are ordered chronologically by project topic. They include the
available user prompts, AI responses, tool traces, corrections, rejected
suggestions, failures, and reported validation results. The combined file
`AI_TRANSCRIPTS_COMPLETE.md` contains the same 11 records in one document.

## Editing policy

These are edited English submission copies, not byte-for-byte raw exports.
Readability edits were limited to project-specific titles, faithful translation
of meaningful Hebrew fragments, removal of obvious keyboard noise and repeated
export boilerplate, Markdown repair, and explicit privacy redaction. Absolute
local paths are replaced with `[LOCAL_HOME]`. No missing prompt, response,
result, or decision was reconstructed or invented.

Cursor speaker headings were normalized. Codex tool traces and collapsed-history
markup were preserved where supplied because they form part of the authentic
export structure.

## Completeness

Ten topic files are complete supplied exports. Transcript 08 is a partial,
unstructured Stage 16 excerpt: its original implementation prompt is truncated
and its final diff fragment is incomplete. It is retained and clearly marked
rather than repaired or expanded.

No raw ChatGPT account or conversation export was supplied, so this package
does not present a ChatGPT transcript as authentic. Original filenames,
completeness status, editing notes, duplicate exclusions, and available SHA-256
hashes are recorded in `MANIFEST.md`.

## Transcript index

1. [Assignment Analysis and Project Foundation](transcripts/01-assignment-analysis-and-foundation.md)
2. [Tokenizer Implementation](transcripts/02-tokenizer-implementation.md)
3. [Immutable AST, Parser, and Core Evaluation](transcripts/03-parser-ast-and-core-evaluation.md)
4. [Language Semantics: Stages 5-9](transcripts/04-language-semantics-stages-5-to-9.md)
5. [Local Bindings, Compilation, and Functions](transcripts/05-local-bindings-compilation-and-functions.md)
6. [Built-in and Registered Functions](transcripts/06-built-in-and-registered-functions.md)
7. [Local Function Syntax, Evaluation, and Test Review](transcripts/07-local-function-syntax.md)
8. [Local Function Evaluation - Partial Excerpt](transcripts/08-local-function-evaluation.md)
9. [Function Validation and Errors](transcripts/09-function-validation-and-errors.md)
10. [Final Technical Hardening](transcripts/10-final-technical-hardening.md)
11. [Final Write-up and Product Design](transcripts/11-final-writeup-and-product-design.md)
