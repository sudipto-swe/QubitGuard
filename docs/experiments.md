# QubitGuard: Experimental Methodology & Protocol

## 1. Experimental Design Overview
The empirical evaluation of QubitGuard investigates five research questions (RQ1–RQ5) across benchmark quantum programs spanning fundamental computational paradigms:
- Entanglement verification (Bell State, GHZ-3q)
- Quantum communication protocols (Teleportation-3q)
- Structured database search (Grover-2q)
- Phase estimation primitive (Quantum Fourier Transform QFT-3q)
- Variational quantum algorithms (QAOA MaxCut-3q)

---

## 2. Parameter Matrix

| Parameter | Configuration Values | Rationale |
|---|---|---|
| **Measurement Shots** | 1024 | Standard compromise between shot noise variance and evaluation speed. |
| **Noise Levels ($\epsilon$)** | 0.00 (Ideal), 0.01 (1%), 0.02 (2%), 0.05 (5%) | Covers near-term physical error rates observed on transmon QPUs. |
| **Noise Channels** | Depolarizing, Pauli bit/phase-flip, Readout error | Rigorous representation of physical environmental decoherence. |
| **Mutation Operators** | 8 standard operators ($O_{gom}, O_{wg}, O_{wq}, O_{pp}, O_{gos}, O_{mm}, O_{co}, O_{rg}$) | Representative taxonomy of quantum software programming mistakes. |
| **Localization Metrics** | Ochiai, Tarantula, DStar, Differential Gain | Quantitative comparison of spectrum-based localization algorithms. |
| **Repair Search Budget** | 25 candidates per task | Realistic heuristic search limits preventing combinatorial explosion. |

---

## 3. Data Flow & Provenance
1. **Raw Run Logging**: Every mutant execution is serialized to `experiments/outputs/raw_detection_runs.csv` with mutant metadata, pass/fail counts, and detected flags.
2. **Localization Records**: Gate suspicion rankings and ground-truth hit flags are logged to `experiments/outputs/raw_localization_runs.csv`.
3. **Repair Records**: Generated patches, test-adequacy, and validation statuses are logged to `experiments/outputs/raw_repair_runs.csv`.
4. **Summary Aggregation**: High-level statistical summaries answering each research question are compiled into `experiments/outputs/benchmark_summary.json`.
