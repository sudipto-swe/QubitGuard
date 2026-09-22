"""QubitGuard - Machine Learning Assistance for Fault Risk & Gate Vulnerability."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from qubitguard.core.circuit import CircuitProgram, GateMetadata


@dataclass
class CircuitFeatureVector:
    """Feature representation of a quantum circuit or gate location for ML analysis."""
    num_qubits: int
    circuit_depth: int
    num_gates: int
    two_qubit_ratio: float
    measurement_count: int
    gate_position_ratio: float  # index / total_gates
    is_controlled: int
    num_gate_params: int


class QuantumFaultRiskPredictor:
    """Uses structural and topological circuit features to predict fault vulnerability."""

    def __init__(self, random_state: int = 42):
        self.model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=random_state)
        self.is_fitted = False

    @staticmethod
    def extract_gate_features(program: CircuitProgram, gate_index: int) -> np.ndarray:
        """Extracts numerical features for a specific gate in the circuit."""
        gates = program.get_gate_metadata_list()
        total_gates = max(1, len(gates))
        gate = gates[gate_index] if gate_index < total_gates else gates[-1]

        num_2q = sum(1 for g in gates if len(g.qubits) >= 2)
        ratio_2q = num_2q / total_gates

        feat = [
            float(program.num_qubits),
            float(program.depth),
            float(total_gates),
            float(ratio_2q),
            float(program.circuit.num_clbits),
            float(gate_index / total_gates),
            1.0 if gate.is_controlled else 0.0,
            float(len(gate.params)),
        ]
        return np.array(feat, dtype=float)

    def train_synthetic_baseline(self) -> Dict[str, float]:
        """Trains baseline model on synthetic structural circuit distributions without data leakage."""
        np.random.seed(42)
        n_samples = 400
        # Synthetic feature generation mimicking diverse circuit topologies
        qubits = np.random.randint(2, 10, size=n_samples)
        depths = np.random.randint(5, 50, size=n_samples)
        gates = depths * qubits // 2
        ratios_2q = np.random.uniform(0.1, 0.6, size=n_samples)
        clbits = qubits
        pos_ratios = np.random.uniform(0.0, 1.0, size=n_samples)
        is_ctrl = np.random.binomial(1, 0.35, size=n_samples)
        params_num = np.random.binomial(2, 0.25, size=n_samples)

        X = np.column_stack([qubits, depths, gates, ratios_2q, clbits, pos_ratios, is_ctrl, params_num])
        
        # Ground truth rule for bug vulnerability: 2-qubit gates and parameterized gates in deep circuits have higher defect impact
        vuln_score = (
            0.35 * is_ctrl +
            0.25 * (ratios_2q > 0.4) +
            0.20 * (pos_ratios < 0.5) + # earlier gates cascade errors
            0.20 * (params_num > 0) +
            np.random.normal(0, 0.1, size=n_samples)
        )
        y = (vuln_score > 0.45).astype(int)

        split = int(0.75 * n_samples)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        self.model.fit(X_train, y_train)
        self.is_fitted = True

        y_pred = self.model.predict(X_test)
        return {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        }

    def predict_gate_risk(self, program: CircuitProgram, gate_index: int) -> float:
        """Returns predicted probability [0, 1] that this gate location is high-vulnerability."""
        if not self.is_fitted:
            self.train_synthetic_baseline()
        feat = self.extract_gate_features(program, gate_index).reshape(1, -1)
        prob = self.model.predict_proba(feat)[0][1]
        return float(prob)
