# Research Questions (RQs) in QubitGuard

QubitGuard evaluates quantum software testing, spectrum-based fault localization (SBFL), and automated program repair (APR) through five empirical research questions formulated for noisy intermediate-scale quantum (NISQ) software engineering.

---

### RQ1: Fault Detection Efficacy
**How effectively can multi-strategy testing (metamorphic relations and property invariants) detect injected quantum program faults across standard benchmark families?**
- *Hypothesis*: Combining unitary inverse symmetries, qubit permutation equivariance, and invariant parity checks will expose over 85% of semantic faults under ideal simulation, outperforming naive output sampling.
- *Metric*: Mutation Score ($MS = D / M$), True Positive Rate, False Positive Rate under statistical significance ($\alpha = 0.05$).

---

### RQ2: Fault Class Vulnerability & Hardness
**Which quantum gate fault classes are most difficult to detect and localize?**
- *Hypothesis*: Small phase parameter perturbations ($\delta \theta \in [0.05\pi, 0.15\pi]$) and redundant identity gates produce output probability deviations within shot noise bounds, making them significantly harder to detect than structural gate omissions or wrong-target errors.
- *Metric*: Detection rate stratified by fault class (Gate Omission, Wrong Gate, Wrong Qubit, Parameter Perturbation, Gate Order, Measurement Mutation, Controlled Operation, Redundant Gate).

---

### RQ3: Noise Robustness and Masking
**How does physical execution noise (depolarizing, bit/phase flip, and readout errors) impact fault detection sensitivity and false alarm rates?**
- *Hypothesis*: As environmental error rates increase ($\epsilon \ge 0.03$), stochastic noise masks true semantic mutations while inflating false positive rates on fault-free circuits unless statistical divergence thresholds are noise-calibrated.
- *Metric*: Precision, Recall, F1-Score, Total Variation Distance (TVD) across noise levels $\epsilon \in \{0.00, 0.01, 0.02, 0.05\}$.

---

### RQ4: Quantum Spectrum-Based Fault Localization (Q-SBFL)
**How accurately can spectrum-based localization formulas (Ochiai, Tarantula, DStar) isolate the exact mutated gate operations in quantum circuits?**
- *Hypothesis*: Ochiai suspicion ranking applied to gate-level execution spectra will localize faulty gates within Top-1 in $\ge 50\%$ and Top-3 in $\ge 75\%$ of detectable cases.
- *Metric*: Top-$k$ Accuracy ($k \in \{1, 3, 5\}$), Mean First Rank (MFR), and Exam Score (percentage of statements/gates inspected before locating the fault).

---

### RQ5: Automated Quantum Program Repair (Q-APR)
**To what extent can heuristic and genetic patch search restore intended quantum program semantics without overfitting to test suites?**
- *Hypothesis*: Utilizing localized suspicion rankings to guide patch search enables successful generation of validated repairs for single-fault gate bugs within bounded search budgets (< 50 evaluations).
- *Metric*: Test-Adequate Repair Rate (passes test suite), Validated Repair Rate (restores state fidelity $F \ge 0.99$ on holdout inputs), and Search Time (seconds).
