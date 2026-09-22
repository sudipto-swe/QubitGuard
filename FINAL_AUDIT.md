# QubitGuard: Final Project Audit Report

**Date**: September 22, 2026  
**Auditor**: Lead Research Engineer & Quantum Software Architect  
**Project**: QubitGuard (Automated Testing, Fault Localization, and Repair for Quantum Programs)

---

## 1. Project Implementation Status

| Component | Status | Verification Detail |
|---|---|---|
| **Benchmark Circuits Library** | ✅ COMPLETE | 6 core families implemented: Bell State, GHZ-3q/4q, Teleportation-3q, Grover-2q, QFT-3q (fully decomposed), and QAOA MaxCut-3q. |
| **Fault Injection Engine** | ✅ COMPLETE | 8 standardized mutation operators (`GATE_OMISSION`, `WRONG_GATE`, `WRONG_QUBIT`, `PARAMETER_PERTURBATION`, `GATE_ORDER_SWAP`, `MEASUREMENT_MUTATION`, `CONTROLLED_OPERATION`, `REDUNDANT_GATE`) with deterministic seeds and AST diffs. |
| **Noise Simulation** | ✅ COMPLETE | Parameterized Qiskit Aer Kraus depolarizing channels ($\epsilon \in [0.00, 0.05]$), Pauli bit/phase-flip, and measurement readout errors. |
| **Testing & Detection** | ✅ COMPLETE | Metamorphic relations (Unitary Inverse $U U^\dagger = I$, Qubit Permutation Equivariance), parity invariants, Total Variation Distance (TVD), and $\chi^2$ hypothesis testing. |
| **Fault Localization (Q-SBFL)** | ✅ COMPLETE | Ochiai, Tarantula, DStar ($D^*$) suspicion ranking coupled with differential sub-circuit slicing. |
| **Automated Program Repair (Q-APR)** | ✅ COMPLETE | Heuristic mutation search guided by SBFL rankings with dual-tier validation (test-adequacy + holdout distribution fidelity). |
| **Machine Learning Predictor** | ✅ COMPLETE | Random Forest structural circuit risk predictor based on circuit topology. |
| **Streamlit Interactive UI** | ✅ COMPLETE | 6 interactive web modules (`app/app.py`). |
| **Empirical Evaluation** | ✅ COMPLETE | Full benchmark execution over 200 circuit runs answering RQ1–RQ5 with raw CSV/JSON outputs and generated Plotly figures. |
| **Academic Paper & Docs** | ✅ COMPLETE | LaTeX manuscript (`paper/main.tex`), BibTeX citations (`paper/references.bib`), and full 12-file `docs/` hierarchy. |
| **CI / CD Pipeline** | ✅ COMPLETE | GitHub Actions workflow matrix for Python 3.10, 3.11, 3.12 (`.github/workflows/ci.yml`). |

---

## 2. What Was Actually Verified
1. **Automated Test Suite**: Ran `pytest -v tests/` — all 9 test suites passed with 0 errors.
2. **Deterministic Mutation Coverage**: Tested multi-seed mutation sweeps across all benchmark circuits and operators (0 unhandled exceptions).
3. **End-to-End Empirical Benchmark**: Executed `experiments/scripts/run_benchmark.py` over 200 runs; verified generated outputs:
   - `experiments/outputs/raw_detection_runs.csv` (200 rows)
   - `experiments/outputs/raw_localization_runs.csv` (66 rows)
   - `experiments/outputs/raw_repair_runs.csv` (6 rows)
   - `experiments/outputs/benchmark_summary.json`
4. **Figure Generation**: Executed `experiments/scripts/generate_figures.py`, generating interactive HTML Plotly figures for RQ2, RQ3, and RQ4.
5. **Security & Secrets**: Verified that `.env.example` contains only placeholder tokens and that no credentials or private tokens are committed.
6. **Git History**: Verified clean 7-commit semantic git history on branch `main`.

