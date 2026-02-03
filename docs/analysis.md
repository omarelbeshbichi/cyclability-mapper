# Analysis Modules

The analysis module is experimental and mainly implemented to evaluate sensitivity and to explore the `networkx` package for graph analysis.

Note that for sensitivity analysis, figures have been added to frontend endpoints - see `frontend` documentation.

## Graph Analysis

This analysis evaluates the city street network as graph and identifies which segments provide the largest cyclability improvement given a budget in km. The analysis makes use of a large number of assumptions: the "value" of a segment is determined by first calculating the "edge betweenness centrality", i.e., an indication of how often each segment appears in shortest paths given two arbitrary A-B nodes. Edge value is determined as:

$$
\text{segment\_value} = \frac{\text{segment\_betweenness}}{\text{cyclability\_score}}
$$

A "ratio", describing the value per unit length, is also defined as:

$$
\text{ratio} = \frac{\text{segment\_value}}{\text{effective\_length}}
$$

Effective length is the segment length with a lower limit on minimum length:

$$
\text{effective\_length} = \max(\text{length\_km}, 0.05)
$$

This is done to exclude very short segments from the exercise. Moreover, sampling is used to reduce computational effort.

#### `graph/build.py`
Builds a `networkx` Graph from a GeoDataFrame of street segments.

Each edge represents a street segment with attributes:
  - `length` (meters)
  - `score` (cyclability score)
  - `weight` (cycling cost = length/score)
  - `osm_id` (OSM ID)

#### `graph/metrics.py`
**`city_cyclability(G, sources)`**:  
Approximates average weighted shortest path length across sampled nodes, giving an indication of city cyclability. 

**`best_edges_under_budget(G, budget_km)`**:
Main graph analysis algorithm. It computes the edge betweenness centrality for each segment, calculates an "edge value" based on centrality and current score, and selects the segments with the highest value-to-length ratio until the budget is exhausted. 


## Sensitivity Analysis

This analysis evaluates the effect of changing cyclability metric weights on overall city metrics. Note that weight changes are normalized to ensure total weight sum remains 1.

#### `analysis/sensitivity.py`
**`sensitivity_single_weight_sweep`**: This function performs a sweep over a single feature group’s weight, computing the total city metric at each step.