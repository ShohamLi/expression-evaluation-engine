# Expression Diagnostic Preview

Users configuring expressions often cannot tell whether an unexpected result
comes from the expression, missing input, a null value, or an evaluation error.
This makes debugging slow and can lead to incorrect business rules.

The proposed **Expression Diagnostic Preview** lets a user test an expression
against a sample of recent records before using it. For each sampled
record, it shows the expression result, the input values used, and a clear
status: valid value, null, undefined, or evaluation error. A valid `0` remains a
normal numeric result and is never grouped with missing data or errors.

For example, with `revenue - cost`, one record may show `45`, another may show
undefined because `cost` is missing, and another may show an evaluation error
because `cost` contains text.

This preview helps users find data-quality problems and expression mistakes
before they affect normal workflows. Sampling should be bounded and optional so
previewing does not add significant load to regular evaluation.
