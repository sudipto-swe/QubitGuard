# Changelog

All notable changes to **QubitGuard** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-22
### Added
- **Core Circuit Engine**: Circuit program wrapper with metadata extraction, depth analysis, and gate indexing.
- **Quantum Benchmarks**: Bell State, GHZ-3q/4q, Teleportation-3q, Grover Search (2q), QFT-3q, and QAOA MaxCut ansatz (3q).
- **Fault Injection Engine**: 8 mutation operators (`GATE_OMISSION`, `WRONG_GATE`, `WRONG_QUBIT`, `PARAMETER_PERTURBATION`, `GATE_ORDER_SWAP`, `MEASUREMENT_MUTATION`, `CONTROLLED_OPERATION`, `REDUNDANT_GATE`).
- **Noise Simulation**: Qiskit Aer noise models covering depolarizing, bit/phase-flip, and measurement readout errors.
- **Testing Engine**: Metamorphic testing (inverse identity, qubit permutation equivariance) and property-based invariant checks.
- **Statistical Detection**: Total Variation Distance (TVD), Jensen-Shannon Divergence, and $\chi^2$ hypothesis testing.
- **Quantum SBFL**: Gate-level suspicion ranking via Ochiai, Tarantula, DStar, and differential sub-circuit slicing.
- **Automated Repair (Q-APR)**: Heuristic mutation search generating test-adequate and validated patches.
- **Interactive UI**: Streamlit research dashboard with 6 specialized modules.
- **Empirical Evaluation**: Benchmark runners, statistical summary generators, and Plotly visualization scripts.
