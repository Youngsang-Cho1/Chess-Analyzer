"use client";
import StyleRadarChart from "./StyleRadarChart";

interface StyleVector {
    consistency: number;
    aggression: number;
    accuracy: number;
    tactical: number;
}

interface Stats {
    win_rate: number;
    record: string;
    avg_accuracy: number;
    total_games: number;
    style: string;
    style_tag?: string | null;
    style_vector?: StyleVector;
}

interface Props {
    stats: Stats | null;
}

export default function StatsDashboard({ stats }: Props) {
    if (!stats) return null;

    return (
        <div className="stats-grid">
            <div className="stat-box">
                <div className="stat-label">Win Rate</div>
                <div className="stat-value-xl stat-value-win">{stats.win_rate}%</div>
                <div className="stat-sub">{stats.record}</div>
            </div>
            <div className="stat-box">
                <div className="stat-label">Accuracy</div>
                <div className="stat-value-xl stat-value-acc">{stats.avg_accuracy}%</div>
            </div>
            {stats.style_vector ? (
                <StyleRadarChart styleVector={stats.style_vector} style={stats.style} tag={stats.style_tag} />
            ) : (
                <div className="stat-box">
                    <div className="stat-label">Play Style</div>
                    <div className="stat-value stat-value-style">{stats.style}</div>
                </div>
            )}
            <div className="stat-box">
                <div className="stat-label">Total Games</div>
                <div className="stat-value-xl">{stats.total_games}</div>
            </div>
        </div>
    );
}
