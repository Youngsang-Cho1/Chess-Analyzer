"use client";

interface RiskPoint {
    move_id: number;
    move_number: number;
    color: string;
    risk: number;
    classification: string;
    reasons?: { feature: string; contribution: number }[];
}

// Pretty labels for the raw feature names exposed by the model.
const FEATURE_LABEL: Record<string, string> = {
    prev_eval_user: "current eval",
    eval_volatility: "eval volatility",
    move_number: "move number",
    time_frac: "time fraction",
    time_left_sec: "time left",
    mobility_user: "your mobility",
    material_diff: "material balance",
    king_attackers_user: "attackers on your king",
    king_attackers_enemy: "attackers on enemy king",
    threats_count: "threatened pieces",
    threats_value: "value at risk",
    enemy_threats_count: "your threats on enemy",
    in_check: "in check",
    isolated_pawns_user: "isolated pawns",
    doubled_pawns_user: "doubled pawns",
    passed_pawns_user: "passed pawns",
    passed_pawns_enemy: "enemy passed pawns",
    castling_rights_user: "castling rights",
};

function formatReasons(reasons?: { feature: string; contribution: number }[]): string {
    if (!reasons || reasons.length === 0) return "";
    return reasons
        .map((r) => {
            const sign = r.contribution > 0 ? "↑" : "↓";
            const label = FEATURE_LABEL[r.feature] || r.feature;
            return `${sign} ${label}`;
        })
        .join(", ");
}

interface Props {
    predictions: RiskPoint[];
    totalMoves: number;
    auc?: number;
    onMoveClick: (index: number) => void;
}

function riskColor(p: number): string {
    // 0..1 → green → yellow → red
    if (p < 0.2) return "rgba(132, 204, 22, 0.35)";   // green-500/35
    if (p < 0.4) return "rgba(234, 179, 8, 0.45)";    // yellow-500
    if (p < 0.6) return "rgba(249, 115, 22, 0.55)";   // orange-500
    return "rgba(220, 38, 38, 0.7)";                  // red-600
}

export default function RiskStrip({ predictions, totalMoves, auc, onMoveClick }: Props) {
    if (!predictions || predictions.length === 0) return null;

    // Map prediction by ply index in the full move list (each user-move alternates with opponent)
    // We use the prediction order as the user's ply sequence; ply index inside the full game =
    // index_in_full_list (we approximate by walking 0..totalMoves and picking when color matches).
    // Easier: render N user-move cells in a strip; align by hovering shows move_number.

    return (
        <div className="mt-1">
            <div className="flex items-center justify-between mb-1 px-2">
                <span className="text-[10px] text-gray-400 uppercase tracking-wide">
                    Risk strip {auc !== undefined && <span className="ml-2 opacity-60">(AUC {auc.toFixed(2)})</span>}
                </span>
                <span className="text-[10px] text-gray-500">{predictions.length} of your moves</span>
            </div>
            <div className="flex h-3 w-full overflow-hidden rounded">
                {predictions.map((p, i) => {
                    // ply index in the full game: user color at every other ply.
                    // Best-effort: each user move occupies one cell; click jumps to (i*2+1) approx,
                    // but parent passes totalMoves to scale.
                    const plyIndex = mapToPly(i, p.color, totalMoves, predictions.length);
                    return (
                        <button
                            key={p.move_id}
                            onClick={() => onMoveClick(plyIndex)}
                            title={`Move ${p.move_number} (${p.color}) — risk ${(p.risk * 100).toFixed(0)}%${p.classification ? " · " + p.classification : ""}${
                                p.reasons && p.reasons.length
                                    ? "\nDrivers: " + formatReasons(p.reasons)
                                    : ""
                            }`}
                            className="flex-1 h-full hover:opacity-100 opacity-90 transition-opacity"
                            style={{ background: riskColor(p.risk) }}
                        />
                    );
                })}
            </div>
        </div>
    );
}

function mapToPly(userMoveIdx: number, color: string, totalMoves: number, predCount: number): number {
    // Total user moves ≈ totalMoves / 2. If predCount matches that, ply ≈ userMoveIdx*2 + (color==='white'?1:2).
    const offset = color === "white" ? 1 : 2;
    const ply = userMoveIdx * 2 + offset;
    return Math.min(totalMoves, Math.max(1, ply));
}
