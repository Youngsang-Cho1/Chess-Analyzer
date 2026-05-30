"""Tests for the ML risk label mapping (ml_features.label_for)."""
from ml_features import label_for, LABEL_NOISE_CAP, BAD_CLASSES


def test_good_classes_are_negative_label():
    for cls in ("Best", "Excellent", "Good", "Book", "Brilliant", "Great"):
        assert label_for(cls) == 0


def test_bad_classes_are_positive_label():
    for cls in BAD_CLASSES:  # Blunder, Mistake, Miss
        assert label_for(cls, my_cp=0) == 1


def test_none_classification_is_negative():
    assert label_for(None) == 0


def test_bad_move_in_decided_position_is_dropped():
    # A "blunder" when already winning/losing by > cap is noise -> drop (None)
    assert label_for("Blunder", my_cp=LABEL_NOISE_CAP + 1) is None
    assert label_for("Blunder", my_cp=-(LABEL_NOISE_CAP + 1)) is None


def test_bad_move_at_cap_boundary_is_kept():
    # exactly at the cap is still kept (strict > in the impl)
    assert label_for("Blunder", my_cp=LABEL_NOISE_CAP) == 1


def test_good_move_never_dropped_even_in_decided_position():
    assert label_for("Best", my_cp=5000) == 0