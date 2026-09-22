# QubitGuard: Empirical Research Report

**Author**: Sudipto Biswas (Lead Research Engineer)  
**Artifact Repository**: [QubitGuard GitHub Archive](https://github.com/sudiptob1/QubitGuard)  
**Evaluation Date**: September 2026  
**Execution Environment**: Linux (Debian/Ubuntu, Python 3.12, Qiskit 2.5.2, Qiskit Aer 0.17.2)

---

## Abstract
Testing and debugging quantum programs on Noisy Intermediate-Scale Quantum (NISQ) platforms is severely constrained by the quantum oracle problem, wavefunction collapse upon measurement, and physical decoherence that confounds software faults with environmental noise. This report presents the empirical findings of **QubitGuard**, a comprehensive quantum software engineering platform providing reproducible fault injection (8 mutation operators), metamorphic and property-based test suites, statistical divergence fault detection, spectrum-based fault localization (Q-SBFL), and automated program repair (Q-APR). In an empirical evaluation across 200 circuit executions over 6 standard benchmark families (Bell, GHZ, Teleportation, Grover, QFT, QAOA) under depolarizing noise levels $\epsilon \in \{0.00, 0.01, 0.02, 0.05\}$, QubitGuard achieved a 98.5% detection precision and 0.840 F1-score, localized faulty operations within the top-3 suspicious gates in 69.7% of cases, and synthesized validated semantic patches for 50% of single-fault repair tasks within an average of 16.1 seconds.

---

## 1. Research Questions & Empirical Answers

### RQ1: Fault Detection Efficacy
> *How effectively can multi-strategy testing (metamorphic relations and property invariants) detect injected quantum program faults across standard benchmark families?*

- **Total Mutants Evaluated**: 176 faulty programs (+ 24 clean reference executions to evaluate False Positives).
- **Mutants Detected**: 129
- **Overall Mutation Score (Recall)**: **73.30%**
- **Precision**: **98.47%**
- **F1-Score**: **0.8404**
- **Finding**: Multi-strategy testing achieves outstanding precision (98.5%), producing virtually zero false alarms on clean programs under low-to-moderate noise while exposing almost three-quarters of all injected gate defects.

---

### RQ2: Fault Class Vulnerability & Hardness
> *Which quantum gate fault classes are most difficult to detect and localize?*

| Fault Class | Total Injected | Detection Rate (Mutation Score) | Empirical Hardness |
|---|---|---|---|
| **CONTROLLED_OPERATION** | 24 | **87.50%** | Easiest to detect |
| **WRONG_GATE** | 24 | **83.33%** | Low |
| **WRONG_QUBIT** | 24 | **83.33%** | Low |
| **GATE_OMISSION** | 24 | **75.00%** | Moderate |
| **GATE_ORDER_SWAP** | 24 | **66.67%** | Moderate-High |
| **MEASUREMENT_MUTATION** | 24 | **66.67%** | Moderate-High |
| **REDUNDANT_GATE** | 24 | **58.33%** | High |
| **PARAMETER_PERTURBATION** | 8 | **50.00%** | **Hardest to detect** |

- **Finding**: **Parameter perturbations** ($R_x, R_z$ small rotation drifts) and **redundant gates** are the hardest fault classes to detect (50.0% and 58.3% detection respectively), as their induced probability shifts often lie close to finite sampling shot noise boundaries. Structural control conversions and wrong-gate substitutions cause catastrophic distribution shifts and are detected with high sensitivity (>83%).

---

### RQ3: Noise Robustness and Masking
> *How does physical execution noise affect fault-detection sensitivity and false alarm rates?*

| Depolarizing Error ($\epsilon$) | Mutants | Detected | Mutation Score | Precision | Recall | F1-Score |
|---|---|---|---|---|---|---|
| **0.00 (Ideal)** | 44 | 33 | 75.00% | 1.0000 | 0.7500 | **0.8571** |
| **0.01 (1%)** | 44 | 33 | 75.00% | 1.0000 | 0.7500 | **0.8571** |
| **0.02 (2%)** | 44 | 32 | 72.73% | 0.9697 | 0.7273 | **0.8312** |
| **0.05 (5%)** | 44 | 31 | 70.45% | 0.9688 | 0.7045 | **0.8158** |

- **Finding**: As physical error rates increase from 0% to 5%, the framework's F1-score degrades gracefully from 0.857 to 0.816. The noise-calibrated divergence thresholds successfully maintain precision above 96.8% even under heavy depolarizing noise ($\epsilon = 0.05$).

---

### RQ4: Quantum Spectrum-Based Fault Localization (Q-SBFL)
> *How accurately can spectrum-based localization formulas isolate the exact mutated gate operations?*

- **Total Evaluated Localization Tasks**: 66 detectable mutants across ideal and low noise.
- **Top-1 Accuracy**: **43.94%** (The actual faulty gate was ranked #1 suspicious in 44% of cases).
- **Top-3 Accuracy**: **69.70%** (The actual faulty gate was within the Top-3 suspicious gates in ~70% of cases).
- **Mean First Rank (MFR)**: **3.42**
- **Mean Exam Score**: **31.79%** (A debugger need only inspect less than 32% of total circuit gates to locate the bug).
- **Finding**: Blending sub-circuit differential TVD gain with Ochiai suspicion spectra effectively isolates the source of quantum distribution collapse in compact circuits.

---

### RQ5: Automated Quantum Program Repair (Q-APR)
> *To what extent can heuristic patch search restore intended quantum program semantics without test-suite overfitting?*

- **Total Repair Sessions Evaluated**: 6 standard single-fault tasks (Bell, GHZ, Grover under gate omission and wrong gate).
- **Validated Repair Rate**: **50.00%** (3 out of 6 tasks produced patches validated on both test suites and holdout state fidelity).
- **Average Search Time**: **16.09 seconds** per repair task.
- **Average Candidate Evaluations**: **11.7 evaluations** per repair task.
- **Finding**: Localized search guided by SBFL rankings enables rapid synthesis of validated patches within an average of 12 evaluations, avoiding combinatorial search explosion.

---

## 2. Scientific Threats to Validity & Limitations
1. **Simulator Modeling**: Evaluations use Qiskit Aer density matrix simulation with Kraus depolarizing maps. Physical QPU phenomena such as non-Markovian phase drift and spectator crosstalk were not modeled.
2. **Circuit Scale**: Benchmark circuits range from 2 to 4 qubits (depth $\le 25$). Scaling to 50+ qubit circuits will require hierarchical sub-circuit decomposition.
3. **Multi-Fault Co-occurrence**: The current APR engine assumes single-fault mutations; multi-fault interactions expand the search space exponentially.
