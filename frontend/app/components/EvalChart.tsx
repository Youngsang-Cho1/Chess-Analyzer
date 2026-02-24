"use client";

import { useRef } from "react";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ResponsiveContainer,
} from "recharts";

interface MovePoint {
    index: number;
    label: string;
    score: number;
    raw: number;
    mate_in?: number | null;
    classification: string;
}

interface EvalChartProps {
    points: MovePoint[];
    currentIndex: number;
    onMoveClick: (index: number) => void;
}

const CAP = 800;

function capScore(score: number, mate_in?: number | null): number {
    if (mate_in !== null && mate_in !== undefined) {
        return mate_in > 0 ? CAP : -CAP;
    }
    return Math.max(-CAP, Math.min(CAP, score));
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { payload: MovePoint }[] }) => {
    if (active && payload && payload.length) {
        const d = payload[0].payload;
        const scoreLabel = d.mate_in !== null && d.mate_in !== undefined
            ? `M${Math.abs(d.mate_in)}`
            : `${(d.raw / 100).toFixed(2)}`;
        return (
            <div className="eval-tooltip">
                <div className="eval-tooltip-label">{d.label}</div>
                <div>Score: <span className={d.raw >= 0 ? "eval-score-positive" : "eval-score-negative"}>{scoreLabel}</span></div>
                <div className="eval-tooltip-class">{d.classification}</div>
            </div>
        );
    }
    return null;
};

const CustomDot = (props: { cx?: number; cy?: number; payload?: MovePoint; currentIndex?: number }) => {
    const { cx, cy, payload, currentIndex } = props;
    if (!payload || cx === undefined || cy === undefined) return null;
    if (payload.index !== currentIndex) return null;
    return <circle cx={cx} cy={cy} r={5} fill="#818cf8" stroke="#312e81" strokeWidth={2} />;
};

export default function EvalChart({ points, currentIndex, onMoveClick }: EvalChartProps) {
    const data = points.map((p) => ({
        ...p,
        score: capScore(p.raw, p.mate_in),
    }));

    // Track hovered point via ref to avoid stale closure in click handler
    const hoveredPoint = useRef<MovePoint | null>(null);

    return (
        <div
            className="eval-chart-container"
            onClick={() => {
                if (hoveredPoint.current) {
                    onMoveClick(hoveredPoint.current.index);
                }
            }}
        >
            <ResponsiveContainer width="100%" height={140}>
                <AreaChart
                    data={data}
                    margin={{ top: 8, right: 8, left: -28, bottom: 0 }}
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    onMouseMove={(e: any) => {
                        if (e && e.activePayload && e.activePayload[0]) {
                            hoveredPoint.current = e.activePayload[0].payload as MovePoint;
                        }
                    }}
                    onMouseLeave={() => { hoveredPoint.current = null; }}
                >
                    <defs>
                        <linearGradient id="whiteGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#e2e8f0" stopOpacity={0.35} />
                            <stop offset="95%" stopColor="#e2e8f0" stopOpacity={0.05} />
                        </linearGradient>
                        <linearGradient id="blackGrad" x1="0" y1="1" x2="0" y2="0">
                            <stop offset="5%" stopColor="#1e1b4b" stopOpacity={0.7} />
                            <stop offset="95%" stopColor="#1e1b4b" stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                        dataKey="index"
                        tick={{ fill: "#64748b", fontSize: 10 }}
                        tickLine={false}
                        axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
                        interval="preserveStartEnd"
                    />
                    <YAxis
                        domain={[-CAP, CAP]}
                        tick={{ fill: "#64748b", fontSize: 10 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(v) => (v > 0 ? `+${v / 100}` : `${v / 100}`)}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeWidth={1} />

                    {/* White advantage area (score > 0) */}
                    <Area
                        type="monotone"
                        dataKey="score"
                        stroke="#94a3b8"
                        strokeWidth={1.5}
                        fill="url(#whiteGrad)"
                        dot={<CustomDot currentIndex={currentIndex} />}
                        activeDot={{ r: 4, fill: "#818cf8" }}
                        isAnimationActive={false}
                        baseValue={0}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
