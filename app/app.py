"""QubitGuard - Interactive Web Research Platform (Streamlit)."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go

from qubitguard.benchmarks.circuits import get_all_benchmarks
from qubitguard.fault_injection.injector import FaultInjector, FaultType
from qubitguard.execution.executor import CircuitExecutor
from qubitguard.detection.detector import FaultDetector
from qubitguard.test_generation.generator import QuantumTestGenerator
from qubitguard.localization.localizer import FaultLocalizer
from qubitguard.repair.repairer import QuantumProgramRepairer
from qubitguard.noise.models import NoiseConfig, NoiseType
from qubitguard.ml.predictor import QuantumFaultRiskPredictor
from qubitguard.utils.visualization import (
    create_distribution_comparison_chart,
    create_localization_ranking_chart,
)

# App Configuration
st.set_page_config(
    page_title="QubitGuard: Quantum Software Testing & Repair",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚛️ QubitGuard: Automated Testing, Fault Localization & Repair for Quantum Programs")
st.markdown(
    """
    *A research-grade Quantum Software Engineering (QSE) platform combining metamorphic testing, 
    statistical divergence detection, spectrum-based fault localization (Q-SBFL), and automated program repair (Q-APR).*
    """
)

# Sidebar Navigation
st.sidebar.header("Navigation & Settings")
page = st.sidebar.radio(
    "Select Module",
    [
        "1. Overview & Research",
        "2. Circuit & Fault Injection Lab",
        "3. Test Suite & Fault Detection",
        "4. Quantum Fault Localization (SBFL)",
        "5. Automated Program Repair (APR)",
        "6. Empirical Benchmark Results",
    ]
)

benchmarks = get_all_benchmarks()

# Global session states
if "selected_circuit_name" not in st.session_state:
    st.session_state.selected_circuit_name = "Bell_State"
if "mutated_program" not in st.session_state:
    st.session_state.mutated_program = None
if "mutation_record" not in st.session_state:
    st.session_state.mutation_record = None

# -------------------------------------------------------------
# PAGE 1: OVERVIEW & RESEARCH
# -------------------------------------------------------------
if page == "1. Overview & Research":
    st.header("Project Overview & Research Questions")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
            ### Research Motivation
            Quantum computing systems are inherently susceptible to both physical decoherence and subtle software design defects.
            Conventional testing frameworks fail in quantum domains due to:
            1. **The Quantum Test Oracle Problem**: Lack of deterministic expected outputs for arbitrary quantum states.
            2. **Decoherence Confounding**: Hardware noise produces measurement deviations that mimic algorithmic bugs.
            3. **Non-Cloning & Measurement Collapse**: Debuggers cannot probe runtime states without altering wavefunctions.

            QubitGuard systematically tackles these challenges through an end-to-end framework:
            - **Reproducible Fault Taxonomy**: 8 quantum gate mutation operators.
            - **Noise-Calibrated Statistical Testing**: Total Variation Distance (TVD) & $\chi^2$ hypothesis testing over Aer simulations.
            - **Quantum Spectrum-Based Fault Localization (Q-SBFL)**: Ochiai, Tarantula, and DStar suspicion ranking with sub-circuit slicing.
            - **Guided Heuristic Quantum Program Repair (Q-APR)**: Search-based synthesis of test-adequate and validated patches.
            """
        )

        st.subheader("Core Research Questions")
        st.markdown(
            """
            - **RQ1 (Detection Efficacy)**: How effectively can metamorphic relations and property invariants detect injected quantum program faults?
            - **RQ2 (Fault Class Vulnerability)**: Which quantum gate fault classes are most difficult to detect and localize?
            - **RQ3 (Noise Robustness)**: How does environmental noise affect fault-detection sensitivity and false alarm rates?
            - **RQ4 (Fault Localization Accuracy)**: How accurately can Q-SBFL isolate faulty quantum operations?
            - **RQ5 (Automated Repair Efficacy)**: How often can heuristic search synthesize valid patches that restore intended semantics?
            """
        )

    with col2:
        st.info("System Status")
        st.metric("Benchmark Circuits", len(benchmarks))
        st.metric("Fault Operators", len(FaultType))
        st.metric("Noise Models", 4)
        st.success("Qiskit Aer Simulator: Active")
        st.caption("Developed by Sudipto Biswas (Lead Research Engineer)")

