# Contributing to QubitGuard

Thank you for your interest in contributing to **QubitGuard**! We welcome contributions from researchers, software engineers, and quantum physicists.

## Development Workflow
1. **Fork and Clone**:
   ```bash
   git clone https://github.com/sudiptob1/QubitGuard.git
   cd QubitGuard
   ```
2. **Setup Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --no-build-isolation -e .
   ```
3. **Run Test Suite**:
   ```bash
   pytest -v tests/
   ```
4. **Code Quality**:
   - Follow PEP 8 guidelines.
   - Maintain static typing (`typing`, `dataclasses`).
   - Add unit tests for any new mutation operators or repair heuristics.

## Pull Request Guidelines
- Provide a clear explanation of what problem your PR solves.
- Verify that all tests pass cleanly without regressions.
- If introducing an empirical claim or new benchmark, provide reproducible seed configurations.
