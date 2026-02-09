import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Props {
    data: Record<string, number>;
}

const COLORS: Record<string, string> = {
    'Brilliant': '#1baca6', // Teal
    'Great': '#5b8c5a',     // Green
    'Best': '#8cac8a',      // Light Green
    'Excellent': '#96c997', // Lighter Green
    'Good': '#b3d9b4',      // Pale Green
    'Inaccuracy': '#f4d160',// Yellow
    'Mistake': '#e08e79',   // Orange
    'Blunder': '#b82e2e',   // Red
    'Miss': '#d95f5f'       // Light Red
};

export default function MoveQualityChart({ data }: Props) {
    if (!data) return (
        <div className="chart-card flex items-center justify-center">
            <p className="text-gray-400">No move data available</p>
        </div>
    );

    const chartData = Object.keys(data).map(key => ({
        name: key,
        count: data[key]
    }));

    const validKeys = ['Brilliant', 'Great', 'Best', 'Excellent', 'Good', 'Inaccuracy', 'Mistake', 'Blunder', 'Miss'];
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
            <h3 className="chart-title">🎯 Move Quality</h3>
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
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                            {filteredData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#8884d8'} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