# -------------------------------------------------------------
# PAGE 2: CIRCUIT & FAULT INJECTION LAB
# -------------------------------------------------------------
elif page == "2. Circuit & Fault Injection Lab":
    st.header("Circuit Design & Fault Injection Laboratory")

    c_name = st.selectbox("Select Target Benchmark Circuit", list(benchmarks.keys()), index=0)
    st.session_state.selected_circuit_name = c_name
    ref_prog = benchmarks[c_name]

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    col_meta1.metric("Qubits", ref_prog.num_qubits)
    col_meta2.metric("Circuit Depth", ref_prog.depth)
    col_meta3.metric("Total Gates", ref_prog.size)
    col_meta4.metric("Family", ref_prog.properties.get("family", "general"))

    st.subheader("Original Circuit Diagram")
    st.text(ref_prog.circuit.draw(output="text"))

    st.markdown("---")
    st.subheader("Fault Injection Engine")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        selected_fault = st.selectbox("Fault Type", [f.value for f in FaultType])
    with col_f2:
        injector = FaultInjector(seed=42)
        valid_indices = injector.get_injectable_indices(ref_prog, FaultType(selected_fault))
        if valid_indices:
            target_idx = st.selectbox("Target Gate Index", valid_indices)
        else:
            st.warning("No injectable gates for this fault type in this circuit.")
            target_idx = None
    with col_f3:
        seed_val = st.number_input("Random Seed", value=42, step=1)

    if st.button("Inject Fault into Circuit", type="primary"):
        if target_idx is not None:
            inj = FaultInjector(seed=seed_val)
            mut_prog, rec = inj.inject_fault(ref_prog, FaultType(selected_fault), target_index=target_idx)
            st.session_state.mutated_program = mut_prog
            st.session_state.mutation_record = rec
            st.success(f"Fault injected: {rec.description}")

    if st.session_state.mutated_program is not None and st.session_state.mutation_record is not None:
        st.subheader("Mutated (Faulty) Circuit Diagram")
        st.text(st.session_state.mutated_program.circuit.draw(output="text"))
        st.json(st.session_state.mutation_record.to_dict())

# -------------------------------------------------------------
# PAGE 3: TEST SUITE & FAULT DETECTION
# -------------------------------------------------------------
elif page == "3. Test Suite & Fault Detection":
    st.header("Quantum Test Suite & Statistical Fault Detection")

    c_name = st.session_state.selected_circuit_name
    ref_prog = benchmarks[c_name]
    mut_prog = st.session_state.mutated_program

    st.write(f"Target Circuit: **{c_name}** | Status: **{'Mutant Loaded' if mut_prog else 'Clean (Baseline)'}**")

    col_n1, col_n2, col_n3 = st.columns(3)
    with col_n1:
        noise_type = st.selectbox("Noise Simulation Model", [n.value for n in NoiseType], index=0)
    with col_n2:
        noise_rate = st.slider("Depolarizing Error Rate (epsilon)", 0.0, 0.08, 0.00, step=0.01)
    with col_n3:
        shots_val = st.select_slider("Measurement Shots", options=[256, 512, 1024, 2048, 4096], value=1024)

    noise_cfg = NoiseConfig(noise_type=NoiseType(noise_type), error_rate=noise_rate) if noise_rate > 0 else None

    if st.button("Execute Quantum Test Suite", type="primary"):
        executor = CircuitExecutor(default_shots=shots_val)
        generator = QuantumTestGenerator(executor=executor)
        
        target_to_test = mut_prog if mut_prog is not None else ref_prog
        report = generator.run_suite(target_to_test, reference_program=ref_prog, noise_config=noise_cfg)

        st.subheader("Test Suite Execution Report")
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Tests Executed", report.total_tests)
        col_res2.metric("Tests Passed", f"{report.passed_tests} ({report.pass_rate*100:.1f}%)")
        col_res3.metric("Fault Detected", "YES (BUG FOUND)" if report.is_fault_detected else "NO (CLEAN / UNDETECTED)")

        # Display test cases
        st.table(pd.DataFrame([
            {
                "Test Strategy": t.strategy.upper(),
                "Test Name": t.test_name,
                "Status": "PASSED" if t.passed else "FAILED",
                "Description": t.description,
            }
            for t in report.test_results
        ]))

        # Compare output distributions
        res_ref = executor.run(ref_prog, shots=shots_val, noise_config=noise_cfg)
        res_cand = executor.run(target_to_test, shots=shots_val, noise_config=noise_cfg)
        fig_dist = create_distribution_comparison_chart(
            res_ref.probabilities,
            res_cand.probabilities,
            title=f"Distribution Comparison: Reference vs {target_to_test.name}"
        )
        st.plotly_chart(fig_dist, use_container_width=True)

