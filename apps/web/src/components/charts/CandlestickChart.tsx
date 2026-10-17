"use client";

import React, { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  IChartApi,
  ISeriesApi,
  LineSeries,
} from "lightweight-charts";
import { StockBar } from "@/lib/types";

interface CandlestickChartProps {
  bars: StockBar[];
  height?: number;
  onChartReady?: (chart: IChartApi | null) => void;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  bars,
  height = 420,
  onChartReady,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const sma20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Khởi tạo Lightweight Chart
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#090d16" },
        textColor: "#94a3b8",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(30, 41, 59, 0.5)" },
        horzLines: { color: "rgba(30, 41, 59, 0.5)" },
      },
      crosshair: {
        vertLine: {
          color: "rgba(148, 163, 184, 0.4)",
          width: 1,
          style: 3,
        },
        horzLine: {
          color: "rgba(148, 163, 184, 0.4)",
          width: 1,
          style: 3,
        },
      },
      rightPriceScale: {
        borderColor: "rgba(30, 41, 59, 0.8)",
        scaleMargins: {
          top: 0.1,
          bottom: 0.25, // Dành 25% phía dưới cho volume
        },
      },
      timeScale: {
        borderColor: "rgba(30, 41, 59, 0.8)",
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height: height,
    });

    chartRef.current = chart;
    onChartReady?.(chart);

    // Series 1: Candlestick (Giá OHLCV)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981", // Xanh lục (Tăng)
      downColor: "#ef4444", // Đỏ (Giảm)
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
      priceFormat: {
        type: "price",
        precision: 2,
        minMove: 0.05,
      },
    });
    candleSeriesRef.current = candleSeries;

    // Series 2: Volume Histogram (Khối lượng phiên)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "volume_scale",
    });
    volumeSeriesRef.current = volumeSeries;

    chart.priceScale("volume_scale").applyOptions({
      scaleMargins: {
        top: 0.75, // Đặt volume ở 25% phía dưới biểu đồ
        bottom: 0,
      },
      visible: false,
    });

    // Series 3: SMA 20 (Đường trung bình 20 phiên)
    const sma20Series = chart.addSeries(LineSeries, {
      color: "#f59e0b", // Vàng hổ phách
      lineWidth: 2,
      priceLineVisible: false,
      title: "SMA 20",
    });
    sma20SeriesRef.current = sma20Series;

    // Resize Observer tự động đáp ứng kích thước khung hình
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
      onChartReady?.(null);
      chart.remove();
      chartRef.current = null;
    };
  }, [height, onChartReady]);

  // Cập nhật dữ liệu khi prop bars thay đổi
  useEffect(() => {
    if (!bars || bars.length === 0) return;
    if (!candleSeriesRef.current || !volumeSeriesRef.current || !sma20SeriesRef.current) return;

    // Chuẩn hóa và sort theo thời gian tăng dần
    const sorted = [...bars].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    // Format cho Candlestick
    const candleData = sorted.map((b) => ({
      time: b.date,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    // Format cho Volume (phân màu nến tăng hay giảm)
    const volumeData = sorted.map((b) => ({
      time: b.date,
      value: b.volume,
      color:
        b.close >= b.open
          ? "rgba(16, 185, 129, 0.45)" // Xanh bán trong suốt
          : "rgba(239, 68, 68, 0.45)", // Đỏ bán trong suốt
    }));

    // Tính toán SMA 20
    const smaData: { time: string; value: number }[] = [];
    const windowSize = 20;
    for (let i = 0; i < sorted.length; i++) {
      if (i >= windowSize - 1) {
        let sum = 0;
        for (let j = i - windowSize + 1; j <= i; j++) {
          sum += sorted[j].close;
        }
        smaData.push({
          time: sorted[i].date,
          value: parseFloat((sum / windowSize).toFixed(2)),
        });
      }
    }

    try {
      candleSeriesRef.current.setData(candleData);
      volumeSeriesRef.current.setData(volumeData);
      sma20SeriesRef.current.setData(smaData);
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.warn("Lỗi cập nhật dữ liệu biểu đồ:", err);
    }
  }, [bars]);

  return (
    <div className="relative w-full rounded-xl border border-slate-800 bg-slate-950 p-2 shadow-2xl">
      <div className="mb-2 flex items-center justify-between px-2 pt-1">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400"></span> Nến OHLCV
          </span>
          <span className="flex items-center gap-1.5 text-xs font-medium text-amber-400">
            <span className="h-0.5 w-3 bg-amber-400"></span> SMA(20)
          </span>
          <span className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            <span className="h-2 w-2 rounded-sm bg-slate-600"></span> Khối lượng (Volume)
          </span>
        </div>
        <span className="text-[11px] text-slate-500">Kéo/Phóng to (Pan & Zoom)</span>
      </div>
      <div ref={containerRef} className="w-full" style={{ height: `${height}px` }} />
    </div>
  );
};
