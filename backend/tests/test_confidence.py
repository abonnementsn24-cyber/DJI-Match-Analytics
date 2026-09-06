from app.analytics.confidence import ConfidenceInputs, compute_confidence
from app.models.enums import Confidence


def test_insufficient_data_below_threshold():
    result = compute_confidence(
        ConfidenceInputs(probabilities=(0.5, 0.3, 0.2), matches_played_min=2, model_home_win_probabilities=[0.5])
    )
    assert result == Confidence.INSUFFICIENT_DATA


def test_clear_favourite_lots_of_data_agreement_is_high_confidence():
    result = compute_confidence(
        ConfidenceInputs(
            probabilities=(0.75, 0.15, 0.10),
            matches_played_min=40,
            model_home_win_probabilities=[0.74, 0.76, 0.75, 0.77],
        )
    )
    assert result in (Confidence.HIGH, Confidence.VERY_HIGH)


def test_close_call_little_data_disagreement_is_low_confidence():
    result = compute_confidence(
        ConfidenceInputs(
            probabilities=(0.36, 0.34, 0.30),
            matches_played_min=6,
            model_home_win_probabilities=[0.2, 0.5, 0.36, 0.6],
        )
    )
    assert result in (Confidence.VERY_LOW, Confidence.LOW, Confidence.MEDIUM)


def test_calibration_error_shifts_composite_score():
    inputs_good_calibration = ConfidenceInputs(
        probabilities=(0.6, 0.25, 0.15),
        matches_played_min=30,
        model_home_win_probabilities=[0.6, 0.6],
        calibration_error=0.02,
    )
    inputs_bad_calibration = ConfidenceInputs(
        probabilities=(0.6, 0.25, 0.15),
        matches_played_min=30,
        model_home_win_probabilities=[0.6, 0.6],
        calibration_error=0.3,
    )
    levels = list(Confidence)
    assert levels.index(compute_confidence(inputs_good_calibration)) >= levels.index(
        compute_confidence(inputs_bad_calibration)
    )
