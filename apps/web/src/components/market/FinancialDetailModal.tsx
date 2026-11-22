"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { X, ArrowUpRight, ArrowDownRight, RefreshCw } from "lucide-react";
import { DetailIndicatorChart } from "@/components/charts/DetailIndicatorChart";
import { IndicatorSearch } from "./IndicatorSearch";
import {
  getStockHistory,
  getChartIndicators,
  getStockSummary,
} from "@/lib/api";
import {
  DEFAULT_INDICATORS,
  INDICATOR_STORAGE_KEY,
  parseSelection,
  type ChartIndicatorBar,
} from "@/lib/chartIndicators";
import { StockBar, StockSummaryResponse } from "@/lib/types";

export type DetailTimeframe =
  "1D" | "1W" | "1M" | "3M" | "6M" | "1Y" | "ALL" | "CUSTOM";

export interface TimeframePreset {
  id: DetailTimeframe;
  label: string;
  count: number;
  description: string;
}

export const TIMEFRAME_PRESETS: TimeframePreset[] = [
  {
    id: "1D",
    label: "1D",
    count: 1,
    description: "1 phiên giao dịch gần nhất",
  },
  {
    id: "1W",
    label: "1W",
    count: 5,
    description: "1 tuần giao dịch (5 phiên)",
  },
  {
    id: "1M",
    label: "1M",
    count: 22,
    description: "1 tháng giao dịch (22 phiên)",
  },
  {
    id: "3M",
    label: "3M",
    count: 66,
    description: "1 quý giao dịch (66 phiên)",
  },
  {
    id: "6M",
    label: "6M",
    count: 130,
    description: "6 tháng giao dịch (130 phiên)",
  },
  {
    id: "1Y",
    label: "1Y",
    count: 250,
    description: "1 năm giao dịch (250 phiên)",
  },
  {
    id: "ALL",
    label: "ALL",
    count: 9999,
    description: "Toàn bộ chuỗi nến lịch sử",
  },
];

export interface FinancialItemContext {
  symbol: string;
  name?: string;
  exchange?: string;
  isIndex?: boolean;
  sector?: string;
  currentValue?: number;
  change?: number;
  changePct?: number;
  volumeStr?: string;
  valueStr?: string;
  advancing?: number;
  ceiling?: number;
  unchanged?: number;
  declining?: number;
  floor?: number;
  reference?: number;
  dayHigh?: number;
  dayLow?: number;
  stockCeiling?: number;
  stockFloor?: number;
  volume?: number;
}

export interface FinancialDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  // Hỗ trợ cả object item hoàn chỉnh hoặc các props lẻ truyền thống
  item?: FinancialItemContext | null;
  symbol?: string;
  name?: string;
  currentValue?: number;
  change?: number;
  changePct?: number;
}

const INDEX_SYMBOLS = new Set([
  "VNINDEX",
  "VN30",
  "HNX",
  "HNX30",
  "VN100",
  "UPCOM",
  "VN30F1M",
  "DJI_FUT",
]);

