import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';
import { useRouter } from "next/navigation";

interface Props {
    data: Record<string, number>;
    username: string;
}

const COLORS: Record<string, string> = {
    'Brilliant': '#1baca6',
    'Great': '#a8c7fa',
    'Book': '#d38e0395',
    'Best': '#5b8c5a',
    'Excellent': '#96c997',
    'Good': '#8cac8a',
    'Inaccuracy': '#f4d160',
    'Mistake': '#e67f12',
    'Blunder': '#e62e2e',
    'Miss': '#d95f5f'
};

export default function MoveQualityChart({ data, username }: Props) {
    const router = useRouter();
    if (!data) return (
        <div className="chart-card flex items-center justify-center">
            <p className="chart-empty-state">No move data available</p>
        </div>
    );

    const chartData = Object.keys(data).map(key => ({
        name: key,
        count: data[key]
    }));

    const validKeys = ['Brilliant', 'Great', 'Book', 'Best', 'Excellent', 'Good', 'Inaccuracy', 'Mistake', 'Blunder', 'Miss'];
    const filteredData = chartData.filter(d => validKeys.includes(d.name));

    if (filteredData.length === 0 || filteredData.every(d => d.count === 0)) {
        return (
            <div className="chart-card">
                <h3 className="chart-title">🎯 Move Quality</h3>
                <div className="flex-1 flex items-center justify-center text-gray-400">
                    No moves to analyze yet
                </div>
            </div>
        );
    }

    return (
        <div className="chart-card">
            <h3 className="chart-title">Move Quality</h3>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={filteredData} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                        <XAxis
                            dataKey="name"
                            tick={{ fontSize: 10, fill: '#64748b' }}
                            interval={0}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            tick={{ fontSize: 11, fill: '#64748b' }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip
                            cursor={{ fill: '#f8fafc' }}
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}
                            onClick={(data) => {
                                router.push(`/moves/${username}/${data.name}`)
                            }}
                            style={{ cursor: "pointer" }}
                        >
                            {filteredData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#8884d8'} />
                            ))}
                            <LabelList
                                dataKey="count"
                                position="top"
                                style={{ fontSize: 11, fontWeight: 700, fill: '#475569' }}
                                formatter={(value: unknown) => Number(value) > 0 ? String(value) : ''}
                            />

                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
