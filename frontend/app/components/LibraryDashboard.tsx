"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface HistoryRow {
    id: number;
    is_white: boolean;
    opponent: string;
    result: "Win" | "Loss" | "Draw";
    accuracy: number;
    opening: string;
}

interface Stats {
    username: string;
    total_games: number;
    win_rate: number;
    record: string;
    avg_accuracy: number;
    classifications: Record<string, number>;
    style: string;
    history: HistoryRow[];
    ai_insight: string;
}

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

interface Insights {
    username: string;
    games_analyzed: number;
    phases: PhaseRow[];
    weakest_phase: string | null;
    openings: OpeningRow[];
    best_opening: OpeningRow | null;
    worst_opening: OpeningRow | null;
    blunder_buckets: { range: string; count: number }[];
    worst_move_range: string | null;
    blunders_by_captured_piece: { piece: string; count: number }[];
    total_bad_moves: number;
    color_quality: Record<string, { moves: number; avg_quality: number }>;
}

interface Props {
    username: string;
}

const CLS_ORDER = ["Brilliant", "Great", "Best", "Excellent", "Good", "Book", "Inaccuracy", "Mistake", "Miss", "Blunder"];

const CLS_META: Record<string, { color: string; glyph: string }> = {
    Brilliant: { color: "var(--cls-brilliant)", glyph: "!!" },
    Great: { color: "var(--cls-great)", glyph: "!" },
    Best: { color: "var(--cls-best)", glyph: "★" },
    Excellent: { color: "var(--cls-excellent)", glyph: "★" },
    Good: { color: "var(--cls-good)", glyph: "✓" },
    Book: { color: "var(--cls-book)", glyph: "📖" },
    Inaccuracy: { color: "var(--cls-inaccuracy)", glyph: "?!" },
    Mistake: { color: "var(--cls-mistake)", glyph: "?" },
    Miss: { color: "var(--cls-miss)", glyph: "✕" },
    Blunder: { color: "var(--cls-blunder)", glyph: "??" },
};

export default function LibraryDashboard({ username }: Props) {
    const [stats, setStats] = useState<Stats | null>(null);
    const [insights, setInsights] = useState<Insights | null>(null);
    const [selectedClass, setSelectedClass] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!username) return;
        let cancelled = false;
        setLoading(true);
        Promise.all([
            fetch(`http://localhost:8000/stats/${username}`).then((r) => r.ok ? r.json() : null),
            fetch(`http://localhost:8000/insights/${username}`).then((r) => r.ok ? r.json() : null),
        ]).then(([s, i]) => {
            if (cancelled) return;
            setStats(s?.stats || null);
            setInsights(i?.insights || null);
        }).finally(() => {
            if (!cancelled) setLoading(false);
        });
        return () => { cancelled = true; };
    }, [username]);

    if (loading) return <div className="lib-card"><div className="empty-state">Loading…</div></div>;
    if (!stats) return <div className="lib-card"><div className="empty-state">No data. Analyze some games first.</div></div>;

    return (
        <div className="lib">
            <section className="lib-grid-profile">
                <ProfileCard username={username} stats={stats} gamesAnalyzed={insights?.games_analyzed ?? stats.total_games} />
                <KPITiles stats={stats} />
            </section>

            {insights && <HeadlineInsight insights={insights} />}

            <section className="lib-grid-charts">
                <AccuracyTrend history={stats.history} />
                <ResultDonut history={stats.history} />
            </section>

            <MoveQualityBars
                data={stats.classifications}
                selected={selectedClass}
                onSelect={setSelectedClass}
            />

            {insights && (
                <section className="lib-grid-insights">
                    <PhaseTable insights={insights} />
                    <OpeningExtremes insights={insights} />
                    <BlunderBuckets insights={insights} />
                </section>
            )}

            <section className="lib-grid-bottom">
                <TopOpenings history={stats.history} />
                <RecentGames history={stats.history} username={username} />
            </section>
        </div>
    );
}

