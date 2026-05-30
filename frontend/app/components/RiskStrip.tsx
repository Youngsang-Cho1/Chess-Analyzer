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
    currentPly?: number;
    onMoveClick: (index: number) => void;
}

function riskColor(p: number): string {
    // 0..1 → green → yellow → red
    if (p < 0.2) return "rgba(132, 204, 22, 0.35)";   // green-500/35
    if (p < 0.4) return "rgba(234, 179, 8, 0.45)";    // yellow-500
    if (p < 0.6) return "rgba(249, 115, 22, 0.55)";   // orange-500
    return "rgba(220, 38, 38, 0.7)";                  // red-600
}

export default function RiskStrip({ predictions, totalMoves, auc, currentPly, onMoveClick }: Props) {
    if (!predictions || predictions.length === 0) return null;

    return (
        <div className="mt-1">
            <div className="flex items-center justify-between mb-1 px-2">
                <span className="text-[10px] text-gray-400 uppercase tracking-wide">
                    Risk strip {auc !== undefined && <span className="ml-2 opacity-60">(AUC {auc.toFixed(2)})</span>}
                </span>
                <span className="text-[10px] text-gray-500">{predictions.length} of your moves</span>
            </div>
            <div className="relative">
                <div className="flex h-3 w-full overflow-hidden rounded">
                    {predictions.map((p, i) => {
                        const plyIndex = mapToPly(i, p.color, totalMoves);
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
                {/* Current move indicator dot */}
                {currentPly != null && currentPly > 0 && (() => {
                    const idx = predictions.findIndex((p, i) =>
                        mapToPly(i, p.color, totalMoves) === currentPly
                    );
                    if (idx < 0) return null;
                    const pct = (idx + 0.5) / predictions.length * 100;
                    return (
                        <div
                            className="absolute -top-1.5 w-2.5 h-2.5 rounded-full border-2 border-white shadow-md pointer-events-none"
                            style={{ left: `calc(${pct}% - 5px)`, background: "var(--primary)", transition: "left 0.2s ease" }}
                        />
                    );
                })()}
            </div>
        </div>
    );
}

function mapToPly(userMoveIdx: number, color: string, totalMoves: number): number {
    const offset = color === "white" ? 1 : 2;
    const ply = userMoveIdx * 2 + offset;
    return Math.min(totalMoves, Math.max(1, ply));
}
