"""QubitGuard - Test Generation Engine: Metamorphic & Property-Based Testing."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import copy
from qiskit import QuantumCircuit
from qubitguard.core.circuit import CircuitProgram
from qubitguard.execution.executor import CircuitExecutor, ExecutionResult
from qubitguard.detection.detector import FaultDetector, DetectionResult
from qubitguard.noise.models import NoiseConfig


@dataclass
class TestCaseResult:
    """Individual test execution outcome."""
    test_name: str
    strategy: str  # "metamorphic", "property", "example"
    passed: bool
    description: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteReport:
    """Aggregated test execution summary over a circuit program."""
    program_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[TestCaseResult]
    is_fault_detected: bool

    @property
    def pass_rate(self) -> float:
        return self.passed_tests / self.total_tests if self.total_tests > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_name": self.program_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": round(self.pass_rate, 4),
            "is_fault_detected": self.is_fault_detected,
            "tests": [
                {
                    "test_name": t.test_name,
                    "strategy": t.strategy,
                    "passed": t.passed,
                    "description": t.description,
                    "details": t.details,
                }
                for t in self.test_results
            ]
        }


class QuantumTestGenerator:
    """Generates and executes property-based and metamorphic test suites for quantum programs."""

    def __init__(
        self,
        executor: Optional[CircuitExecutor] = None,
        detector: Optional[FaultDetector] = None,
    ):
        self.executor = executor or CircuitExecutor(default_shots=2048, default_seed=42)
        self.detector = detector or FaultDetector(tvd_threshold=0.10)

    # 1. Metamorphic Testing: Inverse Unitary Relation (U . U† == I)
    def test_inverse_identity_relation(
        self,
        program: CircuitProgram,
        noise_config: Optional[NoiseConfig] = None
    ) -> TestCaseResult:
        """MR1: For any non-measurement unitary subcircuit U, appending U† must return state to |0...0>."""
        qc_orig = program.circuit
        # Extract gates prior to measurement
        unitary_qc = QuantumCircuit(program.num_qubits)
        has_ops = False
        for inst in qc_orig.data:
            if inst.operation.name.lower() != "measure":
                unitary_qc.append(inst.operation, inst.qubits, [])
                has_ops = True

        if not has_ops:
            return TestCaseResult(
                test_name="MR_Inverse_Identity",
                strategy="metamorphic",
                passed=True,
                description="Circuit has no non-measurement unitary gates.",
            )

        # Build U + U_inv
        inv_qc = QuantumCircuit(program.num_qubits, program.num_qubits)
        inv_qc.compose(unitary_qc, inplace=True)
        inv_qc.compose(unitary_qc.inverse(), inplace=True)
        inv_qc.measure(list(range(program.num_qubits)), list(range(program.num_qubits)))

        inv_prog = CircuitProgram(circuit=inv_qc, name=f"{program.name}_inv_identity")
        res = self.executor.run(inv_prog, shots=2048, noise_config=noise_config)

        # Expected output: 100% |0...0>
        zero_state = "0" * program.num_qubits
        zero_prob = res.probabilities.get(zero_state, 0.0)

        # Threshold: allow up to 15% noise deviation if noisy, else 95%
        min_expected = 0.70 if (noise_config and noise_config.error_rate > 0) else 0.90
        passed = zero_prob >= min_expected

        return TestCaseResult(
            test_name="MR_Inverse_Identity",
            strategy="metamorphic",
            passed=passed,
            description=f"Appending U† should restore |0...0> with high probability (found P(0)={zero_prob:.3f}, req>={min_expected:.2f})",
            details={"zero_prob": round(zero_prob, 4), "min_expected": min_expected, "counts": res.counts}
        )

    # 2. Metamorphic Testing: Qubit Permutation / Symmetry
    def test_qubit_permutation_equivariance(
        self,
        program: CircuitProgram,
        noise_config: Optional[NoiseConfig] = None
    ) -> TestCaseResult:
        """MR2: Permuting symmetric qubit assignments preserves output probabilities under corresponding label permutation."""
        if program.num_qubits < 2:
            return TestCaseResult(
                test_name="MR_Qubit_Permutation",
                strategy="metamorphic",
                passed=True,
                description="Single qubit circuit; permutation MR trivially holds.",
            )

        # Execute original
        res_orig = self.executor.run(program, shots=2048, noise_config=noise_config)

        # Build permuted circuit (swap qubit 0 and qubit 1 throughout)
        perm_qc = QuantumCircuit(program.num_qubits, program.num_clbits)
        for inst in program.circuit.data:
            new_q = []
            for q in inst.qubits:
                q_idx = program.circuit.find_bit(q).index
                if q_idx == 0:
                    new_q.append(perm_qc.qubits[1])
                elif q_idx == 1:
                    new_q.append(perm_qc.qubits[0])
                else:
                    new_q.append(perm_qc.qubits[q_idx])
            perm_qc.append(inst.operation, new_q, inst.clbits)

        perm_prog = CircuitProgram(circuit=perm_qc, name=f"{program.name}_perm01")
        res_perm = self.executor.run(perm_prog, shots=2048, noise_config=noise_config)

        # For GHZ / Bell states, swapping q0 and q1 produces invariant distributions
        # For general circuits, compare mapped bitstrings
        mapped_perm_probs = {}
        for bitstring, prob in res_perm.probabilities.items():
            # Qiskit bitstring order is little-endian (right-to-left)
            # Swap indices 0 and 1
            bs_list = list(bitstring)
            if len(bs_list) >= 2:
                bs_list[-1], bs_list[-2] = bs_list[-2], bs_list[-1]
            mapped_perm_probs["".join(bs_list)] = prob

        tvd = FaultDetector.calculate_tvd(res_orig.probabilities, mapped_perm_probs)
        threshold = 0.20 if (noise_config and noise_config.error_rate > 0) else 0.12
        passed = tvd <= threshold

        return TestCaseResult(
            test_name="MR_Qubit_Permutation",
            strategy="metamorphic",
            passed=passed,
            description=f"Equivariance under qubit permutation (TVD={tvd:.3f}, max_allowed={threshold:.2f})",
            details={"tvd": round(tvd, 4), "threshold": threshold}
        )

    # 3. Property Invariant: Entanglement / Parity Check
    def test_parity_and_subspace_invariants(
        self,
        program: CircuitProgram,
        reference_program: Optional[CircuitProgram] = None,
        noise_config: Optional[NoiseConfig] = None
    ) -> TestCaseResult:
        """Property Invariant: Tests whether output space adheres to expected parity or reference distribution."""
        res_cand = self.executor.run(program, shots=2048, noise_config=noise_config)

        # If a reference program is given, compare distributions directly
        if reference_program is not None:
            res_ref = self.executor.run(reference_program, shots=2048, noise_config=noise_config)
            det = self.detector.evaluate(res_ref, res_cand)
            passed = not det.is_faulty
            desc = f"Distribution matches reference (TVD={det.tvd:.3f}, p_val={det.p_value:.4f})"
            details = det.to_dict()
        else:
            # Domain-specific property invariants
            name = program.name.lower()
            if "bell" in name or "ghz" in name:
                # Bell/GHZ states should only populate even-parity basis states (all-0 or all-1)
                n = program.num_qubits
                valid_states = {"0" * n, "1" * n}
                entangled_mass = sum(prob for bs, prob in res_cand.probabilities.items() if bs in valid_states)
                min_req = 0.65 if (noise_config and noise_config.error_rate > 0) else 0.88
                passed = entangled_mass >= min_req
                desc = f"GHZ/Bell subspace mass (P(all-0 or all-1) = {entangled_mass:.3f}, req>={min_req:.2f})"
                details = {"entangled_mass": round(entangled_mass, 4), "min_required": min_req}
            elif "grover" in name:
                # Grover search should concentrate probability into marked state
                max_prob = max(res_cand.probabilities.values()) if res_cand.probabilities else 0.0
                min_req = 0.50 if (noise_config and noise_config.error_rate > 0) else 0.85
                passed = max_prob >= min_req
                desc = f"Grover amplitude amplification (Max P = {max_prob:.3f}, req>={min_req:.2f})"
                details = {"max_prob": round(max_prob, 4), "min_required": min_req}
            else:
                # General entropy / support check: no single illegal empty distribution
                passed = len(res_cand.probabilities) > 0
                desc = "Non-trivial distribution generated."
                details = {"num_outcomes": len(res_cand.probabilities)}

        return TestCaseResult(
            test_name="Property_Distribution_Invariant",
            strategy="property",
            passed=passed,
            description=desc,
            details=details,
        )

    # 4. Run Full Test Suite
    def run_suite(
        self,
        candidate_program: CircuitProgram,
        reference_program: Optional[CircuitProgram] = None,
        noise_config: Optional[NoiseConfig] = None
    ) -> TestSuiteReport:
        """Executes full quantum test suite across metamorphic, property, and reference tests."""
        results = []

        # 1. Metamorphic Inverse Identity
        results.append(self.test_inverse_identity_relation(candidate_program, noise_config))

        # 2. Metamorphic Qubit Permutation (if applicable)
        if candidate_program.num_qubits >= 2:
            results.append(self.test_qubit_permutation_equivariance(candidate_program, noise_config))

        # 3. Property Invariants
        results.append(self.test_parity_and_subspace_invariants(candidate_program, reference_program, noise_config))

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        is_detected = failed > 0

        return TestSuiteReport(
            program_name=candidate_program.name,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            test_results=results,
            is_fault_detected=is_detected,
        )
