import os
import chess.pgn
import chess.polyglot
import io
import json
from dotenv import load_dotenv
from stockfish import Stockfish
from math import exp
import statistics

load_dotenv()

stockfish_path = os.getenv("STOCKFISH_PATH")
base_dir = os.path.dirname(os.path.abspath(__file__))

# Load Opening Data (ECO)
eco_data = {}
try:
    with open("eco.json", "r") as f:
        raw_data = json.load(f)
        for k, v in raw_data.items():
            # e.g.) k = "rnb... b KQkq e3 0 1"
            # normalized = "rnb... b KQkq" (removing en passant, half move, full move)
            norm_key = " ".join(k.split(" ")[:3])
            eco_data[norm_key] = v
    print(f"Loaded {len(eco_data)} openings (ECO).")
except Exception as e:
    print(f"Warning: ECO data missing: {e}")

# Polyglot Opening Book
polyglot_path = os.path.join(base_dir, "gm2001.bin")
has_polyglot = os.path.exists(polyglot_path)

if has_polyglot:
    print(f"Polyglot book loaded: {polyglot_path}")
else:
    print("Warning: Polyglot book (gm2001.bin) not found. Using ECO only.")

def get_opening_name(board):
    # ECO lookup
    fen_parts = board.fen().split(" ")
    norm_key = " ".join(fen_parts[:3])
    return eco_data.get(norm_key)

def is_in_book(board):
    # Polyglot book move check
    if not has_polyglot:
        return False
    try:
        with chess.polyglot.open_reader(polyglot_path) as reader:
            reader.find(board)
            return True
    except (KeyError, IndexError):
        return False

def get_win_prob(cp):
    if cp is None: 
        return 50.0
    # sigmoid function for getting the win probability based on the current centipawn score
    return 50 + 50 * (2 / (1 + exp(-0.00368 * cp)) - 1)

## Move-classification thresholds (chess.com Expected Points Model, % points)
THRESH_EXCELLENT  = 2
THRESH_GOOD       = 5
THRESH_INACCURACY = 10
THRESH_MISTAKE    = 20

## Brilliant gating
BRILLIANT_CP_LOSS_MAX  = 50
BRILLIANT_MY_CP_MIN    = -100   # after the sac, still roughly balanced
BRILLIANT_MY_CP_MAX    = 500
BRILLIANT_PREV_CP_MIN  = -150   # before the sac, position must not already be lost

## Great move: best move + 2nd-best is much worse, in roughly balanced position
GREAT_SECOND_GAP_MIN  = 400
GREAT_MY_CP_LIMIT     = 500

## Miss: failed to punish opponent's bad move. Requires (a) prev opponent move
## was bad enough, and (b) our reply is materially worse than the best reply.
MISS_PREV_BAD_CLASSES = {"Mistake", "Blunder", "Miss"}
MISS_MIN_CP_LOSS      = 150     # we left at least 1.5 pawns on the table
MISS_MIN_BEST_CP      = 150     # the punishing line had to be visibly winning


def classify_by_win_diff(win_diff: float) -> str:
    """Chess.com Expected Points Model — pure win%-loss tiers."""
    if win_diff <= THRESH_EXCELLENT:  return "Excellent"
    if win_diff <= THRESH_GOOD:       return "Good"
    if win_diff <= THRESH_INACCURACY: return "Inaccuracy"
    if win_diff <= THRESH_MISTAKE:    return "Mistake"
    return "Blunder"


def classify_move(
    *,
    move_uci: str,
    best_move_uci: str,
    is_only_legal: bool,
    is_book: bool,
    win_diff: float,
    cp_loss: int,
    my_cp: int,
    best_cp: int,
    second_cp: int | None,
    my_mate_in: int | None,
    best_mate_in: int | None,
    is_white: bool,
    is_sac: bool,
    prev_classification: str | None,
    prev_cp: int = 0,
) -> str:
    """Single source of truth for move classification.

    Order matters: Book > Best/Great/Forced > tier (Excellent..Blunder)
    > Miss override > Brilliant override.
    """
    # 1. Book moves
    if is_book:
        return "Book"

    # 2. Best move family (and its richer variants)
    if move_uci == best_move_uci:
        cls = "Forced" if is_only_legal else "Best"
        # Great: clearly better than the second-best response, in a balanced game
        if (
            second_cp is not None
            and abs(second_cp - best_cp) >= GREAT_SECOND_GAP_MIN
            and -GREAT_MY_CP_LIMIT < my_cp < GREAT_MY_CP_LIMIT
        ):
            cls = "Great"
    else:
        # 3. Win%-loss tier for non-best moves
        cls = classify_by_win_diff(win_diff)

        # 4. Miss override (Chess.com semantic: failed to punish a bad move)
        if _is_miss(
            cls=cls,
            prev_classification=prev_classification,
            cp_loss=cp_loss,
            best_cp=best_cp,
            my_mate_in=my_mate_in,
            best_mate_in=best_mate_in,
            is_white=is_white,
        ):
            cls = "Miss"

    # 5. Brilliant override — real material sacrifice OR verified trap
    # (ignores a hanging piece but has a profitable counter if opponent takes).
    if (
        not is_book
        and is_sac
        and cp_loss <= BRILLIANT_CP_LOSS_MAX
        and BRILLIANT_MY_CP_MIN < my_cp < BRILLIANT_MY_CP_MAX
        and prev_cp > BRILLIANT_PREV_CP_MIN
    ):
        cls = "Brilliant"

    return cls


