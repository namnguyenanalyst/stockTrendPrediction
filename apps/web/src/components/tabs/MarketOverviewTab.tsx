"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  Calendar,
  ChevronRight,
  Eye,
  Layers,
  Percent,
  Search,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { IChartApi } from "lightweight-charts";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { RSIChart } from "@/components/charts/RSIChart";
import {
  FinancialDetailModal,
  FinancialItemContext,
} from "@/components/market/FinancialDetailModal";
import { IndexRibbon } from "@/components/market/IndexRibbon";
import { ManageRibbonModal } from "@/components/market/ManageRibbonModal";
import {
  MarketBoardResponse,
  StockBar,
  StockIndicatorBar,
  StockSummaryResponse,
} from "@/lib/types";

interface MarketOverviewTabProps {
  symbol: string;
  onSelectSymbol?: (symbol: string) => void;
  bars: StockBar[];
  indicators: StockIndicatorBar[];
  summary: StockSummaryResponse | null;
  marketBoard: MarketBoardResponse | null;
  loading: boolean;
  onGoToPrediction?: () => void;
}

type Timeframe = "1M" | "3M" | "6M" | "1Y" | "ALL";
type ViewMode = "split" | "board" | "chart";

const DEFAULT_RIBBON_SYMBOLS = ["VN30", "VNINDEX", "HNX30", "VN30F1M"];

