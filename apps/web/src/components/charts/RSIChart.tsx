"use client";

import React, { useEffect, useRef } from "react";
import {
  ColorType,
  createChart,
  IChartApi,
  ISeriesApi,
  LineSeries,
} from "lightweight-charts";
import { StockIndicatorBar } from "@/lib/types";

interface RSIChartProps {
  indicators: StockIndicatorBar[];
  height?: number;
}

export const RSIChart: React.FC<RSIChartProps> = ({
  indicators,
  height = 140,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const rsiSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#090d16" },
        textColor: "#94a3b8",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: "rgba(30, 41, 59, 0.3)" },
        horzLines: { color: "rgba(30, 41, 59, 0.3)" },
      },
      crosshair: {
        vertLine: { color: "rgba(148, 163, 184, 0.3)", width: 1, style: 3 },
        horzLine: { color: "rgba(148, 163, 184, 0.3)", width: 1, style: 3 },
      },
      rightPriceScale: {
        borderColor: "rgba(30, 41, 59, 0.8)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "rgba(30, 41, 59, 0.8)",
        visible: true,
      },
      width: containerRef.current.clientWidth,
      height: height,
    });

    chartRef.current = chart;

    const rsiSeries = chart.addSeries(LineSeries, {
      color: "#818cf8", // Màu tím nhạt Indigo
      lineWidth: 2,
      priceFormat: {
        type: "custom",
        formatter: (val: number) => val.toFixed(1),
      },
    });
    rsiSeriesRef.current = rsiSeries;

    // Vạch ngưỡng quá mua 70
    rsiSeries.createPriceLine({
      price: 70,
      color: "rgba(239, 68, 68, 0.7)",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Quá mua (70)",
    });

    // Vạch ngưỡng quá bán 30
    rsiSeries.createPriceLine({
      price: 30,
      color: "rgba(16, 185, 129, 0.7)",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Quá bán (30)",
    });

    // Vạch cân bằng 50
    rsiSeries.createPriceLine({
      price: 50,
      color: "rgba(148, 163, 184, 0.3)",
      lineWidth: 1,
      lineStyle: 3,
      axisLabelVisible: false,
      title: "50",
    });

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!indicators || indicators.length === 0 || !rsiSeriesRef.current) return;

    const sorted = [...indicators].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const rsiData = sorted
      .filter((item) => item.rsi_14 !== null && item.rsi_14 !== undefined && !isNaN(item.rsi_14))
      .map((item) => ({
        time: item.date,
        value: item.rsi_14,
      }));

    try {
      rsiSeriesRef.current.setData(rsiData);
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.warn("Lỗi vẽ đường RSI:", err);
    }
  }, [indicators]);

  const latestRSI =
    indicators && indicators.length > 0
      ? indicators[indicators.length - 1].rsi_14
      : null;

  return (
    <div className="relative w-full rounded-xl border border-slate-800 bg-slate-950 p-2 shadow-lg">
      <div className="mb-1 flex items-center justify-between px-2 pt-0.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300">
            Chỉ số Sức mạnh Tương đối RSI (14)
          </span>
          {latestRSI !== null && (
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                latestRSI >= 70
                  ? "bg-rose-500/20 text-rose-400"
                  : latestRSI <= 30
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-slate-800 text-indigo-300"
              }`}
            >
              Hiện tại: {latestRSI.toFixed(1)}{" "}
              {latestRSI >= 70
                ? "• Quá mua"
                : latestRSI <= 30
                ? "• Quá bán"
                : "• Trung tính"}
            </span>
          )}
        </div>
        <span className="text-[10px] text-slate-500">Chu kỳ 14 phiên</span>
      </div>
      <div ref={containerRef} className="w-full" style={{ height: `${height}px` }} />
    </div>
  );
};
