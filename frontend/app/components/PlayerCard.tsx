"use client";

interface Props {
    color: "white" | "black";
    name: string;
    rating?: number | null;
    accuracy?: number | null;
    isToMove?: boolean;
    isWinner?: boolean;
}

export default function PlayerCard({ color, name, rating, accuracy, isToMove, isWinner }: Props) {
    const initial = (name || "?").trim().charAt(0).toUpperCase() || "?";
    return (
        <div className={`player-card ${isToMove ? "is-active" : ""}`}>
            <div className="player-card-head">
                <div className={`player-avatar ${color === "white" ? "is-white" : "is-black"}`}>
                    {initial}
                </div>
                <div className="player-card-name">
                    <div className="player-card-side">{color}</div>
                    <div className="player-card-username" title={name}>{name || "—"}</div>
                </div>
            </div>
            <div className="player-card-elo">{rating ? `${rating} ELO` : "Unrated"}</div>
            <div className="player-card-acc">
                <span className={`player-card-acc-val ${isWinner ? "is-winner" : ""}`}>
                    {accuracy != null ? accuracy.toFixed(1) : "—"}
                </span>
                <span className="player-card-acc-unit">%</span>
            </div>
            <div className="player-card-acc-label">Accuracy</div>
        </div>
    );
}
