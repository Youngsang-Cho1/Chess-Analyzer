import os
import chess.pgn
import io
from dotenv import load_dotenv
from stockfish import Stockfish

load_dotenv()

stockfish_path = os.getenv("STOCKFISH_PATH")

def get_classification(diff):
    if diff <= 20: return "Excellent"
    if diff <= 50: return "Good"
    if diff <= 100: return "Inaccuracy"
    if diff <= 200: return "Mistake"
    return "Blunder"

def analyze_game(pgn_string: str):
    # init engine
    engine = Stockfish(path=stockfish_path, depth=15, parameters={"Threads": 2, "Hash": 128})
    
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    
    board = game.board()
    
    analysis_results = []
    prev_score = 0
    
    print("--- Starting Detailed Analysis ---")

    for i, move in enumerate(game.mainline_moves()):
        is_white = board.turn # white turn?
        
        # get best move
        engine.set_fen_position(board.fen())
        best_move = engine.get_best_move()
        
        # push move
        board.push(move)
        
        # evaluate
        engine.set_fen_position(board.fen())
        eval_data = engine.get_evaluation()
        
        # handle mate
        if eval_data['type'] == 'mate':
            score_val = 20000 if eval_data['value'] > 0 else -20000
        else:
            score_val = eval_data['value']

        # current score (white POV)
        curr_score_white = score_val
        
        # classify move
        classification = "Normal"
        
        if move.uci() == best_move:
            classification = "Best"
            diff = 0
        else:
            # calc diff (player perspective)
            if is_white:
                diff = prev_score - curr_score_white
            else:
                diff = curr_score_white - prev_score
            
            # clamp neg diffs (position improved)
            if diff < 0: diff = 0
            
            classification = get_classification(diff)

        result = {
            "move_number": i + 1,
            "move_uci": move.uci(),
            "score": curr_score_white,
            "classification": classification,
            "best_move": best_move
        }
        analysis_results.append(result)
        
        print(f"Move: {move}, Class: {classification}, Score: {curr_score_white}, Best: {best_move}")
        
        prev_score = curr_score_white

    return analysis_results
