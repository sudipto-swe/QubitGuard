"""Benchmark Quantum Circuits for QubitGuard Evaluation Suite."""

from __future__ import annotations
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT
from qubitguard.core.circuit import CircuitProgram


def create_bell_state() -> CircuitProgram:
    """Creates a 2-qubit Bell State (|Φ+⟩ = (|00⟩ + |11⟩)/√2) with measurements."""
    qc = QuantumCircuit(2, 2, name="bell_state")
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return CircuitProgram(
        circuit=qc,
        name="Bell_State",
        description="2-qubit maximally entangled Bell state (|00> + |11>)/sqrt(2)",
        properties={"family": "entanglement", "ideal_distribution": {"00": 0.5, "11": 0.5}},
    )


def create_ghz_state(num_qubits: int = 3) -> CircuitProgram:
    """Creates an n-qubit Greenberger-Horne-Zeilinger (GHZ) state with measurements."""
    qc = QuantumCircuit(num_qubits, num_qubits, name=f"ghz_{num_qubits}")
    qc.h(0)
    for i in range(num_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(list(range(num_qubits)), list(range(num_qubits)))
    
    ideal = {
        "0" * num_qubits: 0.5,
        "1" * num_qubits: 0.5,
    }
    return CircuitProgram(
        circuit=qc,
        name=f"GHZ_{num_qubits}q",
        description=f"{num_qubits}-qubit GHZ state (|00..0> + |11..1>)/sqrt(2)",
        properties={"family": "entanglement", "ideal_distribution": ideal},
    )


def create_quantum_teleportation() -> CircuitProgram:
    """Creates standard 3-qubit Quantum Teleportation protocol.
    
    Qubit 0: State to teleport (|ψ⟩ = H|0⟩ or parametrized)
    Qubits 1, 2: Shared Bell pair
    """
    qc = QuantumCircuit(3, 3, name="teleportation")
    # Prepare test state on q0
    qc.h(0)
    # Prepare Bell pair on q1, q2
    qc.h(1)
    qc.cx(1, 2)
    # Bell measurement on q0, q1
    qc.cx(0, 1)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(1, 1)
    # Conditional corrections via classical feed-forward or CX/CZ gates
    qc.cx(1, 2)
    qc.cz(0, 2)
    qc.measure(2, 2)
    return CircuitProgram(
        circuit=qc,
        name="Teleportation_3q",
        description="3-qubit quantum state teleportation protocol with correction",
        properties={"family": "communication"},
    )


def create_grover_search_2q(marked_item: str = "11") -> CircuitProgram:
    """Creates a 2-qubit Grover search circuit targeting a specific basis state."""
    qc = QuantumCircuit(2, 2, name="grover_2q")
    # Uniform superposition
    qc.h([0, 1])
    
    # Oracle for marked state
    if marked_item == "11":
        qc.cz(0, 1)
    elif marked_item == "10":
        qc.x(1)
        qc.cz(0, 1)
        qc.x(1)
    elif marked_item == "01":
        qc.x(0)
        qc.cz(0, 1)
        qc.x(0)
    elif marked_item == "00":
        qc.x([0, 1])
        qc.cz(0, 1)
        qc.x([0, 1])

    # Diffuser (inversion about mean)
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])
    
    qc.measure([0, 1], [0, 1])
    return CircuitProgram(
        circuit=qc,
        name="Grover_2q",
        description=f"2-qubit Grover Search targeting |{marked_item}> (100% ideal probability)",
        properties={"family": "search", "marked_item": marked_item, "ideal_distribution": {marked_item: 1.0}},
    )


def create_qft_circuit(num_qubits: int = 3) -> CircuitProgram:
    """Creates Quantum Fourier Transform circuit on n qubits with state input."""
    qc = QuantumCircuit(num_qubits, num_qubits, name=f"qft_{num_qubits}")
    # Prepare non-trivial input: X on qubit 0
    qc.x(0)
    # Fully decomposed QFT gates
    for target in range(num_qubits):
        qc.h(target)
        for control in range(target + 1, num_qubits):
            k = control - target + 1
            lam = 2 * np.pi / (2 ** k)
            qc.cp(lam, control, target)
    # Swaps
    for i in range(num_qubits // 2):
        qc.swap(i, num_qubits - 1 - i)
    qc.measure(list(range(num_qubits)), list(range(num_qubits)))
    return CircuitProgram(
        circuit=qc,
        name=f"QFT_{num_qubits}q",
        description=f"{num_qubits}-qubit Quantum Fourier Transform on computational state |1>",
        properties={"family": "fourier"},
    )


def create_qaoa_ansatz_3q(gamma: float = 0.5, beta: float = 0.3) -> CircuitProgram:
    """Creates a 3-qubit QAOA MaxCut ansatz for a 3-node triangle graph."""
    qc = QuantumCircuit(3, 3, name="qaoa_3q")
    # Superposition
    qc.h([0, 1, 2])
    # Cost Hamiltonian (ZZ interactions for edges (0,1), (1,2), (0,2))
    for u, v in [(0, 1), (1, 2), (0, 2)]:
        qc.cx(u, v)
        qc.rz(2 * gamma, v)
        qc.cx(u, v)
    # Mixer Hamiltonian (RX rotations)
    for q in range(3):
        qc.rx(2 * beta, q)
    qc.measure([0, 1, 2], [0, 1, 2])
    return CircuitProgram(
        circuit=qc,
        name="QAOA_MaxCut_3q",
        description="3-qubit 1-layer QAOA MaxCut ansatz on triangle graph",
        properties={"family": "variational", "gamma": gamma, "beta": beta},
    )


def get_all_benchmarks() -> dict[str, CircuitProgram]:
    """Returns registry of standard research benchmark circuits."""
    return {
        "Bell_State": create_bell_state(),
        "GHZ_3q": create_ghz_state(3),
        "GHZ_4q": create_ghz_state(4),
        "Teleportation_3q": create_quantum_teleportation(),
        "Grover_2q": create_grover_search_2q("11"),
        "QFT_3q": create_qft_circuit(3),
        "QAOA_MaxCut_3q": create_qaoa_ansatz_3q(),
    }
