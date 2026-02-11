"use client";

import { useState } from "react";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";

interface Props {
    chess_PGN: string;
}

export default function ChessBoard({ chess_PGN }: Props) {
    const game = new Chess();
    game.loadPgn(chess_PGN);

    const moves = game.history(); // all moves
    const [moveIndex, setMoveIndex] = useState(moves.length); // display last move first

    const getPosition = () => {
        const tempGame = new Chess();
        for (let i = 0; i < moveIndex; i++) {
            tempGame.move(moves[i]);
        }
        return tempGame.fen();
    };

    const goToStart = () => setMoveIndex(0);
    const goBack = () => setMoveIndex(Math.max(0, moveIndex - 1));
    const goForward = () => setMoveIndex(Math.min(moves.length, moveIndex + 1));
    const goToEnd = () => setMoveIndex(moves.length);

    return (
        <div className="board-wrapper">
            <div className="chessboard-container">
                <Chessboard options={{ position: getPosition(), allowDragging: false }} />
            </div>

            <div className="board-controls">
                <button onClick={goToStart} className="board-btn">start</button>
                <button onClick={goBack} className="board-btn">⟨</button>
                <span className="board-move-counter">
                    {moveIndex} / {moves.length}
                </span>
                <button onClick={goForward} className="board-btn">⟩</button>
                <button onClick={goToEnd} className="board-btn">end</button>
            </div>
        </div>
    );
}