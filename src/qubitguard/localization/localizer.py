"""QubitGuard - Spectrum-Based Fault Localization (SBFL) & Differential Slicing."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import math
import copy

from qiskit import QuantumCircuit
from qubitguard.core.circuit import CircuitProgram, GateMetadata
from qubitguard.execution.executor import CircuitExecutor
from qubitguard.detection.detector import FaultDetector
from qubitguard.test_generation.generator import QuantumTestGenerator, TestSuiteReport
from qubitguard.noise.models import NoiseConfig


@dataclass
class GateSuspiciousness:
    """Calculated fault suspicion score for a specific gate in a quantum circuit."""
    gate_index: int
    gate_name: str
    qubits: List[int]
    suspiciousness: float
    ochiai_score: float
    tarantula_score: float
    dstar_score: float
    differential_drop: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_index": self.gate_index,
            "gate_name": self.gate_name,
            "qubits": self.qubits,
            "suspiciousness": round(self.suspiciousness, 4),
            "ochiai_score": round(self.ochiai_score, 4),
            "tarantula_score": round(self.tarantula_score, 4),
            "dstar_score": round(self.dstar_score, 4),
            "differential_drop": round(self.differential_drop, 4),
        }


@dataclass
class LocalizationResult:
    """Ranked fault localization findings for a quantum circuit."""
    rankings: List[GateSuspiciousness]
    top_1_index: Optional[int] = None
    top_3_indices: List[int] = field(default_factory=list)
    actual_fault_index: Optional[int] = None
    rank_of_actual_fault: Optional[int] = None
    exam_score: Optional[float] = None  # Percentage of gates examined before finding bug

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rankings": [r.to_dict() for r in self.rankings],
            "top_1_index": self.top_1_index,
            "top_3_indices": self.top_3_indices,
            "actual_fault_index": self.actual_fault_index,
            "rank_of_actual_fault": self.rank_of_actual_fault,
            "exam_score": round(self.exam_score, 4) if self.exam_score is not None else None,
        }


class FaultLocalizer:
    """Spectrum-Based Fault Localization (SBFL) & Slicing engine for quantum circuits."""

    def __init__(
        self,
        executor: Optional[CircuitExecutor] = None,
        generator: Optional[QuantumTestGenerator] = None
    ):
        self.executor = executor or CircuitExecutor(default_shots=1024, default_seed=42)
        self.generator = generator or QuantumTestGenerator(executor=self.executor)

    @staticmethod
    def _ochiai(n_cf: int, n_uf: int, n_cs: int) -> float:
        """Ochiai SBFL coefficient: n_cf / sqrt((n_cf + n_uf) * (n_cf + n_cs))."""
        denominator = math.sqrt((n_cf + n_uf) * (n_cf + n_cs))
        return (n_cf / denominator) if denominator > 0 else 0.0

    @staticmethod
    def _tarantula(n_cf: int, n_uf: int, n_cs: int, n_us: int) -> float:
        """Tarantula SBFL coefficient: (n_cf / (n_cf + n_uf)) / ((n_cf / (n_cf + n_uf)) + (n_cs / (n_cs + n_us)))."""
        total_failed = n_cf + n_uf
        total_passed = n_cs + n_us
        if total_failed == 0 or total_passed == 0:
            return 0.0
        num = n_cf / total_failed
        denom = num + (n_cs / total_passed)
        return (num / denom) if denom > 0 else 0.0

    @staticmethod
    def _dstar(n_cf: int, n_uf: int, n_cs: int, star: float = 2.0) -> float:
        """DStar SBFL metric: (n_cf^star) / (n_uf + n_cs)."""
        denom = n_uf + n_cs
        if denom == 0:
            return float(n_cf ** star) if n_cf > 0 else 0.0
        return float((n_cf ** star) / denom)

    def localize_faults(
        self,
        candidate_program: CircuitProgram,
        reference_program: Optional[CircuitProgram] = None,
        actual_fault_index: Optional[int] = None,
        noise_config: Optional[NoiseConfig] = None,
    ) -> LocalizationResult:
        """Calculates gate-level suspiciousness rankings using SBFL spectra and differential slicing."""
        gates = candidate_program.get_gate_metadata_list()
        num_gates = len(gates)
        if num_gates == 0:
            return LocalizationResult(rankings=[])

        # Execute test suite to collect global pass/fail context
        suite_report = self.generator.run_suite(candidate_program, reference_program, noise_config)
        
        # Slicing: Create prefix and sub-circuit variations to isolate gate contributions
        # For each gate index, evaluate impact of removing / bypassing that gate
        differential_drops = {}
        ref_res = self.executor.run(reference_program, shots=1024, noise_config=noise_config) if reference_program else None
        cand_res = self.executor.run(candidate_program, shots=1024, noise_config=noise_config)

        for gate in gates:
            if gate.is_measurement:
                continue
            idx = gate.index
            # Build mutated copy omitting gate idx
            sliced_qc = copy.deepcopy(candidate_program.circuit)
            sliced_data = list(sliced_qc.data)
            if idx < len(sliced_data):
                sliced_data.pop(idx)
                sliced_qc.data = sliced_data
                sliced_prog = CircuitProgram(circuit=sliced_qc, name="sliced")
                res_sliced = self.executor.run(sliced_prog, shots=1024, noise_config=noise_config)

                if ref_res is not None:
                    # TVD drop: how much closer to reference does omitting this gate bring us?
                    tvd_with_gate = FaultDetector.calculate_tvd(ref_res.probabilities, cand_res.probabilities)
                    tvd_without_gate = FaultDetector.calculate_tvd(ref_res.probabilities, res_sliced.probabilities)
                    # Positive delta means omitting the gate improved fidelity toward reference
                    gain = max(0.0, tvd_with_gate - tvd_without_gate)
                    differential_drops[idx] = gain
                else:
                    # Inherent divergence delta
                    tvd_shift = FaultDetector.calculate_tvd(cand_res.probabilities, res_sliced.probabilities)
                    differential_drops[idx] = tvd_shift

        # Compute SBFL spectra per gate
        # Spectrum: n_cf (covered in failed tests), n_cs (covered in passed tests), etc.
        rankings = []
        for gate in gates:
            idx = gate.index
            diff_score = differential_drops.get(idx, 0.0)

            # Heuristic spectrum mapping for quantum circuit:
            # Gates that create large state divergence participate predominantly in failing executions
            if suite_report.is_fault_detected:
                n_cf = 1 if diff_score > 0.05 else 0
                n_cs = 1 if diff_score <= 0.05 else 0
                n_uf = suite_report.failed_tests - n_cf
                n_us = suite_report.passed_tests - n_cs
            else:
                n_cf, n_uf, n_cs, n_us = 0, 0, 1, 0

            ochiai = self._ochiai(n_cf, n_uf, n_cs)
            tarantula = self._tarantula(n_cf, n_uf, n_cs, n_us)
            dstar = self._dstar(n_cf, n_uf, n_cs)

            # Blended suspiciousness score: 60% differential gain + 40% Ochiai
            composite = 0.60 * min(1.0, diff_score * 2.5) + 0.40 * ochiai

            rankings.append(GateSuspiciousness(
                gate_index=idx,
                gate_name=gate.gate_name,
                qubits=gate.qubits,
                suspiciousness=float(composite),
                ochiai_score=float(ochiai),
                tarantula_score=float(tarantula),
                dstar_score=float(dstar),
                differential_drop=float(diff_score),
            ))

        # Sort descending by suspiciousness
        rankings.sort(key=lambda x: x.suspiciousness, reverse=True)

        top_1 = rankings[0].gate_index if rankings else None
        top_3 = [r.gate_index for r in rankings[:3]]

        # Evaluate performance against ground truth if actual_fault_index is known
        rank_of_actual = None
        exam = None
        if actual_fault_index is not None:
            for rank_idx, r in enumerate(rankings, start=1):
                if r.gate_index == actual_fault_index:
                    rank_of_actual = rank_idx
                    exam = (rank_idx / num_gates) if num_gates > 0 else 1.0
                    break

        return LocalizationResult(
            rankings=rankings,
            top_1_index=top_1,
            top_3_indices=top_3,
            actual_fault_index=actual_fault_index,
            rank_of_actual_fault=rank_of_actual,
            exam_score=exam,
        )
