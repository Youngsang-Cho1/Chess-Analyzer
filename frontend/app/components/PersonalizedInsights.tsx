"use client";

import { useEffect, useState } from "react";

interface PhaseRow {
    phase: string;
    moves: number;
    avg_quality: number;
    bad_move_rate: number;
}

interface OpeningRow {
    opening: string;
    games: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
    avg_accuracy: number;
}

interface BlunderBucket {
    range: string;
    count: number;
}

interface Insights {
    username: string;
    games_analyzed: number;
    phases: PhaseRow[];
    weakest_phase: string | null;
    openings: OpeningRow[];
    best_opening: OpeningRow | null;
    worst_opening: OpeningRow | null;
    blunder_buckets: BlunderBucket[];
    worst_move_range: string | null;
    blunders_by_captured_piece: { piece: string; count: number }[];
    total_bad_moves: number;
    color_quality: Record<string, { moves: number; avg_quality: number }>;
}

interface Props {
    username: string;
}

const phaseLabel: Record<string, string> = {
    opening: "Opening (≤ move 10)",
    middlegame: "Middlegame (11–29)",
    endgame: "Endgame (≥ move 30)",
};

function qualityTone(q: number): string {
    if (q >= 1) return "text-green-400";
    if (q >= 0) return "text-gray-300";
    if (q >= -0.5) return "text-yellow-400";
    return "text-red-400";
}