/* ─────────────── sub-components ─────────────── */

function ProfileCard({ username, stats, gamesAnalyzed }: { username: string; stats: Stats; gamesAnalyzed: number }) {
    const initial = (username || "?").trim().charAt(0).toUpperCase();
    return (
        <div className="lib-profile">
            <div className="lib-profile-row">
                <div className="lib-profile-avatar">{initial}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="lib-eyebrow">Player</div>
                    <div className="lib-profile-name">{username}</div>
                    <div className="lib-profile-meta">{stats.style}</div>
                </div>
            </div>
            <div className="lib-profile-divider" />
            <div className="lib-profile-stat">
                <span>RECORD</span>
                <span className="lib-profile-stat-val">{stats.record}</span>
            </div>
            <div className="lib-profile-stat">
                <span>ANALYZED</span>
                <span className="lib-profile-stat-val">{gamesAnalyzed} games</span>
            </div>
        </div>
    );
}

function KPITiles({ stats }: { stats: Stats }) {
    const tiles = [
        { mod: "win", label: "Win Rate", value: `${stats.win_rate}%`, sub: stats.record },
        { mod: "acc", label: "Accuracy", value: `${stats.avg_accuracy.toFixed(1)}%`, sub: "across all games" },
        { mod: "style", label: "Play Style", value: stats.style, sub: "computed from move mix" },
        { mod: "games", label: "Games", value: String(stats.total_games), sub: "analyzed" },
    ];
    return (
        <div className="lib-kpi-grid">
            {tiles.map((t) => (
                <div key={t.label} className={`lib-kpi lib-kpi--${t.mod}`}>
                    <div className="lib-eyebrow">{t.label}</div>
                    <div className="lib-kpi-value">{t.value}</div>
                    <div className="lib-mono">{t.sub}</div>
                </div>
            ))}
        </div>
    );
}

function HeadlineInsight({ insights }: { insights: Insights }) {
    const wp = insights.phases.find((p) => p.phase === insights.weakest_phase);
    const best = insights.best_opening;
    const worst = insights.worst_opening;

    return (
        <div className="lib-headline">
            <div className="lib-headline-badge">GM</div>
            <div style={{ flex: 1 }}>
                <div className="lib-eyebrow" style={{ marginBottom: "0.4rem" }}>AI Coach · Headline</div>
                <div className="lib-headline-text">
                    {wp && insights.weakest_phase && (
                        <>“Your <span className="hi-bad">{insights.weakest_phase}</span> is the weakest area — {wp.bad_move_rate.toFixed(1)}% bad-move rate, quality <span className="hi-warn">{wp.avg_quality > 0 ? "+" : ""}{wp.avg_quality.toFixed(2)}</span>. </>
                    )}
                    {best && best.games >= 3 && best.win_rate >= 55 && (
                        <>You play <span className="hi-good">{best.opening}</span> well ({best.win_rate}% over {best.games}). </>
                    )}
                    {worst && worst.games >= 3 && worst.win_rate < 50 && worst.opening !== best?.opening && (
                        <>Trouble in <span className="hi-bad">{worst.opening}</span> ({worst.win_rate}% over {worst.games}). </>
                    )}
                    {!wp && !best && !worst && "Analyze more games for personalized coaching."}
                    {(wp || best || worst) && "”"}
                </div>
            </div>
        </div>
    );
}

