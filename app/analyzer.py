import os
import chess.pgn
import io
import json
from dotenv import load_dotenv
from stockfish import Stockfish

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
            # normalized = "rnb... b KQkq e3. removing en passant and move counts parts"
            norm_key = " ".join(k.split(" ")[:4])
            eco_data[norm_key] = v
            
    print(f"Loaded {len(eco_data)} openings (Normalized).")
except Exception as e:
    print(f"Warning: ECO data missing: {e}")

def get_opening_details(board):
    # Lookup using Normalized FEN (Position + Turn + Castle + En Passant)
    fen_parts = board.fen().split(" ")
    norm_key = " ".join(fen_parts[:4])
    
    return eco_data.get(norm_key)

def get_classification(diff):
    # move quality classification
    if diff <= 20: 
        return "Excellent"
    if diff <= 50: 
        return "Good"
    if diff <= 100: 
        return "Inaccuracy"
    if diff <= 200: 
        return "Mistake"

    return "Blunder"

def analyze_game(pgn_string: str):
    # init engine
    engine = Stockfish(path=stockfish_path, depth=15, parameters={"Threads": 2, "Hash": 128})
    
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    board = game.board()
    
    analysis_results = []
    prev_score = 0
    current_opening = "Book Move"
    
    print("--- Analysis Start ---")

    for i, move in enumerate(game.mainline_moves()):
        is_white = board.turn
        move_uci = move.uci()
        
        # 1. Update board & Identify Opening
        board.push(move)
        opening_info = get_opening_details(board)
        if opening_info:
            current_opening = opening_info.get('name', current_opening)
        
        # 2. Get Best Move (before move)
        board.pop()
        engine.set_fen_position(board.fen())

        top_moves = engine.get_top_moves(2)['Move']


        best_move = top_moves[0]
        best_move_score = top_moves[0]['Centipawn']
        
        second_best_move = top_moves[1]
        second_best_move_score = None

        if second_best_move:
            second_best_move_score = top_moves[1]['Centipawn']
        
        board.push(move) # Restore state
        
        # 3. Evaluate Position
        engine.set_fen_position(board.fen())
        eval_data = engine.get_evaluation()
        
        if eval_data['type'] == 'mate':
            score_val = 20000 if eval_data['value'] > 0 else -20000
        else:
            score_val = eval_data['value']

        curr_score_white = score_val
        
        # 4. Classify Move
        classification = "Normal"
        second_best_move = engine.get_top_moves(2)[1]['Move']
        if move_uci == best_move and curr_score_white - second_best_move > 150:
            classification = "Great"
        
        if move_uci == best_move:
            classification = "Best" # if the move is the best move, the classification is just "Best"
            diff = 0

            if second_best_move_score and second_best_move_score - best_move_score > 150:
                classification = "Great" # if the move is the best move, but the second best move is much worse, the classification is "Great"
                                         # indicating that was the only "good" move in the position
        else:
            # POSITIVE diff = Bad move (Loss)
            # NEGATIVE diff = Good move (Gain, e.g. opponent blundered or the player found better move)
            
            if is_white: 
                diff = prev_score - curr_score_white 
            else:        
                diff = curr_score_white - prev_score 
            
            # If diff is negative (we improved position), simply treat loss as 0
            if diff < 0: 
                diff = 0

            classification = get_classification(diff)

        result = {
            "move_number": i + 1,
            "move_uci": move_uci,
            "score": curr_score_white,
            "classification": classification,
            "best_move": best_move,
            "opening": current_opening
        }
        analysis_results.append(result)
        
        print(f"Move: {move_uci}, Class: {classification}, Score: {curr_score_white}, Opening: {current_opening}")
        
        prev_score = curr_score_white

    return analysis_results
