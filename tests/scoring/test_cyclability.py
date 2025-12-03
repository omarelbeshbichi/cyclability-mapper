from cmm import compute_cyclability_score

def test_compute_cyclability_score():
    assert compute_cyclability_score(1, 1, 1, 1, 1) == 1
    assert compute_cyclability_score(0, 0, 0, 0, 0) == 0
    assert compute_cyclability_score(0.5, 0.5, 0.5, 0.5, 0.5) == 0.5
    assert compute_cyclability_score(1, 0, 0, 0, 0) == 0.3
    assert compute_cyclability_score(0, 0, 1, 0, 0) == 0.2
    assert compute_cyclability_score(0, 0, 0, 0, 1) == 0.1