def _is_miss(
    *,
    cls: str,
    prev_classification: str | None,
    cp_loss: int,
    best_cp: int,
    my_mate_in: int | None,
    best_mate_in: int | None,
    is_white: bool,
) -> bool:
    """Miss = failed to capitalize on opponent's bad move OR missed a forced mate.

    Forced-mate miss: engine had mate but we didn't play into it.
    Tactical miss: opponent just blundered/missed, the punishing line was
    clearly winning (best_cp ≥ +150), and our reply gave up significant
    material vs. that line (cp_loss ≥ 150).
    """
    # (A) Missed a forced mate that was ours
    if best_mate_in is not None and my_mate_in is None:
        ours = (is_white and best_mate_in > 0) or (not is_white and best_mate_in < 0)
        if ours:
            return True

    # (B) Failed-to-punish tactical miss
    if prev_classification in MISS_PREV_BAD_CLASSES:
        if cp_loss >= MISS_MIN_CP_LOSS and best_cp >= MISS_MIN_BEST_CP:
            # Only escalate from non-Blunder tiers — a Blunder already conveys
            # the magnitude. Miss should NOT downgrade a Blunder.
            if cls != "Blunder":
                return True
    return False

PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

def _piece_val(board, square):
    p = board.piece_at(square)
    return PIECE_VALUES[p.piece_type] if p else 0


def static_exchange_eval(board, move):
    """
    Static Exchange Evaluation (SEE) for `move` on its target square.

    Returns the net material (in pawns) the mover nets after both sides keep
    recapturing on `to_square` with their cheapest attacker. Negative means the
    move loses material in the exchange — the basis of a sacrifice. Works on a
    board copy so the caller's stack is untouched. En-passant/promotion are
    approximated (negligible for sac detection).
    """
    to_sq = move.to_square
    b = board.copy(stack=False)

    captured = _piece_val(b, to_sq)            # value we capture with the move
    on_square = _piece_val(b, move.from_square)  # our piece, now recapturable

    b.push(move)

    gain = [captured]
    occupied_value = on_square
    side = b.turn  # opponent recaptures first

    while True:
        attackers = b.attackers(side, to_sq)
        if not attackers:
            break
        cheapest_sq = min(attackers, key=lambda s: _piece_val(b, s))
        recapture = chess.Move(cheapest_sq, to_sq)
        if recapture not in b.legal_moves:
            break  # pinned / illegal — exchange stops
        gain.append(occupied_value - gain[-1])
        occupied_value = _piece_val(b, cheapest_sq)
        b.push(recapture)
        side = not side

    # Minimax back up the swap list.
    for i in range(len(gain) - 2, -1, -1):
        gain[i] = -max(-gain[i], gain[i + 1])
    return gain[0]


def is_sacrifice(board, move):
    """A move is a sacrifice if the exchange on its target square loses
    material (SEE < 0) — i.e. the mover willingly gives up more than they get,
    rather than making an even trade or winning material."""
    try:
        see = static_exchange_eval(board, move)
    except Exception:
        return False
    # Lose at least ~2 points in the exchange to count as a real sacrifice.
    return see <= -2


def get_score_val(move_data):
    # Handle Stockfish get_evaluation() format {'type': 'cp'/'mate', 'value': ...}
    if 'type' in move_data:
        if move_data['type'] == 'mate':
            mate_in = move_data['value']
            return (20000 - abs(mate_in) * 10) * (1 if mate_in > 0 else -1)
        return move_data['value']
        
    # Handle Stockfish get_top_moves() format {'Mate': ..., 'Centipawn': ...}
    if move_data.get('Mate') is not None:
        mate_in = move_data['Mate']
        return (20000 - abs(mate_in) * 10) * (1 if mate_in > 0 else -1)
    return move_data.get('Centipawn', 0)

