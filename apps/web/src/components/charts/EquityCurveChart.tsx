"use client";

import React, { useMemo, useState } from "react";
import { EquityCurvePoint } from "@/lib/types";

interface EquityCurveChartProps {
  equityCurve: EquityCurvePoint[];
  initialCapital: number;
  height?: number;
  strategyLabel?: string;
  strategyShortLabel?: string;
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  equityCurve,
  initialCapital,
  height = 320,
  strategyLabel,
  strategyShortLabel,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const { points, minVal, maxVal, width, padding } = useMemo(() => {
    const width = 800;
    const padding = { top: 20, right: 30, bottom: 30, left: 65 };

    if (!equityCurve || equityCurve.length === 0) {
      return { points: [], minVal: 0, maxVal: 1, width, padding };
    }

    // Chuẩn hóa dữ liệu phòng thủ chống trường hợp PascalCase hoặc thiếu trường
    const normalizedData: EquityCurvePoint[] = equityCurve.map((pt) => {
      const anyPt = pt as unknown as Record<string, unknown>;
      const totalEquity = Number(pt.total_equity ?? anyPt.Total_Equity ?? initialCapital);
      const benchmarkEquity = Number(pt.benchmark_equity ?? anyPt.Benchmark_Equity ?? initialCapital);
      const drawdownPct = Number(pt.drawdown_pct ?? anyPt.Drawdown_Pct ?? 0);
      const dailyReturn = Number(pt.daily_return ?? anyPt.Daily_Return ?? 0);
      const dateStr = String(pt.date ?? anyPt.Date ?? "");

      return {
        date: dateStr,
        total_equity: isNaN(totalEquity) ? initialCapital : totalEquity,
        benchmark_equity: isNaN(benchmarkEquity) ? initialCapital : benchmarkEquity,
        drawdown_pct: isNaN(drawdownPct) ? 0 : drawdownPct,
        daily_return: isNaN(dailyReturn) ? 0 : dailyReturn,
      };
    });

    // Lấy min và max giá trị tài sản
    let min = initialCapital;
    let max = initialCapital;

    normalizedData.forEach((pt) => {
      if (pt.total_equity < min) min = pt.total_equity;
      if (pt.total_equity > max) max = pt.total_equity;
      if (pt.benchmark_equity < min) min = pt.benchmark_equity;
      if (pt.benchmark_equity > max) max = pt.benchmark_equity;
    });

    // Thêm biên độ 5% trên dưới
    const range = max - min || 1;
    const paddedMin = Math.max(0, min - range * 0.05);
    const paddedMax = max + range * 0.05;

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const scaleX = (idx: number) =>
      padding.left + (idx / Math.max(normalizedData.length - 1, 1)) * chartW;

    const scaleY = (val: number) =>
      padding.top + chartH - ((val - paddedMin) / (paddedMax - paddedMin || 1)) * chartH;

    const pts = normalizedData.map((pt, idx) => ({
      x: scaleX(idx),
      yAI: scaleY(pt.total_equity),
      yBH: scaleY(pt.benchmark_equity),
      yBase: scaleY(initialCapital),
      data: pt,
    }));

    return {
      points: pts,
      minVal: paddedMin,
      maxVal: paddedMax,
      width,
      padding,
    };
  }, [equityCurve, initialCapital, height]);

  if (!equityCurve || equityCurve.length === 0) {
    return (
      <div className="flex h-64 w-full items-center justify-center rounded-xl border border-slate-800 bg-slate-950 text-xs text-slate-500">
        Chưa có dữ liệu đường cong tài sản
      </div>
    );
  }

