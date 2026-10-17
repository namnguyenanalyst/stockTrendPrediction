"use client";

import React, { useCallback, useMemo, useRef, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  Calendar,
  Layers,
  Percent,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { IChartApi } from "lightweight-charts";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { RSIChart } from "@/components/charts/RSIChart";
import {
  StockBar,
  StockIndicatorBar,
  StockSummaryResponse,
} from "@/lib/types";

interface MarketOverviewTabProps {
  symbol: string;
  bars: StockBar[];
  indicators: StockIndicatorBar[];
  summary: StockSummaryResponse | null;
  loading: boolean;
}

type Timeframe = "1M" | "3M" | "6M" | "1Y" | "ALL";

export const MarketOverviewTab: React.FC<MarketOverviewTabProps> = ({
  symbol,
  bars,
  indicators,
  summary,
  loading,
}) => {
  const [timeframe, setTimeframe] = useState<Timeframe>("6M");
  const candleChartRef = useRef<IChartApi | null>(null);
  const rsiChartRef = useRef<IChartApi | null>(null);

  // Lọc dữ liệu theo Timeframe được chọn
  const filteredBars = useMemo(() => {
    if (!bars || bars.length === 0) return [];
    if (timeframe === "ALL") return bars;

    const countMap: Record<Timeframe, number> = {
      "1M": 22,
      "3M": 66,
      "6M": 130,
      "1Y": 250,
      ALL: bars.length,
    };

    return bars.slice(-countMap[timeframe]);
  }, [bars, timeframe]);

  // Đồng bộ tập nến của RSI chính xác theo các phiên của Candlestick
  const filteredIndicators = useMemo(() => {
    if (!indicators || indicators.length === 0 || !filteredBars || filteredBars.length === 0) {
      return [];
    }
    const validDates = new Set(filteredBars.map((b) => b.date));
    return indicators.filter((ind) => validDates.has(ind.date));
  }, [indicators, filteredBars]);

  // Đồng bộ hóa tương tác Pan & Zoom (VisibleLogicalRange) giữa 2 biểu đồ
  const syncTimeScales = useCallback(() => {
    const c1 = candleChartRef.current;
    const c2 = rsiChartRef.current;
    if (!c1 || !c2) return;

    let isSyncing = false;

    c1.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isSyncing || !range || !rsiChartRef.current) return;
      isSyncing = true;
      try {
        rsiChartRef.current.timeScale().setVisibleLogicalRange(range);
      } catch (err) {
        console.debug("Lỗi đồng bộ RSI timeScale:", err);
      }
      isSyncing = false;
    });

    c2.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isSyncing || !range || !candleChartRef.current) return;
      isSyncing = true;
      try {
        candleChartRef.current.timeScale().setVisibleLogicalRange(range);
      } catch (err) {
        console.debug("Lỗi đồng bộ Candle timeScale:", err);
      }
      isSyncing = false;
    });
  }, []);

  const handleCandleReady = useCallback(
    (chart: IChartApi | null) => {
      candleChartRef.current = chart;
      syncTimeScales();
    },
    [syncTimeScales]
  );

  const handleRsiReady = useCallback(
    (chart: IChartApi | null) => {
      rsiChartRef.current = chart;
      syncTimeScales();
    },
    [syncTimeScales]
  );

  const latestInd =
    indicators && indicators.length > 0
      ? indicators[indicators.length - 1]
      : null;

  const isPriceUp = (summary?.change_pct ?? 0) >= 0;

  return (
    <div className="space-y-4">
      {/* 1. Header Card: Thị giá hiện tại & Bộ lọc Khung thời gian */}
      <div className="flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-slate-100 sm:text-2xl">
                {symbol}
              </h2>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300">
                HOSE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {summary?.latest_date ? `Phiên: ${summary.latest_date}` : "Đang đồng bộ..."}
            </p>
          </div>

          {/* Khối hiển thị thị giá */}
          <div className="flex items-baseline gap-3 border-l border-slate-800 pl-4">
            <span className="text-2xl font-black text-slate-100 sm:text-3xl">
              {summary ? (summary.latest_close * 1000).toLocaleString("vi-VN") : "---"}{" "}
              <span className="text-xs font-normal text-slate-400">VNĐ</span>
            </span>
            {summary && (
              <span
                className={`flex items-center gap-0.5 rounded-md px-2 py-1 text-xs font-bold ${
                  isPriceUp
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-rose-500/10 text-rose-400"
                }`}
              >
                {isPriceUp ? (
                  <ArrowUpRight className="h-3.5 w-3.5 stroke-[2.5]" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5 stroke-[2.5]" />
                )}
                {isPriceUp ? "+" : ""}
                {summary.change_pct.toFixed(2)}%
              </span>
            )}
          </div>
        </div>

        {/* Bộ nút chọn khung thời gian */}
        <div className="flex items-center gap-1 self-start rounded-lg border border-slate-800 bg-slate-950 p-1 sm:self-auto">
          <Calendar className="ml-1 mr-1 h-3.5 w-3.5 text-slate-500" />
          {(["1M", "3M", "6M", "1Y", "ALL"] as Timeframe[]).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`rounded px-2.5 py-1 text-xs font-semibold transition-all ${
                timeframe === tf
                  ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tf === "ALL" ? "Tất cả" : tf}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Biểu đồ nến kỹ thuật tương tác */}
      {loading ? (
        <div className="flex h-96 w-full items-center justify-center rounded-xl border border-slate-800 bg-slate-950">
          <div className="flex flex-col items-center gap-3 text-slate-400">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
            <span className="text-xs">Đang tải dữ liệu nến OHLCV từ máy chủ...</span>
          </div>
        </div>
      ) : (
        <>
          <CandlestickChart
            bars={filteredBars}
            height={420}
            onChartReady={handleCandleReady}
          />
          <RSIChart
            indicators={filteredIndicators}
            height={140}
            onChartReady={handleRsiReady}
          />
        </>
      )}

      {/* 3. Lưới các chỉ báo kỹ thuật cốt lõi (13 Đặc trưng ML) */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium">Lệch SMA(20)</span>
            <Layers className="h-3.5 w-3.5" />
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span
              className={`text-base font-bold ${
                (summary?.sma_20_dev ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {summary ? `${(summary.sma_20_dev * 100).toFixed(2)}%` : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">So với đường TB 20 phiên</p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium">Lệch SMA(50)</span>
            <Layers className="h-3.5 w-3.5" />
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span
              className={`text-base font-bold ${
                (summary?.sma_50_dev ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {summary ? `${(summary.sma_50_dev * 100).toFixed(2)}%` : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Xu hướng trung hạn</p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium">Biến động CV(50)</span>
            <Percent className="h-3.5 w-3.5" />
          </div>
          <div className="mt-1">
            <span className="text-base font-bold text-slate-200">
              {latestInd ? `${(latestInd.cv_50 * 100).toFixed(2)}%` : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Hệ số biến thiên giá 50p</p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium">Thanh khoản Vol Ratio</span>
            <BarChart2 className="h-3.5 w-3.5" />
          </div>
          <div className="mt-1">
            <span
              className={`text-base font-bold ${
                (latestInd?.vol_ratio ?? 1) >= 1.2
                  ? "text-emerald-400"
                  : (latestInd?.vol_ratio ?? 1) <= 0.8
                  ? "text-amber-400"
                  : "text-slate-200"
              }`}
            >
              {latestInd ? `${latestInd.vol_ratio.toFixed(2)}x` : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">So với TB thanh khoản 20p</p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium">Khối lượng GD</span>
            <BarChart2 className="h-3.5 w-3.5" />
          </div>
          <div className="mt-1">
            <span className="text-base font-bold text-slate-200">
              {summary ? (summary.volume / 1000).toLocaleString("vi-VN") : "---"}{" "}
              <span className="text-[10px] font-normal text-slate-400">k CP</span>
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Khối lượng khớp phiên</p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium">Thị trường VN-Index</span>
            {(latestInd?.vnindex_return_1d ?? 0) >= 0 ? (
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
            )}
          </div>
          <div className="mt-1">
            <span
              className={`text-base font-bold ${
                (latestInd?.vnindex_return_1d ?? 0) >= 0
                  ? "text-emerald-400"
                  : "text-rose-400"
              }`}
            >
              {latestInd
                ? `${((latestInd.vnindex_return_1d ?? 0) * 100).toFixed(2)}%`
                : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Lợi suất toàn sàn 1D</p>
        </div>
      </div>
    </div>
  );
};
