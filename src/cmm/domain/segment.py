from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Segment:
    id: Any
    name: Optional[str]
    geometry: Any

    # Base method to assign metrics
    def set_metrics(self, metrics_name: str, value: float) -> None:
        raise NotImplementedError

@dataclass
class CyclabilitySegment(Segment):

    bike_infrastructure: str
    oneway: str
    
    maxspeed: Optional[str]
    surface: str
    lighting: str
    highway: str

    cyclability_metrics: Optional[float] = None

    # Add method to assign metrics for cyclability
    def set_metrics(self, metrics_name: str, value: float) -> None:
        
        # Only allow cyclability metrics for this class
        if metrics_name != "cyclability":
            raise ValueError("Invalid metrics for CyclabilitySegment")
        
        # Set metrics
        self.cyclability_metrics = value