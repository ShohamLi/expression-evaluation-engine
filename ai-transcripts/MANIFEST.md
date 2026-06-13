# Transcript Manifest

All listed files are edited English submission copies. `Complete` means the
supplied export or pasted record is complete as provided; it does not claim that
the AI tool exposed history beyond that export. `Partial` is used where the
supplied record is visibly truncated.

| # | Tool | Topic | Final file | Original supplied file | Completeness | Translation / redaction note | Duplicate exclusion | Original SHA-256 |
|---:|---|---|---|---|---|---|---|---|
| 1 | Cursor | Assignment analysis and project foundation | [01-assignment-analysis-and-foundation.md](transcripts/01-assignment-analysis-and-foundation.md) | `cursor_expression_evaluation_engine_ass.md1.md` | Complete | English copy; headings normalized; Hebrew translated; 2 local paths redacted | None | `487e1d74e041c7d9f6f5a5ae6a55331962b0d75c8cc516bbf5227948866077c0` |
| 2 | Cursor | Tokenizer implementation | [02-tokenizer-implementation.md](transcripts/02-tokenizer-implementation.md) | `cursor_tokenizer_implementation_for_exp.md` | Complete | English copy; headings normalized; Hebrew translated; no path redaction | `cursor_tokenizer_implementation_for_exp.md1.md` excluded as a duplicate export | `5e602a297bdb823468dd1759c7828d43a6542a8f864bfb1172b6eeb67959b02f` |
| 3 | Cursor | Immutable AST, parser, and core evaluation | [03-parser-ast-and-core-evaluation.md](transcripts/03-parser-ast-and-core-evaluation.md) | `cursor_stage_3_implementation_of_expres.md` | Complete | English copy; headings normalized; Hebrew translated; 3 local paths redacted | None | `150c7f8731ddcfe4681a7ff328a7c37f28708dd28b3f36ffc98f2965e427018b` |
| 4 | Cursor | Comparisons, Boolean logic, conditionals, strings, and local syntax | [04-language-semantics-stages-5-to-9.md](transcripts/04-language-semantics-stages-5-to-9.md) | `cursor_expression_evaluation_engine_ass.md` | Complete | English copy; headings normalized; Hebrew translated; 1 local path redacted | None | `fdc3cfa4b7f5c8fa6e0d0b6b88a9d6c8e15c76026abd439983e512306875662a` |
| 5 | Cursor | Local bindings, compilation API, functions, and product design | [05-local-bindings-compilation-and-functions.md](transcripts/05-local-bindings-compilation-and-functions.md) | `cursor_local_variable_binding_evaluatio.md` | Complete | English copy; headings normalized; Hebrew translated; no path redaction | None | `5f478a4efa9568cab5052f1b90cc80bfffcd1dce19d8b3bef9b8c4c7c3ae30e9` |
| 6 | Codex | Built-in and registered functions | [06-built-in-and-registered-functions.md](transcripts/06-built-in-and-registered-functions.md) | `Pasted markdown (2).md` | Complete | Codex export structure preserved; 1 local path redacted | None | `9611542c701c4eae809d2057128350ad348d56227feff95efe3b62b057514059` |
| 7 | Codex | Local-function syntax, evaluation, and test review | [07-local-function-syntax.md](transcripts/07-local-function-syntax.md) | `Pasted markdown (6).md` | Complete | Codex export structure preserved; 14 local paths redacted | None | `12b05f27106dbcc7224af0d2278d711c413f40d9314f9d373557b6f2bff533a1` |
| 8 | Codex | Local-function evaluation and test review | [08-local-function-evaluation.md](transcripts/08-local-function-evaluation.md) | `Pasted text.txt` | **Partial** | Unstructured excerpt preserved; no path redaction; missing content not reconstructed | None | `11fc25ae4c06b76b308a07fcf9f036bd30e079294403f62b12a7c385935330dc` |
| 9 | Codex | Function validation and error normalization | [09-function-validation-and-errors.md](transcripts/09-function-validation-and-errors.md) | `Pasted markdown (5).md` | Complete | Codex export structure preserved; 14 local paths redacted | None | `a335e0bc136e079b11e40debd99a0883ae830a79bf236198a0afe38d73d19f3c` |
| 10 | Codex | Final technical hardening | [10-final-technical-hardening.md](transcripts/10-final-technical-hardening.md) | `Pasted markdown (3).md` | Complete | Codex export structure preserved; 7 local paths redacted | None | `ed41539bb7cac33665fa6d224c9223aaf9e56c0a7564d66d400f0285520f6931` |
| 11 | Codex | Final write-up and product design | [11-final-writeup-and-product-design.md](transcripts/11-final-writeup-and-product-design.md) | `Pasted markdown (4).md` | Complete | Codex export structure preserved; 11 local paths redacted | None | `e24c3bc3894130f0991f15e11418142f0d1b7ba67bf11d3c1d6b8cd17517a28c` |

## Notes

- The excluded tokenizer file differs only in export timestamp metadata and
  duplicates the included tokenizer conversation.
- Historical branch names, commits, and test counts are preserved as reported;
  they are not rewritten to match the repository's later state.
- Model names are `Unknown` because none were supplied in the source records.
  Exact conversation dates are also `Unknown` in these submission copies; no
  date was inferred from file order or repository history.
- No raw ChatGPT export was supplied, so no ChatGPT transcript was reconstructed.
