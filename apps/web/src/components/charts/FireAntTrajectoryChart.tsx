"use client";
import { buildTrajectory, trajectoryProblem } from "@/lib/predictionTrajectory";
import { formatPercentVi, formatPriceVnd } from "@/lib/predictionPresentation";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  AreaSeries,
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  IChartApi,
  ISeriesApi,
  IPriceLine,
  LineSeries,
  LineStyle,
  LineType,
} from "lightweight-charts";
import {
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  Sparkles,
} from "lucide-react";
import { PredictionResponse, StockBar } from "@/lib/types";

interface FireAntTrajectoryChartProps {
  symbol: string;
  bars: StockBar[];
  prediction: PredictionResponse | null;
  modelType: "lightgbm" | "lstm";
  height?: number;
}

// Hàm tính SMA (Simple Moving Average)
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

export const FireAntTrajectoryChart: React.FC<FireAntTrajectoryChartProps> = ({
  symbol,
  bars,
  prediction,
  modelType,
  height = 460,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // Series Refs
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const sma20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const trajectorySeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const trajectoryAreaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const targetPriceLineRef = useRef<IPriceLine | null>(null);

  // Tùy chọn hiển thị
  const [showTrajectory, setShowTrajectory] = useState<boolean>(true);
  const [showSMA20, setShowSMA20] = useState<boolean>(true);
  const [showSMA50, setShowSMA50] = useState<boolean>(false);
  const [showVolume, setShowVolume] = useState<boolean>(true);
  const [timeRange, setTimeRange] = useState<"1M" | "3M" | "6M" | "ALL">("3M");

  // Hover state cho nến đang xem
  const [hoveredBar, setHoveredBar] = useState<StockBar | null>(null);

  // Sắp xếp nến theo thời gian tăng dần
  const sortedBars = useMemo(() => {
    if (!bars || bars.length === 0) return [];
    return [...bars].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [bars]);

  // Lọc theo khung thời gian (1M ~ 22 phiên, 3M ~ 65 phiên, 6M ~ 130 phiên)
  const displayBars = useMemo(() => {
    if (sortedBars.length === 0) return [];
    if (timeRange === "1M") return sortedBars.slice(-25);
    if (timeRange === "3M") return sortedBars.slice(-65);
    if (timeRange === "6M") return sortedBars.slice(-130);
    return sortedBars;
  }, [sortedBars, timeRange]);

  // Nến cuối cùng (Phiên T)
  const lastBar = sortedBars[sortedBars.length - 1];

  // Tính toán các điểm giá cho Quỹ đạo dự phóng 3 phiên (T+1 -> T+3)
  const trajectoryError = trajectoryProblem(prediction, symbol, modelType, lastBar);
  const trajectoryPoints = useMemo(() => buildTrajectory(prediction, symbol, modelType, lastBar), [lastBar, prediction, symbol, modelType]);

  // Khởi tạo Lightweight Chart
  useEffect(() => {
    if (!containerRef.current) return;

    // Khởi tạo Canvas Chart
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#090d16" },
        textColor: "#94a3b8",
        fontSize: 11,
      },
      localization: {
        locale: "vi-VN",
        priceFormatter: (price: number) =>
          Math.round(price * 1000).toLocaleString("vi-VN"),
      },
      grid: {
        vertLines: { color: "rgba(30, 41, 59, 0.45)" },
        horzLines: { color: "rgba(30, 41, 59, 0.45)" },
      },
      crosshair: {
        vertLine: {
          color: "rgba(148, 163, 184, 0.5)",
          width: 1,
          style: LineStyle.Dashed,
        },
        horzLine: {
          color: "rgba(148, 163, 184, 0.5)",
          width: 1,
          style: LineStyle.Dashed,
        },
      },
      rightPriceScale: {
        borderColor: "rgba(30, 41, 59, 0.8)",
        scaleMargins: {
          top: 0.12,
          bottom: 0.22,
        },
      },
      timeScale: {
        borderColor: "rgba(30, 41, 59, 0.8)",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 12, // Khoảng trống bên phải cho Quỹ đạo tương lai vươn tới
      },
      width: containerRef.current.clientWidth,
      height: height,
    });

    chartRef.current = chart;

    // 1. Series Candlestick (Giá thực tế lịch sử)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981", // Xanh lục
      downColor: "#ef4444", // Đỏ
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
      priceFormat: {
        type: "price",
        precision: 2,
        // Shared price-scale formatter also formats the illustration. Preserve
        // its two decimals instead of rounding a value such as 232.07 to 232.05.
        minMove: 0.01,
      },
    });
    candleSeriesRef.current = candleSeries;

    // 2. Series Volume Histogram (Khối lượng phiên)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "volume_scale",
    });
    volumeSeriesRef.current = volumeSeries;

    chart.priceScale("volume_scale").applyOptions({
      scaleMargins: {
        top: 0.78,
        bottom: 0,
      },
      visible: false,
    });

    // 3. Series SMA 20 (Đường trung bình 20 phiên - Xanh biển TradingView)
    const sma20Series = chart.addSeries(LineSeries, {
      color: "#3b82f6",
      lineWidth: 2,
      priceLineVisible: false,
      title: "SMA 20",
    });
    sma20SeriesRef.current = sma20Series;

    // 4. Series SMA 50 (Đường trung bình 50 phiên - Vàng cam)
    const sma50Series = chart.addSeries(LineSeries, {
      color: "#f59e0b",
      lineWidth: 2,
      priceLineVisible: false,
      title: "SMA 50",
    });
    sma50SeriesRef.current = sma50Series;

    // 5. Series Vùng diện tích mờ dưới Quỹ đạo AI (Glow Area)
    const trajectoryAreaSeries = chart.addSeries(AreaSeries, {
      topColor: "rgba(56, 189, 248, 0.22)",
      bottomColor: "rgba(56, 189, 248, 0.0)",
      lineColor: "transparent",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    trajectoryAreaSeriesRef.current = trajectoryAreaSeries;

    // 6. Series Quỹ đạo Dự phóng AI (FireAnt Trajectory Curve - Đường cong tương lai với chấm tròn)
    const trajectorySeries = chart.addSeries(LineSeries, {
      color: "#38bdf8", // Xanh lơ dạ quang FireAnt
      lineWidth: 3,
      lineType: LineType.Curved, // Đường cong uốn lượn mượt mà chuẩn FireAnt
      pointMarkersVisible: true, // Hiển thị các chấm tròn tại các mốc T+1, T+2, T+3
      pointMarkersRadius: 5,
      priceFormat: {
        type: "price",
        precision: 2,
        minMove: 0.01,
      },
      priceLineVisible: false,
      lastValueVisible: false,
      priceLineWidth: 1,
      priceLineStyle: LineStyle.Dashed,
      priceLineColor: "#38bdf8",
      title: "",
    });
    trajectorySeriesRef.current = trajectorySeries;

    // Lắng nghe sự kiện di chuyển chuột trên chart để hiển thị OHLC thanh lịch
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData) {
        setHoveredBar(null);
        return;
      }
      const candleData = param.seriesData.get(candleSeries) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      const volData = param.seriesData.get(volumeSeries) as
        | { value: number }
        | undefined;

      if (candleData) {
        setHoveredBar({
          date: String(param.time),
          open: candleData.open,
          high: candleData.high,
          low: candleData.low,
          close: candleData.close,
          volume: volData ? volData.value : 0,
        });
      }
    });

    // Resize Handler
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        });
      }
    };
    window.addEventListener("resize", handleResize);
    const resizeObserver =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => handleResize())
        : null;
    if (resizeObserver && containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener("resize", handleResize);
      resizeObserver?.disconnect();
      chart.remove();
      targetPriceLineRef.current = null;
      chartRef.current = null;
    };
  }, [height]);

  // Cập nhật tùy chọn hiển thị theo toggle
  useEffect(() => {
    sma20SeriesRef.current?.applyOptions({ visible: showSMA20 });
    sma50SeriesRef.current?.applyOptions({ visible: showSMA50 });
    volumeSeriesRef.current?.applyOptions({ visible: showVolume });
    trajectorySeriesRef.current?.applyOptions({ visible: showTrajectory });
    trajectoryAreaSeriesRef.current?.applyOptions({ visible: showTrajectory });
  }, [showSMA20, showSMA50, showVolume, showTrajectory, height]);

  // Cập nhật dữ liệu Candlestick, Volume & Quỹ đạo AI vào Chart
  useEffect(() => {
    if (!displayBars || displayBars.length === 0) return;
    if (
      !candleSeriesRef.current ||
      !volumeSeriesRef.current ||
      !sma20SeriesRef.current ||
      !sma50SeriesRef.current ||
      !trajectorySeriesRef.current ||
      !trajectoryAreaSeriesRef.current
    )
      return;

    // Dữ liệu Nến OHLCV
    const candleData = displayBars.map((b) => ({
      time: b.date,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    // Dữ liệu Khối lượng Volume
    const volumeData = displayBars.map((b) => ({
      time: b.date,
      value: b.volume,
      color:
        b.close >= b.open
          ? "rgba(16, 185, 129, 0.45)"
          : "rgba(239, 68, 68, 0.45)",
    }));

    // Tính SMA trên toàn bộ chuỗi sortedBars để không bị đứt đoạn
    const allSma20 = calculateSMA(sortedBars, 20);
    const allSma50 = calculateSMA(sortedBars, 50);
    const visibleDateSet = new Set(displayBars.map((b) => b.date));

    const sma20Data = allSma20.filter((item) => visibleDateSet.has(item.time));
    const sma50Data = allSma50.filter((item) => visibleDateSet.has(item.time));

    // Dữ liệu Quỹ đạo Dự phóng T+1 -> T+3
    const trajectoryData = trajectoryPoints.map((p) => ({
      time: p.date,
      value: p.price,
    }));

    // Màu sắc quỹ đạo theo xu hướng đích T+3
    const targetPoint = trajectoryPoints[trajectoryPoints.length - 1];
    let trajectoryColor = "#38bdf8"; // Xanh lơ (mặc định)
    let areaColorTop = "rgba(56, 189, 248, 0.22)";

    if (targetPoint?.trend === "TĂNG") {
      trajectoryColor = "#22c55e"; // Xanh ngọc phát sáng
      areaColorTop = "rgba(34, 197, 94, 0.25)";
    } else if (targetPoint?.trend === "GIẢM") {
      trajectoryColor = "#f43f5e"; // Đỏ san hô
      areaColorTop = "rgba(244, 63, 94, 0.25)";
    }

    try {
      candleSeriesRef.current.setData(candleData);
      volumeSeriesRef.current.setData(volumeData);
      sma20SeriesRef.current.setData(sma20Data);
      sma50SeriesRef.current.setData(sma50Data);

      trajectorySeriesRef.current.applyOptions({
        color: trajectoryColor,
        priceLineColor: trajectoryColor,
        title: "",
      });
      trajectoryAreaSeriesRef.current.applyOptions({
        topColor: areaColorTop,
      });

      trajectorySeriesRef.current.setData(trajectoryData);
      trajectoryAreaSeriesRef.current.setData(trajectoryData);
      if (targetPriceLineRef.current) {
        trajectorySeriesRef.current.removePriceLine(targetPriceLineRef.current);
        targetPriceLineRef.current = null;
      }
      // The library's last-value label follows the last *visible* point when
      // panning. A dedicated price line keeps the T+3 label tied to T+3.
      if (targetPoint) {
        targetPriceLineRef.current = trajectorySeriesRef.current.createPriceLine({
          price: targetPoint.price,
          color: trajectoryColor,
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: "Minh hoạ T+3",
        });
      }

      // Tự động căn chỉnh vừa khung nhìn, tạo khoảng thoáng bên phải cho Quỹ đạo AI
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.warn("Lỗi cập nhật biểu đồ nến Quỹ đạo FireAnt:", err);
    }
  }, [displayBars, sortedBars, trajectoryPoints, height]);

  // Thông tin thanh nến hiển thị trên Header (khi hover hoặc mặc định là nến cuối cùng)
  const currentInspectBar = hoveredBar || lastBar;
  const inspectChange =
    currentInspectBar && currentInspectBar.open > 0
      ? currentInspectBar.close - currentInspectBar.open
      : 0;
  const inspectChangePct =
    currentInspectBar && currentInspectBar.open > 0
      ? (inspectChange / currentInspectBar.open) * 100
      : 0;
  const isUp = inspectChange >= 0;

  // Điểm đích T+3 của Quỹ đạo
  const targetT3 = trajectoryPoints[trajectoryPoints.length - 1];

  return (
    <div className="mt-4 flex flex-col rounded-xl border border-slate-800 bg-slate-950 shadow-2xl overflow-hidden">
      {trajectoryError && <p role="status" className="border-b border-slate-800 px-4 py-3 text-sm text-amber-300">{trajectoryError}</p>}
      {/* 1. Header Biểu đồ Phong cách FireAnt / TradingView */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800/80 bg-slate-900/80 px-4 py-2.5 gap-2 text-xs">
        {/* Nhãn Ticker & Chỉ số Giá tức thời */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5">
            <span className="flex h-5 items-center justify-center rounded bg-purple-600/30 border border-purple-500/40 px-2 font-mono text-xs font-black text-purple-200">
              {symbol}
            </span>
            <span className="font-semibold text-slate-200">1D</span>
            <span className="text-[11px] text-slate-400">• HOSE</span>
          </div>

          {currentInspectBar && (
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px]">
              <span className="text-slate-400">
                O: <strong className="text-slate-200">{formatPriceVnd(currentInspectBar.open, false)}</strong>
              </span>
              <span className="text-slate-400">
                H: <strong className="text-slate-200">{formatPriceVnd(currentInspectBar.high, false)}</strong>
              </span>
              <span className="text-slate-400">
                L: <strong className="text-slate-200">{formatPriceVnd(currentInspectBar.low, false)}</strong>
              </span>
              <span className="text-slate-400">
                C:{" "}
                <strong className={isUp ? "text-emerald-400" : "text-rose-400"}>
                  {formatPriceVnd(currentInspectBar.close)}
                </strong>
              </span>
              <span
                className={`font-semibold ${isUp ? "text-emerald-400" : "text-rose-400"
                  }`}
              >
                {isUp ? "+" : ""}
                {Math.round(inspectChange * 1000).toLocaleString("vi-VN")} đ ({isUp ? "+" : ""}
                {formatPercentVi(inspectChangePct, 2)})
              </span>
              <span className="text-slate-400">
                Vol: {(currentInspectBar.volume / 1_000_000).toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}M
              </span>
            </div>
          )}
        </div>

        {/* Bộ lọc Khung thời gian & Toggles */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {/* Nút lọc thời gian */}
          <div className="flex items-center rounded-lg border border-slate-800 bg-slate-950 p-0.5 text-[11px] font-semibold">
            {(["1M", "3M", "6M", "ALL"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                aria-pressed={timeRange === r}
                className={`min-h-9 min-w-9 rounded px-2 py-0.5 transition-all ${timeRange === r
                    ? "bg-purple-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                  }`}
              >
                {r === "ALL" ? "Tất cả" : r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Thanh Legend Chỉ báo Kỹ thuật & Quỹ đạo AI */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800/60 bg-slate-950/60 px-4 py-1.5 text-[11px] gap-2">
        <div className="flex flex-wrap items-center gap-3">
          {/* Toggle Quỹ đạo AI FireAnt */}
          <button
            onClick={() => setShowTrajectory(!showTrajectory)}
            aria-pressed={showTrajectory}
            className={`flex min-h-9 items-center gap-1.5 font-bold transition-opacity ${showTrajectory ? "text-sky-300" : "text-slate-400 line-through"
              }`}
            title="Bật/Tắt đường đi xu hướng dự báo AI của các phiên tiếp theo"
          >
            <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse"></span>
            <span>Kịch bản minh họa (T+1 → T+3)</span>
          </button>

          {/* Toggle SMA 20 */}
          <button
            onClick={() => setShowSMA20(!showSMA20)}
            aria-pressed={showSMA20}
            className={`flex min-h-9 items-center gap-1.5 font-medium transition-opacity ${showSMA20 ? "text-blue-400" : "text-slate-400 line-through"
              }`}
          >
            <span className="h-0.5 w-3 bg-blue-500"></span>
            <span>SMA 20</span>
          </button>

          {/* Toggle SMA 50 */}
          <button
            onClick={() => setShowSMA50(!showSMA50)}
            aria-pressed={showSMA50}
            className={`flex min-h-9 items-center gap-1.5 font-medium transition-opacity ${showSMA50 ? "text-amber-400" : "text-slate-400 line-through"
              }`}
          >
            <span className="h-0.5 w-3 bg-amber-400"></span>
            <span>SMA 50</span>
          </button>

          {/* Toggle Khối lượng Volume */}
          <button
            onClick={() => setShowVolume(!showVolume)}
            aria-pressed={showVolume}
            className={`flex min-h-9 items-center gap-1.5 font-medium transition-opacity ${showVolume ? "text-slate-300" : "text-slate-400 line-through"
              }`}
          >
            <span className="h-2 w-2 rounded-sm bg-slate-600"></span>
            <span>Khối lượng</span>
          </button>
        </div>

        {/* Nhãn Mục tiêu Dự phóng T+3 nổi bật */}
        {targetT3 && showTrajectory && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-400">Giá minh họa T+3 ({modelType.toUpperCase()}):</span>
            <span
              className={`font-mono font-bold px-2 py-0.5 rounded border text-xs shadow-sm ${targetT3.changePct >= 0
                  ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400"
                  : "bg-rose-500/10 border-rose-500/40 text-rose-400"
                }`}
            >
              {formatPriceVnd(targetT3.price)} ({targetT3.changePct >= 0 ? "+" : ""}
              {formatPercentVi(targetT3.changePct, 2)})
            </span>
          </div>
        )}
      </div>

      {/* 3. Vùng Canvas Vẽ Biểu đồ Nến & Quỹ đạo */}
      <div ref={containerRef} className="w-full relative" style={{ height: `${height}px` }} />

      {/* 4. Thước đo 4 Mốc Quỹ đạo Tương tác (T -> T+1 -> T+2 -> T+3) */}
      <div className="border-t border-slate-800/80 bg-slate-900/60 p-3 sm:p-4">
        <div className="mb-2.5 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between text-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-200">
            <Sparkles className="h-4 w-4 text-sky-400 shrink-0" />
            <span>Chi tiết Tọa độ Quỹ đạo Đường đi Xu hướng ({modelType.toUpperCase()})</span>
          </div>
          <span className="text-[11px] text-slate-400">
            Đơn vị giá: VNĐ. Đường giá do quy tắc minh họa tạo ra, không phải dự báo giá hoặc khoảng tin cậy. {prediction?.trajectory?.length === 3 && prediction.trajectory.every(step => step.holiday_calendar_verified) ? "Ngày tương lai đã đối chiếu lịch nghỉ giao dịch 2026." : "Lịch nghỉ lễ của các ngày tương lai chưa được xác minh đầy đủ."}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-2.5 min-[420px]:grid-cols-2 sm:grid-cols-4">
          {trajectoryPoints.map((point, idx) => {
            const isPointUp = point.changePct > 0;
            const isPointDown = point.changePct < 0;

            const roleLabels = [
              "Dữ liệu căn cứ",
              "Mốc minh họa T+1",
              "Mốc minh họa T+2",
              "Mốc minh họa T+3",
            ];

            return (
              <div
                key={point.date + idx}
                className={`flex min-w-0 flex-col justify-between rounded-lg border p-3 transition-all ${idx === 0
                    ? "border-slate-800 bg-slate-950/70"
                    : "border-slate-800/80 bg-slate-900/50"
                  }`}
              >
                <div>
                  <div className="flex flex-wrap items-center justify-between gap-1 border-b border-slate-800/60 pb-1.5 mb-2">
                    <span className="font-bold text-slate-200 text-xs">
                      {idx === 0 ? "Phiên T (Chốt)" : `Phiên ${point.dayName}`}
                    </span>
                    <span className="font-mono text-[10px] text-slate-400">
                      {point.date}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-baseline justify-between gap-1 mb-1">
                    <span className="font-mono text-sm sm:text-base font-black text-slate-100 whitespace-nowrap">
                      {formatPriceVnd(point.price)}
                    </span>
                    {idx > 0 ? (
                      <span
                        className={`font-mono text-xs font-bold flex items-center whitespace-nowrap ${isPointUp
                            ? "text-emerald-400"
                            : isPointDown
                              ? "text-rose-400"
                              : "text-amber-400"
                          }`}
                      >
                        {isPointUp ? (
                          <ArrowUpRight className="h-3.5 w-3.5 inline mr-0.5" />
                        ) : isPointDown ? (
                          <ArrowDownRight className="h-3.5 w-3.5 inline mr-0.5" />
                        ) : (
                          <Minus className="h-3.5 w-3.5 inline mr-0.5" />
                        )}
                        {point.changePct > 0 ? "+" : ""}
                        {formatPercentVi(point.changePct, 2)}
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">
                        Tham chiếu
                      </span>
                    )}
                  </div>

                  <div className="text-[11px] text-slate-400 font-medium">
                    {roleLabels[idx] || ""}
                  </div>
                </div>

                <div className="mt-2.5 flex flex-wrap items-center justify-between gap-1 text-[11px] text-slate-300 border-t border-slate-800/40 pt-1.5">
                  <span className="font-semibold">{idx === 0 ? "Chốt phiên" : point.signal}</span>
                  {idx > 0 && (
                    <span className="font-semibold text-sky-400 font-mono text-[10px]">
                      {formatPercentVi(point.confidence * 100, 1)} xác suất lớp
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Khuyến nghị Thực chiến tổng hợp (Executive Strategy Guidance) */}
        {prediction?.summary_guidance && (
          <div className="mt-3 flex items-start gap-2.5 rounded-lg border border-sky-500/30 bg-sky-950/30 p-3 text-xs text-sky-200">
            <Sparkles className="h-4 w-4 shrink-0 text-sky-400 mt-0.5" />
            <div>
              <strong className="font-semibold text-sky-300">Nhận định định lượng: </strong>
              <span>{prediction.summary_guidance}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