// Component Sparkline mini cho từng dòng của bảng giá
const TableSparkline: React.FC<{ data: number[]; isUp: boolean }> = ({ data, isUp }) => {
  if (!data || data.length < 2) {
    return <div className="h-6 w-20 rounded bg-slate-900/40" />;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 80;
  const height = 24;

  const points = data
    .map((val, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const color = isUp ? "#10b981" : "#ef4444";

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

export const MarketOverviewTab: React.FC<MarketOverviewTabProps> = ({
  symbol,
  onSelectSymbol,
  bars,
  indicators,
  summary,
  marketBoard,
  loading,
  onGoToPrediction,
}) => {
  // Trạng thái Băng chuyền chỉ số (Ribbon)
  const [activeRibbonSymbols, setActiveRibbonSymbols] = useState<string[]>(DEFAULT_RIBBON_SYMBOLS);

  // Đọc cấu hình ribbon từ localStorage sau khi component mount để tránh Next.js Hydration Mismatch
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        const saved = localStorage.getItem("active_ribbon_symbols");
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setActiveRibbonSymbols(parsed);
          }
        }
      } catch {
        // Bỏ qua lỗi truy cập localStorage
      }
    }, 0);
    return () => clearTimeout(timer);
  }, []);
  const [isRibbonCollapsed, setIsRibbonCollapsed] = useState<boolean>(false);
  const [isManageModalOpen, setIsManageModalOpen] = useState<boolean>(false);

  // Trạng thái Modal chi tiết chuẩn hóa (FinancialDetailModal)
  const [detailModalItem, setDetailModalItem] = useState<FinancialItemContext | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

  const openDetailModal = (item: FinancialItemContext) => {
    setDetailModalItem(item);
    setIsDetailModalOpen(true);
  };

  const [timeframe, setTimeframe] = useState<Timeframe>("6M");
  const [viewMode, setViewMode] = useState<ViewMode>("split");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const candleChartRef = useRef<IChartApi | null>(null);
  const rsiChartRef = useRef<IChartApi | null>(null);

  // Lọc dữ liệu nến theo Timeframe được chọn
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

  // Lọc danh sách cổ phiếu theo Category & Search Query
  const filteredStocks = useMemo(() => {
    if (!marketBoard || !marketBoard.stocks) return [];
    let list = marketBoard.stocks;

    if (selectedCategory === "CORE") {
      const coreSet = new Set(["VIC", "HPG", "FPT", "VNM", "MWG"]);
      list = list.filter((s) => coreSet.has(s.symbol));
    } else if (selectedCategory === "BANK") {
      list = list.filter((s) => s.sector.includes("Ngân hàng"));
    } else if (selectedCategory === "REAL_ESTATE") {
      list = list.filter((s) => s.sector.includes("Bất động sản"));
    } else if (selectedCategory === "TECH") {
      list = list.filter((s) => s.sector.includes("Công nghệ"));
    } else if (selectedCategory === "RETAIL") {
      list = list.filter((s) => s.sector.includes("Bán lẻ") || s.sector.includes("tiêu dùng"));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toUpperCase();
      list = list.filter(
        (s) => s.symbol.toUpperCase().includes(q) || s.name.toUpperCase().includes(q)
      );
    }

    return list;
  }, [marketBoard, selectedCategory, searchQuery]);

  return (
    <div className="space-y-4">
      {/* ========================================================================= */}
      {/* 1. BĂNG CHUYỂN CHỈ SỐ THỊ TRƯỜNG TÁCH BIỆT (INDEX RIBBON COMPONENT)       */}
      {/* ========================================================================= */}
      <IndexRibbon
        indices={marketBoard?.indices || []}
        stocks={marketBoard?.stocks || []}
        activeSymbols={activeRibbonSymbols}
        isCollapsed={isRibbonCollapsed}
        onToggleCollapse={() => setIsRibbonCollapsed(!isRibbonCollapsed)}
        onOpenManageModal={() => setIsManageModalOpen(true)}
        onSelectCard={(card) => {
          openDetailModal({
            symbol: card.symbol,
            name: card.name,
            currentValue: card.value,
            change: card.change,
            changePct: card.changePct,
            isIndex: !card.isStock,
            volumeStr: card.volumeStr,
            valueStr: card.valueStr,
            advancing: card.advancing,
            ceiling: card.ceiling,
            unchanged: card.unchanged,
            declining: card.declining,
            floor: card.floor,
          });
        }}
      />

      {/* ========================================================================= */}
      {/* 2. TOOLBAR LỌC & THỐNG KÊ ĐỘ RỘNG THỊ TRƯỜNG                              */}
      {/* ========================================================================= */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        {/* Nhóm Tabs Phân loại */}
        <div className="flex flex-wrap items-center gap-1">
          {[
            { id: "ALL", label: "Tất cả" },
            { id: "CORE", label: "Rổ Core VN30" },
            { id: "BANK", label: "Ngân hàng" },
            { id: "REAL_ESTATE", label: "Bất động sản" },
            { id: "TECH", label: "Công nghệ" },
            { id: "RETAIL", label: "Bán lẻ / Tiêu dùng" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                selectedCategory === cat.id
                  ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/30"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Thanh công cụ tìm kiếm & Độ rộng thị trường */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Ô tìm kiếm mã nhanh */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Tìm mã cổ phiếu..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-7 w-36 rounded-lg border border-slate-800 bg-slate-950 pl-8 pr-2 text-xs text-slate-100 placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none sm:w-44"
            />
          </div>

          {/* Thước đo độ rộng thị trường (Market Breadth) */}
          {marketBoard?.breadth && (
            <div className="hidden items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1 text-[10px] font-bold md:flex">
              <span className="rounded bg-purple-500/10 px-1.5 py-0.5 text-purple-400" title="Trần">
                Trần: {marketBoard.breadth.ceiling}
              </span>
              <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-400" title="Tăng">
                Tăng: {marketBoard.breadth.advancing}
              </span>
              <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-amber-400" title="Tham chiếu">
                TC: {marketBoard.breadth.unchanged}
              </span>
              <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-rose-400" title="Giảm">
                Giảm: {marketBoard.breadth.declining}
              </span>
              <span className="rounded bg-cyan-500/10 px-1.5 py-0.5 text-cyan-400" title="Sàn">
                Sàn: {marketBoard.breadth.floor}
              </span>
            </div>
          )}

          {/* Bộ chọn Chế độ hiển thị (View Mode Switcher) */}
          <div className="flex items-center rounded-lg border border-slate-800 bg-slate-950 p-0.5">
            <button
              onClick={() => setViewMode("split")}
              className={`rounded px-2 py-0.5 text-xs font-semibold transition-all ${
                viewMode === "split"
                  ? "bg-slate-800 text-emerald-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
              title="Chế độ Kết hợp Bảng giá & Biểu đồ"
            >
              Kết hợp
            </button>
            <button
              onClick={() => setViewMode("board")}
              className={`rounded px-2 py-0.5 text-xs font-semibold transition-all ${
                viewMode === "board"
                  ? "bg-slate-800 text-emerald-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
              title="Chỉ Bảng giá"
            >
              Bảng giá
            </button>
            <button
              onClick={() => setViewMode("chart")}
              className={`rounded px-2 py-0.5 text-xs font-semibold transition-all ${
                viewMode === "chart"
                  ? "bg-slate-800 text-emerald-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
              title="Chuyên sâu Biểu đồ nến"
            >
              Biểu đồ
            </button>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. BẢNG GIÁ CHỨNG KHOÁN HIỆN ĐẠI & PHÂN HỆ PHỤ BÊN PHẢI (DNSE LAYOUT)     */}
      {/* ========================================================================= */}
      {viewMode !== "chart" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* CỘT TRÁI: BẢNG GIÁ ĐIỆN TỬ (70% - 75% CHIỀU RỘNG) */}
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg backdrop-blur-sm lg:col-span-8 xl:col-span-9">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800/80 bg-slate-950/80 text-[11px] font-bold text-slate-400">
                    <th className="py-2.5 pl-4 pr-2">MÃ CHỨNG KHOÁN</th>
                    <th className="px-3 py-2.5 text-right">GIÁ KHỚP</th>
                    <th className="px-3 py-2.5 text-right">BIẾN ĐỘNG</th>
                    <th className="px-3 py-2.5 text-right">TỔNG KHỐI LƯỢNG</th>
                    <th className="px-3 py-2.5 text-center">BIỂU ĐỒ 10P</th>
                    <th className="px-3 py-2.5 text-center">LỰC MUA / BÁN</th>
                    <th className="px-3 py-2.5 text-center">AI BIAS</th>
                    <th className="py-2.5 pl-2 pr-4 text-center">THAO TÁC</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {filteredStocks.map((stock) => {
                    const isSelected = symbol === stock.symbol;
                    const isUp = stock.change > 0;
                    const isCeiling = stock.close >= stock.ceiling;
                    const isFloor = stock.close <= stock.floor;
                    const isRef = stock.change === 0;

                    let priceColor = "text-amber-400";
                    if (isCeiling) priceColor = "text-purple-400 font-black";
                    else if (isFloor) priceColor = "text-cyan-400 font-black";
                    else if (isUp) priceColor = "text-emerald-400 font-bold";
                    else if (!isRef) priceColor = "text-rose-400 font-bold";

                    return (
                      <tr
                        key={stock.symbol}
                        onClick={() => onSelectSymbol?.(stock.symbol)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-emerald-500/10 hover:bg-emerald-500/15"
                            : "hover:bg-slate-800/50"
                        }`}
                      >
                        {/* 1. Mã chứng khoán & Logo */}
                        <td className="py-2 pl-4 pr-2">
                          <div className="flex items-center gap-2">
                            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 font-black text-slate-200 ring-1 ring-slate-700/60">
                              {stock.symbol.slice(0, 2)}
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className="font-extrabold tracking-tight text-slate-100">
                                  {stock.symbol}
                                </span>
                                <span className="rounded bg-slate-800 px-1 py-0.2 text-[9px] text-slate-400">
                                  {stock.exchange}
                                </span>
                              </div>
                              <p className="line-clamp-1 text-[10px] text-slate-400">
                                {stock.name}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* 2. Giá khớp */}
                        <td className="px-3 py-2 text-right">
                          <span className={`text-sm ${priceColor}`}>
                            {stock.close.toFixed(2)}
                          </span>
                        </td>

                        {/* 3. Biến động */}
                        <td className="px-3 py-2 text-right">
                          <div
                            className={`flex items-center justify-end gap-0.5 font-semibold ${
                              isUp
                                ? "text-emerald-400"
                                : isRef
                                ? "text-amber-400"
                                : "text-rose-400"
                            }`}
                          >
                            {isUp && <ArrowUpRight className="h-3 w-3 stroke-[2.5]" />}
                            {!isUp && !isRef && (
                              <ArrowDownRight className="h-3 w-3 stroke-[2.5]" />
                            )}
                            <span>
                              {isUp ? "+" : ""}
                              {stock.change_pct.toFixed(2)}%
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-500">
                            {isUp ? "+" : ""}
                            {stock.change.toFixed(2)}
                          </p>
                        </td>

                        {/* 4. Tổng khối lượng */}
                        <td className="px-3 py-2 text-right font-medium text-slate-200">
                          {stock.volume.toLocaleString("vi-VN")}
                        </td>

                        {/* 5. Biểu đồ mini */}
                        <td className="px-3 py-2 text-center">
                          <div className="inline-block">
                            <TableSparkline data={stock.sparkline} isUp={isUp} />
                          </div>
                        </td>

                        {/* 6. Lực Mua / Bán chủ động */}
                        <td className="px-3 py-2">
                          <div className="mx-auto w-24">
                            <div className="flex justify-between text-[9px] font-bold">
                              <span className="text-emerald-400">{stock.buy_ratio}%</span>
                              <span className="text-rose-400">{stock.sell_ratio}%</span>
                            </div>
                            <div className="mt-0.5 flex h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                              <div
                                style={{ width: `${stock.buy_ratio}%` }}
                                className="bg-emerald-500 transition-all"
                              />
                              <div
                                style={{ width: `${stock.sell_ratio}%` }}
                                className="bg-rose-500 transition-all"
                              />
                            </div>
                          </div>
                        </td>

                        {/* 7. AI Bias */}
                        <td className="px-3 py-2 text-center">
                          <span
                            className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold ${
                              stock.ai_bias === "TĂNG"
                                ? "bg-emerald-500/10 text-emerald-400"
                                : stock.ai_bias === "GIẢM"
                                ? "bg-rose-500/10 text-rose-400"
                                : "bg-slate-800 text-slate-300"
                            }`}
                          >
                            {stock.ai_bias}
                          </span>
                        </td>

                        {/* 8. Thao tác */}
                        <td className="py-2 pl-2 pr-4 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectSymbol?.(stock.symbol);
                              openDetailModal({
                                symbol: stock.symbol,
                                name: stock.name,
                                exchange: stock.exchange,
                                sector: stock.sector,
                                currentValue: stock.close,
                                change: stock.change,
                                changePct: stock.change_pct,
                                reference: stock.reference,
                                stockCeiling: stock.ceiling,
                                stockFloor: stock.floor,
                                volume: stock.volume,
                                isIndex: false,
                              });
                            }}
                            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-semibold transition-all ${
                              isSelected
                                ? "bg-emerald-500 text-slate-950 font-bold"
                                : "border border-slate-700/80 bg-slate-800 text-slate-300 hover:border-emerald-500/50 hover:text-emerald-400"
                            }`}
                          >
                            <Eye className="h-3 w-3" />
                            <span>Soi nến</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* CỘT PHẢI: TRỢ LÝ AI & TOP BIẾN ĐỘNG THỊ TRƯỜNG (28% - 30% CHIỀU RỘNG) */}
          <div className="space-y-3 lg:col-span-4 xl:col-span-3">
            {/* Widget 1: ENSA / AI Market Insight */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 shadow-lg backdrop-blur-sm">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-100">
                      Trợ lý AI Định lượng nói gì?
                    </h3>
                    <p className="text-[10px] text-slate-400">Tổng quan phiên {marketBoard?.updated_at.split(" ")[1]}</p>
                  </div>
                </div>
              </div>

              <div className="mt-2.5 rounded-lg border border-slate-800/80 bg-slate-950/70 p-2.5 text-[11px] leading-relaxed text-slate-300">
                {marketBoard?.ai_market_insight ||
                  "VN-Index tiếp tục xu hướng tích cực, lực cầu lan tỏa mạnh mẽ ở nhóm ngành trụ cột."}
              </div>

              {/* Box Callout tương tác */}
              <div className="mt-3 flex items-center justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2">
                <div className="text-[11px]">
                  <p className="font-semibold text-emerald-300">Xem Tín hiệu Học máy?</p>
                  <p className="text-[10px] text-slate-400">LightGBM & PyTorch LSTM</p>
                </div>
                <button
                  onClick={onGoToPrediction}
                  className="flex items-center gap-1 rounded-md bg-emerald-500 px-2.5 py-1 text-xs font-bold text-slate-950 shadow-sm shadow-emerald-500/30 transition-all hover:bg-emerald-400"
                >
                  <span>Khám phá</span>
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </div>

            {/* Widget 2: Top Cổ phiếu Tăng mạnh nhất */}
            {marketBoard?.top_gainers && marketBoard.top_gainers.length > 0 && (
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3 shadow-lg backdrop-blur-sm">
                <div className="mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                    <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                    Top Cổ phiếu Tăng mạnh
                  </span>
                  <span className="text-[10px] text-slate-500">HOSE</span>
                </div>
                <div className="space-y-1.5">
                  {marketBoard.top_gainers.slice(0, 4).map((g) => (
                    <div
                      key={g.symbol}
                      onClick={() => {
                        onSelectSymbol?.(g.symbol);
                        openDetailModal({
                          symbol: g.symbol,
                          name: g.name,
                          exchange: g.exchange,
                          sector: g.sector,
                          currentValue: g.close,
                          change: g.change,
                          changePct: g.change_pct,
                          isIndex: false,
                        });
                      }}
                      className="flex cursor-pointer items-center justify-between rounded-lg border border-slate-800/50 bg-slate-950/50 px-2.5 py-1.5 transition-all hover:border-slate-700 hover:bg-slate-800/50"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100">{g.symbol}</span>
                        <span className="text-[10px] text-slate-400 line-clamp-1 max-w-[90px]">
                          {g.sector}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="font-bold text-emerald-400">{g.close.toFixed(2)}</span>
                        <span className="ml-1 text-[11px] font-bold text-emerald-400">
                          +{g.change_pct.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. KHUNG PHÂN TÍCH KỸ THUẬT CHI TIẾT THEO MÃ (DEEP-DIVE TECHNICAL VIEW)  */}
      {/* ========================================================================= */}
      {(viewMode === "split" || viewMode === "chart") && (
        <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl backdrop-blur-sm">
          {/* Header Card chi tiết của mã đang soi */}
          <div className="flex flex-col gap-3 border-b border-slate-800 pb-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-base font-black text-emerald-400 ring-1 ring-emerald-500/30">
                  {symbol}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold tracking-tight text-slate-100 sm:text-xl">
                      {symbol}
                    </h2>
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-300">
                      HOSE
                    </span>
                    <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                      {summary?.latest_date ? `Phiên: ${summary.latest_date}` : "Đang cập nhật..."}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Chi tiết Hành động Giá OHLCV, Khối lượng & Dao động RSI
                  </p>
                </div>
              </div>

              {/* Khối hiển thị thị giá */}
              <div className="flex items-baseline gap-2.5 border-l border-slate-800 pl-4">
                <span className="text-2xl font-black text-slate-100">
                  {summary ? (summary.latest_close * 1000).toLocaleString("vi-VN") : "---"}{" "}
                  <span className="text-xs font-normal text-slate-400">VNĐ</span>
                </span>
                {summary && (
                  <span
                    className={`flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-bold ${
                      isPriceUp
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-rose-500/10 text-rose-400"
                    }`}
                  >
                    {isPriceUp ? (
                      <ArrowUpRight className="h-3 w-3 stroke-[2.5]" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3 stroke-[2.5]" />
                    )}
                    {isPriceUp ? "+" : ""}
                    {summary.change_pct.toFixed(2)}%
                  </span>
                )}
              </div>
            </div>

            {/* Bộ nút chọn khung thời gian (Timeframe Selector) */}
            <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1">
              <Calendar className="ml-1 mr-1 h-3.5 w-3.5 text-slate-500" />
              {(["1M", "3M", "6M", "1Y", "ALL"] as Timeframe[]).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`rounded px-2.5 py-1 text-xs font-semibold transition-all ${
                    timeframe === tf
                      ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/30 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tf === "ALL" ? "Tất cả" : tf}
                </button>
              ))}
            </div>
          </div>

          {/* Biểu đồ Nến Canvas & RSI Canvas */}
          {loading ? (
            <div className="flex h-96 w-full items-center justify-center rounded-xl border border-slate-800 bg-slate-950">
              <div className="flex flex-col items-center gap-3 text-slate-400">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                <span className="text-xs">Đang tải dữ liệu nến OHLCV từ máy chủ...</span>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <CandlestickChart
                bars={filteredBars}
                height={380}
                onChartReady={handleCandleReady}
              />
              <RSIChart
                indicators={filteredIndicators}
                height={130}
                onChartReady={handleRsiReady}
              />
            </div>
          )}

          {/* Lưới 6 Thẻ Đo lường Kỹ thuật Cốt lõi (13 Đặc trưng ML) */}
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6 pt-1">
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-2.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-medium">Lệch SMA(20)</span>
                <Layers className="h-3 w-3" />
              </div>
              <div className="mt-1">
                <span
                  className={`text-sm font-bold ${
                    (summary?.sma_20_dev ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {summary ? `${(summary.sma_20_dev * 100).toFixed(2)}%` : "---"}
                </span>
              </div>
              <p className="mt-0.5 text-[9px] text-slate-500">So với TB 20 phiên</p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-2.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-medium">Lệch SMA(50)</span>
                <Layers className="h-3 w-3" />
              </div>
              <div className="mt-1">
                <span
                  className={`text-sm font-bold ${
                    (summary?.sma_50_dev ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {summary ? `${(summary.sma_50_dev * 100).toFixed(2)}%` : "---"}
                </span>
              </div>
              <p className="mt-0.5 text-[9px] text-slate-500">Xu hướng trung hạn</p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-2.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-medium">Biến động CV(50)</span>
                <Percent className="h-3 w-3" />
              </div>
              <div className="mt-1">
                <span className="text-sm font-bold text-slate-200">
                  {latestInd ? `${(latestInd.cv_50 * 100).toFixed(2)}%` : "---"}
                </span>
              </div>
              <p className="mt-0.5 text-[9px] text-slate-500">Hệ số biến thiên 50p</p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-2.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-medium">Vol Ratio</span>
                <BarChart2 className="h-3 w-3" />
              </div>
              <div className="mt-1">
                <span
                  className={`text-sm font-bold ${
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
              <p className="mt-0.5 text-[9px] text-slate-500">So với TB 20 phiên</p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-2.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-medium">Khối lượng GD</span>
                <BarChart2 className="h-3 w-3" />
              </div>
              <div className="mt-1">
                <span className="text-sm font-bold text-slate-200">
                  {summary ? (summary.volume / 1000).toLocaleString("vi-VN") : "---"}{" "}
                  <span className="text-[10px] font-normal text-slate-400">k CP</span>
                </span>
              </div>
              <p className="mt-0.5 text-[9px] text-slate-500">Khớp phiên gần nhất</p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-2.5">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-[11px] font-medium">VN-Index 1D</span>
                {(latestInd?.vnindex_return_1d ?? 0) >= 0 ? (
                  <TrendingUp className="h-3 w-3 text-emerald-400" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-rose-400" />
                )}
              </div>
              <div className="mt-1">
                <span
                  className={`text-sm font-bold ${
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
              <p className="mt-0.5 text-[9px] text-slate-500">Lợi suất toàn sàn 1D</p>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. MODAL XEM BIỂU ĐỒ NẾN KỸ THUẬT TIÊU CHUẨN (FINANCIAL DETAIL MODAL)    */}
      {/* ========================================================================= */}
      <FinancialDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        item={detailModalItem}
      />

      {/* ========================================================================= */}
      {/* 6. MODAL THÊM BIỂU ĐỒ VÀO BĂNG CHUYỀN (SCREENSHOT 3)                      */}
      {/* ========================================================================= */}
      <ManageRibbonModal
        isOpen={isManageModalOpen}
        onClose={() => setIsManageModalOpen(false)}
        activeSymbols={activeRibbonSymbols}
        marketBoard={marketBoard}
        onUpdateActiveSymbols={(newSyms) => {
          setActiveRibbonSymbols(newSyms);
          try {
            localStorage.setItem("active_ribbon_symbols", JSON.stringify(newSyms));
          } catch {}
        }}
      />
    </div>
  );
};
