"""QubitGuard - Command-Line Interface."""

from __future__ import annotations
import argparse
import sys
import json
from qubitguard.benchmarks.circuits import get_all_benchmarks
from qubitguard.fault_injection.injector import FaultInjector, FaultType
from qubitguard.execution.executor import CircuitExecutor
from qubitguard.test_generation.generator import QuantumTestGenerator
from qubitguard.localization.localizer import FaultLocalizer
from qubitguard.repair.repairer import QuantumProgramRepairer
from qubitguard.noise.models import NoiseConfig, NoiseType


def main():
    parser = argparse.ArgumentParser(description="QubitGuard - Quantum Software Testing and Repair Framework")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Benchmarks command
    bench_parser = subparsers.add_parser("benchmarks", help="List available quantum benchmark circuits")

    # Inject command
    inject_parser = subparsers.add_parser("inject", help="Inject a fault into a benchmark circuit")
    inject_parser.add_argument("--circuit", default="Bell_State", help="Target benchmark circuit")
    inject_parser.add_argument("--fault", default="GATE_OMISSION", choices=[f.value for f in FaultType])
    inject_parser.add_argument("--seed", type=int, default=42)

    # Test command
    test_parser = subparsers.add_parser("test", help="Run test suite on a benchmark circuit")
    test_parser.add_argument("--circuit", default="Bell_State")
    test_parser.add_argument("--noise", type=float, default=0.0, help="Depolarizing noise level")

    # Repair command
    repair_parser = subparsers.add_parser("repair", help="Inject fault and execute automated repair")
    repair_parser.add_argument("--circuit", default="Bell_State")
    repair_parser.add_argument("--fault", default="GATE_OMISSION", choices=[f.value for f in FaultType])
    repair_parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    benchmarks = get_all_benchmarks()

    if args.command == "benchmarks":
        print("Available Benchmark Circuits:")
        for name, prog in benchmarks.items():
            print(f" - {name} ({prog.num_qubits} qubits, depth {prog.depth}): {prog.description}")

    elif args.command == "inject":
        if args.circuit not in benchmarks:
            print(f"Error: Unknown circuit '{args.circuit}'", file=sys.stderr)
            sys.exit(1)
        prog = benchmarks[args.circuit]
        injector = FaultInjector(seed=args.seed)
        mut_prog, record = injector.inject_fault(prog, FaultType(args.fault))
        print(f"Successfully injected fault into {args.circuit}:")
        print(json.dumps(record.to_dict(), indent=2))

    elif args.command == "test":
        if args.circuit not in benchmarks:
            print(f"Error: Unknown circuit '{args.circuit}'", file=sys.stderr)
            sys.exit(1)
        prog = benchmarks[args.circuit]
        noise_cfg = NoiseConfig(noise_type=NoiseType.DEPOLARIZING, error_rate=args.noise) if args.noise > 0 else None
        gen = QuantumTestGenerator()
        report = gen.run_suite(prog, reference_program=prog, noise_config=noise_cfg)
        print(f"Test Suite for {args.circuit} (Noise={args.noise}):")
        print(f"Passed: {report.passed_tests}/{report.total_tests} | Fault Detected: {report.is_fault_detected}")
        for t in report.test_results:
            status = "PASS" if t.passed else "FAIL"
            print(f" [{status}] {t.test_name}: {t.description}")

    elif args.command == "repair":
        if args.circuit not in benchmarks:
            print(f"Error: Unknown circuit '{args.circuit}'", file=sys.stderr)
            sys.exit(1)
        ref_prog = benchmarks[args.circuit]
        injector = FaultInjector(seed=args.seed)
        mut_prog, record = injector.inject_fault(ref_prog, FaultType(args.fault))
        print(f"Injected: {record.description}")
        repairer = QuantumProgramRepairer(seed=args.seed)
        report = repairer.repair(mut_prog, reference_program=ref_prog)
        print(f"Repair Complete in {report.search_time_sec:.2f}s:")
        print(f"Candidates evaluated: {report.total_candidates_evaluated}")
        print(f"Validated patches: {len(report.validated_patches)}")
        if report.best_patch:
            print(f"Best Patch: {report.best_patch.description} (Fitness: {report.best_patch.fitness_score:.3f})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
