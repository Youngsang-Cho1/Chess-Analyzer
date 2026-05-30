"use client";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface StyleVector {
  consistency: number;
  aggression: number;
  accuracy: number;
  tactical: number;
}

interface Props {
  styleVector: StyleVector;
  style: string;
  tag?: string | null;
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { payload: { axis: string; value: number } }[] }) => {
  if (!active || !payload?.length) return null;
  const { axis, value } = payload[0].payload;
  return (
    <div style={{
      background: "#0E0F12",
      border: "1px solid rgba(212,162,76,0.3)",
      borderRadius: 4,
      padding: "6px 10px",
      fontSize: 12,
      fontFamily: "monospace",
    }}>
      <span style={{ color: "#8A8478", textTransform: "uppercase", letterSpacing: "0.08em", fontSize: 10 }}>{axis}</span>
      <div style={{ color: "#D4A24C", fontWeight: 700, fontSize: 18, lineHeight: 1.2 }}>{value}</div>
    </div>
  );
};

export default function StyleRadarChart({ styleVector, style, tag }: Props) {
  const data = [
    { axis: "Consistency", value: styleVector.consistency },
    { axis: "Aggression", value: styleVector.aggression },
    { axis: "Accuracy",   value: styleVector.accuracy },
    { axis: "Tactical",   value: styleVector.tactical },
  ];

  return (
    <div className="stat-box" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-start" }}>
      <div className="stat-label" style={{ position: "absolute", top: "1rem" }}>Play Style</div>
      <div style={{ marginTop: "1.75rem", marginBottom: "0.25rem", display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center" }}>
        <span className="stat-value stat-value-style" style={{ fontSize: "1.2rem" }}>{style}</span>
        {tag && (
          <span style={{
            fontFamily: "monospace",
            fontSize: "0.6rem",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            padding: "0.15rem 0.45rem",
            borderRadius: "3px",
            border: "1px solid rgba(212,162,76,0.35)",
            color: "var(--primary)",
            background: "rgba(212,162,76,0.08)",
          }}>{tag}</span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={190}>
        <RadarChart data={data} margin={{ top: 8, right: 28, bottom: 8, left: 28 }}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "#8A8478", fontSize: 11, fontFamily: "monospace" }}
            tickLine={false}
          />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          <Tooltip content={<CustomTooltip /> as any} />
          <Radar
            dataKey="value"
            stroke="#D4A24C"
            strokeWidth={1.5}
            fill="#D4A24C"
            fillOpacity={0.15}
            dot={{ r: 3, fill: "#D4A24C", strokeWidth: 0 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}