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

def get_classification(win_diff):
    """Chess.com Expected Points Model (win% loss based)"""
    if win_diff <= 2:    
        return "Excellent"
    if win_diff <= 5:    
        return "Good"
    if win_diff <= 10:   
        return "Inaccuracy"
    if win_diff <= 20:   
        return "Mistake"
    
    return "Blunder"     

PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

def is_sacrifice(board, move):
    is_sacrifice = False
    
    if board.is_capture(move): 
        # Check for Recapture
        is_recapture = False
        if board.move_stack: 
            last_move = board.peek() 
            if move.to_square == last_move.to_square:
                board.pop() 
                if board.is_capture(last_move): 
                    is_recapture = True
                board.push(last_move) 

        # Case A: Active Sacrifice
        my_piece = board.piece_at(move.from_square)
        target_piece = board.piece_at(move.to_square)
        
        if my_piece and target_piece:
            my_val = PIECE_VALUES[my_piece.piece_type]
            target_val = PIECE_VALUES[target_piece.piece_type]
            val_diff = my_val - target_val
            
            if board.is_attacked_by(not board.turn, move.to_square):
                if is_recapture:
                    # Equal trade (Rook x Rook)
                    if my_val == target_val:
                        is_sacrifice = False
                    # Winning trade (Pawn x Rook)
                    elif my_val < target_val:
                        is_sacrifice = False
                    # Losing trade (Rook x Pawn)
                    else:
                        threats = board.attackers(not board.turn, move.to_square)
                        
                        # Filter out King if the square is protected (King cannot capture protected piece)
                        is_protected = board.is_attacked_by(board.turn, move.to_square)
                        
                        min_threat_val = 100
                        for square in threats:
                            tp = board.piece_at(square)
                            if tp:
                                # Skip King if the piece is protected
                                if tp.piece_type == chess.KING and is_protected:
                                    continue
                                min_threat_val = min(min_threat_val, PIECE_VALUES[tp.piece_type])
                        
                        # Threatened by smaller piece : Sacrifice
                        if min_threat_val < my_val and min_threat_val < 100:
                            is_sacrifice = True
                else:
                    if val_diff >= 2:
                        is_sacrifice = True
                        
    else:
        # Case B: Passive Sacrifice
        if board.is_attacked_by(not board.turn, move.to_square):
            my_piece = board.piece_at(move.from_square)
            threats = board.attackers(not board.turn, move.to_square)
            
            # Check if piece is protected
            is_protected = board.is_attacked_by(board.turn, move.to_square)
            
            min_threat_val = 100
            for square in threats:
                threat_piece = board.piece_at(square)
                # Skip King if protected
                if threat_piece.piece_type == chess.KING and is_protected:
                    continue
                min_threat_val = min(min_threat_val, PIECE_VALUES[threat_piece.piece_type])
            
            if PIECE_VALUES[my_piece.piece_type] - min_threat_val >= 2:
                is_sacrifice = True

    return is_sacrifice


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
def analyze_game(pgn_string: str):
    engine = Stockfish(path=stockfish_path, depth=18, parameters={"Threads": 6, "Hash": 256})
    
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    board = game.board()
    
    analysis_results = []
    prev_score = 0
    
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

    all_win_percentages = []
    all_accuracies = []
    
    print("--- Analysis Start ---")

    is_book = True
    for i, move in enumerate(game.mainline_moves()):
        if i // 2 >= 12 and current_opening == "Opening Move" and not is_book:
             current_opening = "No Opening"
        is_white = board.turn
        move_uci = move.uci()
        move_san = board.san(move)
        
        board.push(move)
        opening_info = get_opening_name(board)
        if opening_info:
            current_opening = opening_info.get('name', current_opening)
            is_book = True
        else:
            is_book = is_in_book(board)
        
        # 2. Get Top Moves
        board.pop()
        engine.set_fen_position(board.fen())
        
        top_moves = engine.get_top_moves(2)
        best_move = top_moves[0]['Move']
        best_score = get_score_val(top_moves[0])

        second_score = None

        if len(top_moves) > 1:
            second_score = get_score_val(top_moves[1])

        # Check Sacrifice (Must be done while board is popped / before move is pushed)
        is_sac = is_sacrifice(board, move)

        board.push(move) 
        
        # 3. Evaluate Current Position
        engine.set_fen_position(board.fen())
        eval_data = engine.get_evaluation()
        
        score_val = get_score_val(eval_data)

        curr_score_white = score_val
        
        # Convert to Win Probability (0-100)
        my_cp = curr_score_white if is_white else -curr_score_white
        best_cp = best_score if is_white else -best_score
        second_cp = second_score if is_white else -second_score if second_score is not None else None
        prev_cp_pers = prev_score if is_white else -prev_score

        prev_win_prob = get_win_prob(prev_cp_pers)
        curr_win_prob = get_win_prob(my_cp)
        best_win_prob = get_win_prob(best_cp)
        
        # 4. Classify Move
        win_diff = best_win_prob - curr_win_prob
        if win_diff < 0: 
            win_diff = 0
        
        cp_loss = best_cp - my_cp
        if cp_loss < 0:
            cp_loss = 0
            
        # Calculate Previous Win Probability
        prev_cp_pers = prev_score if is_white else -prev_score
        prev_win_prob = get_win_prob(prev_cp_pers)
        
        classification = "Normal"

        if is_book:
            classification = "Book"
        
        elif move_uci == best_move:
            if len(top_moves) == 1:
                classification = "Forced" # only available move
            else:
                classification = "Best"
            
            # Great Move: Best Move + large gap to 2nd best
            if second_cp is not None:
                second_cp_loss = abs(second_cp - best_cp)
                # 2nd best is much worse and position is balanced
                if second_cp_loss >= 250 and -500 < my_cp < 500:
                     classification = "Great"
        else:
            classification = get_classification(win_diff)
            
            if (best_cp > 300 and my_cp < 100) or (best_cp > 2000 and my_cp < 1000) or (best_cp > 500 and cp_loss > 300 and classification != "Blunder"):
                classification = "Miss"
            
        # Brilliant: Sacrifice that's nearly optimal (≤50cp loss, not losing)
        if is_sac:
            print(f"debug: move={move_uci}, is_sac={is_sac}, cp_loss={cp_loss:.1f}, my_cp={my_cp:.1f}, is_white={is_white}")
        if is_sac and cp_loss <= 50 and my_cp > -300:
             classification = "Brilliant"


        # 5. Accuracy Calculation 
        move_accuracy = 103.1668 * exp(-0.04354 * win_diff) - 3.1669
        move_accuracy = max(0, min(100, move_accuracy))


        result = {
            "move_number": (i // 2) + 1,
            "move_uci": move_uci,
            "move_san": move_san,
            "score": curr_score_white,
            "classification": classification,
            "best_move": best_move,
            "opening": current_opening,
            "accuracy": round(move_accuracy, 1),
            "win_chance": round(curr_win_prob, 1),
            "cp_loss": cp_loss,
            "win_percent_before": round(prev_win_prob, 1),
            "win_percent_after": round(curr_win_prob, 1)
        }
        analysis_results.append(result)
        all_win_percentages.append(curr_win_prob)
    
        # Calculate White's Win Probability for stable logging
        white_win_prob = get_win_prob(curr_score_white)
        
        print(f"Move: {move_san:<10} | Class: {classification:<10} | Acc: {result['accuracy']:>5.1f}% | Eval: {curr_score_white:>+5} (White Win%: {white_win_prob:.1f}%) | Opening: {current_opening}") 

        prev_score = curr_score_white
        
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

