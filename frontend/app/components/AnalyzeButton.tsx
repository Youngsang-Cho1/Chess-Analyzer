"use client";
import { useState } from "react";

interface Props {
    isAnalyzing: boolean;
    handleAnalyze: (limit: number) => void;
    username: string;
}

const PRESETS = [5, 20, 50, 100];

export default function AnalyzeButton({ isAnalyzing, handleAnalyze, username }: Props) {
    const [selected, setSelected] = useState(20);

    return (
        <div className="analyze-hero">
            <div className="analyze-hero-label">NEW GAMES TO ANALYZE</div>
            <div className="analyze-hero-controls">
                <div className="analyze-preset-row">
                    {PRESETS.map((n) => (
                        <button
                            key={n}
                            onClick={() => setSelected(n)}
                            disabled={isAnalyzing}
                            className={`analyze-preset-btn ${selected === n ? "analyze-preset-active" : ""}`}
                        >
                            {n}
                        </button>
                    ))}
                    <input
                        type="number"
                        min="1"
                        max="500"
                        value={selected}
                        onChange={(e) => setSelected(Number(e.target.value) || 5)}
                        disabled={isAnalyzing}
                        className="analyze-custom-input"
                    />
                </div>
                <button
                    onClick={() => handleAnalyze(selected)}
                    disabled={isAnalyzing}
                    className={`analyze-hero-btn ${isAnalyzing ? "analyze-hero-btn--busy" : ""}`}
                >
                    {isAnalyzing
                        ? <><span className="analyze-spinner" /> Analyzing {username}…</>
                        : <>Analyze {username}</>
                    }
                </button>
            </div>
        </div>
    );
}
