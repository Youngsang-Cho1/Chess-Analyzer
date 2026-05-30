"""Tests for Static Exchange Evaluation and sacrifice detection."""
import chess

from game_analysis import static_exchange_eval, is_sacrifice


def test_free_capture_gains_material():
    # White rook on e1, black pawn on e5, nothing defends e5.
    # Rxe5 wins a clean pawn.
    board = chess.Board("4k3/8/8/4p3/8/8/8/4R1K1 w - - 0 1")
    move = chess.Move.from_uci("e1e5")
    assert static_exchange_eval(board, move) == 1
    assert not is_sacrifice(board, move)


def test_defended_capture_even_trade():
    # White pawn d4 takes black pawn e5, which is defended by a pawn on d6.
    # Pawn for pawn: net 0.
    board = chess.Board("4k3/8/3p4/4p3/3P4/8/8/4K3 w - - 0 1")
    move = chess.Move.from_uci("d4e5")
    assert static_exchange_eval(board, move) == 0
    assert not is_sacrifice(board, move)


def test_losing_capture_is_sacrifice():
    # White queen takes a pawn on e5 that is defended by a pawn on d6.
    # Win 1 (pawn) then lose the queen (9): net -8. Clear sacrifice.
    board = chess.Board("4k3/8/3p4/4p3/8/8/8/3QK3 w - - 0 1")
    move = chess.Move.from_uci("d1e5")  # Qxe5??
    see = static_exchange_eval(board, move)
    assert see <= -2
    assert is_sacrifice(board, move)


def test_quiet_move_not_capture_not_sacrifice():
    board = chess.Board()
    move = chess.Move.from_uci("g1f3")  # Nf3, no capture
    assert static_exchange_eval(board, move) == 0
    assert not is_sacrifice(board, move)