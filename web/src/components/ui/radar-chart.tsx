"use client";

import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";

interface RadarChartProps {
  data: { dimension: string; score: number }[];
  size?: number;
}

export function RadarChart({ data, size = 220 }: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={size}>
      <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid
          gridType="circle"
          stroke="#27272a"
          strokeDasharray="3 3"
        />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: "#71717a", fontSize: 10 }}
          stroke="#3f3f46"
        />
        <Radar
          dataKey="score"
          stroke="#818cf8"
          fill="#818cf8"
          fillOpacity={0.2}
          strokeWidth={2}
          isAnimationActive={true}
          animationDuration={800}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}