  // Tạo đường dẫn SVG Path cho AI Strategy
  const aiPath = points.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.yAI.toFixed(1)}`;
  }, "");

  // Tạo đường dẫn SVG Path cho Benchmark
  const bhPath = points.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.yBH.toFixed(1)}`;
  }, "");

  // Đường cơ sở vốn ban đầu
  const baseY = points[0]?.yBase || height / 2;

  const hoveredPoint =
    hoveredIndex !== null && points[hoveredIndex] ? points[hoveredIndex] : null;

  return (
    <div className="relative w-full rounded-xl border border-slate-800 bg-slate-950 p-3 shadow-xl">
      {/* Legend & Chú giải */}
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-2 text-xs">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-semibold text-emerald-400">
            <span className="h-0.5 w-3.5 bg-emerald-400" /> {strategyLabel || "Chiến lược AI (Đo lường OOS)"}
          </span>
          <span className="flex items-center gap-1.5 font-medium text-cyan-400">
            <span className="h-0.5 w-3.5 bg-cyan-400" /> Buy & Hold Benchmark
          </span>
          <span className="flex items-center gap-1.5 font-normal text-slate-500">
            <span className="h-0.5 w-3.5 border-t border-dashed border-slate-500" /> Vốn ban đầu (100%)
          </span>
        </div>
        <span className="text-[11px] text-slate-500">Đơn vị: VNĐ</span>
      </div>

      {/* SVG Canvas Responsive */}
      <div className="w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="aiGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Vạch lưới ngang */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct) => {
            const val = minVal + (maxVal - minVal) * (1 - pct);
            const y = padding.top + (height - padding.top - padding.bottom) * pct;
            return (
              <g key={pct}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="rgba(30, 41, 59, 0.6)"
                  strokeDasharray="2 3"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                >
                  {(val / 1_000_000).toFixed(1)}M
                </text>
              </g>
            );
          })}

          {/* Đường vốn ban đầu Base Line */}
          <line
            x1={padding.left}
            y1={baseY}
            x2={width - padding.right}
            y2={baseY}
            stroke="#475569"
            strokeDasharray="4 4"
            strokeWidth="1"
          />

          {/* Vùng đổ màu Gradient AI */}
          {points.length > 0 && (
            <path
              d={`${aiPath} L ${points[points.length - 1].x} ${
                height - padding.bottom
              } L ${points[0].x} ${height - padding.bottom} Z`}
              fill="url(#aiGradient)"
            />
          )}

          {/* Đường Benchmark */}
          <path
            d={bhPath}
            fill="none"
            stroke="#06b6d4"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />

          {/* Đường Chiến lược AI */}
          <path
            d={aiPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinejoin="round"
          />

          {/* Con trỏ Hover tương tác */}
          {hoveredPoint && (
            <g>
              <line
                x1={hoveredPoint.x}
                y1={padding.top}
                x2={hoveredPoint.x}
                y2={height - padding.bottom}
                stroke="#94a3b8"
                strokeDasharray="2 2"
                strokeWidth="1"
              />
              {/* Điểm AI */}
              <circle
                cx={hoveredPoint.x}
                cy={hoveredPoint.yAI}
                r="4"
                fill="#10b981"
                stroke="#0f172a"
                strokeWidth="2"
              />
              {/* Điểm Benchmark */}
              <circle
                cx={hoveredPoint.x}
                cy={hoveredPoint.yBH}
                r="4"
                fill="#06b6d4"
                stroke="#0f172a"
                strokeWidth="2"
              />
            </g>
          )}

          {/* Vùng nhận diện sự kiện Mouse Hover */}
          {points.map((pt, idx) => (
            <rect
              key={idx}
              x={pt.x - (width / points.length) / 2}
              y={padding.top}
              width={width / points.length}
              height={height - padding.top - padding.bottom}
              fill="transparent"
              className="cursor-crosshair"
              onMouseEnter={() => setHoveredIndex(idx)}
            />
          ))}
        </svg>
      </div>

      {/* Hover Info Tooltip Bar */}
      {hoveredPoint && (
        <div className="mt-2 flex flex-wrap items-center justify-between rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs">
          <span className="font-semibold text-slate-300">
            Ngày: {hoveredPoint.data.date || "--"}
          </span>
          <div className="flex items-center gap-4">
            <span className="font-bold text-emerald-400">
              {strategyShortLabel || "AI"}: {(hoveredPoint.data.total_equity ?? 0).toLocaleString("vi-VN")} đ (
              {(
                (((hoveredPoint.data.total_equity ?? initialCapital) - initialCapital) /
                  (initialCapital || 1)) *
                100
              ).toFixed(2)}
              %)
            </span>
            <span className="font-bold text-cyan-400">
              B&H: {(hoveredPoint.data.benchmark_equity ?? 0).toLocaleString("vi-VN")} đ (
              {(
                (((hoveredPoint.data.benchmark_equity ?? initialCapital) - initialCapital) /
                  (initialCapital || 1)) *
                100
              ).toFixed(2)}
              %)
            </span>
            <span className="text-slate-400">
              Drawdown:{" "}
              <strong className="text-rose-400">
                {(hoveredPoint.data.drawdown_pct ?? 0).toFixed(2)}%
              </strong>
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
