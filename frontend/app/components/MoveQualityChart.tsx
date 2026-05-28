"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';
import { useRouter } from "next/navigation";

interface Props {
    data: Record<string, number>;
    username: string;
}

// Mirrors globals.css --cls-* tokens so everything matches.
const COLORS: Record<string, string> = {
    Brilliant: "#26c2a3",   // teal
    Great: "#5b8bb4",       // slate blue
    Best: "#4caf50",        // deep green
    Excellent: "#81c784",   // medium green
    Good: "#a5d6a7",        // light sage green
    Book: "#a88b5e",
    Inaccuracy: "#f7c631",
    Mistake: "#e6912b",
    Blunder: "#ca3431",
    Miss: "#ff6b6b",
};

const ORDER = ["Brilliant", "Great", "Book", "Best", "Excellent", "Good", "Inaccuracy", "Mistake", "Blunder", "Miss"];

export default function MoveQualityChart({ data, username }: Props) {
    const router = useRouter();

    if (!data) return (
        <div className="chart-card flex items-center justify-center">
            <p className="chart-empty-state">No move data available</p>
        </div>
    );

    const chartData = ORDER.map((name) => ({ name, count: data[name] || 0 }));

    if (chartData.every((d) => d.count === 0)) {
        return (
            <div className="chart-card">
                <h3 className="chart-title">Move Quality</h3>
                <div className="flex-1 flex items-center justify-center text-gray-400">
                    No moves to analyze yet
                </div>
            </div>
        );
    }

    const goToClass = (name?: string) => {
        if (!name) return;
        router.push(`/moves/${username}/${name}`);
    };

    return (
        <div className="chart-card">
            <h3 className="chart-title">Move Quality</h3>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={chartData}
                        margin={{ top: 16, right: 5, bottom: 0, left: -20 }}
                        // Click anywhere in a category column (not just on the bar).
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        onClick={(e: any) => {
                            const label = e?.activeLabel as string | undefined;
                            goToClass(label);
                        }}
                        style={{ cursor: "pointer" }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                        <XAxis
                            dataKey="name"
                            tick={{ fontSize: 10, fill: "var(--muted-fg)" }}
                            interval={0}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            tick={{ fontSize: 11, fill: "var(--muted-fg)" }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip
                            // The full-width cursor highlight doubles as visual confirmation
                            // that anywhere in this column is clickable.
                            cursor={{ fill: "rgba(212,162,76,0.08)" }}
                            contentStyle={{
                                background: "var(--card-bg)",
                                border: "1px solid var(--border)",
                                borderRadius: 4,
                                fontSize: 12,
                            }}
                            labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
                            itemStyle={{ color: "var(--primary)" }}
                        />
                        <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[entry.name] || "#8884d8"} />
                            ))}
                            <LabelList
                                dataKey="count"
                                position="top"
                                style={{ fontSize: 11, fontWeight: 700, fill: "var(--foreground)" }}
                                formatter={(value: unknown) => (Number(value) > 0 ? String(value) : "")}
                            />
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}