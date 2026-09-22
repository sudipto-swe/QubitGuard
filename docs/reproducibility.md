# Reproducibility Guide & Experimental Protocol

This document provides exact, deterministic commands to reproduce all scientific evaluations reported in QubitGuard.

---

## 1. System Requirements & Environment
- **OS**: Linux (tested on Ubuntu 24.04 LTS / Debian x86_64)
- **Python**: Python 3.10, 3.11, or 3.12
- **Hardware**: Standard multi-core CPU (no GPU or quantum hardware required; runs via local Qiskit Aer simulation).

---

## 2. Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/sudiptob1/QubitGuard.git
cd QubitGuard

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies and package in editable mode
pip install --no-build-isolation -e .
```

---

## 3. Automated Test Suite Execution

To execute the unit and integration verification test suite:

```bash
pytest -v tests/
```

Expected output: 9 passed tests across core circuits, mutators, noise models, detectors, SBFL localization, and repair search.

---

## 4. Reproducing the Empirical Benchmark Evaluation (RQ1–RQ5)

Run the end-to-end benchmark suite:

```bash
python experiments/scripts/run_benchmark.py
```

This command:
1. Loads the standardized config `experiments/configs/default.yaml`.
2. Evaluates 6 benchmark circuit families (Bell, GHZ, Teleportation, Grover, QFT, QAOA).
3. Injects 8 distinct fault types across random seeds.
4. Sweeps physical depolarizing noise rates ($\epsilon \in \{0.00, 0.01, 0.02, 0.05\}$).
5. Computes Q-SBFL rankings (Top-1, Top-3, Exam scores).
6. Executes automated repair searches on mutant programs.
7. Saves raw artifacts:
   - `experiments/outputs/raw_detection_runs.csv`
   - `experiments/outputs/raw_localization_runs.csv`
   - `experiments/outputs/raw_repair_runs.csv`
   - `experiments/outputs/benchmark_summary.json`

---

## 5. Generating Scientific Figures & HTML Reports

To generate the evaluation plots from the raw outputs:

```bash
python experiments/scripts/generate_figures.py
```

Generates:
- `figure_rq2_fault_detection.html`
- `figure_rq3_noise_sensitivity.html`
- `figure_rq4_localization.html`

---

## 6. Launching the Interactive Web UI

Launch the Streamlit research dashboard:

```bash
streamlit run app/app.py
```

The interactive dashboard will be accessible at `http://localhost:8501`.
