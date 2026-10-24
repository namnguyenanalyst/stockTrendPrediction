"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  AreaSeries,
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  IChartApi,
  ISeriesApi,
  LineSeries,
  LineStyle,
  LineType,
} from "lightweight-charts";
import {
  ArrowDownRight,
  ArrowUpRight,
  Maximize2,
  Minus,
  Sparkles,
} from "lucide-react";
import { DayForecast, PredictionResponse, StockBar } from "@/lib/types";

interface FireAntTrajectoryChartProps {
  symbol: string;
  bars: StockBar[];
  prediction: PredictionResponse | null;
  modelType: "lightgbm" | "lstm";
  height?: number;
}

interface TrajectoryStepPoint {
  date: string;
  dayName: string;
  price: number;
  changePct: number;
  trend: "TĂNG" | "ĐI NGANG" | "GIẢM";
  confidence: number;
  signal: string;
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

// Hàm tìm ngày giao dịch kế tiếp (bỏ qua Thứ 7, Chủ Nhật)
function getNextTradingDay(dateStr: string): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + 1);
  while (d.getDay() === 0 || d.getDay() === 6) {
    d.setDate(d.getDate() + 1);
  }
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
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
  const trajectoryPoints: TrajectoryStepPoint[] = useMemo(() => {
    if (!lastBar) return [];

    const basePrice = lastBar.close;
    const baseDate = lastBar.date;

    const trajectory = prediction?.trajectory || [];
    const points: TrajectoryStepPoint[] = [];

    // Điểm gốc: Phiên T (Nến hiện tại)
    points.push({
      date: baseDate,
      dayName: "Phiên T (Hiện tại)",
      price: basePrice,
      changePct: 0,
      trend: "ĐI NGANG",
      confidence: 1.0,
      signal: "CHỐT PHIÊN",
    });

    let currentPrice = basePrice;
    let prevDate = baseDate;

    // Duyệt qua 3 bước T+1, T+2, T+3
    for (let i = 0; i < 3; i++) {
      const step: DayForecast | undefined = trajectory[i];
      const dayName = step?.day_name || `T+${i + 1}`;
      const trend = step?.predicted_trend || (prediction?.class_name as "TĂNG" | "ĐI NGANG" | "GIẢM") || "ĐI NGANG";
      const confidence = step?.confidence || 0.55;
      const signal = step?.signal || "NẮM GIỮ (HOLD)";

      // Xác định ngày tương lai hợp lệ (phải lớn hơn ngày trước đó)
      let stepDate = step?.date;
      if (!stepDate || new Date(stepDate) <= new Date(prevDate)) {
        stepDate = getNextTradingDay(prevDate);
      }
      prevDate = stepDate;

      // Tính toán tỷ lệ biến động giá dự kiến dựa trên xu hướng và xác suất
      let driftPct = 0;
      if (trend === "TĂNG") {
        driftPct = 0.012 + (confidence - 0.33) * 0.02; // Tăng +1.4% đến +2.2%
      } else if (trend === "GIẢM") {
        driftPct = -(0.012 + (confidence - 0.33) * 0.02); // Giảm -1.4% đến -2.2%
      } else {
        const pUp = step?.probabilities?.["TĂNG"] ?? 0.33;
        const pDown = step?.probabilities?.["GIẢM"] ?? 0.33;
        driftPct = (pUp - pDown) * 0.008; // Đi ngang giằng co quanh biên hẹp
      }

      currentPrice = parseFloat((currentPrice * (1 + driftPct)).toFixed(2));
      const totalChangePct = parseFloat(
        (((currentPrice - basePrice) / basePrice) * 100).toFixed(2)
      );

      points.push({
        date: stepDate,
        dayName,
        price: currentPrice,
        changePct: totalChangePct,
        trend,
        confidence,
        signal,
      });
    }

    return points;
  }, [lastBar, prediction]);

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
        minMove: 0.05,
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
      priceLineVisible: true, // Đường gióng ngang chỉ giá mục tiêu T+3 trên trục phải
      priceLineWidth: 1,
      priceLineStyle: LineStyle.Dashed,
      priceLineColor: "#38bdf8",
      title: "Forecast",
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

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
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
  }, [showSMA20, showSMA50, showVolume, showTrajectory]);

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
        title: "Forecast",
      });
      trajectoryAreaSeriesRef.current.applyOptions({
        topColor: areaColorTop,
      });

      trajectorySeriesRef.current.setData(trajectoryData);
      trajectoryAreaSeriesRef.current.setData(trajectoryData);

      // Tự động căn chỉnh vừa khung nhìn, tạo khoảng thoáng bên phải cho Quỹ đạo AI
      chartRef.current?.timeScale().fitContent();
    } catch (err) {
      console.warn("Lỗi cập nhật biểu đồ nến Quỹ đạo FireAnt:", err);
    }
  }, [displayBars, sortedBars, trajectoryPoints]);

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
      {/* 1. Header Biểu đồ Phong cách FireAnt / TradingView */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800/80 bg-slate-900/80 px-4 py-2.5 gap-2 text-xs">
        {/* Nhãn Ticker & Chỉ số Giá tức thời */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5">
            <span className="flex h-5 items-center justify-center rounded bg-purple-600/30 border border-purple-500/40 px-2 font-mono text-xs font-black text-purple-200">
              {symbol}
            </span>
            <span className="font-semibold text-slate-200">1D</span>
            <span className="text-[11px] text-slate-500">• HOSE</span>
          </div>

          {currentInspectBar && (
            <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
              <span className="text-slate-400">
                O: <strong className="text-slate-200">{currentInspectBar.open.toLocaleString()}</strong>
              </span>
              <span className="text-slate-400">
                H: <strong className="text-slate-200">{currentInspectBar.high.toLocaleString()}</strong>
              </span>
              <span className="text-slate-400">
                L: <strong className="text-slate-200">{currentInspectBar.low.toLocaleString()}</strong>
              </span>
              <span className="text-slate-400">
                C:{" "}
                <strong className={isUp ? "text-emerald-400" : "text-rose-400"}>
                  {currentInspectBar.close.toLocaleString()}
                </strong>
              </span>
              <span
                className={`font-semibold ${
                  isUp ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isUp ? "+" : ""}
                {inspectChange.toFixed(1)} ({isUp ? "+" : ""}
                {inspectChangePct.toFixed(2)}%)
              </span>
              <span className="text-slate-500">
                Vol: {(currentInspectBar.volume / 1_000_000).toFixed(2)}M
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
                className={`rounded px-2 py-0.5 transition-all ${
                  timeRange === r
                    ? "bg-purple-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {r === "ALL" ? "Tất cả" : r}
              </button>
            ))}
          </div>

          {/* Nút Đặt lại góc nhìn Fit Content */}
          <button
            onClick={() => chartRef.current?.timeScale().fitContent()}
            className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/80 px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            title="Căn chỉnh toàn bộ biểu đồ về vừa khung nhìn"
          >
            <Maximize2 className="h-3 w-3" />
            <span className="hidden sm:inline">Vừa màn hình</span>
          </button>
        </div>
      </div>

      {/* 2. Thanh Legend Chỉ báo Kỹ thuật & Quỹ đạo AI */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800/60 bg-slate-950/60 px-4 py-1.5 text-[11px] gap-2">
        <div className="flex flex-wrap items-center gap-3">
          {/* Toggle Quỹ đạo AI FireAnt */}
          <button
            onClick={() => setShowTrajectory(!showTrajectory)}
            className={`flex items-center gap-1.5 font-bold transition-opacity ${
              showTrajectory ? "text-sky-300" : "text-slate-500 line-through opacity-60"
            }`}
            title="Bật/Tắt đường đi xu hướng dự báo AI của các phiên tiếp theo"
          >
            <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse"></span>
            <span>FA - Quỹ đạo AI (T+1 → T+3)</span>
          </button>

          {/* Toggle SMA 20 */}
          <button
            onClick={() => setShowSMA20(!showSMA20)}
            className={`flex items-center gap-1.5 font-medium transition-opacity ${
              showSMA20 ? "text-blue-400" : "text-slate-500 line-through opacity-60"
            }`}
          >
            <span className="h-0.5 w-3 bg-blue-500"></span>
            <span>SMA 20</span>
          </button>

          {/* Toggle SMA 50 */}
          <button
            onClick={() => setShowSMA50(!showSMA50)}
            className={`flex items-center gap-1.5 font-medium transition-opacity ${
              showSMA50 ? "text-amber-400" : "text-slate-500 line-through opacity-60"
            }`}
          >
            <span className="h-0.5 w-3 bg-amber-400"></span>
            <span>SMA 50</span>
          </button>

          {/* Toggle Khối lượng Volume */}
          <button
            onClick={() => setShowVolume(!showVolume)}
            className={`flex items-center gap-1.5 font-medium transition-opacity ${
              showVolume ? "text-slate-300" : "text-slate-500 line-through opacity-60"
            }`}
          >
            <span className="h-2 w-2 rounded-sm bg-slate-600"></span>
            <span>Khối lượng</span>
          </button>
        </div>

        {/* Nhãn Mục tiêu Dự phóng T+3 nổi bật */}
        {targetT3 && showTrajectory && (
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Mục tiêu T+3 ({modelType.toUpperCase()}):</span>
            <span
              className={`font-mono font-bold px-2 py-0.5 rounded border text-xs shadow-sm ${
                targetT3.changePct >= 0
                  ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400"
                  : "bg-rose-500/10 border-rose-500/40 text-rose-400"
              }`}
            >
              {targetT3.price.toLocaleString()} VNĐ ({targetT3.changePct >= 0 ? "+" : ""}
              {targetT3.changePct}%)
            </span>
          </div>
        )}
      </div>

      {/* 3. Vùng Canvas Vẽ Biểu đồ Nến & Quỹ đạo */}
      <div ref={containerRef} className="w-full relative" style={{ height: `${height}px` }} />

      {/* 4. Thước đo 4 Mốc Quỹ đạo Tương tác (T -> T+1 -> T+2 -> T+3) */}
      <div className="border-t border-slate-800/80 bg-slate-900/60 p-3 sm:p-4">
        <div className="mb-2 flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-200">
            <Sparkles className="h-4 w-4 text-sky-400" />
            <span>Chi tiết Tọa độ Quỹ đạo Đường đi Xu hướng ({modelType.toUpperCase()})</span>
          </div>
          <span className="text-[11px] text-slate-400">
            Đường cong xanh lơ thể hiện xung lực quán tính và kỳ vọng giá của AI
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {trajectoryPoints.map((point, idx) => {
            const isTarget = idx === trajectoryPoints.length - 1;
            const isPointUp = point.changePct > 0;
            const isPointDown = point.changePct < 0;

            return (
              <div
                key={point.date + idx}
                className={`flex flex-col justify-between rounded-lg border p-2.5 transition-all ${
                  isTarget
                    ? "border-sky-500/40 bg-sky-950/20 shadow-md shadow-sky-950/40 ring-1 ring-sky-500/20"
                    : idx === 0
                    ? "border-slate-800 bg-slate-950/60"
                    : "border-slate-800/80 bg-slate-900/40"
                }`}
              >
                <div className="flex items-center justify-between border-b border-slate-800/60 pb-1.5 mb-1.5">
                  <span className="font-bold text-slate-200 text-xs">
                    {idx === 0 ? "Phiên T (Chốt)" : `Phiên ${point.dayName}`}
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">
                    {point.date}
                  </span>
                </div>

                <div className="flex items-baseline justify-between">
                  <span className="font-mono text-sm font-black text-slate-100">
                    {point.price.toLocaleString()}
                  </span>
                  {idx > 0 ? (
                    <span
                      className={`font-mono text-xs font-bold flex items-center ${
                        isPointUp
                          ? "text-emerald-400"
                          : isPointDown
                          ? "text-rose-400"
                          : "text-amber-400"
                      }`}
                    >
                      {isPointUp ? (
                        <ArrowUpRight className="h-3 w-3 inline" />
                      ) : isPointDown ? (
                        <ArrowDownRight className="h-3 w-3 inline" />
                      ) : (
                        <Minus className="h-3 w-3 inline" />
                      )}
                      {point.changePct > 0 ? "+" : ""}
                      {point.changePct}%
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">
                      Giá tham chiếu
                    </span>
                  )}
                </div>

                <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-800/40 pt-1">
                  <span>{idx === 0 ? "Dữ liệu căn cứ" : point.signal}</span>
                  {idx > 0 && (
                    <span className="font-semibold text-purple-300">
                      {(point.confidence * 100).toFixed(0)}% tin cậy
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
