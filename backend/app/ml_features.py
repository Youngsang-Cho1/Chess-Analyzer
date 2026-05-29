"""
Feature extraction for the blunder-risk classifier.

For each move, we describe the BOARD STATE BEFORE THE MOVE WAS PLAYED, plus
some game-level context. The target is whether the user's next move ends up
being a bad move (Blunder / Mistake / Miss).

We replay each game's PGN once and pair every position with the corresponding
MoveAnalysis row. Stockfish evals are intentionally NOT used as features —
they leak the label.
"""
from __future__ import annotations

import io
import re
from typing import Iterable, Iterator

import chess
import chess.pgn

from game_analysis import static_exchange_eval

# Pieces and their material values.
PIECE_VALUE = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

# Class label set — moves we want the classifier to flag in advance.
BAD_CLASSES = {"Blunder", "Mistake", "Miss"}


def _material(board: chess.Board, color: bool) -> int:
    total = 0
    for piece_type, value in PIECE_VALUE.items():
        total += value * len(board.pieces(piece_type, color))
    return total


def _king_attackers(board: chess.Board, color: bool) -> int:
    """How many enemy pieces attack squares around our king."""
    king_sq = board.king(color)
    if king_sq is None:
        return 0
    enemy = not color
    count = 0
    for sq in chess.SquareSet(chess.BB_KING_ATTACKS[king_sq]):
        attackers = board.attackers(enemy, sq)
        count += len(attackers)
    return count


def _isolated_pawns(board: chess.Board, color: bool) -> int:
    files_with_pawn = {chess.square_file(sq) for sq in board.pieces(chess.PAWN, color)}
    isolated = 0
    for f in files_with_pawn:
        neighbors = {f - 1, f + 1}
        if not neighbors & files_with_pawn:
            isolated += 1
    return isolated


def _doubled_pawns(board: chess.Board, color: bool) -> int:
    files = [chess.square_file(sq) for sq in board.pieces(chess.PAWN, color)]
    return sum(1 for f in set(files) if files.count(f) > 1)


def _passed_pawns(board: chess.Board, color: bool) -> int:
    """Pawns with no enemy pawn on same/adjacent file ahead."""
    enemy_pawns = list(board.pieces(chess.PAWN, not color))
    enemy_files_ranks = [(chess.square_file(s), chess.square_rank(s)) for s in enemy_pawns]
    passed = 0
    for sq in board.pieces(chess.PAWN, color):
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        ahead = (lambda er: er > r) if color == chess.WHITE else (lambda er: er < r)
        blocked = any(
            abs(ef - f) <= 1 and ahead(er) for ef, er in enemy_files_ranks
        )
        if not blocked:
            passed += 1
    return passed


def _threats_count(board: chess.Board, color: bool) -> tuple[int, int]:
    """How many of `color`'s pieces are under a positive-SEE attack right now.
    Returns (count, total_value_at_risk). Pawns count toward count but not value."""
    enemy = not color
    count = 0
    total = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if not piece or piece.color != color or piece.piece_type == chess.KING:
            continue
        attackers = board.attackers(enemy, sq)
        if not attackers:
            continue
        cheapest = min(attackers, key=lambda s: PIECE_VALUE[board.piece_at(s).piece_type])
        capture = chess.Move(cheapest, sq)
        b = board.copy(stack=False)
        if b.turn != enemy:
            b.turn = enemy
        if capture not in b.legal_moves:
            continue
        try:
            see = static_exchange_eval(b, capture)
        except Exception:
            continue
        if see > 0:
            count += 1
            total += PIECE_VALUE[piece.piece_type]
    return count, total


_CLK_RE = re.compile(r"\[%clk\s+(\d+):(\d+):(\d+(?:\.\d+)?)\]")


def _parse_clock_seconds(comment: str) -> float | None:
    """Pull `[%clk H:MM:SS.s]` from a PGN move comment. Returns seconds."""
    m = _CLK_RE.search(comment or "")
    if not m:
        return None
    h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mn * 60 + s


def _initial_time_seconds(headers) -> float | None:
    """Parse `TimeControl` header (e.g. '300', '300+5', '180+0')."""
    tc = headers.get("TimeControl", "")
    if not tc:
        return None
    base = tc.split("+")[0].strip()
    try:
        return float(base)
    except ValueError:
        return None


