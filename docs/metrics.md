# Cyclability Metrics Model

This project implements a simplified cyclability metrics model to quantify cycling conditions for each segment of a city city network.

Let a city be represented by a set of road segments:

$${s_1, s_2, ..., s_N}$$

Each segment, $s_i$, is defined by:
- $L_i$: segment length in meters.
- $x_i = {x_{i,f}}$: raw features values from Overpass API
- $m_i = {m_{i,f}}$: missingness indicators

where:

$$
\begin{cases} 
{m_{i,f}} = 0 & \text{if data available} \\
{m_{i,f}} = 1 & \text{otherwise}
\end{cases}
$$

The features currently considered are:
- `bike_infrastructure`
- `surface`
- `maxspeed`
- `lighting`

Note that for `bike_infrastructure` it is always assumed that missing data represents missing infrastructure (so ${m_{i,{bi}}}$ is always zero).

Raw features represent different domains and are not directly comparable. As a consequence, each feature $f$ is mapped to a normalized score $[0, 1]$ using a predefined transformation table stored in YAML format:

$$
\overline{x_{i,f}} = \begin{cases} 
N_f({x_{i,f}}) & \text{if data available} \\
\mu_f & \text{otherwise} 
\end{cases}
$$

where:
- $N_f$ is a normalization function specific to each feature
- $\overline{x_{i,f}}$ is the normalized feature score
  - 1: highest score
  - 0: lowest score
- $\mu_f$ is a penalty value (default: $0.5$) used to account conservatively for missing data. It is defined in the same YAML transformation table. To be noted that the contribution of this assumed value to the score is quantified by the feature uncertainty $C_f$ and, in aggregate, to the total city uncertainty $U$ (see below).

For feature `maxspeed`, if `bike_infrastructure` is available and of high quality (structurally protected), the associated score is automatically considered maximum, 1.0, as it is assumed that traffic is not interfering with the cycleway:
$$
\overline{x_{i,maxspeed}} = \begin{cases} 
1.0 & \text{if protected} \\ 
\mu_f & \text{if missing and unconstrained} \\ 
N_{maxspeed}({x_{i,{maxspeed}}}) & \text{otherwise}
\end{cases}
$$

Normalization of features is at this stage based on domain judgment only.


## Feature Grouping and Weights

Features are organized in groups:
1) Infrastructure
   1) `bike_infrastructure`
2) Physical
   1) `surface`
   2) `lighting`
3) Traffic
   1) `maxspeed`
4) Regulation
   1) `oneway`

Each group has a weight, and each feature inside a group has a relative weight.

- groups $g$ $∈$ G
- features $f$ $∈$ $g$

$$
\displaystyle \sum_{\text{$g$ $∈$ $g$} } w_g = 1
$$

$$
\displaystyle \sum_{\text{$f$ $∈$ $g$} } w_{f|g} = 1
$$

Therefore, the effective weight of each feature $f$ is:

$$
W_f = w_{f|g} * w_g
$$

The weight structure is stored in a dedicated YAML file.


# Segment Cyclability Score

For each segment $s_i$, the cyclability score is computed as a weighted linear combination of normalized features:

$$
S_i = \sum_{f}W_f*\overline{x_{i,f}}
$$

The score is fully deterministic given the segment inputs and the conservative assumptions provided by $\mu_f$.


# Aggregated Cyclability Score

The total network length is:

$$
L_{tot} =  \displaystyle \sum_{i=1}^{N} L_i
$$

The city-level cyclability metric is defined as a length-weighted average of segment scores:

$$
S_{city} = \frac{1}{L_{tot}}\displaystyle \sum_{i=1}^{N}S_i L_i
$$

Therefore, longer segments contribute more to aggregate metrics. Network effects are not considered at this stage (topology, etc.).


# Missing Data

For each feature $f$, the associated length-weighted missing fraction can be defined as:

$$
U_f = \frac{1}{L_{tot}}\displaystyle \sum_{i=1}^{N}m_{i,f} L_i
$$

This quantity quantifies the part of the city network that misses information about feature $f$ (observability).


## Feature Uncertainty

To relate the missing data to the metrics themselves, $U_f$ is weighted by feature importance (that is, by using weight $W_f$):

$$
C_f = U_f*W_f
$$

C_f is the uncertainty contribution of feature $f$.


## Total City Uncertainty

Total uncertainty of the city is then computed as:

$$
U = \displaystyle \sum_{f}C_f
$$


# Reported Outputs

For a city, the model produces and stores the following quantities in PostGIS:

1) Segment-level cyclability score set, ${S_{i,city}}$
2) Total cyclability score, $S_{city}$
3) Uncertainty contributions for each feature, ${C_f}$
4) Total cyclability uncertainty, $U_{city}$

For example:
```
Cyclability: 0.58
Cyclability uncertainty: 0.22
```

Means: 22% of the cyclability score is related to segments where relevant input data is missing, given the currently used model weights.



# Missing data assumptions

As shown, I have tracked missing data for `maxspeed`, `surface`, and `lighting` - which are used to compute the cyclability index with `bike_infrastructure`. 

Missing data is handled in this project by assuming a default neutral quality score of 0.5 ($\mu_f$). A value of 0.0 may also be assumed depending on the analysis scope, but for now, it is not addressed.
