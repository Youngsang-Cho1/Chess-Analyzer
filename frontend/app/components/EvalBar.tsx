"use client";

interface Props {
    score: number;          // centipawns from White's POV
    mateIn?: number | null;
    height?: number;
}

const CAP = 1000;

export default function EvalBar({ score, mateIn, height = 520 }: Props) {
    let v = Math.max(-CAP, Math.min(CAP, score)) / CAP * 10; // -10..10
    if (mateIn !== null && mateIn !== undefined) v = mateIn > 0 ? 10 : -10;

    const whitePct = 50 + (v / 10) * 50;
    const label = mateIn !== null && mateIn !== undefined
        ? `M${Math.abs(mateIn)}`
        : (v >= 0 ? `+${(v).toFixed(1)}` : v.toFixed(1));

    return (
        <div className="evalbar" style={{ height }}>
            <div className="evalbar-white" style={{ height: `${whitePct}%` }} />
            <div className="evalbar-divider" style={{ top: `${100 - whitePct}%` }} />
            <div className={`evalbar-label ${v >= 0 ? "is-positive" : "is-negative"}`}>
                {label}
            </div>
        </div>
    );
}
