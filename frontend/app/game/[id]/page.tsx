"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ChessBoard from "../../components/ChessBoard";
import EvalChart from "../../components/EvalChart";
import RiskStrip from "../../components/RiskStrip";
import EvalBar from "../../components/EvalBar";
import PlayerCard from "../../components/PlayerCard";
import GMCommentary from "../../components/GMCommentary";
import MoveGrid from "../../components/MoveGrid";

interface GameData {
    id: number;
    pgn: string;
    white_username: string;
    black_username: string;
    white_rating?: number | null;
    black_rating?: number | null;
    white_accuracy?: number | null;
    black_accuracy?: number | null;
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
    mate_in?: number | null;
    best_mate_in?: number | null;
    classification: string;
    color: string;
    best_move: string;
    opening: string;
}

interface RiskPred {
    move_id: number;
    move_number: number;
    color: string;
    risk: number;
    classification: string;
    reasons?: { feature: string; contribution: number }[];
}

export default function GamePage() {
    const params = useParams();
    const [game, setGame] = useState<GameData | null>(null);
    const [analysis, setAnalysis] = useState<MoveAnalysis[]>([]);
    const [currentMoveIndex, setCurrentMoveIndex] = useState(0);
    const [llmReview, setLlmReview] = useState("");
    const [isReviewLoading, setIsReviewLoading] = useState(false);

    const [riskData, setRiskData] = useState<{ predictions: RiskPred[]; trained: boolean; auc?: number; reason?: string }>({
        predictions: [],
        trained: false,
    });
    const [trainingRisk, setTrainingRisk] = useState(false);
    const [trainError, setTrainError] = useState<string | null>(null);

    useEffect(() => {
        const fetchGame = async () => {
            const res = await fetch(`http://localhost:8000/game/${params.id}`);
            const data = await res.json();
            setGame(data.game);
            setAnalysis(data.analysis || []);
        };
        fetchGame();
    }, [params.id]);

    useEffect(() => {
        const fetchRisk = async () => {
            try {
                const res = await fetch(`http://localhost:8000/risk/${params.id}`);
                if (!res.ok) return;
                const data = await res.json();
                setRiskData({
                    predictions: data.predictions || [],
                    trained: !!data.trained,
                    auc: data.auc,
                    reason: data.reason,
                });
            } catch (e) {
                console.error("risk fetch failed", e);
            }
        };
        fetchRisk();
    }, [params.id]);

    // Keyboard nav
    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === "ArrowRight" && currentMoveIndex < analysis.length) handleMoveClick(currentMoveIndex + 1);
            else if (e.key === "ArrowLeft" && currentMoveIndex > 0) handleMoveClick(currentMoveIndex - 1);
            else if (e.key === "Home") handleMoveClick(0);
            else if (e.key === "End") handleMoveClick(analysis.length);
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentMoveIndex, analysis.length]);

    const handleMoveChange = (index: number) => setCurrentMoveIndex(index);

    const handleMoveClick = async (index: number) => {
        setCurrentMoveIndex(index);
        if (index === 0) {
            setLlmReview("");
            return;
        }
        const move = analysis[index - 1];
        if (!move) return;

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

    const trainRiskModel = async () => {
        if (!game) return;
        const username = game.white_username;
        setTrainingRisk(true);
        setTrainError(null);
        try {
            const res = await fetch(`http://localhost:8000/risk/train/${username}`, { method: "POST" });
            const data = await res.json();
            if (!res.ok) {
                setTrainError(data.detail || "Training failed");
            } else {
                const r = await fetch(`http://localhost:8000/risk/${params.id}`);
                if (r.ok) {
                    const rd = await r.json();
                    setRiskData({
                        predictions: rd.predictions || [],
                        trained: !!rd.trained,
                        auc: rd.auc,
                        reason: rd.reason,
                    });
                }
            }
        } catch (e) {
            setTrainError(String(e));
        } finally {
            setTrainingRisk(false);
        }
    };

    const chartPoints = analysis.map((move, i) => ({
        index: i + 1,
        label: `${move.move_number}${move.color === "black" ? "..." : "."} ${move.move_san || move.move_uci}`,
        raw: move.score,
        score: move.score,
        mate_in: move.mate_in,
        classification: move.classification,
    }));

    const currentAnalysis = analysis.length > 0 && currentMoveIndex > 0 ? analysis[currentMoveIndex - 1] : null;
    const sideToMove = currentMoveIndex % 2 === 0 ? "white" : "black";

    if (!game) {
        return <div className="analysis-page">Loading…</div>;
    }

    const whiteWon = game.white_result === "1";
    const blackWon = game.black_result === "1";

    return (
        <div className="analysis-page salon">
            <div className="max-w-container">
                <Link href="/" className="back-link">← Dashboard</Link>

                {/* Title block */}
                <div className="salon-title-block">
                    <div className="salon-title">
                        {game.opening?.split(":")[0] || "Game"}
                    </div>
                    <div className="salon-subtitle">
                        Move {Math.ceil(Math.max(1, currentMoveIndex) / 2)} · {sideToMove} to play · {game.time_control}
                    </div>
                </div>

                <div className="salon-layout">
                    {/* Left rail: player cards + result */}
                    <aside className="salon-rail">
                        <PlayerCard
                            color="black"
                            name={game.black_username}
                            rating={game.black_rating}
                            accuracy={game.black_accuracy}
                            isToMove={sideToMove === "black" && currentMoveIndex < analysis.length}
                            isWinner={blackWon}
                        />
                        <div className="salon-rail-center">
                            <div className="salon-result">
                                {whiteWon ? "1–0" : blackWon ? "0–1" : "½–½"}
                            </div>
                            <div className="salon-result-detail">
                                {whiteWon ? "White wins" : blackWon ? "Black wins" : "Draw"}
                            </div>
                        </div>
                        <PlayerCard
                            color="white"
                            name={game.white_username}
                            rating={game.white_rating}
                            accuracy={game.white_accuracy}
                            isToMove={sideToMove === "white" && currentMoveIndex < analysis.length}
                            isWinner={whiteWon}
                        />
                    </aside>

                    {/* Center: board + eval bar + eval chart */}
                    <section className="salon-center">
                        <div className="salon-board-row">
                            <EvalBar
                                score={currentAnalysis?.score ?? 0}
                                mateIn={currentAnalysis?.mate_in}
                            />
                            <div className="salon-board-wrap">
                                <ChessBoard
                                    chess_PGN={game.pgn}
                                    initialMoveIndex={currentMoveIndex}
                                    onMoveChange={handleMoveChange}
                                />
                            </div>
                        </div>

                        {chartPoints.length > 0 && (
                            <div className="salon-evalcard">
                                <div className="salon-evalcard-head">
                                    <span>Evaluation</span>
                                    <span className="salon-evalcard-meta">
                                        {currentAnalysis ? currentAnalysis.move_san : "—"}
                                    </span>
                                </div>
                                <EvalChart
                                    points={chartPoints}
                                    currentIndex={currentMoveIndex}
                                    onMoveClick={handleMoveClick}
                                />
                                {riskData.trained && riskData.predictions.length > 0 && (
                                    <RiskStrip
                                        predictions={riskData.predictions}
                                        totalMoves={analysis.length}
                                        auc={riskData.auc}
                                        currentPly={currentMoveIndex}
                                        onMoveClick={handleMoveClick}
                                    />
                                )}
                                {!riskData.trained && (
                                    <div className="salon-risk-empty">
                                        <span>{riskData.reason || "Risk model not trained."}</span>
                                        <button
                                            onClick={trainRiskModel}
                                            disabled={trainingRisk}
                                            className="salon-risk-btn"
                                        >
                                            {trainingRisk ? "Training…" : "Train risk model"}
                                        </button>
                                    </div>
                                )}
                                {trainError && <div className="salon-risk-err">{trainError}</div>}
                            </div>
                        )}
                    </section>

                    {/* Right: GM commentary + move grid */}
                    <aside className="salon-aside">
                        <GMCommentary
                            move={currentAnalysis}
                            review={llmReview}
                            loading={isReviewLoading}
                        />

                        <MoveGrid
                            moves={analysis}
                            currentPly={currentMoveIndex}
                            onSelect={handleMoveClick}
                        />
                    </aside>
                </div>
            </div>
        </div>
    );
}
