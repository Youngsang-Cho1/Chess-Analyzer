"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import ChessBoard from "../../components/ChessBoard";

interface GameData {
    id: number;
    pgn: string;
    white_username: string;
    black_username: string;
    white_result: string;
    black_result: string;
    time_control: string;
    opening: string;
}

interface MoveAnalysis {
    id: number;
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

export default function GamePage() {
    const params = useParams();
    const [game, setGame] = useState<GameData | null>(null);
    const [analysis, setAnalysis] = useState<MoveAnalysis[]>([]);
    const [currentMoveIndex, setCurrentMoveIndex] = useState(0);
    const [llmReview, setLlmReview] = useState("");
    const [isReviewLoading, setIsReviewLoading] = useState(false);
    const moveListRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchGame = async () => {
            const res = await fetch(`http://localhost:8000/game/${params.id}`);
            const data = await res.json();
            setGame(data.game);
            setAnalysis(data.analysis || []);
        };
        fetchGame();
    }, [params.id]);

    // Auto-scroll move list to current move
    useEffect(() => {
        if (moveListRef.current) {
            const activeItem = moveListRef.current.querySelector(".move-active");
            if (activeItem) {
                activeItem.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }
    }, [currentMoveIndex]);

    const handleMoveChange = (index: number) => {
        setCurrentMoveIndex(index);
    };

    const handleMoveClick = async (index: number) => {
        setCurrentMoveIndex(index);

        // Fetch LLM review for this move
        const move = analysis[index - 1];
        if (!move) return;

        setIsReviewLoading(true);
        setLlmReview("");
        try {
            const res = await fetch(`http://localhost:8000/review/move/${move.id}`, {
                method: "POST",
            });
            const data = await res.json();
            setLlmReview(data.review);
        } catch {
            setLlmReview("Failed to load review.");
        }
        setIsReviewLoading(false);
    };

    // Get classification for current move
    const currentAnalysis = analysis.length > 0 && currentMoveIndex > 0
        ? analysis[currentMoveIndex - 1]
        : null;

    if (!game) {
        return <div className="analysis-page">Loading...</div>;
    }

    return (
        <div className="analysis-page">
            <div className="max-w-container">
                <h1 className="page-title">
                    {game.white_username} vs {game.black_username}
                </h1>
                <p className="game-subtitle">
                    {game.opening} • {game.time_control}
                </p>

                <div className="review-layout">
                    {/* Left: ChessBoard + Move Info + LLM Review */}
                    <div className="review-board">
                        <ChessBoard
                            chess_PGN={game.pgn}
                            initialMoveIndex={currentMoveIndex}
                            onMoveChange={handleMoveChange}
                        />
                    </div>

                    {/* Right: Move List */}
                    <div className="review-moves" ref={moveListRef}>
                        <h3 className="moves-header">Moves</h3>

                        {/* LLM Review */}
                        {isReviewLoading && (
                            <div className="llm-review-card">
                                <div className="review-loading">
                                    <span className="loading-dot"></span>
                                    <span className="loading-dot"></span>
                                    <span className="loading-dot"></span>
                                    Reviewing...
                                </div>
                            </div>
                        )}
                        {llmReview && !isReviewLoading && (
                            <div className="llm-review-card">
                                <h4 className="review-title">AI Coach</h4>
                                <p className="review-text">{llmReview}</p>
                            </div>
                        )}

                        {/* Current move info */}
                        {currentAnalysis && (
                            <div className="move-info-card">
                                <span
                                    className="classification-badge"
                                    style={{ background: classColors[currentAnalysis.classification] || "#64748b" }}
                                >
                                    {currentAnalysis.classification}
                                </span>
                                <span className="move-detail">
                                    Move {currentAnalysis.move_number} ({currentAnalysis.color})
                                    {currentAnalysis.best_move && currentAnalysis.classification !== "Best" && currentAnalysis.classification !== "Book" && (
                                        <span className="best-move-hint"> • Best: {currentAnalysis.best_move}</span>
                                    )}
                                </span>
                            </div>
                        )}
                        {analysis.map((move, i) => (
                            <div
                                key={move.id}
                                className={`move-item ${currentMoveIndex === i + 1 ? "move-active" : ""}`}
                                onClick={() => handleMoveClick(i + 1)}
                            >
                                <span className="move-num">
                                    {move.move_number}.{move.color === "black" ? ".." : ""}
                                </span>
                                <span className="move-uci">{move.move_san || move.move_uci}</span>
                                <span
                                    className="move-class-dot"
                                    style={{ background: classColors[move.classification] || "#64748b" }}
                                    title={move.classification}
                                >
                                    {move.classification}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