function AccuracyTrend({ history }: { history: HistoryRow[] }) {
    const sorted = [...history].sort((a, b) => a.id - b.id);
    const W = 720, H = 220;
    const pad = { top: 16, right: 24, bottom: 28, left: 36 };
    const innerW = W - pad.left - pad.right;
    const innerH = H - pad.top - pad.bottom;
    const N = sorted.length;
    if (N === 0) return <Card title="Accuracy Trend" eyebrow="No data"><div className="empty-state">No games yet.</div></Card>;

    const xOf = (i: number) => pad.left + (i / Math.max(N - 1, 1)) * innerW;
    const yOf = (v: number) => pad.top + innerH - (v / 100) * innerH;

    const linePath = sorted.map((p, i) => `${i === 0 ? "M" : "L"} ${xOf(i)} ${yOf(p.accuracy)}`).join(" ");
    const areaPath = `${linePath} L ${xOf(N - 1)} ${pad.top + innerH} L ${xOf(0)} ${pad.top + innerH} Z`;
    const avg = sorted.reduce((s, p) => s + p.accuracy, 0) / N;

    return (
        <Card
            title="Accuracy Trend"
            eyebrow={`Last ${N} games · chronological`}
            right={<Chip label={`avg ${avg.toFixed(1)}%`} tone="gold" />}
        >
            <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
                <defs>
                    <linearGradient id="acc-grad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#D4A24C" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#D4A24C" stopOpacity="0.02" />
                    </linearGradient>
                </defs>
                {[0, 25, 50, 75, 100].map((g) => (
                    <g key={g}>
                        <line x1={pad.left} y1={yOf(g)} x2={W - pad.right} y2={yOf(g)}
                            stroke="rgba(212,162,76,0.16)" strokeDasharray="2 4" strokeWidth={0.5} />
                        <text x={pad.left - 8} y={yOf(g) + 3} fontSize={9} textAnchor="end"
                            fill="#8A8478" fontFamily="var(--font-mono)">{g}</text>
                    </g>
                ))}
                <path d={areaPath} fill="url(#acc-grad)" />
                <path d={linePath} fill="none" stroke="#D4A24C" strokeWidth={2} />
                <line x1={pad.left} y1={yOf(avg)} x2={W - pad.right} y2={yOf(avg)}
                    stroke="#E8C77D" strokeDasharray="4 4" strokeWidth={1} opacity={0.5} />
                {sorted.map((p, i) => {
                    const color = p.result === "Win" ? "var(--cls-best)" : p.result === "Loss" ? "var(--cls-blunder)" : "#8A8478";
                    return (
                        <circle key={i} cx={xOf(i)} cy={yOf(p.accuracy)} r={4}
                            fill="var(--background)" stroke={color} strokeWidth={1.5} />
                    );
                })}
                {sorted.map((p, i) => (
                    <text key={`x${i}`} x={xOf(i)} y={H - pad.bottom + 16}
                        fontSize={9} textAnchor="middle" fill="#8A8478" fontFamily="var(--font-mono)">
                        G{p.id}
                    </text>
                ))}
            </svg>
            <div style={{ display: "flex", gap: "0.875rem", marginTop: "0.5rem", justifyContent: "flex-end" }}>
                <LegendDot color="var(--cls-best)" label="WIN" />
                <LegendDot color="var(--cls-blunder)" label="LOSS" />
                <LegendDot color="#8A8478" label="DRAW" />
            </div>
        </Card>
    );
}

