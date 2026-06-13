"""Reproducible microbenchmarks for compilation and repeated evaluation.

Run from the repository root with::

    PYTHONPATH=src python benchmarks/benchmark_engine.py

Results are specific to the current machine, Python implementation, and system
load. The suite measures compilation separately from evaluation and reuses one
compiled expression and one stable variable mapping per evaluation workload.
"""

from __future__ import annotations

import argparse
import platform
import statistics
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from time import perf_counter_ns

from expression_engine import Engine


DEFAULT_ITERATIONS = 20_000
DEFAULT_SAMPLES = 5


@dataclass(frozen=True, slots=True)
class Workload:
    name: str
    operation: Callable[[], object]


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _measure(
    workload: Workload,
    iterations: int,
    samples: int,
    warmup_iterations: int,
) -> tuple[float, float, float]:
    for _ in range(warmup_iterations):
        workload.operation()

    durations: list[int] = []
    for _ in range(samples):
        start = perf_counter_ns()
        for _ in range(iterations):
            workload.operation()
        durations.append(perf_counter_ns() - start)

    median_duration_ns = statistics.median(durations)
    nanoseconds_per_operation = median_duration_ns / iterations
    operations_per_second = 1_000_000_000 / nanoseconds_per_operation
    return median_duration_ns, nanoseconds_per_operation, operations_per_second


def _build_workloads() -> tuple[Workload, tuple[Workload, ...]]:
    compilation_engine = Engine()
    compilation_source = "2 + 3 * (x - 1)"
    compilation = Workload(
        "compile arithmetic",
        lambda: compilation_engine.compile(compilation_source),
    )

    empty_variables: dict[str, object] = {}

    constant_expression = Engine().compile("2 + 3 * (4 - 1)")
    constant_arithmetic = Workload(
        "evaluate constant arithmetic",
        lambda: constant_expression.evaluate(empty_variables),
    )

    variable_expression = Engine().compile("2 + 3 * (x - 1)")
    variable_mapping = {"x": 5}
    variable_arithmetic = Workload(
        "evaluate variable arithmetic",
        lambda: variable_expression.evaluate(variable_mapping),
    )

    conditional_expression = Engine().compile("value if enabled else fallback")
    conditional_mapping = {"value": 10, "enabled": True, "fallback": 0}
    conditional = Workload(
        "evaluate conditional",
        lambda: conditional_expression.evaluate(conditional_mapping),
    )

    builtin_expression = Engine().compile("sqrt(x) + abs(y)")
    builtin_mapping = {"x": 9, "y": -4}
    builtin_functions = Workload(
        "evaluate built-in functions",
        lambda: builtin_expression.evaluate(builtin_mapping),
    )

    def increment(value: int) -> int:
        return value + 1

    registered_engine = Engine(functions={"increment": increment})
    registered_expression = registered_engine.compile("increment(x)")
    registered_mapping = {"x": 5}
    registered_function = Workload(
        "evaluate registered function",
        lambda: registered_expression.evaluate(registered_mapping),
    )

    local_expression = Engine().compile(
        "let add(a, b) = a + b in add(x, y)"
    )
    local_mapping = {"x": 2, "y": 3}
    local_function = Workload(
        "evaluate local function",
        lambda: local_expression.evaluate(local_mapping),
    )

    evaluation = (
        constant_arithmetic,
        variable_arithmetic,
        conditional,
        builtin_functions,
        registered_function,
        local_function,
    )
    return compilation, evaluation


def _format_duration(nanoseconds: float) -> str:
    if nanoseconds < 1_000:
        return f"{nanoseconds:.1f} ns"
    if nanoseconds < 1_000_000:
        return f"{nanoseconds / 1_000:.3f} us"
    if nanoseconds < 1_000_000_000:
        return f"{nanoseconds / 1_000_000:.3f} ms"
    return f"{nanoseconds / 1_000_000_000:.3f} s"


def _print_result(
    workload: Workload,
    iterations: int,
    samples: int,
    warmup_iterations: int,
) -> None:
    median_ns, per_operation_ns, operations_per_second = _measure(
        workload, iterations, samples, warmup_iterations
    )
    print(workload.name)
    print(f"  median sample: {_format_duration(median_ns)}")
    print(f"  time/op:       {_format_duration(per_operation_ns)}")
    print(f"  operations/s:  {operations_per_second:,.0f}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iterations",
        type=_positive_int,
        default=DEFAULT_ITERATIONS,
        help=f"operations per recorded sample (default: {DEFAULT_ITERATIONS})",
    )
    parser.add_argument(
        "--samples",
        type=_positive_int,
        default=DEFAULT_SAMPLES,
        help=f"recorded samples per workload (default: {DEFAULT_SAMPLES})",
    )
    args = parser.parse_args(argv)
    warmup_iterations = min(1_000, max(1, args.iterations // 10))

    print("Expression Evaluation Engine benchmark")
    print(f"Python version:        {platform.python_version()}")
    print(f"Python implementation: {platform.python_implementation()}")
    print(f"Platform:              {platform.platform()}")
    print(f"Machine:               {platform.machine() or 'unknown'}")
    print(f"Iterations/sample:     {args.iterations:,}")
    print(f"Recorded samples:      {args.samples}")
    print(f"Warm-up operations:    {warmup_iterations:,} per workload")
    print("Results are machine-, interpreter-, and load-specific.")

    compilation, evaluation_workloads = _build_workloads()

    print("\nCompilation")
    _print_result(
        compilation, args.iterations, args.samples, warmup_iterations
    )

    print("\nEvaluation (compiled once; stable mappings reused)")
    for workload in evaluation_workloads:
        _print_result(
            workload, args.iterations, args.samples, warmup_iterations
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
