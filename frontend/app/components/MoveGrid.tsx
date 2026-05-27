"use client";

interface MoveItem {
    id: number;
    move_number: number;
    move_san?: string;
    move_uci?: string;
    classification: string;
    color: string;
}

interface Props {
    moves: MoveItem[];
    currentPly: number;
    onSelect: (ply: number) => void;
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
    Inaccuracy: "?!",
    Mistake: "?",
    Miss: "✕",
    Blunder: "??",
};

export default function MoveGrid({ moves, currentPly, onSelect }: Props) {
    // Pair into rows of (white, black)
    const rows: { num: number; w?: MoveItem & { ply: number }; b?: MoveItem & { ply: number } }[] = [];
    moves.forEach((m, i) => {
        const ply = i + 1;
        const rowIdx = Math.floor(i / 2);
        if (!rows[rowIdx]) rows[rowIdx] = { num: rowIdx + 1 };
        const cell = { ...m, ply };
        if (m.color === "white") rows[rowIdx].w = cell;
        else rows[rowIdx].b = cell;
    });

    return (
        <div className="movegrid">
            <div className="movegrid-head">
                <span>Moves</span>
                <span className="movegrid-count">{moves.length} ply</span>
            </div>
            <div className="movegrid-scroll">
                {rows.map((row) => (
                    <div key={row.num} className="movegrid-row">
                        <span className="movegrid-num">{row.num}.</span>
                        <MoveCell cell={row.w} currentPly={currentPly} onSelect={onSelect} />
                        <MoveCell cell={row.b} currentPly={currentPly} onSelect={onSelect} />
                    </div>
                ))}
            </div>
        </div>
    );
}

function MoveCell({
    cell,
    currentPly,
    onSelect,
}: {
    cell?: MoveItem & { ply: number };
    currentPly: number;
    onSelect: (ply: number) => void;
}) {
    if (!cell) return <div className="movegrid-cell movegrid-cell-empty" />;
    const active = currentPly === cell.ply;
    const color = CLS_COLOR[cell.classification] || "var(--foreground)";
    const glyph = CLS_GLYPH[cell.classification];
    return (
        <button
            className={`movegrid-cell ${active ? "is-active" : ""}`}
            onClick={() => onSelect(cell.ply)}
            style={active ? { borderColor: color } : undefined}
        >
            <span className="movegrid-san" style={{ color: active ? color : undefined }}>
                {cell.move_san || cell.move_uci}
            </span>
            {glyph && <span className="movegrid-glyph" style={{ color }}>{glyph}</span>}
        </button>
    );
}
