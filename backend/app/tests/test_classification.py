"""Unit tests for move classification — the core of the analyzer.

These pin down every branch of `classify_move`, the win%-loss tiers, and the
Miss / Brilliant overrides. If a threshold in game_analysis.py is changed,
the affected case here breaks loudly instead of silently shifting labels.
"""
import chess
import pytest

from game_analysis import (
    classify_by_win_diff,
    classify_move,
)


# --- helper -----------------------------------------------------------------
def make(**overrides):
    """Build classify_move kwargs from a sane 'neutral best move' baseline,
    overriding only the fields a given test cares about."""
    base = dict(
        move_uci="g1f3",
        best_move_uci="g1f3",   # by default the move IS the best move
        is_only_legal=False,
        is_book=False,
        win_diff=0.0,
        cp_loss=0,
        my_cp=20,
        best_cp=20,
        second_cp=None,
        my_mate_in=None,
        best_mate_in=None,
        is_white=True,
        is_sac=False,
        prev_classification=None,
        prev_cp=0,
    )
    base.update(overrides)
    return base


def classify(**overrides):
    return classify_move(**make(**overrides))


# --- win%-loss tier table ---------------------------------------------------
@pytest.mark.parametrize(
    "win_diff,expected",
    [
        (0, "Excellent"),
        (2, "Excellent"),    # boundary THRESH_EXCELLENT
        (2.1, "Good"),
        (5, "Good"),         # boundary THRESH_GOOD
        (5.1, "Inaccuracy"),
        (10, "Inaccuracy"),  # boundary THRESH_INACCURACY
        (10.1, "Mistake"),
        (20, "Mistake"),     # boundary THRESH_MISTAKE
        (20.1, "Blunder"),
        (60, "Blunder"),
    ],
)
def test_win_diff_tiers(win_diff, expected):
    assert classify_by_win_diff(win_diff) == expected


# --- Book / Best family -----------------------------------------------------
def test_book_move_wins_over_everything():
    # in_book_line=True overrides even a would-be blunder eval
    assert classify(is_book=True, win_diff=60, cp_loss=900) == "Book"


def test_best_move():
    assert classify(move_uci="g1f3", best_move_uci="g1f3") == "Best"


def test_forced_when_only_legal_move():
    assert classify(is_only_legal=True) == "Forced"


def test_great_move_big_gap_balanced():
    # best is much better than 2nd-best, position roughly balanced
    assert classify(best_cp=300, second_cp=-150, my_cp=300) == "Great"


def test_not_great_when_gap_too_small():
    # gap below GREAT_SECOND_GAP_MIN (400) -> stays Best
    assert classify(best_cp=300, second_cp=100, my_cp=300) == "Best"


def test_not_great_when_already_winning_big():
    # |my_cp| beyond GREAT_MY_CP_LIMIT (500) -> not "Great", just Best
    assert classify(best_cp=800, second_cp=200, my_cp=800) == "Best"


# --- non-best -> tier -------------------------------------------------------
def test_non_best_blunder():
    assert (
        classify(move_uci="a2a3", best_move_uci="g1f3", win_diff=35, cp_loss=600)
        == "Blunder"
    )


def test_non_best_inaccuracy():
    assert (
        classify(move_uci="a2a3", best_move_uci="g1f3", win_diff=8, cp_loss=80)
        == "Inaccuracy"
    )


# --- Miss override ----------------------------------------------------------
def test_miss_failed_to_punish():
    # opponent just blundered, punishing line clearly winning, we left material
    assert (
        classify(
            move_uci="a2a3",
            best_move_uci="d1h5",
            win_diff=12,
            cp_loss=200,
            best_cp=250,
            my_cp=50,
            prev_classification="Blunder",
        )
        == "Miss"
    )


def test_miss_fires_even_from_inaccuracy_tier():
    # win_diff in the Inaccuracy tier (<=10) still becomes Miss when we
    # failed to punish — the override is independent of the win%-loss tier.
    assert (
        classify(
            move_uci="a2a3",
            best_move_uci="d1h5",
            win_diff=8,
            cp_loss=200,
            best_cp=250,
            my_cp=50,
            prev_classification="Mistake",
        )
        == "Miss"
    )


def test_miss_does_not_downgrade_blunder():
    # Even after opp blunder, a real Blunder stays Blunder (Miss must not soften it)
    assert (
        classify(
            move_uci="a2a3",
            best_move_uci="d1h5",
            win_diff=40,
            cp_loss=600,
            best_cp=700,
            my_cp=-200,
            prev_classification="Blunder",
        )
        == "Blunder"
    )


def test_no_miss_when_prev_move_was_fine():
    # prev was a good move -> failed-to-punish Miss should NOT fire.
    # win_diff=12 is past THRESH_INACCURACY (10), so the tier is Mistake;
    # the point is that it stays a plain tier label, not "Miss".
    assert (
        classify(
            move_uci="a2a3",
            best_move_uci="d1h5",
            win_diff=12,
            cp_loss=200,
            best_cp=250,
            my_cp=50,
            prev_classification="Best",
        )
        == "Mistake"
    )


def test_no_miss_when_punishing_line_not_winning_enough():
    # best_cp below MISS_MIN_BEST_CP (150) -> no Miss, just the tier.
    # win_diff=12 lands in the Mistake tier (> 10).
    assert (
        classify(
            move_uci="a2a3",
            best_move_uci="d1h5",
            win_diff=12,
            cp_loss=200,
            best_cp=100,
            my_cp=-100,
            prev_classification="Blunder",
        )
        == "Mistake"
    )


# --- Brilliant override -----------------------------------------------------
def test_brilliant_sacrifice_in_balanced_position():
    assert (
        classify(
            move_uci="c1h6",
            best_move_uci="c1h6",
            is_sac=True,
            cp_loss=0,
            my_cp=80,
            prev_cp=50,
        )
        == "Brilliant"
    )


def test_no_brilliant_when_position_already_lost():
    # prev_cp below BRILLIANT_PREV_CP_MIN (-150): a sac in a lost game is not brilliant
    assert (
        classify(
            move_uci="c1h6",
            best_move_uci="c1h6",
            is_sac=True,
            cp_loss=0,
            my_cp=-200,
            prev_cp=-300,
        )
        != "Brilliant"
    )


def test_no_brilliant_when_not_a_sacrifice():
    assert classify(is_sac=False, my_cp=80, prev_cp=50) != "Brilliant"