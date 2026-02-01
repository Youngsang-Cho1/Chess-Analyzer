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

PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

def get_material_value(board):
    white, black = 0, 0
    for piece in board.piece_map().values():
        val = PIECE_VALUES.get(piece.piece_type, 0)
        if piece.color == chess.WHITE: white += val
        else: black += val
    return white, black

def analyze_game(pgn_string: str):
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
        
        # 1. Update board & Opening
        # Check for Active Sacrifice (Brilliant candidate) before push
        is_sacrifice = False
        if board.is_capture(move) and not board.is_en_passant(move):
            attacker = board.piece_at(move.from_square)
            victim = board.piece_at(move.to_square)
            if attacker and victim:
                val_diff = PIECE_VALUES[attacker.piece_type] - PIECE_VALUES[victim.piece_type]
                if val_diff >= 3: is_sacrifice = True # e.g. RxP (5-1=4), QxN (6)

        board.push(move)
        opening_info = get_opening_details(board)
        if opening_info:
            current_opening = opening_info.get('name', current_opening)
        
        # 2. Get Top Moves (Best & Second Best)
        board.pop()
        engine.set_fen_position(board.fen())
        
        # Get top 2 moves safely
        top_moves = engine.get_top_moves(2)
        best_move = top_moves[0]['Move']
        best_score = top_moves[0].get('Centipawn') 
        
        second_score = None
        if len(top_moves) > 1:
            second_score = top_moves[1].get('Centipawn')

        board.push(move) 
        
        # 3. Evaluate Current Position
        engine.set_fen_position(board.fen())
        eval_data = engine.get_evaluation()
        
        if eval_data['type'] == 'mate':
            score_val = 20000 if eval_data['value'] > 0 else -20000
        else:
            score_val = eval_data['value']

        curr_score_white = score_val
        
        # 4. Classify Move
        classification = "Normal"
        
        if move_uci == best_move:
            classification = "Best"
            diff = 0
            
            # Brilliant: Best Move + Active Sacrifice (e.g. QxN)
            if is_sacrifice:
                classification = "Brilliant"
            # Great: Best Move + Large Gap to 2nd Best (>150cp)
            elif best_score is not None and second_score is not None:
                gap = abs(best_score - second_score)
                if gap > 150:
                    classification = "Great"
                    
        else:
            # Calculate Centipawn Loss
            if is_white: diff = prev_score - curr_score_white 
            else:        diff = curr_score_white - prev_score 
            
            if diff < 0: diff = 0
            classification = get_classification(diff)

        result = {
            "move_number": (i // 2) + 1,
            "move_uci": move_uci,
            "score": curr_score_white,
            "classification": classification,
            "best_move": best_move,
            "opening": current_opening
        }
        analysis_results.append(result)
        
        prev_score = curr_score_white
        
        print(f"Move: {move_uci}, Class: {classification}, Score: {curr_score_white}, Opening: {current_opening}")

    return analysis_results