def extract_position_features(
    board: chess.Board,
    user_color: bool,
    move_number: int,
    prev_score_white_cp: int | None,
    score_window: list[int],
    time_left: float | None = None,
    initial_time: float | None = None,
) -> dict[str, float]:
    """
    Features computed on the board state right BEFORE the user's move.

    `prev_score_white_cp` and `score_window` come from previously stored
    MoveAnalysis rows — they describe the *trajectory*, not the answer to
    "what's the best move here." Using prior eval is OK (the user could see
    the position too); using eval AFTER the move would be leakage.
    """
    enemy = not user_color
    legal_moves = list(board.legal_moves)

    threats_count, threats_value = _threats_count(board, user_color)
    enemy_threats_count, _ = _threats_count(board, enemy)

    # Time pressure as a fraction of starting time (0 = out of time, 1 = full clock).
    if time_left is not None and initial_time and initial_time > 0:
        time_frac = max(0.0, min(1.0, time_left / initial_time))
    else:
        time_frac = 1.0

    feats = {
        "move_number": move_number,
        "material_diff": _material(board, user_color) - _material(board, enemy),
        "mobility_user": len(legal_moves),
        "in_check": 1.0 if board.is_check() else 0.0,
        "king_attackers_user": _king_attackers(board, user_color),
        "king_attackers_enemy": _king_attackers(board, enemy),
        "isolated_pawns_user": _isolated_pawns(board, user_color),
        "doubled_pawns_user": _doubled_pawns(board, user_color),
        "passed_pawns_user": _passed_pawns(board, user_color),
        "passed_pawns_enemy": _passed_pawns(board, enemy),
        "castling_rights_user": int(
            board.has_kingside_castling_rights(user_color)
            or board.has_queenside_castling_rights(user_color)
        ),
        # Capture-pressure: SEE-positive threats on user pieces
        "threats_count": threats_count,
        "threats_value": threats_value,
        "enemy_threats_count": enemy_threats_count,
        # Time pressure
        "time_left_sec": time_left if time_left is not None else 0.0,
        "time_frac": time_frac,
    }

    # Trajectory features — eval from the user's POV before this move
    if prev_score_white_cp is None:
        feats["prev_eval_user"] = 0.0
        feats["eval_volatility"] = 0.0
    else:
        prev_cp = prev_score_white_cp if user_color == chess.WHITE else -prev_score_white_cp
        feats["prev_eval_user"] = max(-1500, min(1500, prev_cp))
        if len(score_window) >= 2:
            mean = sum(score_window) / len(score_window)
            var = sum((s - mean) ** 2 for s in score_window) / len(score_window)
            feats["eval_volatility"] = var ** 0.5
        else:
            feats["eval_volatility"] = 0.0

    return feats


## Positions where the eval is already past `LABEL_NOISE_CAP` cp in either
## direction are excluded from training: a "blunder" in a crushed/winning
## position is noise — the classifier shouldn't try to learn from it.
LABEL_NOISE_CAP = 700


def label_for(classification: str | None, my_cp: int | None = None) -> int | None:
    """Map a move classification to a binary risk label.

    Returns None when the sample should be dropped from training (positions
    that are already decided in either direction produce noisy bad-move
    labels). Callers should skip None.
    """
    if classification not in BAD_CLASSES:
        return 0
    if my_cp is not None and abs(my_cp) > LABEL_NOISE_CAP:
        return None
    return 1


def iter_user_moves(pgn_string: str, username: str, analysis_rows: list) -> Iterator[dict]:
    """
    Walk the PGN; for each USER move yield {features, label, move_number, color}.

    `analysis_rows` is the ordered list of MoveAnalysis ORM objects for the
    game. We index into it in PGN order — analysis was stored that way.
    """
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return

    headers = game.headers
    white_user = headers.get("White", "").lower() == username.lower()
    black_user = headers.get("Black", "").lower() == username.lower()
    if not (white_user or black_user):
        return
    user_color = chess.WHITE if white_user else chess.BLACK

    board = game.board()
    prev_score_white_cp = None
    score_window: list[int] = []
    initial_time = _initial_time_seconds(headers)

    # Walk PGN with node iteration so we can read [%clk] comments.
    node = game
    idx = 0

    while node.variations:
        next_node = node.variation(0)
        move = next_node.move
        is_user_move = (board.turn == user_color)
        if idx >= len(analysis_rows):
            break
        analysis = analysis_rows[idx]

        if is_user_move:
            move_number = (idx // 2) + 1
            time_left = _parse_clock_seconds(next_node.comment)
            my_cp_after = (
                analysis.score if user_color == chess.WHITE else -analysis.score
            ) if analysis.score is not None else None
            label = label_for(analysis.classification, my_cp_after)
            if label is None:
                # noisy sample — skip entirely (don't yield)
                pass
            else:
                feats = extract_position_features(
                    board=board,
                    user_color=user_color,
                    move_number=move_number,
                    prev_score_white_cp=prev_score_white_cp,
                    score_window=score_window[-5:],
                    time_left=time_left,
                    initial_time=initial_time,
                )
                yield {
                    "features": feats,
                    "label": label,
                    "move_number": move_number,
                    "color": "white" if user_color == chess.WHITE else "black",
                    "move_id": analysis.id,
                    "classification": analysis.classification,
                }

        board.push(move)
        if analysis.score is not None:
            prev_score_white_cp = analysis.score
            score_window.append(analysis.score)
        node = next_node
        idx += 1


FEATURE_NAMES = [
    "move_number",
    "material_diff",
    "mobility_user",
    "in_check",
    "king_attackers_user",
    "king_attackers_enemy",
    "isolated_pawns_user",
    "doubled_pawns_user",
    "passed_pawns_user",
    "passed_pawns_enemy",
    "castling_rights_user",
    "threats_count",
    "threats_value",
    "enemy_threats_count",
    "time_left_sec",
    "time_frac",
    "prev_eval_user",
    "eval_volatility",
]
