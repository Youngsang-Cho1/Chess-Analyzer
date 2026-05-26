"""
Personalized insights: phase-by-phase quality, opening win rates, blunder patterns.

Aggregates over all analyzed games for a user and surfaces patterns that
single-game review misses.
"""
from collections import defaultdict
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Game, MoveAnalysis


# Move quality weighting — higher is better.
QUALITY_WEIGHTS = {
    "Brilliant": 4,
    "Great": 3,
    "Best": 2,
    "Excellent": 1,
    "Good": 0,
    "Book": 0,
    "Forced": 0,
    "Inaccuracy": -1,
    "Miss": -2,
    "Mistake": -2,
    "Blunder": -4,
}

# A move counts as a "mistake-class" event for blunder pattern detection.
BAD_CLASSES = {"Inaccuracy", "Mistake", "Blunder", "Miss"}


def _phase_of(move_number: int) -> str:
    if move_number <= 10:
        return "opening"
    if move_number >= 30:
        return "endgame"
    return "middlegame"


def get_player_insights(username: str, limit: int = 100):
    db: Session = SessionLocal()
    try:
        user_lower = username.lower()
        games = (
            db.query(Game)
            .filter(
                or_(
                    Game.white_username.ilike(username),
                    Game.black_username.ilike(username),
                )
            )
            .order_by(Game.id.desc())
            .limit(limit)
            .all()
        )

        if not games:
            return None

        game_ids = [g.id for g in games]
        game_by_id = {g.id: g for g in games}

        moves = (
            db.query(MoveAnalysis)
            .filter(MoveAnalysis.game_id.in_(game_ids))
            .all()
        )

        # ---- Phase quality ----
        phase_totals = defaultdict(lambda: {"weight_sum": 0, "count": 0, "bad": 0})
        # ---- Blunder patterns ----
        bad_by_move_bucket = defaultdict(int)  # "1-10", "11-20", ...
        bad_by_captured = defaultdict(int)
        total_bad = 0
        # ---- Color split ----
        color_quality = {"white": {"weight_sum": 0, "count": 0}, "black": {"weight_sum": 0, "count": 0}}

        for m in moves:
            game = game_by_id.get(m.game_id)
            if not game:
                continue
            is_white_user = (game.white_username or "").lower() == user_lower
            user_color = "white" if is_white_user else "black"
            if m.color != user_color:
                continue

            w = QUALITY_WEIGHTS.get(m.classification, 0)
            phase = _phase_of(m.move_number or 0)
            phase_totals[phase]["weight_sum"] += w
            phase_totals[phase]["count"] += 1
            color_quality[user_color]["weight_sum"] += w
            color_quality[user_color]["count"] += 1

            if m.classification in BAD_CLASSES:
                phase_totals[phase]["bad"] += 1
                total_bad += 1
                mn = m.move_number or 0
                bucket = f"{((mn - 1) // 10) * 10 + 1}-{((mn - 1) // 10) * 10 + 10}"
                bad_by_move_bucket[bucket] += 1
                if m.captured_piece:
                    bad_by_captured[m.captured_piece] += 1

        phase_summary = []
        for phase in ("opening", "middlegame", "endgame"):
            data = phase_totals.get(phase, {"weight_sum": 0, "count": 0, "bad": 0})
            count = data["count"]
            avg = (data["weight_sum"] / count) if count else 0.0
            bad_rate = (data["bad"] / count * 100) if count else 0.0
            phase_summary.append(
                {
                    "phase": phase,
                    "moves": count,
                    "avg_quality": round(avg, 2),
                    "bad_move_rate": round(bad_rate, 1),
                }
            )

        weakest_phase = min(
            (p for p in phase_summary if p["moves"] > 0),
            key=lambda p: p["avg_quality"],
            default=None,
        )

        # ---- Opening performance ----
        opening_agg = defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0, "draws": 0, "acc_sum": 0.0, "acc_n": 0})
        for g in games:
            opening_name = g.opening or "Unknown"
            is_white = (g.white_username or "").lower() == user_lower
            result = g.white_result if is_white else g.black_result
            acc = g.white_accuracy if is_white else g.black_accuracy
            agg = opening_agg[opening_name]
            agg["games"] += 1
            if result == "1":
                agg["wins"] += 1
            elif result == "0":
                agg["losses"] += 1
            else:
                agg["draws"] += 1
            if acc is not None:
                agg["acc_sum"] += acc
                agg["acc_n"] += 1

        openings = []
        for name, agg in opening_agg.items():
            if agg["games"] < 2:
                continue  # ignore one-offs
            win_rate = agg["wins"] / agg["games"] * 100
            avg_acc = (agg["acc_sum"] / agg["acc_n"]) if agg["acc_n"] else 0.0
            openings.append(
                {
                    "opening": name,
                    "games": agg["games"],
                    "wins": agg["wins"],
                    "losses": agg["losses"],
                    "draws": agg["draws"],
                    "win_rate": round(win_rate, 1),
                    "avg_accuracy": round(avg_acc, 1),
                }
            )
        openings.sort(key=lambda o: o["games"], reverse=True)
        best_opening = max(openings, key=lambda o: o["win_rate"], default=None) if openings else None
        worst_opening = min(openings, key=lambda o: o["win_rate"], default=None) if openings else None

        # ---- Blunder patterns ----
        def _bucket_sort_key(b):
            return int(b.split("-")[0])

        blunder_buckets = [
            {"range": k, "count": v}
            for k, v in sorted(bad_by_move_bucket.items(), key=lambda kv: _bucket_sort_key(kv[0]))
        ]
        worst_bucket = max(blunder_buckets, key=lambda b: b["count"], default=None)

        top_captured = sorted(bad_by_captured.items(), key=lambda kv: kv[1], reverse=True)[:5]

        # ---- Color split ----
        color_summary = {}
        for color, data in color_quality.items():
            count = data["count"]
            color_summary[color] = {
                "moves": count,
                "avg_quality": round(data["weight_sum"] / count, 2) if count else 0.0,
            }

        return {
            "username": username,
            "games_analyzed": len(games),
            "phases": phase_summary,
            "weakest_phase": weakest_phase["phase"] if weakest_phase else None,
            "openings": openings[:10],
            "best_opening": best_opening,
            "worst_opening": worst_opening,
            "blunder_buckets": blunder_buckets,
            "worst_move_range": worst_bucket["range"] if worst_bucket else None,
            "blunders_by_captured_piece": [{"piece": p, "count": c} for p, c in top_captured],
            "total_bad_moves": total_bad,
            "color_quality": color_summary,
        }
    finally:
        db.close()
