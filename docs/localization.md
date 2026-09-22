# QubitGuard: Quantum Spectrum-Based Fault Localization (Q-SBFL)

## 1. Adapting SBFL to Quantum Programs
Classical Spectrum-Based Fault Localization (SBFL) calculates the suspiciousness of software statements by correlating their execution profiles across passing and failing test cases.

In classical code:
- Traces indicate which statements executed along a branch path.
- Statements that execute frequently in failing runs and rarely in passing runs receive high suspicion.

In quantum circuits:
- **Unitary static DAGs**: All gates in a circuit execute concurrently on the quantum state vector without classical conditional branching during execution.
- **Differential Sub-Circuit Slicing**: To extract meaningful spectra, QubitGuard generates sub-circuit gate slices $C \setminus \{g_i\}$ and assesses the divergence shift against reference behavior.

---

## 2. Spectrum Formulations in QubitGuard

Let:
- $n_{cf}$: Number of failing test evaluations where gate $g_i$ was actively contributing to error divergence.
- $n_{uf}$: Number of failing test evaluations where gate $g_i$ did not contribute.
- $n_{cs}$: Number of passing test evaluations where gate $g_i$ was covered.
- $n_{us}$: Number of passing test evaluations where gate $g_i$ was omitted/uncovered.

### 2.1 Ochiai Metric
$$S_{Ochiai}(g_i) = \frac{n_{cf}}{\sqrt{(n_{cf} + n_{uf})(n_{cf} + n_{cs})}}$$

### 2.2 Tarantula Metric
$$S_{Tarantula}(g_i) = \frac{\frac{n_{cf}}{n_{cf} + n_{uf}}}{\frac{n_{cf}}{n_{cf} + n_{uf}} + \frac{n_{cs}}{n_{cs} + n_{us}}}$$

### 2.3 DStar ($D^*$) Metric ($\sigma = 2$)
$$S_{D^*}(g_i) = \frac{n_{cf}^2}{n_{uf} + n_{cs}}$$

---

## 3. Blended Composite Suspiciousness
To boost localization fidelity on quantum circuits, QubitGuard synthesizes a composite score combining the Ochiai coefficient with the differential TVD gain $\Delta_{TVD}(g_i)$:
$$\text{Suspiciousness}(g_i) = 0.60 \cdot \min(1.0, 2.5 \cdot \Delta_{TVD}(g_i)) + 0.40 \cdot S_{Ochiai}(g_i)$$
This formulation rewards gates whose omission maximally restores output probability distributions toward expected invariants.
