"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import ChessBoard from "../../components/ChessBoard";
import { Chess } from "chess.js";

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
    const [score, setScore] = useState(0);
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

        if (index === 0) {
            setScore(0);
            setLlmReview("");
            return;
        }

        const move = analysis[index - 1];
        if (!move) return;

        setScore(Number((move.score / 100).toFixed(2)));

        // Calculate FEN for RAG context
        let currentFen = "";
        try {
            const chess = new Chess();
            // Replay moves up to current index
            for (let i = 0; i < index; i++) {
                const m = analysis[i];
                if (m) {
                    try {
                        chess.move(m.move_san || m.move_uci);
                    } catch (e) {
                        try {
                            chess.move({ from: m.move_uci.slice(0, 2), to: m.move_uci.slice(2, 4), promotion: m.move_uci.length > 4 ? m.move_uci[4] : undefined });
                        } catch (e2) {
                            console.error("Move parse error:", m, e2);
                        }
                    }
                }
            }
            currentFen = chess.fen();
        } catch (e) {
            console.error("FEN generation error:", e);
        }

        // Fetch LLM review for this move
        setIsReviewLoading(true);
        setLlmReview("");
        try {
            const res = await fetch(`http://localhost:8000/review/move/${move.id}`);
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
                        <div className="score-container">
                            <span className="score-label">Score:</span>
                            <span className="score-value">{score}</span>
                        </div>

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
                                <div className="move-header">
                                    <span className="move-number-title">Move {currentAnalysis.move_number} ({currentAnalysis.color})</span>
                                    <span
                                        className="classification-badge"
                                        style={{ background: classColors[currentAnalysis.classification] || "#64748b" }}
                                    >
                                        {currentAnalysis.classification}
                                    </span>
                                </div>
                                {currentAnalysis.best_move && currentAnalysis.classification !== "Best" && currentAnalysis.classification !== "Book" && (
                                    <div className="best-move-hint">
                                        Engine recommends: <span className="font-bold">{currentAnalysis.best_move}</span>
                                    </div>
                                )}
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
