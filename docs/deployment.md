# QubitGuard: Production & Cloud Deployment Guide

This guide details how to deploy QubitGuard as a publicly accessible, interactive quantum research dashboard and documentation portal.

---

## 1. Verified Live Deployments

### A. Live Research Documentation Portal (GitHub Pages)
- **Status**: Active & Verified
- **Public URL**: [https://sudipto-swe.github.io/QubitGuard/](https://sudipto-swe.github.io/QubitGuard/)
- **Hosting**: GitHub Pages via `main` branch (`/docs` root).
- **Features**: Research report, formal research questions, quantum fault taxonomy, Q-SBFL formulas, and interactive navigation.

### B. Public Interactive Web Demo (Streamlit Community Cloud)
- **Deployment Platform**: Streamlit Community Cloud ([share.streamlit.io](https://share.streamlit.io))
- **Source Repository**: `https://github.com/sudipto-swe/QubitGuard`
- **Branch**: `main`
- **Main Application File**: `app/app.py`
- **Default Port**: 8501
- **Simulation Engine**: Local Qiskit Aer (No paid quantum hardware accounts required)

---

## 2. Streamlit Community Cloud Deployment Steps

Streamlit Community Cloud deploys Python apps directly from GitHub repositories with zero server administration:

1. **Sign In**: Navigate to [share.streamlit.io](https://share.streamlit.io) and authenticate using your GitHub account (`sudipto-swe`).
2. **Create New App**:
   - Click the **"New app"** button.
   - **Repository**: Select `sudipto-swe/QubitGuard`.
   - **Branch**: `main`.
   - **Main file path**: `app/app.py`.
   - **App URL**: Optionally configure a custom subdomain (e.g. `qubitguard.streamlit.app`).
3. **Advanced Settings (Optional)**:
   - Python Version: Select `3.11` or `3.12`.
   - Environment Variables (Secrets): To optionally enable real hardware runs, insert:
     ```toml
     IBMQ_API_TOKEN = "your_token_here"
     ```
4. **Click Deploy**:
   Streamlit Cloud automatically provisions the container, installs dependencies from `pyproject.toml` and `requirements.txt`, applies theme styling from `.streamlit/config.toml`, and exposes the live URL.

---

## 3. Local Deployment & Container Running

To run the full stack locally:
```bash
# Clone
git clone https://github.com/sudipto-swe/QubitGuard.git
cd QubitGuard

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install --no-build-isolation -e .

# Launch local server
streamlit run app/app.py --server.port 8501
```