function ResultDonut({ history }: { history: HistoryRow[] }) {
    const counts = history.reduce<Record<string, number>>((acc, g) => {
        acc[g.result] = (acc[g.result] || 0) + 1;
        return acc;
    }, {});
    const total = history.length || 1;
    const data = [
        { name: "Win", value: counts.Win || 0, color: "var(--cls-best)" },
        { name: "Draw", value: counts.Draw || 0, color: "#8A8478" },
        { name: "Loss", value: counts.Loss || 0, color: "var(--cls-blunder)" },
    ];

    const cx = 110, cy = 110, ro = 90, ri = 60;
    let acc = -Math.PI / 2;
    const slices = data.map((d) => {
        const a0 = acc;
        const a1 = a0 + (d.value / total) * 2 * Math.PI;
        acc = a1;
        return { ...d, a0, a1 };
    });

    function arcPath(a0: number, a1: number) {
        const o0x = cx + Math.cos(a0) * ro, o0y = cy + Math.sin(a0) * ro;
        const o1x = cx + Math.cos(a1) * ro, o1y = cy + Math.sin(a1) * ro;
        const i0x = cx + Math.cos(a0) * ri, i0y = cy + Math.sin(a0) * ri;
        const i1x = cx + Math.cos(a1) * ri, i1y = cy + Math.sin(a1) * ri;
        const large = a1 - a0 > Math.PI ? 1 : 0;
        return `M ${o0x} ${o0y} A ${ro} ${ro} 0 ${large} 1 ${o1x} ${o1y} L ${i1x} ${i1y} A ${ri} ${ri} 0 ${large} 0 ${i0x} ${i0y} Z`;
    }

    return (
        <Card title="Result Distribution" eyebrow={`${history.length} games`}>
            <div className="lib-donut-row">
                <svg width={220} height={220}>
                    {slices.map((s, i) => s.value > 0 && (
                        <path key={i} d={arcPath(s.a0, s.a1)} fill={s.color} stroke="var(--background)" strokeWidth={2} />
                    ))}
                    <text x={cx} y={cy - 4} textAnchor="middle"
                        fontFamily="var(--font-serif)" fontSize={28} fontWeight={500}
                        fill="var(--foreground)" letterSpacing={-1}>
                        {counts.Win || 0}
                    </text>
                    <text x={cx} y={cy + 16} textAnchor="middle"
                        fontFamily="var(--font-mono)" fontSize={10} letterSpacing="1px"
                        fill="#8A8478">
                        WINS
                    </text>
                </svg>
                <div className="lib-donut-legend">
                    {data.map((d) => (
                        <div key={d.name} className="lib-donut-legend-row">
                            <span className="lib-donut-swatch" style={{ background: d.color }} />
                            <span className="lib-donut-name">{d.name}</span>
                            <span className="lib-donut-value" style={{ color: d.color }}>{d.value}</span>
                            <span className="lib-donut-pct">{((d.value / total) * 100).toFixed(0)}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </Card>
    );
}

function MoveQualityBars({ data, selected, onSelect }: {
    data: Record<string, number>;
    selected: string | null;
    onSelect: (n: string | null) => void;
}) {
    const entries = CLS_ORDER.map((name) => ({ name, count: data[name] || 0 }));
    const max = Math.max(...entries.map((e) => e.count), 1);
    const total = entries.reduce((s, e) => s + e.count, 0);

    return (
        <Card
            title="Move Quality"
            eyebrow={`${total.toLocaleString()} moves · classified by Stockfish`}
            right={<span className="lib-mono">click to drill in →</span>}
        >
            <div className="lib-bars" style={{ gridTemplateColumns: `repeat(${entries.length}, 1fr)` }}>
                {entries.map((e) => {
                    const meta = CLS_META[e.name];
                    const h = (e.count / max) * 180;
                    const active = selected === e.name;
                    const dim = selected && !active;
                    return (
                        <button
                            key={e.name}
                            onClick={() => onSelect(active ? null : e.name)}
                            className="lib-bar-btn"
                            aria-pressed={active}
                        >
                            <div className="lib-bar-count" style={{ color: active ? meta.color : undefined }}>
                                {e.count.toLocaleString()}
                            </div>
                            <div
                                className="lib-bar-fill"
                                style={{
                                    height: Math.max(h, 4),
                                    background: meta.color,
                                    opacity: dim ? 0.3 : 0.9,
                                    boxShadow: active ? `inset 0 0 0 2px ${meta.color}` : undefined,
                                }}
                            />
                        </button>
                    );
                })}
            </div>
            <div className="lib-bar-labels" style={{ gridTemplateColumns: `repeat(${entries.length}, 1fr)` }}>
                {entries.map((e) => {
                    const meta = CLS_META[e.name];
                    return (
                        <div key={e.name} className="lib-bar-label">
                            <span className="lib-bar-glyph" style={{ color: meta.color }}>{meta.glyph}</span>
                            <span>{e.name}</span>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
}

function PhaseTable({ insights }: { insights: Insights }) {
    const phaseLabel: Record<string, string> = {
        opening: "Opening",
        middlegame: "Middlegame",
        endgame: "Endgame",
    };
    return (
        <Card
            title="Phase Quality"
            eyebrow="Where you leak rating points"
            right={insights.weakest_phase ? <Chip label={`weak: ${insights.weakest_phase}`} tone="bad" /> : undefined}
        >
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Phase</th>
                        <th className="num">Moves</th>
                        <th className="num">Quality</th>
                        <th className="num">Bad %</th>
                    </tr>
                </thead>
                <tbody>
                    {insights.phases.map((p) => {
                        const isWeak = p.phase === insights.weakest_phase;
                        const qclass = p.avg_quality >= 0 ? "tone-good"
                            : p.avg_quality > -0.5 ? "tone-warn"
                            : "tone-bad";
                        return (
                            <tr key={p.phase}>
                                <td className="name" style={isWeak ? { color: "var(--cls-blunder)" } : undefined}>
                                    {phaseLabel[p.phase] || p.phase}
                                </td>
                                <td className="num">{p.moves}</td>
                                <td className={`num ${qclass}`} style={{ fontWeight: 700 }}>
                                    {p.avg_quality > 0 ? "+" : ""}{p.avg_quality.toFixed(2)}
                                </td>
                                <td className="num">{p.bad_move_rate.toFixed(1)}%</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <p className="lib-phase-caption">
                Brilliant +4 · Great +3 · Best +2 · Excellent +1 · Inaccuracy −1 · Mistake/Miss −2 · Blunder −4
            </p>
        </Card>
    );
}

function OpeningExtremes({ insights }: { insights: Insights }) {
    return (
        <Card title="Best & Worst" eyebrow="By win rate · min 2 games">
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {insights.best_opening && <ExtremeTile o={insights.best_opening} kind="best" />}
                {insights.worst_opening && insights.worst_opening.opening !== insights.best_opening?.opening && (
                    <ExtremeTile o={insights.worst_opening} kind="worst" />
                )}
                {!insights.best_opening && <div className="empty-state">Need more games.</div>}
            </div>
        </Card>
    );
}

function ExtremeTile({ o, kind }: { o: OpeningRow; kind: "best" | "worst" }) {
    return (
        <div className={`lib-extreme lib-extreme--${kind}`}>
            <div className="lib-extreme-head">
                <span className={`lib-extreme-label ${kind === "best" ? "tone-good" : "tone-bad"}`}>
                    {kind === "best" ? "STRONG" : "WEAK"}
                </span>
                <span className="lib-extreme-name">{o.opening}</span>
            </div>
            <div className="lib-extreme-meta">
                <span><span className={kind === "best" ? "tone-good" : "tone-bad"}>{o.win_rate}%</span> win</span>
                <span><span style={{ color: "var(--foreground)" }}>{o.games}</span> games</span>
                <span><span style={{ color: "var(--foreground)" }}>{o.avg_accuracy}%</span> acc</span>
            </div>
        </div>
    );
}

function BlunderBuckets({ insights }: { insights: Insights }) {
    const max = Math.max(...insights.blunder_buckets.map((b) => b.count), 1);
    return (
        <Card
            title="When Bad Moves Happen"
            eyebrow="Move-number buckets"
            right={insights.worst_move_range ? <Chip label={`cluster: ${insights.worst_move_range}`} tone="warn" /> : undefined}
        >
            {insights.blunder_buckets.length === 0 ? (
                <div className="empty-state">No bad moves recorded.</div>
            ) : (
                <div>
                    {insights.blunder_buckets.map((b) => {
                        const isWorst = b.range === insights.worst_move_range;
                        return (
                            <div key={b.range} className="lib-bucket-row">
                                <div className="lib-bucket-label" style={isWorst ? { color: "var(--cls-mistake)" } : undefined}>
                                    moves {b.range}
                                </div>
                                <div className="lib-bucket-track">
                                    <div
                                        className={`lib-bucket-fill ${isWorst ? "lib-bucket-fill--worst" : ""}`}
                                        style={{ width: `${(b.count / max) * 100}%` }}
                                    />
                                </div>
                                <div className="lib-bucket-count" style={isWorst ? { color: "var(--cls-mistake)" } : undefined}>
                                    {b.count}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
            {insights.worst_move_range && (
                <div className="lib-bucket-footnote">
                    Most errors cluster between moves <span className="tone-warn">{insights.worst_move_range}</span> — typically when both sides commit to a plan.
                </div>
            )}
        </Card>
    );
}

function TopOpenings({ history }: { history: HistoryRow[] }) {
    const counts: Record<string, number> = {};
    for (const g of history) {
        const k = g.opening || "Unknown";
        counts[k] = (counts[k] || 0) + 1;
    }
    const sorted = Object.keys(counts)
        .map((k) => ({ opening: k, count: counts[k] }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);
    const max = Math.max(...sorted.map((s) => s.count), 1);

    return (
        <Card title="Top Openings" eyebrow="Played in this batch">
            {sorted.length === 0 ? (
                <div className="empty-state">No openings yet.</div>
            ) : (
                <div>
                    {sorted.map((row, i) => (
                        <div key={i} className="lib-topop-row">
                            <div className="lib-topop-name" title={row.opening}>{row.opening}</div>
                            <div className="lib-topop-track">
                                <div className="lib-topop-fill" style={{ width: `${(row.count / max) * 100}%` }} />
                            </div>
                            <div className="lib-topop-count">{row.count}</div>
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}

function RecentGames({ history, username }: { history: HistoryRow[]; username: string }) {
    return (
        <Card title="Recent Games" eyebrow={username}>
            {history.length === 0 ? (
                <div className="empty-state">No games yet.</div>
            ) : (
                <div>
                    {history.slice(0, 8).map((g) => {
                        const cls = g.result === "Win" ? "lib-game-result--win" : g.result === "Loss" ? "lib-game-result--loss" : "lib-game-result--draw";
                        return (
                            <div key={g.id} className="lib-game-row">
                                <span className="lib-game-id">G{g.id}</span>
                                <span className="lib-game-opening" title={g.opening}>{g.opening || "Unknown"}</span>
                                <span className="lib-game-acc">{g.accuracy.toFixed(1)}% acc</span>
                                <span className={`lib-game-result ${cls}`}>{g.result}</span>
                                <Link href={`/game/${g.id}`} className="lib-btn">Review →</Link>
                            </div>
                        );
                    })}
                </div>
            )}
        </Card>
    );
}

/* ─────────────── primitives ─────────────── */

function Card({ title, eyebrow, right, children }: {
    title?: string;
    eyebrow?: string;
    right?: React.ReactNode;
    children: React.ReactNode;
}) {
    return (
        <div className="lib-card">
            {(title || eyebrow || right) && (
                <div className="lib-card-head">
                    <div>
                        {eyebrow && <div className="lib-eyebrow" style={{ marginBottom: "0.25rem" }}>{eyebrow}</div>}
                        {title && <div className="lib-card-title">{title}</div>}
                    </div>
                    {right && <div className="lib-card-right">{right}</div>}
                </div>
            )}
            {children}
        </div>
    );
}

function Chip({ label, tone }: { label: string; tone: "gold" | "bad" | "warn" | "good" }) {
    const colorVar = tone === "gold" ? "var(--primary)"
        : tone === "bad" ? "var(--cls-blunder)"
        : tone === "warn" ? "var(--cls-mistake)"
        : "var(--cls-best)";
    return (
        <span className="lib-chip" style={{
            color: colorVar,
            background: `${colorVar}22`,
            border: `1px solid ${colorVar}44`,
        }}>
            {label}
        </span>
    );
}

function LegendDot({ color, label }: { color: string; label: string }) {
    return (
        <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.3rem",
            fontFamily: "var(--font-mono), monospace",
            fontSize: "0.6rem",
            color: "#8A8478",
        }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--background)", border: `1.5px solid ${color}` }} />
            {label}
        </span>
    );
}