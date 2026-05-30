"use client";

interface MoveLike {
    move_san?: string;
    move_uci?: string;
    move_number: number;
    color: string;
    classification: string;
    best_move?: string | null;
    score?: number | null;
    mate_in?: number | null;
}

interface Props {
    move: MoveLike | null;
    review: string;
    loading: boolean;
}

const CLS_COLOR: Record<string, string> = {
    Brilliant: "var(--cls-brilliant)",
    Great: "var(--cls-great)",
    Best: "var(--cls-best)",
    Excellent: "var(--cls-excellent)",
    Good: "var(--cls-good)",
    Book: "var(--cls-book)",
    Forced: "var(--cls-book)",
    Inaccuracy: "var(--cls-inaccuracy)",
    Mistake: "var(--cls-mistake)",
    Miss: "var(--cls-miss)",
    Blunder: "var(--cls-blunder)",
};

const CLS_GLYPH: Record<string, string> = {
    Brilliant: "!!",
    Great: "!",
    Best: "★",
    Excellent: "★",
    Good: "✓",
    Book: "📖",
    Forced: "⤳",
    Inaccuracy: "?!",
    Mistake: "?",
    Miss: "✕",
    Blunder: "??",
};

export default function GMCommentary({ move, review, loading }: Props) {
    if (!move) {
        return (
            <div className="gm-card">
                <div className="gm-header">
                    <div className="gm-badge">GM</div>
                    <div className="gm-voice">AI Coach</div>
                </div>
                <div className="gm-quote">“Pick a move on the board.”</div>
            </div>
        );
    }

    const color = CLS_COLOR[move.classification] || "var(--foreground)";
    const glyph = CLS_GLYPH[move.classification] || "";
    const side = move.color === "white" ? "" : "...";

    const cpLabel = move.mate_in != null
        ? `M${Math.abs(move.mate_in)}`
        : move.score != null
            ? `${move.score >= 0 ? "+" : ""}${(move.score / 100).toFixed(2)}`
            : null;

    const cpPositive = move.mate_in != null ? move.mate_in > 0 : (move.score ?? 0) >= 0;

    return (
        <div className="gm-card">
            <div className="gm-header">
                <div className="gm-badge">GM</div>
                <div className="gm-voice">AI Coach</div>
                <div className="gm-chip" style={{ color, borderColor: `${color}55`, background: `${color}1a` }}>
                    <span className="gm-chip-glyph">{glyph}</span>
                    {move.classification}
                </div>
                {cpLabel && (
                    <div className="gm-cp-pill" style={{ color: cpPositive ? "var(--cls-best)" : "var(--cls-blunder)" }}>
                        {cpLabel}
                    </div>
                )}
            </div>

            <div className="gm-move-row">
                <span className="gm-move-num">
                    {move.move_number}{side ? side : "."}
                </span>
                <span className="gm-move-san" style={{ color }}>
                    {move.move_san || move.move_uci}
                </span>
            </div>

            <div className="gm-quote">
                {loading ? <span className="gm-quote-loading">Coaching…</span> : (review ? `“${review}”` : "Click for an AI review.")}
            </div>

            {move.best_move && !["Best", "Book", "Forced", "Brilliant"].includes(move.classification) && (
                <div className="gm-bestmove">
                    <span className="gm-bestmove-arrow">↑</span>
                    <span className="gm-bestmove-label">Best was</span>
                    <span className="gm-bestmove-san">{move.best_move}</span>
                </div>
            )}
        </div>
    );
}
