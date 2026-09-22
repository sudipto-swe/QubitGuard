# QubitGuard Installation Guide

## 1. Prerequisites
- Linux / macOS / Windows (WSL recommended on Windows)
- Python 3.10, 3.11, or 3.12
- Git

## 2. Standard Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/sudiptob1/QubitGuard.git
cd QubitGuard
```

### Step 2: Virtual Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Package Installation
```bash
pip install --upgrade pip setuptools wheel
pip install --no-build-isolation -e .
```

## 3. Verify Installation
Run the automated test suite:
```bash
pytest -v tests/
```
Verify CLI access:
```bash
qubitguard benchmarks
```

## 4. Optional IBM Quantum Hardware Backend
To configure optional physical quantum hardware execution:
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Insert your IBM Quantum API token:
   ```ini
   IBMQ_API_TOKEN=your_token_here
   ```
*Note: All core features, benchmarks, fault localization, and automated repairs run completely offline using Qiskit Aer simulation without requiring an IBM Quantum account.*
