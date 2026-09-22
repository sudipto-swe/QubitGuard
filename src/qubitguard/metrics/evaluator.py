"""QubitGuard - Experimental Evaluation Metrics."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class DetectionMetrics:
    """Standardized detection metrics."""
    total_mutants: int
    detected_mutants: int
    mutation_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    f1_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_mutants": self.total_mutants,
            "detected_mutants": self.detected_mutants,
            "mutation_score": round(self.mutation_score, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
        }

    @classmethod
    def compute(cls, y_true: List[int], y_pred: List[int]) -> DetectionMetrics:
        """Computes metrics from binary ground truth (1=mutant, 0=clean) and predictions."""
        yt = np.array(y_true)
        yp = np.array(y_pred)

        tp = int(np.sum((yt == 1) & (yp == 1)))
        fp = int(np.sum((yt == 0) & (yp == 1)))
        fn = int(np.sum((yt == 1) & (yp == 0)))
        tn = int(np.sum((yt == 0) & (yp == 0)))

        total_m = int(np.sum(yt == 1))
        det_m = tp
        ms = (det_m / total_m) if total_m > 0 else 0.0

        prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        return cls(
            total_mutants=total_m,
            detected_mutants=det_m,
            mutation_score=ms,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            precision=prec,
            recall=rec,
            f1_score=f1,
        )


@dataclass
class LocalizationMetrics:
    """Standardized fault localization metrics across multiple test executions."""
    total_evaluations: int
    top_1_hits: int
    top_3_hits: int
    top_5_hits: int
    mean_first_rank: float
    mean_exam_score: float

    @property
    def top_1_accuracy(self) -> float:
        return self.top_1_hits / self.total_evaluations if self.total_evaluations > 0 else 0.0

    @property
    def top_3_accuracy(self) -> float:
        return self.top_3_hits / self.total_evaluations if self.total_evaluations > 0 else 0.0

    @property
    def top_5_accuracy(self) -> float:
        return self.top_5_hits / self.total_evaluations if self.total_evaluations > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evaluations": self.total_evaluations,
            "top_1_accuracy": round(self.top_1_accuracy, 4),
            "top_3_accuracy": round(self.top_3_accuracy, 4),
            "top_5_accuracy": round(self.top_5_accuracy, 4),
            "mean_first_rank": round(self.mean_first_rank, 2),
            "mean_exam_score": round(self.mean_exam_score, 4),
        }
