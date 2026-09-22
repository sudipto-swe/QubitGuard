"""QubitGuard - Core Circuit Abstraction & Metadata Tracking."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import copy
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction, Qubit, Clbit, Gate


@dataclass
class GateMetadata:
    """Metadata for an individual quantum gate in a circuit."""
    index: int
    gate_name: str
    qubits: List[int]
    clbits: List[int] = field(default_factory=list)
    params: List[float] = field(default_factory=list)
    is_controlled: bool = False
    is_measurement: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "gate_name": self.gate_name,
            "qubits": self.qubits,
            "clbits": self.clbits,
            "params": [float(p) for p in self.params],
            "is_controlled": self.is_controlled,
            "is_measurement": self.is_measurement,
        }


@dataclass
class CircuitProgram:
    """High-level abstraction of a quantum circuit with execution and AST metadata."""
    circuit: QuantumCircuit
    name: str = "unnamed_circuit"
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_qubits(self) -> int:
        return self.circuit.num_qubits

    @property
    def num_clbits(self) -> int:
        return self.circuit.num_clbits

    @property
    def depth(self) -> int:
        return self.circuit.depth()

    @property
    def size(self) -> int:
        """Total number of operations in circuit."""
        return len(self.circuit.data)

    def clone(self) -> CircuitProgram:
        """Deep clone of this CircuitProgram."""
        return CircuitProgram(
            circuit=copy.deepcopy(self.circuit),
            name=self.name,
            description=self.description,
            properties=copy.deepcopy(self.properties),
        )

    def get_gate_metadata_list(self) -> List[GateMetadata]:
        """Extract indexed list of gates with full metadata."""
        meta_list = []
        for idx, instruction in enumerate(self.circuit.data):
            op = instruction.operation
            q_indices = [self.circuit.find_bit(q).index for q in instruction.qubits]
            c_indices = [self.circuit.find_bit(c).index for c in instruction.clbits]
            
            is_meas = op.name.lower() == "measure"
            is_ctrl = getattr(op, "num_ctrl_qubits", 0) > 0 or op.name.lower() in ("cx", "cz", "ccx", "swap", "cp", "crx", "cry", "crz")

            params_float = []
            for p in op.params:
                try:
                    params_float.append(float(p))
                except (ValueError, TypeError):
                    pass

            meta = GateMetadata(
                index=idx,
                gate_name=op.name,
                qubits=q_indices,
                clbits=c_indices,
                params=params_float,
                is_controlled=is_ctrl,
                is_measurement=is_meas,
            )
            meta_list.append(meta)
        return meta_list

    def to_qasm(self) -> str:
        """Export circuit to OpenQASM 2/3 string."""
        from qiskit import qasm2
        try:
            return qasm2.dumps(self.circuit)
        except Exception:
            return str(self.circuit)