def calculate_stats(moves):
    if not moves:
        return {"accuracy": 0, "classification_counts": {}}
    
    # Extract win percentages
    win_percents = [m['win_percent_before'] for m in moves]
    win_percents.append(moves[-1]['win_percent_after'])
    
    # Extract accuracies
    accuracies = [m['accuracy'] for m in moves]
    
    # Calculate volatility weights (higher std dev = more critical position)
    window_size = get_window_size(len(moves))
    weights = calculate_volatility_weights(win_percents, window_size)
    
    # Weighted mean
    weighted_avg = weighted_mean(accuracies, weights)
    
    # Harmonic mean
    harmonic_avg = harmonic_mean(accuracies)
    
    # Final accuracy: average of both
    lichess_accuracy = (weighted_avg + harmonic_avg) / 2
    
    # Count move classifications
    counts = {
        "Brilliant": 0, "Great": 0, "Book": 0, "Best": 0, "Excellent": 0,
        "Good": 0, "Inaccuracy": 0, "Mistake": 0, "Blunder": 0, "Miss": 0
    }
    
    for m in moves:
        cls = m.get('classification', 'Normal')
        if cls in counts:
            counts[cls] += 1
    
    return {
        "accuracy": round(lichess_accuracy, 1),
        "classification_counts": counts
    }