---

## 3. Empirical Findings (Summary)
- **RQ1 (Detection)**: Mutation score of **73.30%** with **98.47% precision** and **0.8404 F1-score** across 176 mutants.
- **RQ2 (Hardness)**: Parameter Perturbation (50.0%) and Redundant Gates (58.3%) are the hardest fault classes; Controlled Operations (87.5%) and Wrong Gates (83.3%) are the easiest.
- **RQ3 (Noise)**: Precision remained $\ge 96.8\%$ even under $\epsilon = 0.05$ depolarizing noise.
- **RQ4 (Localization)**: Top-1 accuracy **43.94%**, Top-3 accuracy **69.70%**, Mean Exam Score **31.79%**.
- **RQ5 (Repair)**: Synthesized validated semantic patches for **50.00%** of single-fault repair tasks in an average of **16.09 seconds**.

---

## 4. Public Demo & Deployment Verification

- **Public Live Documentation Portal**: [https://sudipto-swe.github.io/QubitGuard/](https://sudipto-swe.github.io/QubitGuard/) (Verified HTTP 200)
- **Public Interactive App URL**: [https://qubitguard.streamlit.app/](https://qubitguard.streamlit.app/)
- **Deployment Platform**: Streamlit Community Cloud ([share.streamlit.io](https://share.streamlit.io)) & GitHub Pages
- **Entry Point**: `app/app.py`
- **Verification Date**: September 22, 2026
- **Tested & Verified Workflows**:
  - **1-Click Quick Demo Pipeline**: Verified live end-to-end execution (Program Selection → Fault Injection → Metamorphic Testing → Statistical Detection → Q-SBFL Localization → Automated Program Repair) completes in < 15 seconds.
  - **Circuit Design & Lab**: Verified Bell, GHZ, Teleportation, Grover, QFT, and QAOA circuit rendering.
  - **Fault Injection Engine**: Verified 8 mutation operators with reproducible random seeds.
  - **Quantum Test Suite**: Verified metamorphic inverse ($U U^\dagger = I$), qubit permutation equivariance, and parity property testing.
  - **Fault Localization (Q-SBFL)**: Verified Ochiai, Tarantula, and DStar ranking with differential sub-circuit slicing.
  - **Automated Repair (Q-APR)**: Verified localized patch candidate synthesis and dual-tier validation.
  - **Noise Simulation**: Verified ideal and noisy Kraus depolarizing sweeps ($\epsilon \in [0.00, 0.05]$).
  - **Empirical Results Viewer**: Verified benchmark dataset loading from `experiments/outputs/benchmark_summary.json` and Plotly scientific figure rendering.
- **GitHub Repository**: [https://github.com/sudipto-swe/QubitGuard](https://github.com/sudipto-swe/QubitGuard)
- **GitHub Actions CI Status**: **PASSED (conclusion=success)** across Python 3.10, 3.11, and 3.12 matrix ([Run #35700876844](https://github.com/sudipto-swe/QubitGuard/actions/runs/35700876844)).
- **Known Deployment Limitations**:
  - Real hardware execution requires user-provided IBM Quantum API token via environment variables (`IBMQ_API_TOKEN`); runs default gracefully to local Qiskit Aer simulation with zero credentials needed.
  - Public Streamlit Cloud containers are subject to community CPU memory quotas; benchmark circuits in the live UI are kept between 2 and 4 qubits to prevent container OOM evictions.

---

## 5. Next Research Directions
1. **Continuous Variational APR**: Implement gradient-based parameter-shift rules to repair continuous rotation angles in variational ansatzes (VQE/QAOA).
2. **Hardware Calibration Coupling**: Integrate live calibration snapshots from IBM Quantum QPUs into the noise model.
3. **Multi-Fault Combinatorial Repair**: Expand repair search using genetic programming beam search or reinforcement learning for multi-gate interaction bugs.
