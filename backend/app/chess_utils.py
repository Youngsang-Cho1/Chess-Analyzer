import chess

def get_board_description(board: chess.Board, opening_name: str) -> str:
    # 1. Basic Game State
    color = "White" if board.turn == chess.WHITE else "Black"
    full_move = board.fullmove_number
    phase = "Opening" if full_move < 10 else "Middlegame" if full_move < 30 else "Endgame"

    # 2. Material & Imbalance
    piece_values = {
        chess.PAWN: 1, 
        chess.KNIGHT: 3, 
        chess.BISHOP: 3, 
        chess.ROOK: 5, 
        chess.QUEEN: 9}
    white_mat = sum(len(board.pieces(p, chess.WHITE)) * v for p, v in piece_values.items())
    black_mat = sum(len(board.pieces(p, chess.BLACK)) * v for p, v in piece_values.items())
    mat_diff = white_mat - black_mat
    
    mat_desc = "Materials are equal"
    if mat_diff > 0: mat_desc = f"White is up {mat_diff} points of material"
    elif mat_diff < 0: mat_desc = f"Black is up {abs(mat_diff)} points of material"

    # 3. Center Control (e4, d4, e5, d5)
    center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
    center_control = []
    for sq in center_squares:
        p = board.piece_at(sq)
        if p and p.piece_type == chess.PAWN:
            center_control.append(f"{chess.COLOR_NAMES[p.color].title()} pawn on {chess.SQUARE_NAMES[sq]}")
    center_desc = ", ".join(center_control) if center_control else "Center is open"

    # 4. Castling Rights & King Safety
    castling_desc = []
    if board.has_kingside_castling_rights(chess.WHITE): castling_desc.append("White can castle kingside")
    if board.has_queenside_castling_rights(chess.WHITE): castling_desc.append("White can castle queenside")
    if board.has_kingside_castling_rights(chess.BLACK): castling_desc.append("Black can castle kingside")
    if board.has_queenside_castling_rights(chess.BLACK): castling_desc.append("Black can castle queenside")
    safety_desc = ". ".join(castling_desc) if castling_desc else "Both sides have lost castling rights"

    # 5. Development (Knights & Bishops off back rank)
    white_dev = sum(1 for sq in [chess.B1, chess.G1, chess.C1, chess.F1] if board.piece_at(sq) is None)
    black_dev = sum(1 for sq in [chess.B8, chess.G8, chess.C8, chess.F8] if board.piece_at(sq) is None)
    dev_desc = f"White has developed {white_dev}/4 minor pieces. Black has developed {black_dev}/4 minor pieces"

    # Construct the semantic description
    description = (
        f"Chess game in the {phase}. Opening: {opening_name}. {mat_desc}. "
        f"Current turn: {color}. "
        f"Center control: {center_desc}. "
        f"Development: {dev_desc}. "
        f"King Safety: {safety_desc}."
    )
    
    return description
