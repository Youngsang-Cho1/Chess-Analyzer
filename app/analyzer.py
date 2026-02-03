import os
import chess.pgn
import io
import json
from dotenv import load_dotenv
from stockfish import Stockfish
import math
from math import exp

load_dotenv()

stockfish_path = os.getenv("STOCKFISH_PATH")

# Load Opening Data (ECO) & Normalize Keys
# Stripped Move Counts (last 2 fields) from keys to ensure fast lookup
eco_data = {}
try:
    with open("eco.json", "r") as f:
        raw_data = json.load(f)
        for k, v in raw_data.items():
            # e.g.) k = "rnb... b KQkq e3 0 1"
            # normalized = "rnb... b KQkq" (removing en passant, half move, full move)
            norm_key = " ".join(k.split(" ")[:3])
            eco_data[norm_key] = v
            
    print(f"Loaded {len(eco_data)} openings (Normalized).")
except Exception as e:
    print(f"Warning: ECO data missing: {e}")

def get_opening_details(board):
    # Lookup using Normalized FEN (Position + Turn + Castle)
    fen_parts = board.fen().split(" ")
    norm_key = " ".join(fen_parts[:3])
    
    return eco_data.get(norm_key)

def get_win_prob(cp):
    if cp is None: 
        return 50.0
    # sigmoid function for getting the win probability based on the current centipawn score
    return 50 + 50 * (2 / (1 + math.exp(-0.00368 * cp)) - 1)

def get_classification(win_diff):
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
            val_diff = PIECE_VALUES[my_piece.piece_type] - PIECE_VALUES[target_piece.piece_type]
            
            if board.is_attacked_by(not board.turn, move.to_square):
                if is_recapture:
                    threats = board.attackers(not board.turn, move.to_square)
                    min_threat_val = 100
                    for square in threats:
                        tp = board.piece_at(square)
                        if tp:
                            min_threat_val = min(min_threat_val, PIECE_VALUES[tp.piece_type])
                    
                    if min_threat_val < PIECE_VALUES[my_piece.piece_type]:
                        is_sacrifice = True
                else:
                    if val_diff >= 2:
                        is_sacrifice = True
                        
    else:
        # Case B: Passive Sacrifice
        if board.is_attacked_by(not board.turn, move.to_square):
            my_piece = board.piece_at(move.from_square)
            threats = board.attackers(not board.turn, move.to_square)
            
            min_threat_val = 100
            for square in threats:
                threat_piece = board.piece_at(square)
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
    
    avg_accuracy = sum(m['accuracy'] for m in moves) / len(moves)
    
    counts = {
        "Brilliant": 0, "Great": 0, "Best": 0, "Excellent": 0,
        "Good": 0, "Inaccuracy": 0, "Mistake": 0, "Blunder": 0, "Miss": 0, "Book": 0
    }
    
    for m in moves:
        cls = m.get('classification', 'Normal')
        if cls in counts:
            counts[cls] += 1
    
    return {
        "accuracy": round(avg_accuracy, 1),
        "classification_counts": counts
    }

# Main Analysis Logic
def analyze_game(pgn_string: str):
    # Optimized for M3 Chip (Threads=6, Hash=256)
    engine = Stockfish(path=stockfish_path, depth=18, parameters={"Threads": 4, "Hash": 256})
    
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    board = game.board()
    
    analysis_results = []
    prev_score = 0
    current_opening = "Opening Move"

    all_win_percentages = []
    all_accuracies = []
    
    print("--- Analysis Start ---")

    for i, move in enumerate(game.mainline_moves()):
        if i // 2 >= 12 and current_opening == "Opening Move":
            current_opening = "No Opening detected"
        is_white = board.turn
        move_uci = move.uci()
        
        board.push(move)
        opening_info = get_opening_details(board)
        if opening_info:
            current_opening = opening_info.get('name', current_opening)
        
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
        
        curr_win_prob = get_win_prob(my_cp)
        best_win_prob = get_win_prob(best_cp)
        
        # 4. Classify Move
        win_diff = best_win_prob - curr_win_prob
        if win_diff < 0: win_diff = 0
        
        classification = "Normal"
        
        if move_uci == best_move:
            classification = "Best"
            
            # Great Move: Best Move + large gap to 2nd best
            if second_cp is not None:
                second_win_prob = get_win_prob(second_cp)
                
                # Gap > 20% and not already winning massively
                if (best_win_prob - second_win_prob) > 20 and 10 < curr_win_prob < 90:
                     classification = "Great"
        else:
            classification = get_classification(win_diff)
        
        # Brilliant Move Override
        # (Sacrifice) and (Win Prob About the Same as Best Move) and (Not Significantly Behind)
        if is_sac and win_diff <= 5 and curr_win_prob > 20:
             classification = "Brilliant"

        # Miss (Winning -> Equal/Lost)
        # Prev Win% > 75% -> Curr Win% < 60%
        prev_cp_pers = prev_score if is_white else -prev_score
        prev_win_prob = get_win_prob(prev_cp_pers)
        
        if prev_win_prob > 75 and curr_win_prob < 60:
            classification = "Miss"

        # 5. CP Loss Calculation
        cp_loss = best_cp - my_cp
        if cp_loss < 0:
            cp_loss = 0

        # 6. Accuracy Calculation 
        move_accuracy = 103.1668 * exp(-0.04354 * win_diff) - 3.1669
        move_accuracy = max(0, min(100, move_accuracy))


        result = {
            "move_number": (i // 2) + 1,
            "move_uci": move_uci,
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
        
        print(f"Move: {move_uci:<5} | Class: {classification:<10} | Acc: {result['accuracy']:>5.1f}% | Eval: {curr_score_white:>+5} (White Win%: {white_win_prob:.1f}%) | Opening: {current_opening}") 

        prev_score = curr_score_white
        
    # Calculate Game Summary
    white_moves = [res for idx, res in enumerate(analysis_results) if idx % 2 == 0]
    black_moves = [res for idx, res in enumerate(analysis_results) if idx % 2 == 1]

    summary = {
        "white": calculate_stats(white_moves),
        "black": calculate_stats(black_moves)
    }

    return {
        "moves": analysis_results,
        "summary": summary
    }

