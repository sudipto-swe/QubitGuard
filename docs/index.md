---
layout: default
title: QubitGuard - Quantum Software Engineering Platform
---

# QubitGuard
### Automated Testing, Fault Localization, and Program Repair for Quantum Circuits

**Author**: Sudipto Biswas (Lead Research Engineer)  
**GitHub Repository**: [https://github.com/sudipto-swe/QubitGuard](https://github.com/sudipto-swe/QubitGuard)  
**CI Build Status**: [![CI](https://github.com/sudipto-swe/QubitGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/sudipto-swe/QubitGuard/actions/workflows/ci.yml)

---

## 🚀 Live Demo & Interactive Application
The QubitGuard interactive research dashboard is ready to launch:
- **Streamlit Community Cloud Demo**: [https://qubitguard.streamlit.app/](https://qubitguard.streamlit.app/) *(or deploy directly via [share.streamlit.io](https://share.streamlit.io))*
- **Deployment Guide**: [Production & Cloud Deployment Guide](deployment.md)

---

## Overview
QubitGuard is an open-source, research-oriented Quantum Software Engineering (QSE) framework that unites:
- **Reproducible Fault Injection**: 8 mutation operators across 6 benchmark circuit families.
- **Multi-Strategy Testing**: Metamorphic relations (Unitary Inverse $U U^\dagger = I$, Qubit Permutation Equivariance) and statistical hypothesis testing (Total Variation Distance, Pearson's $\chi^2$).
- **Noisy Aer Simulation**: Configurable Kraus depolarizing, Pauli bit/phase-flip, and measurement readout channels.
- **Quantum Spectrum-Based Fault Localization (Q-SBFL)**: Ochiai, Tarantula, and DStar ranking with differential sub-circuit slicing.
- **Automated Program Repair (Q-APR)**: Search-based synthesis of test-adequate and validated patches.

---

## Documentation Hierarchy
- [Research Report](research_report.md) — Complete empirical findings across 200 circuit executions.
- [Literature Review](literature_review.md) — Comprehensive survey of quantum software testing and repair.
- [Research Questions](research_questions.md) — Formal formulation of RQ1–RQ5.
- [Architecture & Design](architecture.md) — Subsystem pipeline and class hierarchies.
- [Fault Taxonomy](fault-models.md) — Mathematical definition of 8 quantum mutation operators.
- [Testing Methodology](testing-methodology.md) — Metamorphic relations and statistical divergence assertions.
- [Noise Models](noise-models.md) — Physical noise channels in Qiskit Aer.
- [Fault Localization](localization.md) — Quantum SBFL spectrum formulas and differential slicing.
- [Automated Repair](repair.md) — Patch candidate search and validation criteria.
- [Experimental Protocol](experiments.md) — Parameter matrices and data provenance.
- [Reproducibility Guide](reproducibility.md) — Step-by-step reproduction instructions.
- [Threats to Validity & Limitations](limitations.md) — Known constraints and hardware validity threats.

---

## Empirical Benchmark Summary (RQ1–RQ5)

| Metric | Result |
|---|---|
| **Overall Mutation Score (Recall)** | **73.30%** (129 / 176 detected) |
| **Precision** | **98.47%** |
| **F1-Score** | **0.8404** |
| **Hardest Fault Class (RQ2)** | Parameter Perturbation (50.0%) |
| **Easiest Fault Class (RQ2)** | Controlled Operation (87.5%) |
| **Q-SBFL Top-3 Accuracy (RQ4)** | **69.70%** |
| **Q-SBFL Mean Exam Score (RQ4)** | **31.79%** |
| **Validated Repair Success Rate (RQ5)** | **50.00%** (avg 16.1s search) |

*Full raw datasets available in [`experiments/outputs/`](https://github.com/sudipto-swe/QubitGuard/tree/main/experiments/outputs).*
