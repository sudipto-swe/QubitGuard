"""QubitGuard - Quantum Noise Simulation Models using Qiskit Aer."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    pauli_error,
    ReadoutError,
    thermal_relaxation_error
)


class NoiseType(str, Enum):
    IDEAL = "IDEAL"
    DEPOLARIZING = "DEPOLARIZING"
    BIT_PHASE_FLIP = "BIT_PHASE_FLIP"
    READOUT = "READOUT"
    COMPREHENSIVE_NISQ = "COMPREHENSIVE_NISQ"


@dataclass
class NoiseConfig:
    """Configuration container for quantum noise simulation."""
    noise_type: NoiseType = NoiseType.IDEAL
    error_rate: float = 0.01  # single-qubit gate error or baseline rate
    two_qubit_error_rate: Optional[float] = None
    readout_error_rate: float = 0.02
    t1_us: float = 50.0   # microseconds
    t2_us: float = 70.0   # microseconds
    gate_time_ns: float = 50.0  # nanoseconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "noise_type": self.noise_type.value,
            "error_rate": self.error_rate,
            "two_qubit_error_rate": self.two_qubit_error_rate or (self.error_rate * 5.0),
            "readout_error_rate": self.readout_error_rate,
            "t1_us": self.t1_us,
            "t2_us": self.t2_us,
            "gate_time_ns": self.gate_time_ns,
        }


class NoiseFactory:
    """Generates parameterized Qiskit Aer NoiseModels for realistic NISQ testing."""

    @staticmethod
    def create_noise_model(config: NoiseConfig) -> Optional[NoiseModel]:
        """Builds a Qiskit Aer NoiseModel based on the provided configuration."""
        if config.noise_type == NoiseType.IDEAL or config.error_rate <= 0.0:
            return None

        noise_model = NoiseModel()
        p1 = config.error_rate
        p2 = config.two_qubit_error_rate if config.two_qubit_error_rate is not None else min(1.0, p1 * 5.0)

        # 1. Depolarizing Noise
        if config.noise_type == NoiseType.DEPOLARIZING:
            err_1q = depolarizing_error(p1, 1)
            err_2q = depolarizing_error(p2, 2)
            noise_model.add_all_qubit_quantum_error(err_1q, ["h", "x", "y", "z", "s", "t", "rx", "ry", "rz", "u1", "u2", "u3"])
            noise_model.add_all_qubit_quantum_error(err_2q, ["cx", "cz", "swap"])

        # 2. Bit-flip and Phase-flip (Pauli errors)
        elif config.noise_type == NoiseType.BIT_PHASE_FLIP:
            # px: bit flip, pz: phase flip
            p_bit = p1 / 2.0
            p_phase = p1 / 2.0
            err_1q = pauli_error([("X", p_bit), ("Z", p_phase), ("I", 1.0 - p_bit - p_phase)])
            noise_model.add_all_qubit_quantum_error(err_1q, ["h", "x", "y", "z", "s", "t", "rx", "ry", "rz"])

        # 3. Measurement / Readout Error
        elif config.noise_type == NoiseType.READOUT:
            r_err = config.readout_error_rate
            # 2x2 matrix: P(meas|prep)
            readout_matrix = [
                [1.0 - r_err, r_err],
                [r_err, 1.0 - r_err]
            ]
            r_error = ReadoutError(readout_matrix)
            noise_model.add_all_qubit_readout_error(r_error)

        # 4. Comprehensive NISQ Model (depolarizing + thermal + readout)
        elif config.noise_type == NoiseType.COMPREHENSIVE_NISQ:
            err_1q = depolarizing_error(p1, 1)
            err_2q = depolarizing_error(p2, 2)
            noise_model.add_all_qubit_quantum_error(err_1q, ["h", "x", "y", "z", "s", "t", "rx", "ry", "rz"])
            noise_model.add_all_qubit_quantum_error(err_2q, ["cx", "cz", "swap"])
            
            # Readout error
            r_err = config.readout_error_rate
            r_matrix = [[1.0 - r_err, r_err], [r_err, 1.0 - r_err]]
            noise_model.add_all_qubit_readout_error(ReadoutError(r_matrix))

        return noise_model
