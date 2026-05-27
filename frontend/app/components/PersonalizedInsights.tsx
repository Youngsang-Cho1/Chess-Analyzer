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
    opening: "Opening · moves 1–10",
    middlegame: "Middlegame · 11–29",
    endgame: "Endgame · 30+",
};

function qualityTone(q: number): string {
    if (q >= 1) return "tone-good";
    if (q >= 0) return "tone-mute";
    if (q >= -0.5) return "tone-warn";
    return "tone-bad";
}

function fmtQuality(q: number): string {
    return `${q > 0 ? "+" : ""}${q.toFixed(2)}`;
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
        return (
            <div className="insights-section">
                <div className="empty-state">Loading insights…</div>
            </div>
        );
    }
    if (error || !data) {
        return (
            <div className="insights-section">
                <div className="empty-state">
                    {error === "HTTP 404"
                        ? "Analyze a few games first to unlock personalized insights."
                        : `Could not load insights${error ? `: ${error}` : ""}`}
                </div>
            </div>
        );
    }

    const headline = buildHeadline(data);

    return (
        <div className="insights-stack">
            {/* Headline */}
            <div className="insights-headline">
                <div className="insights-headline-eyebrow">
                    Insights · {data.games_analyzed} games analyzed
                </div>
                <div className="insights-headline-text">{headline}</div>
            </div>

            {/* Phase quality */}
            <div className="insights-section">
                <h3 className="insights-section-title">Phase quality</h3>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Phase</th>
                            <th className="num">Moves</th>
                            <th className="num">Avg quality</th>
                            <th className="num">Bad-move %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.phases.map((p) => (
                            <tr key={p.phase}>
                                <td className="name">{phaseLabel[p.phase] || p.phase}</td>
                                <td className="num">{p.moves}</td>
                                <td className={`num ${qualityTone(p.avg_quality)}`}>
                                    {fmtQuality(p.avg_quality)}
                                </td>
                                <td className="num">{p.bad_move_rate.toFixed(1)}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <p className="insights-section-caption">
                    Quality score: Brilliant +4 · Great +3 · Best +2 · Excellent +1 · Inaccuracy −1 · Mistake/Miss −2 · Blunder −4.
                </p>
            </div>

            {/* Openings */}
            <div className="insights-grid">
                <div className="insights-section">
                    <h3 className="insights-section-title">Best & worst openings</h3>
                    {!data.best_opening && !data.worst_opening ? (
                        <div className="empty-state">Need at least 2 games per opening.</div>
                    ) : (
                        <div className="kpi-row">
                            {data.best_opening && (
                                <div className="kpi-tile">
                                    <div className="kpi-tile-label tone-good">Best</div>
                                    <div className="kpi-tile-name">{data.best_opening.opening}</div>
                                    <div className="kpi-tile-meta">
                                        {data.best_opening.win_rate}% win · {data.best_opening.games} games · {data.best_opening.avg_accuracy}% acc
                                    </div>
                                </div>
                            )}
                            {data.worst_opening && data.worst_opening.opening !== data.best_opening?.opening && (
                                <div className="kpi-tile">
                                    <div className="kpi-tile-label tone-bad">Worst</div>
                                    <div className="kpi-tile-name">{data.worst_opening.opening}</div>
                                    <div className="kpi-tile-meta">
                                        {data.worst_opening.win_rate}% win · {data.worst_opening.games} games · {data.worst_opening.avg_accuracy}% acc
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="insights-section">
                    <h3 className="insights-section-title">Most played openings</h3>
                    {data.openings.length === 0 ? (
                        <div className="empty-state">Not enough data yet.</div>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Opening</th>
                                    <th className="num">Games</th>
                                    <th className="num">Win %</th>
                                    <th className="num">Acc</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.openings.map((o, i) => (
                                    <tr key={i}>
                                        <td className="name" title={o.opening}>{o.opening}</td>
                                        <td className="num">{o.games}</td>
                                        <td className="num">{o.win_rate}%</td>
                                        <td className="num">{o.avg_accuracy}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Blunder patterns */}
            <div className="insights-grid">
                <div className="insights-section">
                    <h3 className="insights-section-title">When bad moves happen</h3>
                    {data.blunder_buckets.length === 0 ? (
                        <div className="empty-state">No bad moves recorded yet.</div>
                    ) : (
                        <BlunderBars buckets={data.blunder_buckets} />
                    )}
                </div>

                <div className="insights-section">
                    <h3 className="insights-section-title">Bad moves by piece captured</h3>
                    {data.blunders_by_captured_piece.length === 0 ? (
                        <div className="empty-state">No capture-related bad moves.</div>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Piece you took</th>
                                    <th className="num">Bad moves</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.blunders_by_captured_piece.map((b, i) => (
                                    <tr key={i}>
                                        <td className="name">{b.piece}</td>
                                        <td className="num">{b.count}</td>
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
        <div>
            {buckets.map((b) => (
                <div key={b.range} className="hbar-row">
                    <div className="hbar-label">moves {b.range}</div>
                    <div className="hbar-track">
                        <div className="hbar-fill" style={{ width: `${(b.count / max) * 100}%` }} />
                    </div>
                    <div className="hbar-count">{b.count}</div>
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
                `Weakest phase is your ${d.weakest_phase} (avg quality ${fmtQuality(wp.avg_quality)}, ${wp.bad_move_rate.toFixed(1)}% bad moves).`
            );
        }
    }
    if (d.worst_opening && d.worst_opening.win_rate < 50 && d.worst_opening.games >= 3) {
        bits.push(
            `You struggle with ${d.worst_opening.opening} (${d.worst_opening.win_rate}% over ${d.worst_opening.games} games).`
        );
    }
    if (d.best_opening && d.best_opening.win_rate >= 60 && d.best_opening.games >= 3) {
        bits.push(
            `You're strong in ${d.best_opening.opening} (${d.best_opening.win_rate}% over ${d.best_opening.games}).`
        );
    }
    if (d.worst_move_range) {
        bits.push(`Most bad moves cluster around moves ${d.worst_move_range}.`);
    }
    return bits.length ? bits.join(" ") : "Not enough data yet — analyze a few more games.";
}
