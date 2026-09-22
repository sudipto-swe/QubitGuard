# Threats to Validity & System Limitations

As a scientific research artifact, QubitGuard acknowledges several fundamental threats to validity and current technical limitations.

---

## 1. Threats to Validity

### 1.1 Internal Validity
- **Simulator vs. Physical Transmon Drift**: All evaluations in this study were executed using Qiskit Aer's density matrix and statevector simulators. While Aer accurately models Kraus operators and Pauli depolarizing channels, it does not capture time-varying non-Markovian 1/f flux noise, spectator qubit crosstalk, or dynamic calibration drift observed on physical QPUs (such as IBM Quantum Eagle or Heron processors).
- **Statistical Significance & Finite Shots**: Quantum executions use finite sampling shots ($N=1024$ or $2048$). Low-probability error events may experience Poisson shot noise that fluctuates around statistical divergence thresholds ($\alpha = 0.05$).

### 1.2 Construct Validity
- **Oracle Approximations in Metamorphic Testing**: Metamorphic relations (such as $U \cdot U^\dagger \to |0\dots 0\rangle$) assume the inverse $U^\dagger$ can be constructed without introducing correlated structural cancellation bugs that mask faulty operations.
- **Spectrum Granularity in SBFL**: In classical software, branching statements yield sparse path coverage matrices. Quantum circuits execute in static directed acyclic graphs (DAGs) without runtime conditional branches, requiring sub-circuit differential slicing to synthesize virtual execution paths.

### 1.3 External Validity
- **Benchmark Scale**: Circuits in the evaluation suite range between 2 and 4 qubits with gate depths up to 25 operations. Although representative of core quantum primitives (entanglement, teleportation, Fourier transforms, variational ansatzes), results may not generalize directly to large-scale quantum error-corrected circuits (e.g., surface code lattices exceeding 1,000 qubits).

---

## 2. Technical Limitations

1. **Multi-Fault Co-occurrence**: The current automated repair and localization engine assumes single-fault or low-order localized defects. Cascading, interacting multi-gate faults expand the APR search space exponentially ($\mathcal{O}(|G|^k)$), requiring beam search or reinforcement learning extensions.
2. **Arbitrary Continuous Unitaries**: Rotational angle repairs in $R_x(\theta), R_y(\theta), R_z(\theta)$ are currently discretized into discrete angle increments ($\delta \in \{\pm 0.1\pi, \pm 0.25\pi, \pm 0.5\pi\}$). Gradient-based parameter optimization (such as gradient descent or Adam via parameter-shift rules) would be required for continuous variational tuning.
3. **Physical Hardware Connectivity Constraints**: The framework assumes an all-to-all qubit coupling graph. Execution on physical hardware topologies (heavy-hex or linear architectures) requires transpilation routing via SWAP networks, which may introduce additional transpile-time faults.
