"""QubitGuard - Visualization and Scientific Plotting Utilities."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def create_distribution_comparison_chart(
    ideal_probs: Dict[str, float],
    measured_probs: Dict[str, float],
    title: str = "Probability Distribution Comparison"
) -> go.Figure:
    """Creates a side-by-side grouped bar chart comparing two probability distributions."""
    all_keys = sorted(set(ideal_probs.keys()).union(set(measured_probs.keys())))
    p_vals = [ideal_probs.get(k, 0.0) for k in all_keys]
    q_vals = [measured_probs.get(k, 0.0) for k in all_keys]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=all_keys, y=p_vals, name="Baseline / Reference", marker_color="#2563eb"))
    fig.add_trace(go.Bar(x=all_keys, y=q_vals, name="Candidate / Mutant", marker_color="#dc2626"))

    fig.update_layout(
        title=title,
        xaxis_title="Computational Basis State",
        yaxis_title="Probability",
        barmode="group",
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def create_localization_ranking_chart(
    rankings: List[Dict[str, Any]],
    actual_fault_idx: Optional[int] = None
) -> go.Figure:
    """Renders ranked gate suspiciousness bar plot with ground-truth highlighting."""
    if not rankings:
        return go.Figure()

    df = pd.DataFrame(rankings)
    labels = [f"#{r['gate_index']} ({r['gate_name']})" for r in rankings]
    colors = []
    for r in rankings:
        if actual_fault_idx is not None and r['gate_index'] == actual_fault_idx:
            colors.append("#dc2626")  # Red for actual fault
        elif r['suspiciousness'] > 0.6:
            colors.append("#ea580c")  # Orange for high suspicion
        elif r['suspiciousness'] > 0.3:
            colors.append("#eab308")  # Yellow
        else:
            colors.append("#94a3b8")  # Slate gray

    fig = go.Figure(go.Bar(
        x=labels,
        y=[r['suspiciousness'] for r in rankings],
        marker_color=colors,
        text=[f"{r['suspiciousness']:.2f}" for r in rankings],
        textposition="auto",
    ))

    fig.update_layout(
        title="Gate Suspiciousness Ranking (SBFL)",
        xaxis_title="Circuit Gate Operation",
        yaxis_title="Suspiciousness Score [0.0 - 1.0]",
        template="plotly_white",
        yaxis=dict(range=[0, 1.05]),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def create_detection_rate_by_fault_chart(fault_metrics: Dict[str, float]) -> go.Figure:
    """Bar chart of detection rate stratified across fault classes (RQ2)."""
    fault_names = list(fault_metrics.keys())
    rates = list(fault_metrics.values())

    fig = go.Figure(go.Bar(
        x=fault_names,
        y=rates,
        marker_color="#0d9488",
        text=[f"{r*100:.1f}%" for r in rates],
        textposition="auto"
    ))
    fig.update_layout(
        title="Fault Detection Rate by Mutation Operator (RQ2)",
        xaxis_title="Fault Injection Operator",
        yaxis_title="Detection Rate (Mutation Score)",
        yaxis=dict(range=[0, 1.1]),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def create_noise_impact_chart(noise_levels: List[float], f1_scores: List[float], precision: List[float], recall: List[float]) -> go.Figure:
    """Line chart tracking F1, Precision, and Recall under increasing physical noise (RQ3)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=noise_levels, y=f1_scores, mode="lines+markers", name="F1-Score", line=dict(color="#2563eb", width=3)))
    fig.add_trace(go.Scatter(x=noise_levels, y=precision, mode="lines+markers", name="Precision", line=dict(color="#16a34a", dash="dash")))
    fig.add_trace(go.Scatter(x=noise_levels, y=recall, mode="lines+markers", name="Recall", line=dict(color="#dc2626", dash="dot")))

    fig.update_layout(
        title="Testing Sensitivity vs. Physical Noise Rate (RQ3)",
        xaxis_title="Depolarizing Noise Rate (epsilon)",
        yaxis_title="Metric Score",
        yaxis=dict(range=[0, 1.05]),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig
