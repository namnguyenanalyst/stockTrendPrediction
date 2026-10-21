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
  allBars?: StockBar[];
  height?: number;
  onChartReady?: (chart: IChartApi | null) => void;
  showSMA20?: boolean;
  showSMA50?: boolean;
  showSMA200?: boolean;
  showVolume?: boolean;
}

function calculateSMA(
  sorted: StockBar[],
  windowSize: number
): { time: string; value: number }[] {
  const result: { time: string; value: number }[] = [];
  for (let i = 0; i < sorted.length; i++) {
    if (i >= windowSize - 1) {
      let sum = 0;
      for (let j = i - windowSize + 1; j <= i; j++) {
        sum += sorted[j].close;
      }
      result.push({
        time: sorted[i].date,
        value: parseFloat((sum / windowSize).toFixed(2)),
      });
    }
  }
  return result;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  bars,
  allBars,
  height = 420,
  onChartReady,
  showSMA20 = true,
  showSMA50 = true,
  showSMA200 = false,
  showVolume = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const sma20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma200SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

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
        vertLines: { color: "rgba(30, 41, 59, 0.45)" },
        horzLines: { color: "rgba(30, 41, 59, 0.45)" },
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
          bottom: 0.25,
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
        top: 0.75,
        bottom: 0,
      },
      visible: false,
    });

    // Series 3: SMA 20 (Đường trung bình 20 phiên - Vàng hổ phách)
    const sma20Series = chart.addSeries(LineSeries, {
      color: "#f59e0b",
      lineWidth: 2,
      priceLineVisible: false,
      title: "SMA 20",
    });
    sma20SeriesRef.current = sma20Series;

    // Series 4: SMA 50 (Đường trung bình 50 phiên - Tím phong lan)
    const sma50Series = chart.addSeries(LineSeries, {
      color: "#a855f7",
      lineWidth: 2,
      priceLineVisible: false,
      title: "SMA 50",
    });
    sma50SeriesRef.current = sma50Series;

    // Series 5: SMA 200 (Đường trung bình 200 phiên - Xanh biển Sky)
    const sma200Series = chart.addSeries(LineSeries, {
      color: "#38bdf8",
      lineWidth: 2,
      priceLineVisible: false,
      title: "SMA 200",
    });
    sma200SeriesRef.current = sma200Series;

    // Resize Observer
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

  // Điều khiển ẩn / hiện chỉ báo kỹ thuật theo props
  useEffect(() => {
    sma20SeriesRef.current?.applyOptions({ visible: showSMA20 });
    sma50SeriesRef.current?.applyOptions({ visible: showSMA50 });
    sma200SeriesRef.current?.applyOptions({ visible: showSMA200 });
    volumeSeriesRef.current?.applyOptions({ visible: showVolume });
  }, [showSMA20, showSMA50, showSMA200, showVolume]);

  // Cập nhật dữ liệu khi prop bars thay đổi
  useEffect(() => {
    if (!bars || bars.length === 0) return;
    if (
      !candleSeriesRef.current ||
      !volumeSeriesRef.current ||
      !sma20SeriesRef.current ||
      !sma50SeriesRef.current ||
      !sma200SeriesRef.current
    )
      return;

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

    // Format cho Volume
    const volumeData = sorted.map((b) => ({
      time: b.date,
      value: b.volume,
      color:
        b.close >= b.open
          ? "rgba(16, 185, 129, 0.45)"
          : "rgba(239, 68, 68, 0.45)",
    }));

    // Tính toán SMA 20, 50, 200 trên toàn bộ chuỗi nến lịch sử (nếu có) để tránh mất đường MA khi xem khung ngắn
    const sourceForSMA = allBars && allBars.length >= bars.length ? allBars : sorted;
    const sortedSMA = [...sourceForSMA].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    const allSma20 = calculateSMA(sortedSMA, 20);
    const allSma50 = calculateSMA(sortedSMA, 50);
    const allSma200 = calculateSMA(sortedSMA, 200);

    const visibleDateSet = new Set(sorted.map((b) => b.date));
    const sma20Data = allSma20.filter((item) => visibleDateSet.has(item.time));
    const sma50Data = allSma50.filter((item) => visibleDateSet.has(item.time));
    const sma200Data = allSma200.filter((item) => visibleDateSet.has(item.time));

    try {
      candleSeriesRef.current.setData(candleData);
      volumeSeriesRef.current.setData(volumeData);
      sma20SeriesRef.current.setData(sma20Data);
      sma50SeriesRef.current.setData(sma50Data);
      sma200SeriesRef.current.setData(sma200Data);
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.warn("Lỗi cập nhật dữ liệu biểu đồ:", err);
    }
  }, [bars, allBars]);

  return (
    <div className="relative w-full rounded-xl border border-slate-800 bg-slate-950 p-2 shadow-2xl">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-2 pt-1 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 font-semibold text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400"></span> Nến OHLCV
          </span>

          {showSMA20 && (
            <span className="flex items-center gap-1.5 font-medium text-amber-400">
              <span className="h-0.5 w-3 bg-amber-400"></span> SMA(20)
            </span>
          )}

          {showSMA50 && (
            <span className="flex items-center gap-1.5 font-medium text-purple-400">
              <span className="h-0.5 w-3 bg-purple-400"></span> SMA(50)
            </span>
          )}

          {showSMA200 && (
            <span className="flex items-center gap-1.5 font-medium text-sky-400">
              <span className="h-0.5 w-3 bg-sky-400"></span> SMA(200)
            </span>
          )}

          {showVolume && (
            <span className="flex items-center gap-1.5 font-medium text-slate-400">
              <span className="h-2 w-2 rounded-sm bg-slate-600"></span> Khối lượng
            </span>
          )}
        </div>

        <span className="text-[11px] text-slate-500">Kéo/Phóng to (Pan & Zoom)</span>
      </div>
      <div ref={containerRef} className="w-full" style={{ height: `${height}px` }} />
    </div>
  );
};
