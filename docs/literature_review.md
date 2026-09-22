# Literature Review: Quantum Software Engineering, Testing, and Repair

## 1. Overview & Research Field
Quantum Software Engineering (QSE) is an emerging discipline addressing the challenges of designing, verifying, testing, debugging, and maintaining quantum software. As quantum circuits scale beyond toy demonstrations toward fault-tolerant regimes, software faults in quantum algorithms, compilers, and transpilers pose substantial risks to computational validity.

Unlike classical software with deterministic state spaces, quantum programs exhibit:
1. Superposition and entanglement, precluding arbitrary cloning (No-Cloning Theorem).
2. Probabilistic measurement outcomes, rendering conventional binary assertions (`assert x == y`) insufficient without statistical thresholding.
3. Measurement collapse, destroying intermediate quantum states upon observation.
4. Physical hardware noise, which induces errors indistinguishable from low-magnitude software bugs.

---

## 2. Related Work & Existing Approaches

### 2.1 Quantum Program Testing & Mutation Analysis
- **Muskit & Quantum Mutation Testing**: Early work by Mendiluze et al. (2021) and Fortunato et al. introduced mutation testing to quantum circuits, defining basic mutation operators such as gate deletion and gate substitution.
- **Metamorphic Testing for Quantum Programs**: Studies by Asprion et al. and Honarvar et al. explored metamorphic relations (e.g., identity additions, basis changes, and input symmetries) to address the quantum test oracle problem where reference outputs are intractable.
- **Property-Based Testing**: Techniques verifying quantum assertions (Gharib et al., Huang & Martonosi) assert invariants (e.g., state norm conservation, subspace orthogonality) without full state tomography.

### 2.2 Fault Localization in Quantum Circuits
- **Spectrum-Based Fault Localization (SBFL)**: Classical SBFL formulas (Ochiai, Tarantula, DStar) correlate statement execution frequency with test pass/fail outcomes. Adapting SBFL to quantum circuits is non-trivial because all gates along an executed path are evaluated simultaneously in circuit execution; QubitGuard overcomes this by generating sub-circuit slices and parameterized test suites that isolate gate activation.
- **Quantum Slicing & Debugging**: Slicing techniques (Miranskyy et al.) attempt to isolate sub-circuits responsible for deviation in measurement distributions.

### 2.3 Automated Quantum Program Repair
- Traditional automated program repair (APR) techniques like GenProg and SemFix have not been directly translatable to quantum computing due to the continuous parameter space of rotation gates ($R_x, R_y, R_z$) and structural constraints of unitary matrices.
- Recent exploratory work uses genetic programming to synthesise replacement gates, but suffers from test-suite overfitting (where a patch passes a few noisy shot evaluations while failing true unitary equivalence).

---

## 3. Related Tools & Frameworks
| Tool | Primary Focus | Mutation Testing | SBFL | Automated Repair | Noise Simulation |
|---|---|---|---|---|---|
| **Muskit** | Mutation Analysis | Yes | No | No | Limited |
| **QSharp / Q# Testing** | Unit Testing | No | No | No | No |
| **QDiff / QuSAL** | Compiler Fuzzing | Limited | No | No | No |
| **Qiskit Experiments** | Hardware Calibration | No | No | No | Yes |
| **QubitGuard (This Work)** | **End-to-End QSE Platform** | **Yes (8 Operators)** | **Yes (Ochiai/Tarantula/DStar)** | **Yes (Heuristic/Genetic)** | **Yes (Realistic Aer Models)** |

---

## 4. Research Gaps & QubitGuard Positioning
1. **Lack of Integrated End-to-End Pipelines**: Existing tools isolate either mutation testing or compiler fuzzing; no unified platform bridges testing, spectrum-based localization, and automated repair.
2. **The Oracle & Noise Confounding Problem**: Classical SBFL fails under noisy quantum simulation because environmental decoherence mimics program bugs. QubitGuard introduces statistical noise-calibrated divergence metrics (TVD, Bhattacharyya, $\chi^2$) to decouple hardware error from algorithmic faults.
3. **Patch Overfitting**: QubitGuard enforces dual-tier patch validation (test-adequate vs holdout invariant validation), ensuring generated candidate patches restore true circuit semantics.
