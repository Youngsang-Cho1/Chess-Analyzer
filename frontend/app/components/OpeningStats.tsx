
interface GameHistory {
    opening: string;
}

interface Props {
    history: GameHistory[];
}

export default function OpeningStats({ history }: Props) {
    if (!history || history.length === 0) return (
        <div className="chart-card">
            <h3 className="chart-title">📖 Top Openings</h3>
            <div className="flex-1 flex items-center justify-center text-gray-400">
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
            <h3 className="chart-title">📖 Top Openings</h3>
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-white">
                        <tr className="border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                            <th className="py-2">Opening</th>
                            <th className="py-2 text-right">Count</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {sorted.map((item, index) => (
                            <tr key={index} className="hover:bg-blue-50/50 transition-colors">
                                <td className="py-3 text-sm text-gray-700 font-medium truncate max-w-[200px]" title={item.opening}>
                                    {item.opening}
                                </td>
                                <td className="py-3 text-sm text-gray-900 font-bold text-right">
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
