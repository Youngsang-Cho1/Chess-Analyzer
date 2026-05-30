"use client";
import { useState } from "react";

interface Props {
    isAnalyzing: boolean;
    handleAnalyze: (limit: number, opponent?: string) => void;
    username: string;
}

export default function OpponentSearch({ isAnalyzing, handleAnalyze }: Props) {
    const [opponent, setOpponent] = useState("");
    const [limit, setLimit] = useState(20);

    const handleClick = () => {
        if (!opponent.trim()) {
            alert("Please enter an opponent username.");
            return;
        }
        handleAnalyze(limit, opponent.trim());
    };

    return (
        <div className="analyze-hero">
            <div className="analyze-hero-label">ANALYZE VS OPPONENT</div>
            <div className="analyze-hero-controls">
                <input
                    type="text"
                    placeholder="Opponent username…"
                    value={opponent}
                    onChange={(e) => setOpponent(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleClick()}
                    disabled={isAnalyzing}
                    className="analyze-custom-input"
                    style={{ width: "160px" }}
                />
                <input
                    type="number"
                    min="1"
                    max="200"
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value) || 20)}
                    disabled={isAnalyzing}
                    className="analyze-custom-input"
                />
                <button
                    onClick={handleClick}
                    disabled={isAnalyzing}
                    className={`analyze-hero-btn ${isAnalyzing ? "analyze-hero-btn--busy" : ""}`}
                >
                    {isAnalyzing ? "Analyzing…" : "Analyze vs Opponent"}
                </button>
            </div>
        </div>
    );
}