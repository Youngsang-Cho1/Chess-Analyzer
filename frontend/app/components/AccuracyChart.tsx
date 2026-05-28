
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
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="id" hide />
                        <YAxis
                            domain={[0, 100]}
                            tick={{ fontSize: 11, fill: "var(--muted-fg)" }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip
                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                            formatter={(value: any) => [`${Number(value).toFixed(1)}%`, "Accuracy"]}
                            labelFormatter={() => ""}
                            contentStyle={{
                                background: "var(--card-bg)",
                                border: "1px solid var(--border)",
                                borderRadius: 4,
                                fontSize: 12,
                            }}
                            labelStyle={{ color: "var(--foreground)" }}
                            itemStyle={{ color: "var(--primary)" }}
                            cursor={{ stroke: "var(--primary)", strokeWidth: 1, strokeDasharray: "4 4", opacity: 0.5 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="accuracy"
                            stroke="#D4A24C"
                            strokeWidth={2}
                            dot={{ r: 3, fill: "#E8C77D", strokeWidth: 1, stroke: "#0E0F12" }}
                            activeDot={{ r: 5, fill: "#E8C77D", strokeWidth: 0 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
