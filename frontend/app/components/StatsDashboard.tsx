
interface Stats {
    win_rate: number;
    record: string;
    avg_accuracy: number;
    total_games: number;
    style: string;
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
                <div className="stat-value stat-value-win">{stats.win_rate}%</div>
                <div className="text-xs text-gray-400 mt-1">{stats.record}</div>
            </div>
            <div className="stat-box">
                <div className="stat-label">Accuracy</div>
                <div className="stat-value stat-value-acc">{stats.avg_accuracy}%</div>
            </div>
            <div className="stat-box">
                <div className="stat-label">Play Style</div>
                <div className="stat-value stat-value-style">{stats.style}</div>
            </div>
            <div className="stat-box">
                <div className="stat-label">Total Games</div>
                <div className="stat-value">{stats.total_games}</div>
            </div>
        </div>
    );
}
