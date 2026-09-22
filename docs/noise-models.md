# QubitGuard: Noise Models & Decoherence Simulation

## 1. Physical Noise in Quantum Hardware
Noisy Intermediate-Scale Quantum (NISQ) devices suffer from environmental decoherence, control signal noise, and state measurement errors. When conducting quantum software engineering research, testing pipelines must account for these noise sources without assuming idealized unitary evolution.

---

## 2. Supported Noise Models in QubitGuard

QubitGuard configures `qiskit_aer.noise.NoiseModel` through parameterized Kraus maps and Pauli channels:

### 2.1 Single- and Two-Qubit Depolarizing Channels
Depolarizing noise models isotropic decay towards the maximally mixed state:
$$\mathcal{E}_{dep}(\rho) = (1 - p)\rho + \frac{p}{d} I$$
where $d = 2^k$ is the Hilbert space dimension.
- Single-qubit error rate: $p_1 = \epsilon$ (applied to $H, X, Y, Z, S, T, R_x, R_y, R_z$).
- Two-qubit entangling error rate: $p_2 = \min(1.0, 5 \cdot \epsilon)$ (applied to $CX, CZ, \text{SWAP}$).

### 2.2 Pauli Stochastic Channels (Bit-Flip & Phase-Flip)
Simulates asymmetric noise processes:
$$\mathcal{E}_{Pauli}(\rho) = (1 - p_x - p_z)\rho + p_x X \rho X + p_z Z \rho Z$$
where $p_x = \epsilon / 2$ and $p_z = \epsilon / 2$.

### 2.3 Measurement Readout Error
Classical bit errors occurring during projective readout:
$$P(\text{measured } i \mid \text{prepared } j) = \begin{pmatrix} 1 - \eta & \eta \\ \eta & 1 - \eta \end{pmatrix}$$
where $\eta \in [0.01, 0.05]$ represents asymmetric or symmetric assignment error.

### 2.4 Composite NISQ Noise Model
Combines depolarizing channel, thermal relaxation ($T_1 = 50\mu s, T_2 = 70\mu s$), and readout assignment error.

---

## 3. Configuration & Noise Calibration
Noise can be supplied programmatically:
```python
from qubitguard.noise.models import NoiseConfig, NoiseType

# 2% depolarizing error
config = NoiseConfig(
    noise_type=NoiseType.DEPOLARIZING,
    error_rate=0.02,
    readout_error_rate=0.03
)
```
In testing assertions, detection thresholds automatically expand from $\tau_{ideal} = 0.10$ to $\tau_{noisy} = 0.20$ to avoid false alarms induced purely by decoherence.
