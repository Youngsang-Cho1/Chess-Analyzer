
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface GameHistory {
    id: number;
    accuracy: number;
}

interface Props {
    history: GameHistory[];
}

export default function AccuracyChart({ history }: Props) {
    if (!history || history.length === 0) return (
        <div className="chart-card">
            <h3 className="chart-title">Accuracy Trend</h3>
            <div className="chart-empty-state">
                No game history available
            </div>
        </div>
    );

    // Sort by ID to show chronological order
    const data = [...history].sort((a, b) => a.id - b.id);

    return (
        <div className="chart-card">
            <h3 className="chart-title">Accuracy Trend</h3>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                        <XAxis dataKey="id" hide />
                        <YAxis
                            domain={[0, 100]}
                            tick={{ fontSize: 11, fill: '#64748b' }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip
                            formatter={(value: any) => [`${Number(value).toFixed(1)}%`, "Accuracy"]}
                            labelFormatter={() => ""}
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="accuracy"
                            stroke="#2563eb"
                            strokeWidth={3}
                            dot={{ r: 4, fill: "#2563eb", strokeWidth: 2, stroke: '#fff' }}
                            activeDot={{ r: 6, strokeWidth: 0 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
