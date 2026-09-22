"""QubitGuard - Circuit Execution Engine (Ideal & Noisy Aer Simulators)."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time
import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qubitguard.core.circuit import CircuitProgram
from qubitguard.noise.models import NoiseConfig, NoiseFactory


@dataclass
class ExecutionResult:
    """Standardized outcome of quantum circuit execution."""
    counts: Dict[str, int]
    probabilities: Dict[str, float]
    shots: int
    execution_time_sec: float
    seed: Optional[int] = None
    noise_config: Optional[Dict[str, Any]] = None

    def get_most_frequent(self) -> str:
        if not self.counts:
            return ""
        return max(self.counts, key=self.counts.get)


class CircuitExecutor:
    """Executes quantum circuits on AerSimulator with reproducible seeds and noise models."""

    def __init__(self, default_shots: int = 1024, default_seed: Optional[int] = 42):
        self.default_shots = default_shots
        self.default_seed = default_seed

    def run(
        self,
        program: CircuitProgram,
        shots: Optional[int] = None,
        seed: Optional[int] = None,
        noise_config: Optional[NoiseConfig] = None,
    ) -> ExecutionResult:
        """Executes the given circuit, returning counts and normalized probability distribution."""
        actual_shots = shots if shots is not None else self.default_shots
        actual_seed = seed if seed is not None else self.default_seed

        qc = program.circuit
        # Ensure measurement exists if not already present
        if not any(inst.operation.name == "measure" for inst in qc.data):
            qc_to_run = qc.copy()
            qc_to_run.measure_all()
        else:
            qc_to_run = qc

        # Setup simulator and noise
        noise_model = None
        noise_dict = None
        if noise_config is not None:
            noise_model = NoiseFactory.create_noise_model(noise_config)
            noise_dict = noise_config.to_dict()

        backend = AerSimulator(noise_model=noise_model, seed_simulator=actual_seed)

        start_time = time.perf_counter()
        transpiled_qc = transpile(qc_to_run, backend, seed_transpiler=actual_seed)
        job = backend.run(transpiled_qc, shots=actual_shots, seed_simulator=actual_seed)
        result = job.result()
        duration = time.perf_counter() - start_time

        counts = result.get_counts()
        # Compute normalized probabilities
        total_shots = sum(counts.values()) if counts else 1
        probs = {k: v / total_shots for k, v in counts.items()}

        return ExecutionResult(
            counts=counts,
            probabilities=probs,
            shots=actual_shots,
            execution_time_sec=duration,
            seed=actual_seed,
            noise_config=noise_dict,
        )
