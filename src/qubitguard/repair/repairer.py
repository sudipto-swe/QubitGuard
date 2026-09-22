"""QubitGuard - Automated Quantum Program Repair (APR) Engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import copy
import random
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction
from qiskit.circuit.library import (
    XGate, YGate, ZGate, HGate, SGate, TGate,
    CXGate, CZGate, SwapGate, RXGate, RYGate, RZGate
)
from qubitguard.core.circuit import CircuitProgram
from qubitguard.execution.executor import CircuitExecutor, ExecutionResult
from qubitguard.detection.detector import FaultDetector
from qubitguard.test_generation.generator import QuantumTestGenerator
from qubitguard.localization.localizer import FaultLocalizer, LocalizationResult
from qubitguard.noise.models import NoiseConfig


class RepairAction(str, Enum):
    REPLACE_GATE = "REPLACE_GATE"
    DELETE_GATE = "DELETE_GATE"
    INSERT_GATE = "INSERT_GATE"
    SWAP_QUBITS = "SWAP_QUBITS"
    TUNE_PARAMETER = "TUNE_PARAMETER"


@dataclass
class CandidatePatch:
    """Detailed candidate repair modification to a quantum circuit."""
    patch_id: str
    target_index: int
    action: RepairAction
    description: str
    is_test_adequate: bool = False
    is_validated: bool = False
    fitness_score: float = 0.0
    tvd_to_reference: float = 1.0
    repaired_program: Optional[CircuitProgram] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "target_index": self.target_index,
            "action": self.action.value,
            "description": self.description,
            "is_test_adequate": self.is_test_adequate,
            "is_validated": self.is_validated,
            "fitness_score": round(self.fitness_score, 4),
            "tvd_to_reference": round(self.tvd_to_reference, 4),
        }


@dataclass
class RepairReport:
    """Comprehensive summary of an automated repair session."""
    faulty_program_name: str
    total_candidates_evaluated: int
    test_adequate_patches: List[CandidatePatch]
    validated_patches: List[CandidatePatch]
    best_patch: Optional[CandidatePatch] = None
    repair_successful: bool = False
    search_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faulty_program_name": self.faulty_program_name,
            "total_candidates_evaluated": self.total_candidates_evaluated,
            "num_test_adequate": len(self.test_adequate_patches),
            "num_validated": len(self.validated_patches),
            "repair_successful": self.repair_successful,
            "best_patch": self.best_patch.to_dict() if self.best_patch else None,
            "search_time_sec": round(self.search_time_sec, 3),
        }


class QuantumProgramRepairer:
    """Automated Program Repair (APR) engine driven by suspiciousness rankings and multi-objective fitness."""

    SEARCH_GATES_1Q = [HGate(), XGate(), YGate(), ZGate(), SGate(), TGate()]
    SEARCH_GATES_2Q = [CXGate(), CZGate(), SwapGate()]

    def __init__(
        self,
        executor: Optional[CircuitExecutor] = None,
        generator: Optional[QuantumTestGenerator] = None,
        localizer: Optional[FaultLocalizer] = None,
        max_evaluations: int = 40,
        seed: Optional[int] = 42
    ):
        self.executor = executor or CircuitExecutor(default_shots=1024, default_seed=seed)
        self.generator = generator or QuantumTestGenerator(executor=self.executor)
        self.localizer = localizer or FaultLocalizer(executor=self.executor, generator=self.generator)
        self.max_evaluations = max_evaluations
        self.rng = random.Random(seed)

    def _generate_candidate_variants(
        self,
        program: CircuitProgram,
        target_idx: int,
    ) -> List[Tuple[CircuitProgram, RepairAction, str]]:
        """Generates localized candidate mutations around suspicious target gate index."""
        variants = []
        data = list(program.circuit.data)
        if target_idx >= len(data):
            return variants

        inst = data[target_idx]
        orig_name = inst.operation.name
        q_indices = [program.circuit.find_bit(q).index for q in inst.qubits]

        # 1. Action: Delete gate
        qc_del = copy.deepcopy(program.circuit)
        del_data = list(qc_del.data)
        del_data.pop(target_idx)
        qc_del.data = del_data
        variants.append((
            CircuitProgram(circuit=qc_del, name=f"patch_del_{target_idx}"),
            RepairAction.DELETE_GATE,
            f"Deleted gate '{orig_name}' at index {target_idx}"
        ))

        # 2. Action: Replace with alternative gates
        if len(q_indices) == 1:
            candidates = [g for g in self.SEARCH_GATES_1Q if g.name.lower() != orig_name.lower()]
        else:
            candidates = [g for g in self.SEARCH_GATES_2Q if g.name.lower() != orig_name.lower()]

        for alt_gate in candidates:
            qc_rep = copy.deepcopy(program.circuit)
            rep_data = list(qc_rep.data)
            rep_data[target_idx] = CircuitInstruction(alt_gate, inst.qubits, inst.clbits)
            qc_rep.data = rep_data
            variants.append((
                CircuitProgram(circuit=qc_rep, name=f"patch_rep_{alt_gate.name}"),
                RepairAction.REPLACE_GATE,
                f"Replaced '{orig_name}' with '{alt_gate.name}' at index {target_idx}"
            ))

        # 3. Action: Swap control/target for 2-qubit gates
        if len(q_indices) == 2:
            qc_swap = copy.deepcopy(program.circuit)
            swap_data = list(qc_swap.data)
            swapped_qubits = [inst.qubits[1], inst.qubits[0]]
            swap_data[target_idx] = CircuitInstruction(inst.operation, swapped_qubits, inst.clbits)
            qc_swap.data = swap_data
            variants.append((
                CircuitProgram(circuit=qc_swap, name=f"patch_swap_{target_idx}"),
                RepairAction.SWAP_QUBITS,
                f"Swapped control and target qubits on '{orig_name}' at index {target_idx}"
            ))

        # 4. Action: Tune Parameter (if parameterized)
        if len(inst.operation.params) > 0:
            for delta in [-0.5 * np.pi, -0.25 * np.pi, -0.1 * np.pi, 0.1 * np.pi, 0.25 * np.pi, 0.5 * np.pi]:
                qc_param = copy.deepcopy(program.circuit)
                param_data = list(qc_param.data)
                new_op = copy.deepcopy(inst.operation)
                new_op.params = [float(p) + delta for p in inst.operation.params]
                param_data[target_idx] = CircuitInstruction(new_op, inst.qubits, inst.clbits)
                qc_param.data = param_data
                variants.append((
                    CircuitProgram(circuit=qc_param, name=f"patch_param_{delta:.2f}"),
                    RepairAction.TUNE_PARAMETER,
                    f"Adjusted parameter on '{orig_name}' at {target_idx} by delta={delta:.2f}"
                ))

        return variants

    def repair(
        self,
        faulty_program: CircuitProgram,
        reference_program: Optional[CircuitProgram] = None,
        noise_config: Optional[NoiseConfig] = None,
        localization_result: Optional[LocalizationResult] = None,
    ) -> RepairReport:
        """Executes guided heuristic program repair to synthesize semantic patches."""
        import time
        start_time = time.perf_counter()

        # Step 1: Localize fault if rankings not already provided
        if localization_result is None:
            localization_result = self.localizer.localize_faults(
                faulty_program,
                reference_program=reference_program,
                noise_config=noise_config
            )

        # Step 2: Extract top suspicious gate locations (Top 3 or all)
        suspicious_indices = [
            r.gate_index for r in localization_result.rankings[:3]
            if not any(inst.operation.name == "measure" for idx, inst in enumerate(faulty_program.circuit.data) if idx == r.gate_index)
        ]
        if not suspicious_indices:
            # Fallback to non-measurement indices
            suspicious_indices = [
                idx for idx, inst in enumerate(faulty_program.circuit.data)
                if inst.operation.name.lower() != "measure"
            ]

        # Step 3: Reference execution baseline
        ref_res = self.executor.run(reference_program, shots=1024, noise_config=noise_config) if reference_program else None

        evaluated_count = 0
        test_adequate_patches: List[CandidatePatch] = []
        validated_patches: List[CandidatePatch] = []

        for target_idx in suspicious_indices:
            if evaluated_count >= self.max_evaluations:
                break

            candidates = self._generate_candidate_variants(faulty_program, target_idx)
            for cand_prog, action, desc in candidates:
                if evaluated_count >= self.max_evaluations:
                    break
                evaluated_count += 1

                # Evaluate against test suite
                suite_report = self.generator.run_suite(cand_prog, reference_program, noise_config)
                is_test_adeq = (suite_report.failed_tests == 0)

                # Compute distance to reference
                tvd = 1.0
                if ref_res is not None:
                    cand_res = self.executor.run(cand_prog, shots=1024, noise_config=noise_config)
                    tvd = FaultDetector.calculate_tvd(ref_res.probabilities, cand_res.probabilities)

                # Validation: True validation requires test-adequacy AND TVD < threshold
                threshold = 0.15 if (noise_config and noise_config.error_rate > 0) else 0.08
                is_validated = is_test_adeq and (tvd <= threshold if ref_res is not None else True)

                # Fitness score: higher is better
                fitness = (1.0 - tvd) * 0.7 + (suite_report.pass_rate) * 0.3

                patch = CandidatePatch(
                    patch_id=f"PATCH_{evaluated_count:03d}",
                    target_index=target_idx,
                    action=action,
                    description=desc,
                    is_test_adequate=is_test_adeq,
                    is_validated=is_validated,
                    fitness_score=fitness,
                    tvd_to_reference=tvd,
                    repaired_program=cand_prog,
                )

                if is_test_adeq:
                    test_adequate_patches.append(patch)
                if is_validated:
                    validated_patches.append(patch)

        # Sort validated patches by fitness
        validated_patches.sort(key=lambda p: p.fitness_score, reverse=True)
        test_adequate_patches.sort(key=lambda p: p.fitness_score, reverse=True)

        best_patch = validated_patches[0] if validated_patches else (test_adequate_patches[0] if test_adequate_patches else None)
        duration = time.perf_counter() - start_time

        return RepairReport(
            faulty_program_name=faulty_program.name,
            total_candidates_evaluated=evaluated_count,
            test_adequate_patches=test_adequate_patches,
            validated_patches=validated_patches,
            best_patch=best_patch,
            repair_successful=(len(validated_patches) > 0),
            search_time_sec=duration,
        )
