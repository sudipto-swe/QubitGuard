"""QubitGuard - Statistical Divergence and Fault Detection Engine."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import math
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import chisquare
from qubitguard.execution.executor import ExecutionResult


@dataclass
class DetectionResult:
    """Quantitative outcome of a fault detection assertion comparing two executions."""
    is_faulty: bool
    tvd: float                      # Total Variation Distance
    js_divergence: float            # Jensen-Shannon Divergence
    chi2_stat: float                # Chi-Square statistic
    p_value: float                  # Chi-Square p-value
    bhattacharyya_distance: float   # Bhattacharyya distance
    threshold_used: float
    confidence_level: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_faulty": bool(self.is_faulty),
            "tvd": round(float(self.tvd), 4),
            "js_divergence": round(float(self.js_divergence), 4),
            "chi2_stat": round(float(self.chi2_stat), 4),
            "p_value": round(float(self.p_value), 6),
            "bhattacharyya_distance": round(float(self.bhattacharyya_distance), 4),
            "threshold_used": round(float(self.threshold_used), 4),
        }


class FaultDetector:
    """Compares probability distributions using quantum-appropriate statistical divergence measures."""

    def __init__(self, tvd_threshold: float = 0.12, alpha: float = 0.05):
        self.tvd_threshold = tvd_threshold
        self.alpha = alpha

    @staticmethod
    def _align_distributions(p_dict: Dict[str, float], q_dict: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
        """Aligns two sparse probability dictionaries over the joint support."""
        all_keys = sorted(set(p_dict.keys()).union(set(q_dict.keys())))
        p_vec = np.array([p_dict.get(k, 0.0) for k in all_keys], dtype=float)
        q_vec = np.array([q_dict.get(k, 0.0) for k in all_keys], dtype=float)
        # Normalize in case of floating roundoff
        if np.sum(p_vec) > 0:
            p_vec = p_vec / np.sum(p_vec)
        if np.sum(q_vec) > 0:
            q_vec = q_vec / np.sum(q_vec)
        return p_vec, q_vec

    @classmethod
    def calculate_tvd(cls, p_dict: Dict[str, float], q_dict: Dict[str, float]) -> float:
        """Computes Total Variation Distance: TVD(P, Q) = 0.5 * sum |P(x) - Q(x)|."""
        p_vec, q_vec = cls._align_distributions(p_dict, q_dict)
        return float(0.5 * np.sum(np.abs(p_vec - q_vec)))

    @classmethod
    def calculate_bhattacharyya(cls, p_dict: Dict[str, float], q_dict: Dict[str, float]) -> float:
        """Computes Bhattacharyya distance: -ln(BC(P, Q))."""
        p_vec, q_vec = cls._align_distributions(p_dict, q_dict)
        bc = float(np.sum(np.sqrt(p_vec * q_vec)))
        bc = max(1e-12, min(1.0, bc))
        return float(-math.log(bc))

    @classmethod
    def calculate_js_divergence(cls, p_dict: Dict[str, float], q_dict: Dict[str, float]) -> float:
        """Computes Jensen-Shannon divergence (base 2)."""
        p_vec, q_vec = cls._align_distributions(p_dict, q_dict)
        # scipy jensenshannon returns the square root (distance)
        js_dist = jensenshannon(p_vec, q_vec, base=2.0)
        return float(js_dist ** 2)

    def evaluate(
        self,
        reference: ExecutionResult,
        candidate: ExecutionResult,
        custom_threshold: float | None = None
    ) -> DetectionResult:
        """Compares candidate run against reference baseline to assert whether candidate is faulty."""
        p_dict = reference.probabilities
        q_dict = candidate.probabilities

        tvd = self.calculate_tvd(p_dict, q_dict)
        bhatt = self.calculate_bhattacharyya(p_dict, q_dict)
        js_div = self.calculate_js_divergence(p_dict, q_dict)

        # Chi-Square Test on observed counts
        p_vec, q_vec = self._align_distributions(p_dict, q_dict)
        # Expected counts under candidate shots
        exp_counts = p_vec * candidate.shots
        obs_counts = q_vec * candidate.shots

        # Avoid zero division in chi-squared test by adding small epsilon
        exp_counts = np.where(exp_counts < 1.0, 1.0, exp_counts)
        obs_counts = np.where(obs_counts < 0.0, 0.0, obs_counts)
        
        try:
            chi2_stat, p_val = chisquare(f_obs=obs_counts, f_exp=exp_counts)
            if np.isnan(p_val):
                p_val = 1.0
                chi2_stat = 0.0
        except Exception:
            p_val = 1.0
            chi2_stat = 0.0

        threshold = custom_threshold if custom_threshold is not None else self.tvd_threshold
        # Candidate is classified as faulty if TVD exceeds threshold OR chi-square p-value is extremely small with significant TVD
        is_faulty = (tvd > threshold) or (p_val < self.alpha and tvd > 0.06)

        return DetectionResult(
            is_faulty=bool(is_faulty),
            tvd=float(tvd),
            js_divergence=float(js_div),
            chi2_stat=float(chi2_stat),
            p_value=float(p_val),
            bhattacharyya_distance=float(bhatt),
            threshold_used=float(threshold),
        )