# -------------------------------------------------------------
# PAGE 4: QUANTUM FAULT LOCALIZATION (SBFL)
# -------------------------------------------------------------
elif page == "4. Quantum Fault Localization (SBFL)":
    st.header("Quantum Spectrum-Based Fault Localization (Q-SBFL)")
    c_name = st.session_state.selected_circuit_name
    ref_prog = benchmarks[c_name]
    mut_prog = st.session_state.mutated_program
    rec = st.session_state.mutation_record

    if mut_prog is None:
        st.warning("Please inject a fault in '2. Circuit & Fault Injection Lab' first.")
    else:
        st.write(f"Analyzing mutant of: **{c_name}** | Ground Truth Fault at Gate Index: **{rec.target_index if rec else 'Unknown'}**")

        if st.button("Run Fault Localization Analysis", type="primary"):
            with st.spinner("Computing sub-circuit spectra and SBFL suspiciousness coefficients..."):
                localizer = FaultLocalizer()
                loc_res = localizer.localize_faults(
                    mut_prog,
                    reference_program=ref_prog,
                    actual_fault_index=rec.target_index if rec else None,
                )

                st.subheader("Suspiciousness Rankings (Top Gates)")
                fig_loc = create_localization_ranking_chart(
                    [r.to_dict() for r in loc_res.rankings],
                    actual_fault_idx=rec.target_index if rec else None,
                )
                st.plotly_chart(fig_loc, use_container_width=True)

                col_l1, col_l2, col_l3 = st.columns(3)
                col_l1.metric("Top-1 Gate Index", f"#{loc_res.top_1_index}")
                col_l2.metric("Top-3 Gate Indices", str(loc_res.top_3_indices))
                if loc_res.rank_of_actual_fault is not None:
                    col_l3.metric("Ground Truth Rank", f"Rank #{loc_res.rank_of_actual_fault}")

                st.dataframe(pd.DataFrame([r.to_dict() for r in loc_res.rankings]))

# -------------------------------------------------------------
# PAGE 5: AUTOMATED PROGRAM REPAIR (APR)
# -------------------------------------------------------------
elif page == "5. Automated Program Repair (APR)":
    st.header("Automated Quantum Program Repair (Q-APR)")
    c_name = st.session_state.selected_circuit_name
    ref_prog = benchmarks[c_name]
    mut_prog = st.session_state.mutated_program

    if mut_prog is None:
        st.warning("Please inject a fault in '2. Circuit & Fault Injection Lab' first.")
    else:
        st.write(f"Repairing faulty circuit: **{mut_prog.name}**")
        max_evals = st.slider("Maximum Patch Search Evaluations", 10, 50, 25)

        if st.button("Launch Automated Repair Search", type="primary"):
            with st.spinner("Searching localized repair space and validating candidate patches..."):
                repairer = QuantumProgramRepairer(max_evaluations=max_evals, seed=42)
                rep_report = repairer.repair(mut_prog, reference_program=ref_prog)

                st.subheader("Automated Repair Results")
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Repair Outcome", "SUCCESS" if rep_report.repair_successful else "FAILED")
                col_r2.metric("Validated Patches", len(rep_report.validated_patches))
                col_r3.metric("Search Time", f"{rep_report.search_time_sec:.2f}s")

                if rep_report.best_patch:
                    st.success(f"Best Validated Patch: **{rep_report.best_patch.description}** (Fitness: {rep_report.best_patch.fitness_score:.3f})")
                    st.subheader("Repaired Circuit Diagram")
                    st.text(rep_report.best_patch.repaired_program.circuit.draw(output="text"))

                st.write("Evaluated Candidates Summary:")
                st.dataframe(pd.DataFrame([p.to_dict() for p in rep_report.test_adequate_patches]))

