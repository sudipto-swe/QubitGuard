"""QubitGuard - Automated Empirical Evaluation and Benchmark Runner.

Executes the formal research experiments addressing:
RQ1: Fault detection efficacy (Mutation Score, TPR, FPR)
RQ2: Hardness by fault class
RQ3: Impact of physical noise on testing sensitivity
RQ4: Spectrum-based fault localization accuracy (Top-1, Top-3, Exam score)
RQ5: Automated repair success rate and patch validation
"""

from __future__ import annotations
import os
import sys
import json
import time
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

from qubitguard.benchmarks.circuits import get_all_benchmarks
from qubitguard.fault_injection.injector import FaultInjector, FaultType
from qubitguard.execution.executor import CircuitExecutor
from qubitguard.detection.detector import FaultDetector
from qubitguard.test_generation.generator import QuantumTestGenerator
from qubitguard.localization.localizer import FaultLocalizer
from qubitguard.repair.repairer import QuantumProgramRepairer
from qubitguard.noise.models import NoiseConfig, NoiseType
from qubitguard.metrics.evaluator import DetectionMetrics, LocalizationMetrics


def run_benchmark(config_path: str = "experiments/configs/default.yaml"):
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    seed = cfg.get("seed", 42)
    shots = cfg.get("shots", 1024)
    out_dir = Path(cfg.get("output_dir", "experiments/outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"==================================================")
    print(f"Starting QubitGuard Evaluation Suite (Seed: {seed})")
    print(f"==================================================")

    all_benchmarks = get_all_benchmarks()
    target_circuits = cfg.get("circuits", list(all_benchmarks.keys()))
    fault_types = [FaultType(f) for f in cfg.get("fault_types", [f.value for f in FaultType])]
    noise_levels = cfg.get("noise_levels", [0.00, 0.01, 0.02, 0.05])

    executor = CircuitExecutor(default_shots=shots, default_seed=seed)
    generator = QuantumTestGenerator(executor=executor)
    localizer = FaultLocalizer(executor=executor, generator=generator)
    repairer = QuantumProgramRepairer(executor=executor, generator=generator, localizer=localizer, max_evaluations=25, seed=seed)

    records = []
    repair_records = []
    loc_records = []

    total_runs = len(target_circuits) * len(fault_types) * len(noise_levels)
    run_idx = 0

    for c_name in target_circuits:
        if c_name not in all_benchmarks:
            continue
        ref_prog = all_benchmarks[c_name]

        for n_level in noise_levels:
            noise_cfg = NoiseConfig(noise_type=NoiseType.DEPOLARIZING, error_rate=n_level) if n_level > 0 else None

            # First, evaluate Clean/Unmutated circuit under this noise level to measure False Positives
            clean_report = generator.run_suite(ref_prog, reference_program=ref_prog, noise_config=noise_cfg)
            records.append({
                "circuit": c_name,
                "num_qubits": ref_prog.num_qubits,
                "circuit_depth": ref_prog.depth,
                "fault_type": "NONE (CLEAN)",
                "noise_level": n_level,
                "is_mutant": 0,
                "detected": int(clean_report.is_fault_detected),
                "passed_tests": clean_report.passed_tests,
                "total_tests": clean_report.total_tests,
                "pass_rate": clean_report.pass_rate,
            })

            for f_type in fault_types:
                run_idx += 1
                injector = FaultInjector(seed=seed + run_idx)
                
                # Check injectability
                valid_idx = injector.get_injectable_indices(ref_prog, f_type)
                if not valid_idx:
                    continue

                mut_prog, mut_rec = injector.inject_fault(ref_prog, f_type)
                print(f"[{run_idx}/{total_runs}] Testing {c_name} | {f_type.value} | noise={n_level}", flush=True)

                # Test detection
                mut_report = generator.run_suite(mut_prog, reference_program=ref_prog, noise_config=noise_cfg)

                records.append({
                    "circuit": c_name,
                    "num_qubits": ref_prog.num_qubits,
                    "circuit_depth": ref_prog.depth,
                    "fault_type": f_type.value,
                    "noise_level": n_level,
                    "is_mutant": 1,
                    "detected": int(mut_report.is_fault_detected),
                    "passed_tests": mut_report.passed_tests,
                    "total_tests": mut_report.total_tests,
                    "pass_rate": mut_report.pass_rate,
                })

                # RQ4: Fault Localization on detectable mutants under ideal/low noise
                if n_level in [0.00, 0.01] and mut_report.is_fault_detected:
                    loc_res = localizer.localize_faults(
                        mut_prog,
                        reference_program=ref_prog,
                        actual_fault_index=mut_rec.target_index,
                        noise_config=noise_cfg,
                    )
                    is_top1 = int(loc_res.top_1_index == mut_rec.target_index)
                    is_top3 = int(mut_rec.target_index in loc_res.top_3_indices)
                    loc_records.append({
                        "circuit": c_name,
                        "fault_type": f_type.value,
                        "noise_level": n_level,
                        "target_index": mut_rec.target_index,
                        "top_1_hit": is_top1,
                        "top_3_hit": is_top3,
                        "rank_of_actual": loc_res.rank_of_actual_fault or len(loc_res.rankings),
                        "exam_score": loc_res.exam_score or 1.0,
                    })

                # RQ5: Automated Program Repair on ideal conditions for key circuits
                if n_level == 0.00 and f_type in [FaultType.GATE_OMISSION, FaultType.WRONG_GATE] and c_name in ["Bell_State", "GHZ_3q", "Grover_2q"]:
                    rep_res = repairer.repair(
                        mut_prog,
                        reference_program=ref_prog,
                        noise_config=noise_cfg,
                    )
                    repair_records.append({
                        "circuit": c_name,
                        "fault_type": f_type.value,
                        "candidates_evaluated": rep_res.total_candidates_evaluated,
                        "test_adequate_patches": len(rep_res.test_adequate_patches),
                        "validated_patches": len(rep_res.validated_patches),
                        "repair_successful": int(rep_res.repair_successful),
                        "search_time_sec": rep_res.search_time_sec,
                    })

    # Save raw results
    df_runs = pd.DataFrame(records)
    df_runs.to_csv(out_dir / "raw_detection_runs.csv", index=False)
    print(f"Saved: {out_dir / 'raw_detection_runs.csv'} ({len(df_runs)} rows)")

    df_loc = pd.DataFrame(loc_records)
    if not df_loc.empty:
        df_loc.to_csv(out_dir / "raw_localization_runs.csv", index=False)
        print(f"Saved: {out_dir / 'raw_localization_runs.csv'} ({len(df_loc)} rows)")

    df_rep = pd.DataFrame(repair_records)
    if not df_rep.empty:
        df_rep.to_csv(out_dir / "raw_repair_runs.csv", index=False)
        print(f"Saved: {out_dir / 'raw_repair_runs.csv'} ({len(df_rep)} rows)")

    # Aggregate summaries for RQs
    summary = {}

    # RQ1: Overall Detection Efficacy
    mutants = df_runs[df_runs["is_mutant"] == 1]
    cleans = df_runs[df_runs["is_mutant"] == 0]
    det_metrics = DetectionMetrics.compute(df_runs["is_mutant"].tolist(), df_runs["detected"].tolist())
    summary["RQ1_overall_detection"] = det_metrics.to_dict()

    # RQ2: Detection Rate by Fault Class
    rq2_series = mutants.groupby("fault_type")["detected"].mean()
    summary["RQ2_detection_by_fault_class"] = {k: round(float(v), 4) for k, v in rq2_series.items()}

    # RQ3: Metrics by Noise Level
    rq3_dict = {}
    for nl, grp in df_runs.groupby("noise_level"):
        m = DetectionMetrics.compute(grp["is_mutant"].tolist(), grp["detected"].tolist())
        rq3_dict[str(nl)] = m.to_dict()
    summary["RQ3_noise_impact"] = rq3_dict

    # RQ4: SBFL Accuracy
    if not df_loc.empty:
        summary["RQ4_localization"] = {
            "total_evaluations": len(df_loc),
            "top_1_accuracy": round(float(df_loc["top_1_hit"].mean()), 4),
            "top_3_accuracy": round(float(df_loc["top_3_hit"].mean()), 4),
            "mean_first_rank": round(float(df_loc["rank_of_actual"].mean()), 2),
            "mean_exam_score": round(float(df_loc["exam_score"].mean()), 4),
        }

    # RQ5: Repair Success Rate
    if not df_rep.empty:
        summary["RQ5_repair"] = {
            "total_repair_tasks": len(df_rep),
            "repair_success_rate": round(float(df_rep["repair_successful"].mean()), 4),
            "avg_candidates_evaluated": round(float(df_rep["candidates_evaluated"].mean()), 1),
            "avg_search_time_sec": round(float(df_rep["search_time_sec"].mean()), 2),
        }

    with open(out_dir / "benchmark_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {out_dir / 'benchmark_summary.json'}")

    print("\n=== Benchmark Summary ===")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run_benchmark()
