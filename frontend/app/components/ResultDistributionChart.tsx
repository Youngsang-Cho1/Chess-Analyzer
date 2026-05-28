
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface GameHistory {
    result: string;
}

interface Props {
    history: GameHistory[];
}

const COLORS = {
    Win: "#99cc68",     // var(--cls-best)
    Loss: "#ca3431",    // var(--cls-blunder)
    Draw: "#8A8478",    // muted
};

export default function ResultDistributionChart({ history }: Props) {
    if (!history || history.length === 0) return (
        <div className="chart-card">
            <h3 className="chart-title">Win/Loss Ratio</h3>
            <div className="chart-empty-state">
                No game history available
            </div>
        </div>
    );

    // Calculate counts
    const counts = history.reduce((acc, game) => {
        const res = game.result || "Draw";
        acc[res] = (acc[res] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const data = Object.keys(counts).map(key => ({
        name: key,
        value: counts[key]
    }));

    return (
        <div className="chart-card">
            <h3 className="chart-title">Win/Loss Ratio</h3>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || '#94a3b8'} stroke="none" />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                background: "var(--card-bg)",
                                border: "1px solid var(--border)",
                                borderRadius: 4,
                                fontSize: 12,
                            }}
                            labelStyle={{ color: "var(--foreground)" }}
                            itemStyle={{ color: "var(--primary)" }}
                        />
                        <Legend
                            verticalAlign="bottom"
                            height={36}
                            iconType="circle"
                            wrapperStyle={{ fontSize: 12, color: "var(--muted-fg)" }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