# -------------------------------------------------------------
# PAGE 6: EMPIRICAL BENCHMARK RESULTS
# -------------------------------------------------------------
elif page == "6. Empirical Benchmark Results":
    st.header("Empirical Benchmark Results & Research Answers")

    from pathlib import Path
    summary_file = Path("experiments/outputs/benchmark_summary.json")
    if summary_file.exists():
        with open(summary_file, "r") as f:
            summary = json.load(f)

        st.subheader("RQ1: Overall Testing Efficacy")
        rq1 = summary.get("RQ1_overall_detection", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Mutants Evaluated", rq1.get("total_mutants", "-"))
        c2.metric("Mutation Score (Recall)", f"{rq1.get('recall', 0.0)*100:.1f}%")
        c3.metric("Precision", f"{rq1.get('precision', 0.0)*100:.1f}%")
        c4.metric("F1-Score", f"{rq1.get('f1_score', 0.0):.3f}")

        st.markdown("---")
        st.subheader("RQ2: Fault Detection Rate by Mutation Operator")
        rq2 = summary.get("RQ2_detection_by_fault_class", {})
        if rq2:
            fig2 = go.Figure(go.Bar(
                x=list(rq2.keys()),
                y=[v * 100 for v in rq2.values()],
                marker_color="#0284c7",
                text=[f"{v*100:.1f}%" for v in rq2.values()],
                textposition="auto"
            ))
            fig2.update_layout(xaxis_title="Fault Operator", yaxis_title="Detection Rate (%)", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("RQ3: Sensitivity vs Noise Level")
        rq3 = summary.get("RQ3_noise_impact", {})
        if rq3:
            df_rq3 = pd.DataFrame([
                {"Noise Level (eps)": k, **v} for k, v in rq3.items()
            ])
            st.table(df_rq3[["Noise Level (eps)", "mutation_score", "precision", "recall", "f1_score"]])

        st.markdown("---")
        st.subheader("RQ4: Spectrum-Based Fault Localization Accuracy (Q-SBFL)")
        rq4 = summary.get("RQ4_localization", {})
        if rq4:
            c_loc1, c_loc2, c_loc3 = st.columns(3)
            c_loc1.metric("Top-1 Accuracy", f"{rq4.get('top_1_accuracy', 0.0)*100:.1f}%")
            c_loc2.metric("Top-3 Accuracy", f"{rq4.get('top_3_accuracy', 0.0)*100:.1f}%")
            c_loc3.metric("Mean First Rank", f"{rq4.get('mean_first_rank', 0.0):.2f}")

        st.markdown("---")
        st.subheader("RQ5: Automated Program Repair Efficacy")
        rq5 = summary.get("RQ5_repair", {})
        if rq5:
            c_rep1, c_rep2, c_rep3 = st.columns(3)
            c_rep1.metric("Repair Success Rate", f"{rq5.get('repair_success_rate', 0.0)*100:.1f}%")
            c_rep2.metric("Avg Search Time", f"{rq5.get('avg_search_time_sec', 0.0):.2f}s")
            c_rep3.metric("Avg Evaluations per Task", f"{rq5.get('avg_candidates_evaluated', 0.0):.1f}")
    else:
        st.info("Run `python experiments/scripts/run_benchmark.py` to generate the empirical benchmark dataset.")
