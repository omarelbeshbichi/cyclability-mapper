"""Metrics utilities

This package exposes functionalities for computing quality metrics.
For now, only a simple implementation for computing the cyclability metrics is included for 
initial testing.
"""

from .compute_metrics import compute_metrics_score_from_segment

__all__ = [compute_metrics_score_from_segment]