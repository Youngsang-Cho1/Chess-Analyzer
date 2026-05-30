"""Tests for mate-aware win probability.

The ±~19990 cp mate encoding saturates the sigmoid near 99% for any mate
distance, which collapses win_diff and hides missed/allowed mates. These pin
the 0/100 endpoint behaviour and the perspective handling.
"""
from game_analysis import _win_prob_with_mate, get_win_prob


def test_no_mate_falls_back_to_sigmoid():
    assert _win_prob_with_mate(0, None, True) == get_win_prob(0)
    assert _win_prob_with_mate(300, None, False) == get_win_prob(300)


def test_white_user_white_mates_is_100():
    assert _win_prob_with_mate(19970, 3, is_white=True) == 100.0


def test_white_user_black_mates_is_0():
    # mate_in_white negative => Black mates; user is White => user is mated
    assert _win_prob_with_mate(-19980, -2, is_white=True) == 0.0


def test_black_user_black_mates_is_100():
    # mate_in_white negative => Black mates; user is Black => user mates
    assert _win_prob_with_mate(19980, -2, is_white=False) == 100.0


def test_black_user_white_mates_is_0():
    assert _win_prob_with_mate(-19970, 3, is_white=False) == 0.0


def test_missed_mate_opens_up_win_diff():
    # best move had a forced mate (100%); the move played is merely +500cp.
    # Previously both saturated near 99% and win_diff ~ 0; now it is sizable.
    best = _win_prob_with_mate(19970, 3, is_white=True)
    played = _win_prob_with_mate(500, None, is_white=True)
    assert best - played > 5.0