export const FinancialDetailModal: React.FC<FinancialDetailModalProps> = ({
  isOpen,
  onClose,
  item,
  symbol: propSymbol,
  name: propName,
  currentValue: propCurrentValue,
  change: propChange,
  changePct: propChangePct,
}) => {
  // Xác định mã và metadata từ item hoặc props lẻ
  const activeSymbol = (item?.symbol || propSymbol || "VNINDEX").toUpperCase();
  const isIndex = item?.isIndex ?? INDEX_SYMBOLS.has(activeSymbol);
  const displayName = item?.name || propName || activeSymbol;

  // Cấu hình Timeframe chuẩn và số phiên nạp động (Phase 2 C: 1D, 1W, 1M, 3M, 6M, 1Y, ALL, CUSTOM)
  const [timeframe, setTimeframe] = useState<DetailTimeframe>("3M");
  const [sessionCount, setSessionCount] = useState<number>(66);

  const [selected, setSelected] = useState<string[]>(DEFAULT_INDICATORS);
  const [selectionLoaded, setSelectionLoaded] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        setSelected(
          parseSelection(localStorage.getItem(INDICATOR_STORAGE_KEY)),
        );
      } catch {
        setSelected([...DEFAULT_INDICATORS]);
      }
      setSelectionLoaded(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);
  useEffect(() => {
    if (selectionLoaded)
      try {
        localStorage.setItem(INDICATOR_STORAGE_KEY, JSON.stringify(selected));
      } catch {}
  }, [selected, selectionLoaded]);
  const removeIndicator = (id: string) =>
    setSelected((ids) => ids.filter((x) => x !== id));
  const [indicatorError, setIndicatorError] = useState(false);
  // Dữ liệu API
  const [bars, setBars] = useState<StockBar[]>([]);
  const [indicators, setIndicators] = useState<ChartIndicatorBar[]>([]);
  const [summary, setSummary] = useState<StockSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const requestId = useRef(0);
  // Tải dữ liệu an toàn, nạp toàn bộ lịch sử (limit 1500) để phục vụ mọi khung thời gian
  const fetchData = useCallback(async (sym: string) => {
    const request = ++requestId.current;
    setLoading(true);
    setIndicatorError(false);
    setIndicators([]);
    setSummary(null);
    setErrorMsg(null);

    try {
      const [histRes, indRes, sumRes] = await Promise.allSettled([
        getStockHistory(sym, undefined, 1500),
        getChartIndicators(sym),
        getStockSummary(sym),
      ]);

      if (request !== requestId.current) return;
      if (histRes.status === "fulfilled") {
        const fetchedBars = histRes.value.bars;
        setBars(fetchedBars);
      } else {
        throw new Error(
          histRes.reason?.message || "Không thể tải lịch sử giá.",
        );
      }

      if (indRes.status === "fulfilled") {
        setIndicators(indRes.value.indicators);
      } else {
        setIndicatorError(true);
      }

      if (sumRes.status === "fulfilled") {
        setSummary(sumRes.value);
      }
    } catch (err: unknown) {
      if (request !== requestId.current) return;
      const message = err instanceof Error ? err.message : "Đã có lỗi xảy ra.";
      console.warn("Lỗi tải chi tiết tài chính:", message);
      setErrorMsg(message);
    } finally {
      if (request === requestId.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isOpen || !activeSymbol) return;
    let isCurrent = true;

    // Trì hoãn một tick để tránh gọi setState đồng bộ trong thân effect (chuẩn React 19)
    const timer = setTimeout(() => {
      if (isCurrent) {
        fetchData(activeSymbol);
      }
    }, 0);

    return () => {
      isCurrent = false;
      // Invalidate async responses when closing or switching symbols.
      // eslint-disable-next-line react-hooks/exhaustive-deps
      requestId.current++;
      clearTimeout(timer);
    };
  }, [isOpen, activeSymbol, fetchData]);

  // Xử lý chuyển đổi khung thời gian chuẩn
  const handleTimeframeChange = (tf: DetailTimeframe) => {
    setTimeframe(tf);
    if (tf === "ALL") {
      setSessionCount(bars.length || 1194);
    } else {
      const preset = TIMEFRAME_PRESETS.find((p) => p.id === tf);
      if (preset) {
        setSessionCount(preset.count);
      }
    }
  };

  // Tinh chỉnh số phiên nạp tùy biến
  const handleCustomSessionChange = (newCount: number) => {
    const maxBars = bars.length > 0 ? bars.length : 2000;
    const clamped = Math.max(1, Math.min(newCount, maxBars));
    setSessionCount(clamped);

    const matched = TIMEFRAME_PRESETS.find(
      (p) => p.id !== "ALL" && p.count === clamped,
    );
    if (matched) {
      setTimeframe(matched.id);
    } else if (clamped >= maxBars) {
      setTimeframe("ALL");
    } else {
      setTimeframe("CUSTOM");
    }
  };

  // Lọc số phiên theo Timeframe và số phiên nạp tinh chỉnh
  const filteredBars = useMemo(() => {
    if (!bars || bars.length === 0) return [];
    const count = Math.min(Math.max(1, sessionCount), bars.length);
    return bars.slice(-count);
  }, [bars, sessionCount]);

  if (!isOpen) return null;

  // Tính toán thị giá hiển thị
  const latestClose =
    bars.length > 0
      ? bars[bars.length - 1].close
      : (summary?.latest_close ?? 0);
  const prevClose =
    bars.length > 1
      ? bars[bars.length - 2].close
      : (summary?.prev_close ?? latestClose);
  const displayVal = item?.currentValue ?? propCurrentValue ?? latestClose;
  const displayChg = item?.change ?? propChange ?? latestClose - prevClose;
  const displayPct =
    item?.changePct ??
    propChangePct ??
    (prevClose > 0 ? (displayChg / prevClose) * 100 : 0);
  const isUp = displayChg >= 0;

  const latestBar = bars.length > 0 ? bars[bars.length - 1] : null;

  return (
    <div
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          e.stopPropagation();
          onClose();
        }
      }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-2 sm:p-4 backdrop-blur-md animate-in fade-in duration-200"
    >
      <div className="relative flex max-h-[95vh] w-full max-w-5xl flex-col rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl overflow-hidden">
        {/* ========================================================================= */}
        {/* 1. HEADER MODAL: THÔNG TIN CỐT LÕI (PHASE 2 A)                            */}
        {/* ========================================================================= */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-base sm:text-xl font-black tracking-tight text-slate-100">
                {activeSymbol}
              </span>
              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-bold text-slate-300">
                {isIndex ? "CHỈ SỐ" : item?.exchange || "HOSE"}
              </span>
              {displayName && displayName !== activeSymbol && (
                <span className="text-xs text-slate-400 hidden sm:inline truncate max-w-[220px]">
                  {displayName}
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-2 border-l border-slate-800 pl-3">
              <span
                className={`text-lg sm:text-2xl font-black ${
                  isUp ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {displayVal.toLocaleString("vi-VN", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
              <span
                className={`flex items-center text-xs font-bold ${
                  isUp ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isUp ? (
                  <ArrowUpRight className="h-3.5 w-3.5 stroke-[2.5]" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5 stroke-[2.5]" />
                )}
                {isUp ? "+" : ""}
                {displayChg.toFixed(2)} ({isUp ? "+" : ""}
                {displayPct.toFixed(2)}%)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchData(activeSymbol)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
              title="Làm mới dữ liệu"
            >
              <RefreshCw
                className={`h-4 w-4 ${loading ? "animate-spin text-emerald-400" : ""}`}
              />
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
              title="Đóng cửa sổ"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* 2. DẢI THÔNG TIN NGỮ CẢNH THEO LOẠI CÔNG CỤ (PHASE 2 E)                    */}
        {/* ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between border-b border-slate-800/80 bg-slate-900/40 px-4 py-2 text-xs text-slate-300">
          {/* Đối với CHỈ SỐ: Hiển thị Độ rộng thị trường + KLGD/GTGD */}
          {isIndex ? (
            <div className="flex flex-wrap items-center gap-4">
              {item?.advancing !== undefined && (
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-slate-400 font-semibold">Độ rộng:</span>
                  <span className="text-emerald-400 font-bold">
                    ▲ {item.advancing}{" "}
                    {item.ceiling ? `(${item.ceiling} Trần)` : ""}
                  </span>
                  <span className="text-amber-400 font-bold">
                    ■ {item.unchanged ?? 0}
                  </span>
                  <span className="text-rose-400 font-bold">
                    ▼ {item.declining ?? 0}{" "}
                    {item.floor ? `(${item.floor} Sàn)` : ""}
                  </span>
                </div>
              )}
              {(item?.volumeStr || item?.valueStr) && (
                <div className="flex items-center gap-2 border-l border-slate-800 pl-3 text-[11px] text-slate-400">
                  {item.volumeStr && (
                    <span>
                      KL:{" "}
                      <strong className="text-slate-200">
                        {item.volumeStr}
                      </strong>
                    </span>
                  )}
                  {item.valueStr && (
                    <span>
                      GT:{" "}
                      <strong className="text-slate-200">
                        {item.valueStr}
                      </strong>
                    </span>
                  )}
                </div>
              )}
            </div>
          ) : (
            /* Đối với CỔ PHIẾU: Hiển thị Tham chiếu, Trần, Sàn, Cao nhất, Thấp nhất */
            <div className="flex flex-wrap items-center gap-3 text-[11px]">
              {item?.sector && (
                <span className="rounded bg-slate-800/80 px-2 py-0.5 text-slate-300">
                  {item.sector}
                </span>
              )}
              {item?.reference !== undefined && (
                <span>
                  TC:{" "}
                  <strong className="text-amber-400">
                    {item.reference.toFixed(2)}
                  </strong>
                </span>
              )}
              {item?.stockCeiling !== undefined && (
                <span>
                  Trần:{" "}
                  <strong className="text-purple-400">
                    {item.stockCeiling.toFixed(2)}
                  </strong>
                </span>
              )}
              {item?.stockFloor !== undefined && (
                <span>
                  Sàn:{" "}
                  <strong className="text-cyan-400">
                    {item.stockFloor.toFixed(2)}
                  </strong>
                </span>
              )}
              {latestBar && (
                <>
                  <span>
                    Cao:{" "}
                    <strong className="text-slate-200">
                      {latestBar.high.toFixed(2)}
                    </strong>
                  </span>
                  <span>
                    Thấp:{" "}
                    <strong className="text-slate-200">
                      {latestBar.low.toFixed(2)}
                    </strong>
                  </span>
                  <span>
                    KL:{" "}
                    <strong className="text-slate-200">
                      {latestBar.volume.toLocaleString("vi-VN")}
                    </strong>
                  </span>
                </>
              )}
            </div>
          )}

          {/* OHLC Status bar hover của phiên gần nhất */}
          {latestBar && (
            <div className="hidden md:flex items-center gap-2 text-[11px] text-slate-400">
              <span>
                O: <strong className="text-slate-200">{latestBar.open}</strong>
              </span>
              <span>
                H: <strong className="text-slate-200">{latestBar.high}</strong>
              </span>
              <span>
                L: <strong className="text-slate-200">{latestBar.low}</strong>
              </span>
              <span>
                C:{" "}
                <strong className={isUp ? "text-emerald-400" : "text-rose-400"}>
                  {latestBar.close}
                </strong>
              </span>
            </div>
          )}
        </div>

        {/* ========================================================================= */}
        {/* 3. TOOLBAR CHỌN TIMEFRAME & BẬT/TẮT CHỈ BÁO KỸ THUẬT (PHASE 2 C & D)      */}
        {/* ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 bg-slate-950 px-4 py-2 text-xs">
          {/* Bộ chọn Timeframe chuẩn kèm tinh chỉnh số phiên */}
          <div className="flex flex-wrap items-center gap-1.5">
            <div className="flex items-center gap-1">
              {TIMEFRAME_PRESETS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleTimeframeChange(p.id)}
                  title={p.description}
                  className={`rounded px-2.5 py-1 text-xs font-bold transition-all ${
                    timeframe === p.id
                      ? "bg-emerald-500 text-slate-950 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Tinh chỉnh số phiên (Session Fine-Tuning) */}
            <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/80 px-2 py-0.5 text-xs text-slate-400">
              <span className="text-[11px] text-slate-500 hidden sm:inline">
                Số phiên:
              </span>
              <button
                type="button"
                onClick={() => handleCustomSessionChange(sessionCount - 10)}
                className="px-1 text-slate-400 hover:text-emerald-400 transition-colors font-bold"
                title="Giảm 10 phiên"
              >
                -
              </button>
              <input
                type="number"
                min={1}
                max={bars.length > 0 ? bars.length : 2000}
                value={sessionCount}
                onChange={(e) =>
                  handleCustomSessionChange(parseInt(e.target.value) || 1)
                }
                className="w-14 rounded bg-slate-950 px-1 py-0.5 text-center text-xs font-bold text-emerald-400 border border-slate-700/60 focus:border-emerald-500 focus:outline-none"
                title="Nhập số phiên nạp mong muốn"
              />
              <button
                type="button"
                onClick={() => handleCustomSessionChange(sessionCount + 10)}
                className="px-1 text-slate-400 hover:text-emerald-400 transition-colors font-bold"
                title="Tăng 10 phiên"
              >
                +
              </button>
            </div>
          </div>

          <IndicatorSearch selected={selected} onChange={setSelected} />
        </div>

        {/* ========================================================================= */}
        {/* 4. KHUNG VẼ BIỂU ĐỒ NẾN & RSI CANVAS (PHASE 2 B)                          */}
        {/* ========================================================================= */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-slate-950">
          {loading ? (
            <div className="flex h-[420px] w-full flex-col items-center justify-center rounded-xl border border-slate-800 bg-slate-950">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
              <span className="mt-3 text-xs text-slate-400">
                Đang nạp dữ liệu nến chuẩn hóa {activeSymbol}...
              </span>
            </div>
          ) : errorMsg ? (
            <div className="flex h-[360px] w-full flex-col items-center justify-center rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-center">
              <p className="text-sm font-semibold text-rose-400">{errorMsg}</p>
              <button
                onClick={() => fetchData(activeSymbol)}
                className="mt-3 rounded-lg bg-slate-800 px-4 py-1.5 text-xs font-bold text-slate-200 hover:bg-slate-700"
              >
                Thử lại
              </button>
            </div>
          ) : filteredBars.length === 0 ? (
            <div className="flex h-[360px] w-full items-center justify-center rounded-xl border border-slate-800 bg-slate-950 text-xs text-slate-500">
              Không có dữ liệu nến lịch sử phù hợp trong khung thời gian này.
            </div>
          ) : (
            <>
              {indicatorError && (
                <div
                  role="status"
                  className="flex items-center justify-between gap-2 text-sm text-amber-300"
                >
                  Không thể tải chỉ báo. Biểu đồ giá vẫn khả dụng.
                  <button
                    onClick={() => fetchData(activeSymbol)}
                    className="min-h-9 underline"
                  >
                    Thử lại
                  </button>
                </div>
              )}
              <DetailIndicatorChart
                bars={filteredBars}
                indicators={indicators}
                selected={selected}
                onRemove={removeIndicator}
              />
            </>
          )}
        </div>

        {/* ========================================================================= */}
        {/* 5. FOOTER STATUS BAR                                                      */}
        {/* ========================================================================= */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-800 bg-slate-900/60 px-4 py-2.5 text-xs text-slate-400">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-[11px] text-slate-400">
            <span className="text-slate-500">Múi giờ: (UTC+7) Việt Nam</span>
            <span className="h-3 w-[1px] bg-slate-800 hidden sm:inline" />
            <span>
              Số phiên nạp:{" "}
              <strong className="text-emerald-400 font-bold">
                {filteredBars.length.toLocaleString("vi-VN")}
              </strong>{" "}
              phiên{" "}
              <span className="text-slate-500">
                (
                {timeframe === "CUSTOM"
                  ? "Tùy chỉnh"
                  : timeframe === "ALL"
                    ? "Toàn bộ"
                    : timeframe}
                )
              </span>
            </span>
            {filteredBars.length > 0 && (
              <>
                <span className="h-3 w-[1px] bg-slate-800 hidden md:inline" />
                <span className="hidden md:inline text-slate-500">
                  Khoảng ngày:{" "}
                  <span className="text-slate-300 font-medium">
                    {filteredBars[0].date}
                  </span>{" "}
                  →{" "}
                  <span className="text-slate-300 font-medium">
                    {filteredBars[filteredBars.length - 1].date}
                  </span>
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="font-semibold text-emerald-400 text-[11px]">
              Dữ liệu SSI FastConnect
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
