
interface GameHistory {
    opening: string;
}

interface Props {
    history: GameHistory[];
}

export default function OpeningStats({ history }: Props) {
    if (!history || history.length === 0) return (
        <div className="chart-card">
            <h3 className="chart-title">Top Openings</h3>
            <div className="chart-empty-state">
                No opening data available
            </div>
        </div>
    );

    // Count openings
    const counts = history.reduce((acc, game) => {
        const op = game.opening || "Unknown";
        acc[op] = (acc[op] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    // Convert to array and sort by count desc
    const sorted = Object.keys(counts)
        .map(key => ({ opening: key, count: counts[key] }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10); // Show top 10

    return (
        <div className="chart-card">
            <h3 className="chart-title">Top Openings</h3>
            <div className="opening-list-container custom-scrollbar">
                <table className="opening-table">
                    <thead className="opening-thead">
                        <tr className="opening-th-row">
                            <th className="opening-th opening-th-left">Opening</th>
                            <th className="opening-th opening-th-right">Count</th>
                        </tr>
                    </thead>
                    <tbody className="opening-tbody">
                        {sorted.map((item, index) => (
                            <tr key={index} className="opening-tr">
                                <td className="opening-td-name" title={item.opening}>
                                    {item.opening}
                                </td>
                                <td className="opening-td-count">
                                    {item.count}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
