"""Test suite for QubitGuard core, fault injection, noise, testing, localization, and repair."""

import pytest
import numpy as np
from qubitguard.benchmarks.circuits import get_all_benchmarks, create_bell_state, create_ghz_state
from qubitguard.fault_injection.injector import FaultInjector, FaultType
from qubitguard.noise.models import NoiseConfig, NoiseType, NoiseFactory
from qubitguard.execution.executor import CircuitExecutor
from qubitguard.detection.detector import FaultDetector
from qubitguard.test_generation.generator import QuantumTestGenerator
from qubitguard.localization.localizer import FaultLocalizer
from qubitguard.repair.repairer import QuantumProgramRepairer
from qubitguard.ml.predictor import QuantumFaultRiskPredictor


def test_benchmarks_instantiation():
    benchmarks = get_all_benchmarks()
    assert len(benchmarks) >= 6
    assert "Bell_State" in benchmarks
    assert "GHZ_3q" in benchmarks
    assert benchmarks["Bell_State"].num_qubits == 2
    assert benchmarks["GHZ_3q"].num_qubits == 3


def test_fault_injection_operators():
    bell = create_bell_state()
    injector = FaultInjector(seed=42)

    # Test Gate Omission
    mut_omission, rec1 = injector.inject_fault(bell, FaultType.GATE_OMISSION)
    assert mut_omission.size < bell.size
    assert rec1.fault_type == FaultType.GATE_OMISSION

    # Test Wrong Gate
    mut_wrong, rec2 = injector.inject_fault(bell, FaultType.WRONG_GATE)
    assert rec2.original_op_name != rec2.mutated_op_name

    # Test Parameter Perturbation (on QAOA)
    from qubitguard.benchmarks.circuits import create_qaoa_ansatz_3q
    qaoa = create_qaoa_ansatz_3q()
    mut_param, rec3 = injector.inject_fault(qaoa, FaultType.PARAMETER_PERTURBATION)
    assert "delta" in rec3.parameters


def test_noise_modeling():
    config = NoiseConfig(noise_type=NoiseType.DEPOLARIZING, error_rate=0.02)
    noise_model = NoiseFactory.create_noise_model(config)
    assert noise_model is not None

    ideal_cfg = NoiseConfig(noise_type=NoiseType.IDEAL)
    assert NoiseFactory.create_noise_model(ideal_cfg) is None


def test_circuit_execution():
    bell = create_bell_state()
    executor = CircuitExecutor(default_shots=500, default_seed=42)
    res = executor.run(bell)
    assert res.shots == 500
    assert "00" in res.probabilities or "11" in res.probabilities
    total_p = sum(res.probabilities.values())
    assert np.isclose(total_p, 1.0)


def test_fault_detection_divergence():
    bell = create_bell_state()
    injector = FaultInjector(seed=42)
    # Inject wrong gate replacing H with X
    mut_bell, _ = injector.inject_fault(bell, FaultType.WRONG_GATE, target_index=0)

    executor = CircuitExecutor(default_shots=1000, default_seed=42)
    res_orig = executor.run(bell)
    res_mut = executor.run(mut_bell)

    detector = FaultDetector(tvd_threshold=0.10)
    det_res = detector.evaluate(res_orig, res_mut)
    assert det_res.is_faulty is True
    assert det_res.tvd > 0.10


def test_test_suite_metamorphic_and_property():
    bell = create_bell_state()
    gen = QuantumTestGenerator()
    report_clean = gen.run_suite(bell, reference_program=bell)
    assert report_clean.passed_tests > 0

    injector = FaultInjector(seed=42)
    mut_bell, _ = injector.inject_fault(bell, FaultType.GATE_OMISSION, target_index=0)
    report_faulty = gen.run_suite(mut_bell, reference_program=bell)
    assert report_faulty.is_fault_detected is True


def test_fault_localization_sbfl():
    bell = create_bell_state()
    injector = FaultInjector(seed=42)
    mut_bell, rec = injector.inject_fault(bell, FaultType.WRONG_GATE, target_index=0)

    localizer = FaultLocalizer()
    loc_res = localizer.localize_faults(mut_bell, reference_program=bell, actual_fault_index=rec.target_index)
    assert len(loc_res.rankings) > 0
    # Top ranked should be high suspicion
    assert loc_res.rankings[0].suspiciousness >= loc_res.rankings[-1].suspiciousness


def test_automated_program_repair():
    bell = create_bell_state()
    injector = FaultInjector(seed=42)
    # Gate omission at index 1 (CX)
    mut_bell, rec = injector.inject_fault(bell, FaultType.GATE_OMISSION, target_index=1)

    repairer = QuantumProgramRepairer(max_evaluations=25, seed=42)
    report = repairer.repair(mut_bell, reference_program=bell)
    assert report.total_candidates_evaluated > 0


def test_ml_fault_risk_predictor():
    predictor = QuantumFaultRiskPredictor()
    metrics = predictor.train_synthetic_baseline()
    assert metrics["accuracy"] > 0.50
    bell = create_bell_state()
    risk = predictor.predict_gate_risk(bell, gate_index=0)
    assert 0.0 <= risk <= 1.0