export default function PersonalizedInsights({ username }: Props) {
    const [data, setData] = useState<Insights | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!username) return;
        let cancelled = false;
        setLoading(true);
        setError(null);
        fetch(`http://localhost:8000/insights/${username}`)
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then((json) => {
                if (!cancelled) setData(json.insights);
            })
            .catch((e) => {
                if (!cancelled) setError(e.message || "Failed to load");
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [username]);

    if (loading) {
        return <div className="chart-card"><div className="chart-empty-state">Loading insights…</div></div>;
    }
    if (error || !data) {
        return (
            <div className="chart-card">
                <div className="chart-empty-state">
                    {error === "HTTP 404"
                        ? "Analyze some games first to unlock personalized insights."
                        : `Could not load insights${error ? `: ${error}` : ""}`}
                </div>
            </div>
        );
    }

    const headline = buildHeadline(data);

    return (
        <div className="space-y-6">
            {/* Headline */}
            <div className="ai-insights-card">
                <div className="ai-header">
                    <div>
                        <h2 className="ai-title">Personalized Insights</h2>
                        <p className="ai-subtitle">
                            Across {data.games_analyzed} analyzed games
                        </p>
                    </div>
                </div>
                <div className="ai-content-box">
                    <p className="ai-text">{headline}</p>
                </div>
            </div>

            {/* Phase quality */}
            <div className="chart-card">
                <h3 className="chart-title">Phase quality</h3>
                <table className="opening-table">
                    <thead className="opening-thead">
                        <tr className="opening-th-row">
                            <th className="opening-th opening-th-left">Phase</th>
                            <th className="opening-th opening-th-right">Moves</th>
                            <th className="opening-th opening-th-right">Avg quality</th>
                            <th className="opening-th opening-th-right">Bad-move %</th>
                        </tr>
                    </thead>
                    <tbody className="opening-tbody">
                        {data.phases.map((p) => (
                            <tr key={p.phase} className="opening-tr">
                                <td className="opening-td-name">{phaseLabel[p.phase] || p.phase}</td>
                                <td className="opening-td-count">{p.moves}</td>
                                <td className={`opening-td-count ${qualityTone(p.avg_quality)}`}>
                                    {p.avg_quality > 0 ? "+" : ""}
                                    {p.avg_quality.toFixed(2)}
                                </td>
                                <td className="opening-td-count">{p.bad_move_rate.toFixed(1)}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <p className="text-xs text-gray-400 mt-3">
                    Quality is a weighted score: Brilliant +4, Great +3, Best +2, Excellent +1, Good 0, Inaccuracy −1, Mistake/Miss −2, Blunder −4.
                </p>
            </div>

            {/* Opening performance */}
            <div className="chart-grid">
                <div className="chart-card">
                    <h3 className="chart-title">Best & worst openings</h3>
                    {data.best_opening ? (
                        <div className="mb-3">
                            <div className="text-sm text-gray-400">Best (≥2 games)</div>
                            <div className="text-lg text-green-400">{data.best_opening.opening}</div>
                            <div className="text-sm text-gray-300">
                                {data.best_opening.win_rate}% win · {data.best_opening.games} games · {data.best_opening.avg_accuracy}% acc
                            </div>
                        </div>
                    ) : (
                        <div className="chart-empty-state">Need more games per opening.</div>
                    )}
                    {data.worst_opening && data.worst_opening.opening !== data.best_opening?.opening && (
                        <div>
                            <div className="text-sm text-gray-400">Worst (≥2 games)</div>
                            <div className="text-lg text-red-400">{data.worst_opening.opening}</div>
                            <div className="text-sm text-gray-300">
                                {data.worst_opening.win_rate}% win · {data.worst_opening.games} games · {data.worst_opening.avg_accuracy}% acc
                            </div>
                        </div>
                    )}
                </div>

                <div className="chart-card">
                    <h3 className="chart-title">Top openings (most played)</h3>
                    <div className="opening-list-container custom-scrollbar">
                        <table className="opening-table">
                            <thead className="opening-thead">
                                <tr className="opening-th-row">
                                    <th className="opening-th opening-th-left">Opening</th>
                                    <th className="opening-th opening-th-right">Games</th>
                                    <th className="opening-th opening-th-right">Win %</th>
                                    <th className="opening-th opening-th-right">Acc</th>
                                </tr>
                            </thead>
                            <tbody className="opening-tbody">
                                {data.openings.map((o, i) => (
                                    <tr key={i} className="opening-tr">
                                        <td className="opening-td-name" title={o.opening}>{o.opening}</td>
                                        <td className="opening-td-count">{o.games}</td>
                                        <td className="opening-td-count">{o.win_rate}%</td>
                                        <td className="opening-td-count">{o.avg_accuracy}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Blunder patterns */}
            <div className="chart-grid">
                <div className="chart-card">
                    <h3 className="chart-title">When bad moves happen</h3>
                    {data.blunder_buckets.length === 0 ? (
                        <div className="chart-empty-state">No bad moves recorded — clean play.</div>
                    ) : (
                        <BlunderBars buckets={data.blunder_buckets} />
                    )}
                </div>

                <div className="chart-card">
                    <h3 className="chart-title">Bad moves by piece captured</h3>
                    {data.blunders_by_captured_piece.length === 0 ? (
                        <div className="chart-empty-state">No capture-related bad moves.</div>
                    ) : (
                        <table className="opening-table">
                            <thead className="opening-thead">
                                <tr className="opening-th-row">
                                    <th className="opening-th opening-th-left">Piece you took</th>
                                    <th className="opening-th opening-th-right">Bad moves</th>
                                </tr>
                            </thead>
                            <tbody className="opening-tbody">
                                {data.blunders_by_captured_piece.map((b, i) => (
                                    <tr key={i} className="opening-tr">
                                        <td className="opening-td-name">{b.piece}</td>
                                        <td className="opening-td-count">{b.count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

function BlunderBars({ buckets }: { buckets: BlunderBucket[] }) {
    const max = Math.max(...buckets.map((b) => b.count), 1);
    return (
        <div className="space-y-2">
            {buckets.map((b) => (
                <div key={b.range} className="flex items-center gap-3">
                    <div className="text-xs text-gray-400 w-16">moves {b.range}</div>
                    <div className="flex-1 bg-gray-800 rounded h-4 overflow-hidden">
                        <div
                            className="bg-red-500 h-full"
                            style={{ width: `${(b.count / max) * 100}%` }}
                        />
                    </div>
                    <div className="text-xs text-gray-300 w-8 text-right">{b.count}</div>
                </div>
            ))}
        </div>
    );
}

function buildHeadline(d: Insights): string {
    const bits: string[] = [];
    if (d.weakest_phase) {
        const wp = d.phases.find((p) => p.phase === d.weakest_phase);
        if (wp) {
            bits.push(
                `Weakest phase: ${d.weakest_phase} (avg quality ${wp.avg_quality > 0 ? "+" : ""}${wp.avg_quality.toFixed(2)}, ${wp.bad_move_rate.toFixed(1)}% bad moves).`
            );
        }
    }
    if (d.worst_opening && d.worst_opening.win_rate < 50 && d.worst_opening.games >= 3) {
        bits.push(
            `Struggle opening: ${d.worst_opening.opening} (${d.worst_opening.win_rate}% over ${d.worst_opening.games}).`
        );
    }
    if (d.best_opening && d.best_opening.win_rate >= 60 && d.best_opening.games >= 3) {
        bits.push(
            `Strong with: ${d.best_opening.opening} (${d.best_opening.win_rate}% over ${d.best_opening.games}).`
        );
    }
    if (d.worst_move_range) {
        bits.push(`Most bad moves happen around moves ${d.worst_move_range}.`);
    }
    return bits.length ? bits.join(" ") : "Not enough data yet — analyze a few more games.";
}
