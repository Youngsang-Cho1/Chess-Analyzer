"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ChessBoard from "../../../components/ChessBoard";

interface MoveData {
    id: number;
    game_id: number;
    move_number: number;
    move_uci: string;
    move_san: string;
    score: number;
    classification: string;
    color: string;
    best_move: string;
    opening: string;
}

const classColors: Record<string, string> = {
    Brilliant: "#26c2a3",
    Great: "#5b8bb4",
    Book: "#a88b5e",
    Best: "#99cc68",
    Excellent: "#99cc68",
    Good: "#81b64c",
    Inaccuracy: "#f7c631",
    Mistake: "#e6912b",
    Blunder: "#ca3431",
    Miss: "#ff6b6b",
};

export default function MovesPage() {
    const params = useParams();
    const [moves, setMoves] = useState<MoveData[]>([]);
    const [gamePGN, setGamePGN] = useState("");
    const [selectedMove, setSelectedMove] = useState<MoveData | null>(null);
    const [moveIndex, setMoveIndex] = useState(0);

    useEffect(() => {
        const fetchMoves = async () => {
            const res = await fetch(`http://localhost:8000/moves/${params.username}/${params.classification}`);
            const data = await res.json();
            setMoves(data.moves);
        };
        fetchMoves();
    }, [params.username, params.classification]);

    const handleClick = async (move: MoveData) => {
        setSelectedMove(move);
        const res = await fetch(`http://localhost:8000/game/${move.game_id}`);
        const data = await res.json();
        setGamePGN(data.game.pgn);
        const idx = move.color === "white"
            ? (move.move_number * 2) - 1
            : (move.move_number * 2);
        setMoveIndex(idx);
    };

    return (
        <div className="analysis-page">
            <div className="max-w-container">
                <h1 className="page-title">
                    {params.classification} Moves ({moves.length})
                </h1>

                <div className="review-layout">
                    {/* Left: ChessBoard */}
                    <div className="review-board">
                        {gamePGN ? (
                            <ChessBoard
                                chess_PGN={gamePGN}
                                initialMoveIndex={moveIndex}
                            />
                        ) : (
                            <p style={{ color: "#64748b" }}>← click a move from the list</p>
                        )}

                        {selectedMove && (
                            <div className="move-info-card">
                                <span
                                    className="classification-badge"
                                    style={{ background: classColors[selectedMove.classification] || "#64748b" }}
                                >
                                    {selectedMove.classification}
                                </span>
                                <span className="move-detail">
                                    Game #{selectedMove.game_id} — Move {selectedMove.move_number} ({selectedMove.color})
                                    {selectedMove.best_move && selectedMove.classification !== "Best" && (
                                        <span className="best-move-hint"> • Best: {selectedMove.best_move}</span>
                                    )}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Right: Move List */}
                    <div className="review-moves">
                        <h3 className="moves-header">{params.classification} Moves</h3>
                        {moves.map((move) => (
                            <div
                                key={move.id}
                                className={`move-item ${selectedMove?.id === move.id ? "move-active" : ""}`}
                                onClick={() => handleClick(move)}
                            >
                                <span className="move-num">
                                    {move.move_number}.{move.color === "black" ? ".." : ""}
                                </span>
                                <span className="move-uci">{move.move_san || move.move_uci}</span>
                                <span
                                    className="move-class-dot"
                                    style={{ background: classColors[move.classification] || "#64748b" }}
                                >
                                    Game #{move.game_id}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}