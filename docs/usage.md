# QubitGuard: Comprehensive User & API Guide

## 1. Quick Start via CLI

List available benchmark quantum circuits:
```bash
qubitguard benchmarks
```

Inject a fault:
```bash
qubitguard inject --circuit Bell_State --fault GATE_OMISSION --seed 42
```

Run test suite under depolarizing noise:
```bash
qubitguard test --circuit GHZ_3q --noise 0.02
```

Run automated repair on a faulty circuit:
```bash
qubitguard repair --circuit Bell_State --fault GATE_OMISSION --seed 42
```

---

## 2. Python API Usage

### 2.1 Generating Circuits & Injecting Mutations
```python
from qubitguard.benchmarks.circuits import create_bell_state
from qubitguard.fault_injection.injector import FaultInjector, FaultType

prog = create_bell_state()
injector = FaultInjector(seed=42)

# Inject gate omission
mutant_prog, mutation_record = injector.inject_fault(
    prog, 
    FaultType.GATE_OMISSION, 
    target_index=1
)
print("Mutant description:", mutation_record.description)
```

### 2.2 Running Quantum Test Suites
```python
from qubitguard.test_generation.generator import QuantumTestGenerator
from qubitguard.noise.models import NoiseConfig, NoiseType

# Optional noise model
noise_cfg = NoiseConfig(noise_type=NoiseType.DEPOLARIZING, error_rate=0.01)

generator = QuantumTestGenerator()
report = generator.run_suite(mutant_prog, reference_program=prog, noise_config=noise_cfg)

print(f"Passed: {report.passed_tests}/{report.total_tests}")
print(f"Bug detected: {report.is_fault_detected}")
```

### 2.3 Spectrum-Based Fault Localization (SBFL)
```python
from qubitguard.localization.localizer import FaultLocalizer

localizer = FaultLocalizer()
loc_res = localizer.localize_faults(
    mutant_prog, 
    reference_program=prog, 
    actual_fault_index=mutation_record.target_index
)

for ranking in loc_res.rankings:
    print(f"Gate #{ranking.gate_index} ({ranking.gate_name}): Suspicion = {ranking.suspiciousness:.3f}")
```

### 2.4 Automated Program Repair (APR)
```python
from qubitguard.repair.repairer import QuantumProgramRepairer

repairer = QuantumProgramRepairer(max_evaluations=25, seed=42)
repair_report = repairer.repair(mutant_prog, reference_program=prog)

if repair_report.repair_successful:
    print("Repaired! Best patch:", repair_report.best_patch.description)
    print("Repaired circuit:\n", repair_report.best_patch.repaired_program.circuit.draw())
```
