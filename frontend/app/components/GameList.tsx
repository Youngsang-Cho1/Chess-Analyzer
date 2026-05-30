"use client";

import { useState } from "react";
import Link from "next/link";

interface Game {
    id: number;
    white_username: string;
    black_username: string;
    white_result: string;
    black_result: string;
    white_accuracy?: number | null;
    black_accuracy?: number | null;
    time_control: string;
    time_class?: string;
    opening?: string;
    end_time?: number;
    url: string;
}

interface Props {
    games: Game[];
    username: string;
}

const TIME_CLASS_ORDER = ["bullet", "blitz", "rapid", "classical", "unknown"];

function resultLabel(r: string) {
    if (r === "1") return { text: "WIN", cls: "gl-result--win" };
    if (r === "0") return { text: "LOSS", cls: "gl-result--loss" };
    return { text: "DRAW", cls: "gl-result--draw" };
}

function formatDate(ts?: number) {
    if (!ts) return "—";
    return new Date(ts * 1000).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function GameList({ games, username }: Props) {
    const [activeTab, setActiveTab] = useState<string | null>(null);

    if (games.length === 0) {
        return <div className="no-games-msg">No games found.</div>;
    }

    // Group by time_class
    const groups: Record<string, Game[]> = {};
    for (const g of games) {
        const tc = (g.time_class || "unknown").toLowerCase();
        if (!groups[tc]) groups[tc] = [];
        groups[tc].push(g);
    }

    const tabs = TIME_CLASS_ORDER.filter((t) => groups[t]?.length > 0);
    const currentTab = activeTab ?? tabs[0] ?? null;
    const visible = currentTab ? (groups[currentTab] || []) : [];

    return (
        <div className="gl-wrap">
            <div className="gl-header">
                <div className="gl-title">Game History</div>
                <div className="gl-tabs">
                    {tabs.map((t) => (
                        <button
                            key={t}
                            onClick={() => setActiveTab(t)}
                            className={`gl-tab ${currentTab === t ? "gl-tab--active" : ""}`}
                        >
                            {t.charAt(0).toUpperCase() + t.slice(1)}
                            <span className="gl-tab-count">{groups[t].length}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="gl-table-wrap">
                <table className="gl-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Opponent</th>
                            <th>Opening</th>
                            <th>Accuracy</th>
                            <th>Result</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {visible.map((game) => {
                            const isWhite = game.white_username.toLowerCase() === username.toLowerCase();
                            const opponent = isWhite ? game.black_username : game.white_username;
                            const myResult = isWhite ? game.white_result : game.black_result;
                            const myAcc = isWhite ? game.white_accuracy : game.black_accuracy;
                            const { text, cls } = resultLabel(myResult);
                            const opening = game.opening
                                ? game.opening.split(":")[0].replace(/-/g, " ")
                                : "—";

                            return (
                                <tr key={game.id} className="gl-row">
                                    <td className="gl-td gl-td--date">{formatDate(game.end_time)}</td>
                                    <td className="gl-td gl-td--opponent">{opponent}</td>
                                    <td className="gl-td gl-td--opening">{opening}</td>
                                    <td className="gl-td gl-td--acc">
                                        {myAcc != null ? `${myAcc.toFixed(1)}%` : "—"}
                                    </td>
                                    <td className="gl-td">
                                        <span className={`gl-result ${cls}`}>{text}</span>
                                    </td>
                                    <td className="gl-td gl-td--action">
                                        <Link href={`/game/${game.id}`} className="gl-btn">
                                            Review →
                                        </Link>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}