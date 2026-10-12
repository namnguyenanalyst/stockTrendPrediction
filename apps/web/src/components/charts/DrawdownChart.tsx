"use client";

import React, { useMemo } from "react";
import { EquityCurvePoint } from "@/lib/types";

interface DrawdownChartProps {
  equityCurve: EquityCurvePoint[];
  height?: number;
}

export const DrawdownChart: React.FC<DrawdownChartProps> = ({
  equityCurve,
  height = 140,
}) => {
  const { points, minDrawdown, width, padding } = useMemo(() => {
    const width = 800;
    const padding = { top: 15, right: 30, bottom: 25, left: 65 };

    if (!equityCurve || equityCurve.length === 0) {
      return { points: [], minDrawdown: -10, width, padding };
    }

    let minDD = 0;
    equityCurve.forEach((pt) => {
      if (pt.drawdown_pct < minDD) minDD = pt.drawdown_pct;
    });

    // Làm tròn min drawdown xuống bội số 5
    const floorMin = Math.min(-5, Math.floor(minDD / 5) * 5);

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const scaleX = (idx: number) =>
      padding.left + (idx / Math.max(equityCurve.length - 1, 1)) * chartW;

    const scaleY = (ddPct: number) =>
      padding.top + (Math.abs(ddPct) / Math.abs(floorMin)) * chartH;

    const pts = equityCurve.map((pt, idx) => ({
      x: scaleX(idx),
      y: scaleY(pt.drawdown_pct),
      dd: pt.drawdown_pct,
      date: pt.date,
    }));

    return {
      points: pts,
      minDrawdown: floorMin,
      width,
      padding,
    };
  }, [equityCurve, height]);

  if (!equityCurve || equityCurve.length === 0) {
    return null;
  }

  // Tạo đường path Drawdown
  const ddPath = points.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`;
  }, "");

  const baseY = padding.top; // Mức 0% nằm trên đỉnh

  return (
    <div className="relative w-full rounded-xl border border-slate-800 bg-slate-950 p-3 shadow-lg">
      <div className="mb-1 flex items-center justify-between px-2 text-xs">
        <span className="font-semibold text-rose-400">
          Đồ thị Sụt giảm Tài sản từ Đỉnh (Underwater Drawdown Timeline)
        </span>
        <span className="text-[11px] text-slate-500">
          Mức sụt giảm sâu nhất:{" "}
          <strong className="text-rose-400">{minDrawdown.toFixed(1)}%</strong>
        </span>
      </div>

      <div className="w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
          <defs>
            <linearGradient id="ddGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Vạch 0% cơ sở */}
          <line
            x1={padding.left}
            y1={baseY}
            x2={width - padding.right}
            y2={baseY}
            stroke="#64748b"
            strokeWidth="1"
          />
          <text
            x={padding.left - 8}
            y={baseY + 3}
            textAnchor="end"
            fill="#94a3b8"
            fontSize="9"
            fontFamily="monospace"
          >
            0%
          </text>

          {/* Vạch đáy Drawdown */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="rgba(239, 68, 68, 0.4)"
            strokeDasharray="2 3"
          />
          <text
            x={padding.left - 8}
            y={height - padding.bottom + 3}
            textAnchor="end"
            fill="#f87171"
            fontSize="9"
            fontFamily="monospace"
          >
            {minDrawdown.toFixed(0)}%
          </text>

          {/* Vùng đổ màu sụt giảm */}
          {points.length > 0 && (
            <path
              d={`${ddPath} L ${points[points.length - 1].x} ${baseY} L ${
                points[0].x
              } ${baseY} Z`}
              fill="url(#ddGradient)"
            />
          )}

          {/* Đường viền Drawdown */}
          <path
            d={ddPath}
            fill="none"
            stroke="#ef4444"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
};
