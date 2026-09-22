"""QubitGuard - Reproducible Quantum Fault Injection Engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
import copy
import random
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction, Gate
from qiskit.circuit.library import (
    XGate, YGate, ZGate, HGate, SGate, TGate,
    CXGate, CZGate, SwapGate, RXGate, RYGate, RZGate
)
from qubitguard.core.circuit import CircuitProgram, GateMetadata


class FaultType(str, Enum):
    GATE_OMISSION = "GATE_OMISSION"
    WRONG_GATE = "WRONG_GATE"
    WRONG_QUBIT = "WRONG_QUBIT"
    PARAMETER_PERTURBATION = "PARAMETER_PERTURBATION"
    GATE_ORDER_SWAP = "GATE_ORDER_SWAP"
    MEASUREMENT_MUTATION = "MEASUREMENT_MUTATION"
    CONTROLLED_OPERATION = "CONTROLLED_OPERATION"
    REDUNDANT_GATE = "REDUNDANT_GATE"


@dataclass
class MutationRecord:
    """Record detailing an injected fault for exact provenance and reproducibility."""
    mutation_id: str
    fault_type: FaultType
    target_index: int
    original_op_name: str
    mutated_op_name: str
    affected_qubits: List[int]
    parameters: Dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "fault_type": self.fault_type.value,
            "target_index": self.target_index,
            "original_op_name": self.original_op_name,
            "mutated_op_name": self.mutated_op_name,
            "affected_qubits": self.affected_qubits,
            "parameters": self.parameters,
            "seed": self.seed,
            "description": self.description,
        }


class FaultInjector:
    """Quantum fault injection engine supporting 8 standardized mutation operators."""

    SINGLE_QUBIT_GATES = [HGate(), XGate(), YGate(), ZGate(), SGate(), TGate()]
    TWO_QUBIT_GATES = [CXGate(), CZGate(), SwapGate()]

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

    def _generate_mutation_id(self, fault_type: FaultType, index: int) -> str:
        s_part = f"_s{self.seed}" if self.seed is not None else ""
        rnd = self.rng.randint(1000, 9999)
        return f"MUT_{fault_type.value[:3]}_idx{index}_{rnd}{s_part}"

    def get_injectable_indices(self, program: CircuitProgram, fault_type: FaultType) -> List[int]:
        """Returns valid instruction indices suitable for a given fault type."""
        data = program.circuit.data
        indices = []
        for idx, inst in enumerate(data):
            op = inst.operation
            is_meas = op.name.lower() == "measure"

            if fault_type == FaultType.MEASUREMENT_MUTATION:
                if is_meas:
                    indices.append(idx)
            elif is_meas:
                continue  # Standard gate faults don't modify measurements
            elif fault_type == FaultType.GATE_OMISSION:
                indices.append(idx)
            elif fault_type == FaultType.WRONG_GATE:
                indices.append(idx)
            elif fault_type == FaultType.WRONG_QUBIT:
                if len(inst.qubits) >= 1 and program.num_qubits > len(inst.qubits):
                    indices.append(idx)
            elif fault_type == FaultType.PARAMETER_PERTURBATION:
                if len(op.params) > 0:
                    indices.append(idx)
            elif fault_type == FaultType.GATE_ORDER_SWAP:
                if idx < len(data) - 1 and data[idx + 1].operation.name.lower() != "measure":
                    indices.append(idx)
            elif fault_type == FaultType.CONTROLLED_OPERATION:
                if len(inst.qubits) == 1 and program.num_qubits >= 2:
                    indices.append(idx)
            elif fault_type == FaultType.REDUNDANT_GATE:
                indices.append(idx)
        return indices

    def inject_fault(
        self,
        program: CircuitProgram,
        fault_type: FaultType,
        target_index: Optional[int] = None,
        **kwargs
    ) -> Tuple[CircuitProgram, MutationRecord]:
        """Injects a specific fault into the circuit and returns mutated program + audit record."""
        valid_indices = self.get_injectable_indices(program, fault_type)
        if not valid_indices:
            raise ValueError(f"No suitable operations in circuit '{program.name}' for {fault_type.value}")

        if target_index is None:
            target_index = self.rng.choice(valid_indices)
        elif target_index not in valid_indices:
            raise ValueError(f"Index {target_index} not valid for {fault_type.value}. Valid: {valid_indices}")

        mutated_qc = copy.deepcopy(program.circuit)
        data = list(mutated_qc.data)
        inst = data[target_index]
        orig_name = inst.operation.name
        q_indices = [mutated_qc.find_bit(q).index for q in inst.qubits]
        mid = self._generate_mutation_id(fault_type, target_index)

        # 1. Gate Omission
        if fault_type == FaultType.GATE_OMISSION:
            data.pop(target_index)
            desc = f"Omitted gate '{orig_name}' at index {target_index} on qubits {q_indices}"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name="NONE (DELETED)",
                affected_qubits=q_indices, seed=self.seed, description=desc
            )

        # 2. Wrong Gate
        elif fault_type == FaultType.WRONG_GATE:
            if len(inst.qubits) == 1:
                cand = [g for g in self.SINGLE_QUBIT_GATES if g.name.lower() != orig_name.lower()]
                replacement = copy.deepcopy(self.rng.choice(cand))
            else:
                cand = [g for g in self.TWO_QUBIT_GATES if g.name.lower() != orig_name.lower()]
                replacement = copy.deepcopy(self.rng.choice(cand) if cand else CXGate())
            data[target_index] = CircuitInstruction(replacement, inst.qubits, inst.clbits)
            desc = f"Substituted gate '{orig_name}' with '{replacement.name}' at index {target_index}"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name=replacement.name,
                affected_qubits=q_indices, seed=self.seed, description=desc
            )

        # 3. Wrong Qubit
        elif fault_type == FaultType.WRONG_QUBIT:
            all_qubits = list(range(program.num_qubits))
            unused_qubits = [q for q in all_qubits if q not in q_indices]
            sub_target = self.rng.choice(unused_qubits)
            pos_to_replace = self.rng.randrange(len(q_indices))
            new_q_indices = list(q_indices)
            new_q_indices[pos_to_replace] = sub_target
            new_qubit_objs = [mutated_qc.qubits[q] for q in new_q_indices]
            data[target_index] = CircuitInstruction(inst.operation, new_qubit_objs, inst.clbits)
            desc = f"Swapped qubit targets at index {target_index}: {q_indices} -> {new_q_indices}"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name=orig_name,
                affected_qubits=new_q_indices,
                parameters={"old_qubits": q_indices, "new_qubits": new_q_indices},
                seed=self.seed, description=desc
            )

        # 4. Parameter Perturbation
        elif fault_type == FaultType.PARAMETER_PERTURBATION:
            delta = kwargs.get("delta", float(self.np_rng.choice([0.1 * np.pi, 0.25 * np.pi, 0.5 * np.pi])))
            old_params = [float(p) for p in inst.operation.params]
            new_params = [p + delta for p in old_params]
            new_op = copy.deepcopy(inst.operation)
            new_op.params = new_params
            data[target_index] = CircuitInstruction(new_op, inst.qubits, inst.clbits)
            desc = f"Perturbed parameter of '{orig_name}' at index {target_index} by delta={delta:.4f}"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name=orig_name,
                affected_qubits=q_indices,
                parameters={"delta": delta, "old_params": old_params, "new_params": new_params},
                seed=self.seed, description=desc
            )

        # 5. Gate Order Swap
        elif fault_type == FaultType.GATE_ORDER_SWAP:
            data[target_index], data[target_index + 1] = data[target_index + 1], data[target_index]
            desc = f"Swapped order of gate {target_index} ('{orig_name}') and gate {target_index + 1} ('{data[target_index].operation.name}')"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name="SWAP_WITH_ADJACENT",
                affected_qubits=q_indices, seed=self.seed, description=desc
            )

        # 6. Measurement Mutation
        elif fault_type == FaultType.MEASUREMENT_MUTATION:
            # Shift measurement to a different qubit or clbit
            all_qubits = list(range(program.num_qubits))
            other_qubits = [q for q in all_qubits if q not in q_indices]
            sub_qubit = self.rng.choice(other_qubits) if other_qubits else q_indices[0]
            data[target_index] = CircuitInstruction(inst.operation, [mutated_qc.qubits[sub_qubit]], inst.clbits)
            desc = f"Redirected measurement at index {target_index} to qubit {sub_qubit}"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name="measure", mutated_op_name="measure",
                affected_qubits=[sub_qubit],
                parameters={"previous_qubit": q_indices[0], "new_qubit": sub_qubit},
                seed=self.seed, description=desc
            )

        # 7. Controlled Operation Mutation (e.g. inject CX instead of single-qubit gate)
        elif fault_type == FaultType.CONTROLLED_OPERATION:
            ctrl_candidates = [q for q in range(program.num_qubits) if q != q_indices[0]]
            ctrl_q = self.rng.choice(ctrl_candidates)
            cx_gate = CXGate()
            data[target_index] = CircuitInstruction(cx_gate, [mutated_qc.qubits[ctrl_q], mutated_qc.qubits[q_indices[0]]], [])
            desc = f"Converted single-qubit gate '{orig_name}' at {target_index} into CX(ctrl={ctrl_q}, tgt={q_indices[0]})"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name="cx",
                affected_qubits=[ctrl_q, q_indices[0]],
                parameters={"control_qubit": ctrl_q, "target_qubit": q_indices[0]},
                seed=self.seed, description=desc
            )

        # 8. Redundant Gate (e.g. inject unintended Pauli-X or H before or after target)
        elif fault_type == FaultType.REDUNDANT_GATE:
            extra_gate = self.rng.choice([XGate(), ZGate(), HGate()])
            redundant_inst = CircuitInstruction(extra_gate, [mutated_qc.qubits[q_indices[0]]], [])
            data.insert(target_index, redundant_inst)
            desc = f"Inserted unintended redundant '{extra_gate.name}' at index {target_index} on qubit {q_indices[0]}"
            record = MutationRecord(
                mutation_id=mid, fault_type=fault_type, target_index=target_index,
                original_op_name=orig_name, mutated_op_name=f"INSERT_{extra_gate.name}",
                affected_qubits=[q_indices[0]], seed=self.seed, description=desc
            )

        mutated_qc.data = data
        mutated_program = CircuitProgram(
            circuit=mutated_qc,
            name=f"{program.name}_{record.mutation_id}",
            description=f"Faulty mutant of {program.name}: {record.description}",
            properties={
                "is_mutant": True,
                "parent_name": program.name,
                "mutation": record.to_dict(),
            }
        )
        return mutated_program, record
