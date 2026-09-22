# QubitGuard: Testing Methodology & Oracles

## 1. The Quantum Test Oracle Problem
Classical assertions rely on deterministic return values:
$$\text{assert } f(x) == y_{expected}$$
In quantum software, program execution yields a probability distribution over eigenvalues:
$$|\psi\rangle = \sum_{x \in \{0, 1\}^n} \alpha_x |x\rangle, \quad P(x) = |\alpha_x|^2$$

Directly checking output distributions is hindered by:
1. **Exponential state space**: $2^n$ basis probabilities require exponential measurement shots.
2. **Shot noise**: Finite measurement shots $N$ introduce Poisson fluctuations $\sim \mathcal{O}(1/\sqrt{N})$.
3. **Decoherence**: Physical hardware noise shifts output distributions even for semantically correct programs.

---

## 2. Metamorphic Testing Strategies

QubitGuard implements Metamorphic Testing (MT) to circumvent the lack of explicit oracles.

### 2.1 MR1: Inverse Unitary Relation ($U \cdot U^\dagger = I$)
- **Concept**: Any non-measurement quantum routine $U$ represents a unitary operation ($U U^\dagger = I$).
- **Test Transformation**: For circuit $U$, QubitGuard constructs:
  $$\mathcal{T}_{inv} = U \circ U^\dagger \circ \mathcal{M}$$
- **Oracle Assertion**: Executing $\mathcal{T}_{inv}$ on $|0\rangle^{\otimes n}$ must yield the ground state $|0\dots 0\rangle$ with probability $P(|0\dots 0\rangle) \ge 1 - \tau_{noise}$.
- **Noise Tolerance**: Under ideal simulation $\tau_{noise} = 0.10$; under depolarizing noise $\tau_{noise} = 0.30$.

### 2.2 MR2: Qubit Permutation Equivariance
- **Concept**: Swapping symmetric input qubits $\pi: q_i \leftrightarrow q_j$ induces a corresponding permutation on output bitstring measurements:
  $$P_{\pi(C)}(\pi(x)) = P_C(x)$$
- **Oracle Assertion**: The Total Variation Distance between mapped probability vectors must satisfy:
  $$\text{TVD}(P_C, P_{\pi(C)}) \le \delta_{threshold}$$

---

## 3. Property-Based Testing Invariants

Where domain-specific properties exist, QubitGuard evaluates structural quantum invariants:
- **Entanglement Parity Conservation**: In Bell and GHZ circuits, measurement outcomes must exhibit even parity (subspace support confined to $|00\dots 0\rangle$ and $|11\dots 1\rangle$).
- **Amplitude Amplification Bounds**: In Grover search algorithms, the marked element must observe probability concentration $P(x^*) \ge 0.50$ regardless of noise level up to $\epsilon \le 0.05$.

---

## 4. Statistical Divergence Hypothesis Testing
To distinguish physical shot/environmental noise from real software bugs, QubitGuard computes:
1. **Total Variation Distance (TVD)**:
   $$\text{TVD}(P, Q) = \frac{1}{2} \sum_{x} |P(x) - Q(x)|$$
2. **Pearson's Chi-Square ($\chi^2$) Goodness-of-Fit**:
   $$\chi^2 = \sum_{x} \frac{(O_x - E_x)^2}{E_x}, \quad p\text{-value} = 1 - F_{\chi^2}(\chi^2, \text{dof})$$
An assertion fails if $\text{TVD} > \tau$ or ($p < 0.05$ with non-negligible effect size).
