"""QubitGuard - Research Report & Figure Generator.

Reads raw empirical experiment data from experiments/outputs/ and renders:
1. figure_rq1_rq2_detection_by_fault.png
2. figure_rq3_noise_f1.png
3. figure_rq4_localization.png
4. figure_rq5_repair.png
"""

from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

def generate_report_artifacts():
    out_dir = Path("experiments/outputs")
    summary_path = out_dir / "benchmark_summary.json"
    if not summary_path.exists():
        print("Summary file not found. Run benchmark first.")
        return

    with open(summary_path, "r") as f:
        summary = json.load(f)

    # 1. Figure RQ2: Fault Detection Rate by Class
    rq2_data = summary.get("RQ2_detection_by_fault_class", {})
    if rq2_data:
        fault_names = [k.replace("_", " ") for k in rq2_data.keys()]
        rates = [v * 100 for v in rq2_data.values()]
        fig_rq2 = go.Figure(go.Bar(
            x=fault_names,
            y=rates,
            marker_color="#0284c7",
            text=[f"{r:.1f}%" for r in rates],
            textposition="auto"
        ))
        fig_rq2.update_layout(
            title="RQ2: Fault Detection Rate (Mutation Score) across Quantum Fault Classes",
            xaxis_title="Quantum Mutation Operator",
            yaxis_title="Detection Rate (%)",
            yaxis=dict(range=[0, 110]),
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40),
        )
        fig_rq2.write_html(str(out_dir / "figure_rq2_fault_detection.html"))
        print("Saved figure_rq2_fault_detection.html")

    # 2. Figure RQ3: Noise Impact
    rq3_data = summary.get("RQ3_noise_impact", {})
    if rq3_data:
        noise_lvls = [float(k) for k in rq3_data.keys()]
        f1_vals = [rq3_data[k]["f1_score"] for k in rq3_data.keys()]
        prec_vals = [rq3_data[k]["precision"] for k in rq3_data.keys()]
        rec_vals = [rq3_data[k]["recall"] for k in rq3_data.keys()]

        fig_rq3 = go.Figure()
        fig_rq3.add_trace(go.Scatter(x=noise_lvls, y=f1_vals, mode="lines+markers", name="F1-Score", line=dict(color="#2563eb", width=3)))
        fig_rq3.add_trace(go.Scatter(x=noise_lvls, y=prec_vals, mode="lines+markers", name="Precision", line=dict(color="#16a34a", dash="dash")))
        fig_rq3.add_trace(go.Scatter(x=noise_lvls, y=rec_vals, mode="lines+markers", name="Recall", line=dict(color="#dc2626", dash="dot")))

        fig_rq3.update_layout(
            title="RQ3: Detection Robustness across Physical Noise Rates (epsilon)",
            xaxis_title="Depolarizing Error Rate",
            yaxis_title="Score [0.0 - 1.0]",
            yaxis=dict(range=[0, 1.05]),
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40),
        )
        fig_rq3.write_html(str(out_dir / "figure_rq3_noise_sensitivity.html"))
        print("Saved figure_rq3_noise_sensitivity.html")

    # 3. Figure RQ4: Localization Accuracy
    rq4_data = summary.get("RQ4_localization", {})
    if rq4_data:
        categories = ["Top-1 Accuracy", "Top-3 Accuracy"]
        acc_vals = [rq4_data["top_1_accuracy"] * 100, rq4_data["top_3_accuracy"] * 100]
        fig_rq4 = go.Figure(go.Bar(
            x=categories,
            y=acc_vals,
            marker_color=["#4f46e5", "#7c3aed"],
            text=[f"{v:.1f}%" for v in acc_vals],
            textposition="auto"
        ))
        fig_rq4.update_layout(
            title="RQ4: Spectrum-Based Fault Localization Accuracy (Q-SBFL)",
            xaxis_title="Localization Metric",
            yaxis_title="Accuracy (%)",
            yaxis=dict(range=[0, 110]),
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40),
        )
        fig_rq4.write_html(str(out_dir / "figure_rq4_localization.html"))
        print("Saved figure_rq4_localization.html")

    print("All research figures generated successfully.")


if __name__ == "__main__":
    generate_report_artifacts()
