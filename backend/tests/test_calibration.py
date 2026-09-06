import random

from app.analytics.calibration import fit_calibrators


def test_falls_back_to_identity_below_platt_threshold():
    probs = [(0.6, 0.25, 0.15)] * 10
    outcomes = ["HOME"] * 10
    calibrators = fit_calibrators(probs, outcomes)

    assert calibrators.method == "identity"
    assert calibrators.apply(probs[0]) == probs[0]


def test_uses_platt_scaling_with_moderate_sample_size():
    random.seed(1)
    probs = [(random.random(), random.random(), random.random()) for _ in range(50)]
    probs = [tuple(p / sum(row) for p in row) for row in probs]
    outcomes = [random.choice(["HOME", "DRAW", "AWAY"]) for _ in range(50)]

    calibrators = fit_calibrators(probs, outcomes)
    assert calibrators.method == "platt"

    adjusted = calibrators.apply(probs[0])
    assert abs(sum(adjusted) - 1.0) < 1e-6


def test_uses_isotonic_regression_with_enough_samples():
    random.seed(2)
    probs = [(random.random(), random.random(), random.random()) for _ in range(250)]
    probs = [tuple(p / sum(row) for p in row) for row in probs]
    outcomes = [random.choice(["HOME", "DRAW", "AWAY"]) for _ in range(250)]

    calibrators = fit_calibrators(probs, outcomes)
    assert calibrators.method == "isotonic"

    adjusted = calibrators.apply(probs[0])
    assert abs(sum(adjusted) - 1.0) < 1e-6
    assert all(0.0 <= p <= 1.0 for p in adjusted)