# Accuracy Logics borrowed from Lichess
def get_window_size(num_moves):
    window_size = max(2, min(8, num_moves // 10))
    return window_size

def calculate_volatility_weights(win_percents, window_size):
    weights = []
    # Ensure window_size doesn't exceed list length
    actual_window_size = min(window_size, len(win_percents))
    for i in range(len(win_percents) - actual_window_size + 1):
        window = win_percents[i:i + actual_window_size]
        std_dev = statistics.stdev(window) if len(window) > 1 else 0.5
        weight = max(0.5, min(12, std_dev))
        weights.append(weight)
    return weights

def weighted_mean(accuracies, weights):
    # Ensure lengths match (weights might be 1 longer due to win_percents)
    min_len = min(len(accuracies), len(weights))
    weighted_sum = sum(accuracies[i] * weights[i] for i in range(min_len))
    total_weight = sum(weights[:min_len])
    
    if total_weight:
        return weighted_sum / total_weight
    return 0

def harmonic_mean(accuracies):
    safe_accuracies = [max(0.1, acc) for acc in accuracies]
    reciprocal_sum = sum(1/acc for acc in safe_accuracies)
    if reciprocal_sum > 0:
        return len(safe_accuracies) / reciprocal_sum
    return 0

# Main Analysis Logic
STOCKFISH_DEPTH = int(os.getenv("STOCKFISH_DEPTH", "16"))
STOCKFISH_THREADS = int(os.getenv("STOCKFISH_THREADS", "2"))
STOCKFISH_HASH_MB = int(os.getenv("STOCKFISH_HASH_MB", "256"))

_engine: Stockfish | None = None

def _get_engine() -> Stockfish:
    global _engine
    if _engine is None:
        _engine = Stockfish(
            path=stockfish_path,
            depth=STOCKFISH_DEPTH,
            parameters={"Threads": STOCKFISH_THREADS, "Hash": STOCKFISH_HASH_MB},
        )
        return _engine
    # Verify process is still alive; respawn if crashed
    try:
        _engine.get_best_move_time(10)
    except Exception:
        _engine = Stockfish(
            path=stockfish_path,
            depth=STOCKFISH_DEPTH,
            parameters={"Threads": STOCKFISH_THREADS, "Hash": STOCKFISH_HASH_MB},
        )
    return _engine


def analyze_game(pgn_string: str):
    engine = _get_engine()
    
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    board = game.board()
    
    analysis_results = []
    prev_score = 0
    prev_classification: str | None = None  # opponent's previous move class (drives Miss)

    # 1. Parse opening name from Chess.com ECOUrl header
    eco_url = game.headers.get("ECOUrl", "")
    pgn_opening = "Opening Move"
    if eco_url:
        parts = eco_url.split("/openings/")
        if len(parts) > 1:
            import re
            raw_name = parts[1].split("?")[0]
            raw_name = re.split(r'-\d+\.', raw_name)[0]
            pgn_opening = raw_name.replace("-", " ").strip()
    
    if pgn_opening == "Opening Move":
        header_opening = game.headers.get("Opening", "")
        if header_opening and header_opening != "?":
            pgn_opening = header_opening
    
    current_opening = pgn_opening

    print("--- Analysis Start ---")

    in_book_line = True
    for i, move in enumerate(game.mainline_moves()):
        if i // 2 >= 12 and current_opening == "Opening Move" and not in_book_line:
             current_opening = "No Opening"
        is_white = board.turn
        move_uci = move.uci()
        move_san = board.san(move)
        
        captured_piece = None
        if board.is_capture(move):
            if board.is_en_passant(move):
                captured_piece = "Pawn"
            else:
                piece = board.piece_at(move.to_square)
                if piece:
                     captured_piece = chess.piece_name(piece.piece_type).capitalize()
        
        board.push(move)
        # Check Book Status for current move: is THIS position a known
        # ECO opening or in the polyglot book?
        is_book = False
        opening_info = get_opening_name(board)

        if opening_info:
            current_opening = opening_info.get('name', current_opening)
            is_book = True
        else:
            is_book = is_in_book(board)

        # Track whether we're still inside the unbroken opening line. Once the
        # game leaves book it stays "out" — a later transposition back into a
        # known position is a coincidence, not opening theory, so we don't want
        # to relabel a real middlegame move as "Book".
        in_book_line = in_book_line and is_book
        
        # 2. Get Top Moves
        board.pop()
        engine.set_fen_position(board.fen())
        
        top_moves = engine.get_top_moves(2)
        best_move = top_moves[0]['Move']
        
        # Convert to SAN while board is in "Before Move" state
        best_move_san = board.san(chess.Move.from_uci(best_move))
        
        best_score = get_score_val(top_moves[0])

        second_score = None

        if len(top_moves) > 1:
            second_score = get_score_val(top_moves[1])

        # Check Sacrifice / hanging-piece (board must be in pre-move state)
        is_sac = is_sacrifice(board, move)


        board.push(move)
        
        # 3. Evaluate Current Position
        engine.set_fen_position(board.fen())
        eval_data = engine.get_evaluation()
        
        score_val = get_score_val(eval_data)
        curr_score_white = score_val

        # Extract explicit mate information
        mate_in = None
        if 'type' in eval_data and eval_data['type'] == 'mate':
            mate_in = eval_data['value']
            
        best_mate_in = top_moves[0].get('Mate')
        
        # Convert to Win Probability (0-100)
        my_cp = curr_score_white if is_white else -curr_score_white
        best_cp = best_score if is_white else -best_score
        if second_score is None:
            second_cp = None
        else:
            second_cp = second_score if is_white else -second_score
        prev_cp_pers = prev_score if is_white else -prev_score

        prev_win_prob = get_win_prob(prev_cp_pers)
        curr_win_prob = get_win_prob(my_cp)
        best_win_prob = get_win_prob(best_cp)

        # 4. Classify Move
        win_diff = max(0, best_win_prob - curr_win_prob)
        cp_loss = max(0, best_cp - my_cp)

        classification = classify_move(
            move_uci=move_uci,
            best_move_uci=best_move,
            is_only_legal=len(top_moves) == 1,
            is_book=in_book_line,
            win_diff=win_diff,
            cp_loss=cp_loss,
            my_cp=my_cp,
            best_cp=best_cp,
            second_cp=second_cp,
            my_mate_in=mate_in,
            best_mate_in=best_mate_in,
            is_white=is_white,
            is_sac=is_sac,

            prev_classification=prev_classification,
            prev_cp=prev_cp_pers,
        )

        # 5. Accuracy Calculation 
        move_accuracy = 103.1668 * exp(-0.04354 * win_diff) - 3.1669
        move_accuracy = max(0, min(100, move_accuracy))

        result = {
            "move_number": (i // 2) + 1,
            "move_uci": move_uci,
            "move_san": move_san,
            "score": curr_score_white,
            "mate_in": mate_in,
            "best_mate_in": best_mate_in,
            "classification": classification,
            "color": "white" if is_white else "black",
            "best_move": best_move_san,
            "opening": current_opening,
            "accuracy": round(move_accuracy, 1),
            "win_chance": round(curr_win_prob, 1),
            "cp_loss": cp_loss,
            "win_percent_before": round(prev_win_prob, 1),
            "win_percent_after": round(curr_win_prob, 1),
            "captured_piece": captured_piece,
            "is_sacrifice": is_sac,
        }
        analysis_results.append(result)

        # Calculate White's Win Probability for stable logging
        white_win_prob = get_win_prob(curr_score_white)
        
        print(f"Move: {move_san:<10} | Class: {classification:<10} | Acc: {result['accuracy']:>5.1f}% | Eval: {curr_score_white:>+5} (White Win%: {white_win_prob:.1f}%) | Opening: {current_opening}") 

        prev_score = curr_score_white
        prev_classification = classification

    # Calculate Game Summary
    white_moves = [res for idx, res in enumerate(analysis_results) if idx % 2 == 0]
    black_moves = [res for idx, res in enumerate(analysis_results) if idx % 2 == 1]

    summary = {
        "white": calculate_stats(white_moves),
        "black": calculate_stats(black_moves)
    } # Gives summarized stats for both players

    return {
        "moves": analysis_results,
        "summary": summary,
        "headers": dict(game.headers),
        "detected_opening": current_opening if current_opening != "No Opening detected" else "Unknown" 
    }

