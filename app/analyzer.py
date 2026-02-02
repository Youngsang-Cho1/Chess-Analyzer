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
    for piece in board.piece_map().values(): # piece_map() returns a dictionary of pieces on the board
        val = PIECE_VALUES.get(piece.piece_type, 0) # get the value of the piece
        if piece.color == chess.WHITE: white += val # if the piece is white, add the value to white
        else: black += val # if the piece is black, add the value to black
    return white, black

def analyze_game(pgn_string: str):
    # Optimized for M3 Chip (Threads=6, Hash=256)
    engine = Stockfish(path=stockfish_path, depth=18, parameters={"Threads": 6, "Hash": 256})
    
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    board = game.board()
    
    analysis_results = []
    prev_score = 0
    current_opening = "Opening Move"
    
    print("--- Analysis Start ---")

    for i, move in enumerate(game.mainline_moves()):
        if i // 2 >= 12 and current_opening == "Opening Move":
            current_opening = "No Opening detected"
        is_white = board.turn
        move_uci = move.uci()
        
        # 1. Checking Sacrifice
        # Check for Active Sacrifice (Brilliant candidate) before push
        is_sacrifice = False
        
        if board.is_capture(move): 
            # Check for Recapture (Opponent captured, I take back on same square)
            is_recapture = False
            if board.move_stack: # if previous move exists
                last_move = board.peek() # get previous move
                # If landing on square opponent just moved to, check if it was a capture
                if move.to_square == last_move.to_square:
                    board.pop() # remove last move
                    if board.is_capture(last_move): # if last move was a capture
                        is_recapture = True
                    board.push(last_move) # add last move back

            # Case A: Active Sacrifice
            my_piece = board.piece_at(move.from_square)
            target_piece = board.piece_at(move.to_square)
            
            if my_piece and target_piece:
                val_diff = PIECE_VALUES[my_piece.piece_type] - PIECE_VALUES[target_piece.piece_type]
                
                if board.is_attacked_by(not board.turn, move.to_square):
                    is_real_sacrifice = False
                    
                    if is_recapture:
                        # Recapture: Only a sacrifice if "Attacked by Cheaper Piece"
                        # e.g. Sac when Knight(3) recaptures Pawn(1), but Pawn(1) defends it
                        # e.g. Not a sac when Knight(3) recaptures Pawn(1), but Queen(9) defends it
    
                        threats = board.attackers(not board.turn, move.to_square) # all squares with defenders
                        min_threat_val = 100
                        for square in threats:
                            tp = board.piece_at(square)
                            if tp:
                                min_threat_val = min(min_threat_val, PIECE_VALUES[tp.piece_type])
                        
                        if min_threat_val < PIECE_VALUES[my_piece.piece_type]:
                            is_sacrifice = True
                    else:
                        # Initiative: Standard threshold (2 pts)
                        if val_diff >= 2:
                            is_sacrifice = True
                            
        else:
            # Case B: Passive Sacrifice (Move into danger w/o capturing)
            if board.is_attacked_by(not board.turn, move.to_square):
                my_piece = board.piece_at(move.from_square)
                threats = board.attackers(not board.turn, move.to_square)
                
                # Find lowest value threat
                min_threat_val = 100
                for square in threats:
                    threat_piece = board.piece_at(square)
                    min_threat_val = min(min_threat_val, PIECE_VALUES[threat_piece.piece_type])
                
                if PIECE_VALUES[my_piece.piece_type] - min_threat_val >= 2:
                    is_sacrifice = True
                    
                    

        board.push(move)
        opening_info = get_opening_details(board)
        if opening_info:
            current_opening = opening_info.get('name', current_opening)
        
        # 2. Get Top Moves (Best & Second Best)
        board.pop()
        engine.set_fen_position(board.fen())
        
        def get_score_val(move_data):
            if move_data.get('Mate') is not None:
                mate_in = move_data['Mate']
                return (20000 - abs(mate_in) * 10) * (1 if mate_in > 0 else -1)
            return move_data.get('Centipawn', 0)

        # Get top 2 moves
        top_moves = engine.get_top_moves(2)
        best_move = top_moves[0]['Move']
        best_score = get_score_val(top_moves[0])

        second_score = None
        if len(top_moves) > 1:
            second_score = get_score_val(top_moves[1])

        board.push(move) 
        
        # 3. Evaluate Current Position
        engine.set_fen_position(board.fen())
        eval_data = engine.get_evaluation()
        
        if eval_data['type'] == 'mate':
            mate_in = eval_data['value']
            score_val = (20000 - abs(mate_in) * 10) * (1 if mate_in > 0 else -1)
        else:
            score_val = eval_data['value']

        curr_score_white = score_val
        
        # Normalize current evaluation
        curr_score = score_val if is_white else -score_val # +: white, -: black advantage
        best_score_normalized = best_score if is_white else -best_score
        second_score_normalized = second_score if is_white else -second_score if second_score is not None else None
        
        # 4. Classify Move
        classification = "Normal"
        
        if move_uci == best_move:
            classification = "Best"
            diff = 0
            
            # Great logic only for Best moves
            if second_score_normalized is not None:
                gap = best_score_normalized - second_score_normalized

                # Gap > 100 & not already winning massively
                if gap > 100 and -200 < curr_score < 500:
                    classification = "Great"

        else:
            # Calculate Centipawn Loss
            if is_white: 
                diff = prev_score - curr_score_white 
            else:        
                diff = curr_score_white - prev_score 
            
            if diff < 0: 
                diff = 0

            classification = get_classification(diff)

        # [Global Check] Brilliant Move Override
        # Sacrifice + Sound Position + (Best or Excellent/Great i.e. diff <= 30)
        if is_sacrifice and diff <= 30 and curr_score > -100:
             classification = "Brilliant"

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
