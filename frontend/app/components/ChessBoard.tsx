"use client";

import { useState, useEffect } from "react";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";

interface Props {
    chess_PGN: string;
    initialMoveIndex: number;
    onMoveChange?: (index: number) => void;
}

export default function ChessBoard({ chess_PGN, initialMoveIndex, onMoveChange }: Props) {
    const game = new Chess();
    game.loadPgn(chess_PGN);

    const moves = game.history();
    const [moveIndex, setMoveIndex] = useState(initialMoveIndex ?? moves.length);

    // If parent changes initialMoveIndex, sync it
    useEffect(() => {
        if (initialMoveIndex !== undefined) {
            setMoveIndex(initialMoveIndex);
        }
    }, [initialMoveIndex]);

    const changeMoveIndex = (newIndex: number) => {
        setMoveIndex(newIndex);
        onMoveChange?.(newIndex);  // notify parent
    };

    const getPosition = () => {
        const tempGame = new Chess();
        for (let i = 0; i < moveIndex; i++) {
            tempGame.move(moves[i]);
        }
        return tempGame.fen();
    };

    const goToStart = () => changeMoveIndex(0);
    const goBack = () => changeMoveIndex(Math.max(0, moveIndex - 1));
    const goForward = () => changeMoveIndex(Math.min(moves.length, moveIndex + 1));
    const goToEnd = () => changeMoveIndex(moves.length);

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