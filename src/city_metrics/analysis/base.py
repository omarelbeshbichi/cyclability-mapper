from dataclasses import dataclass
import numpy as np

@dataclass
class AnalysisResult:
    values: np.ndarray
    description: str