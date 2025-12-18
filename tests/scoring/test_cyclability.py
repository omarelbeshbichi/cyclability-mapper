from cmm import metricscompute_cyclability_metrics

def test_compute_cyclability_metrics():
    assert metricscompute_cyclability_metrics(1, 1, 1, 1, 1) == 1
    assert metricscompute_cyclability_metrics(0, 0, 0, 0, 0) == 0
    assert metricscompute_cyclability_metrics(0.5, 0.5, 0.5, 0.5, 0.5) == 0.5
    assert metricscompute_cyclability_metrics(1, 0, 0, 0, 0) == 0.3
    assert metricscompute_cyclability_metrics(0, 0, 1, 0, 0) == 0.2
    assert metricscompute_cyclability_metrics(0, 0, 0, 0, 1) == 0.1