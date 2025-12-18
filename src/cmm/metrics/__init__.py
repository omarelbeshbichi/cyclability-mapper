"""Metrics utilities

This package exposes functionalities for computing quality metrics.
For now, only a simple implementation for computing the cyclability metrics is included for 
initial testing.
"""

from .cyclability import compute_cyclability_metrics

__all__ = [compute_cyclability_metrics]