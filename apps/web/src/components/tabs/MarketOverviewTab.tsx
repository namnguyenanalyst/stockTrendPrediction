"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  Calendar,
  ChevronRight,
  Layers,
  Minus,
  Percent,
  Search,
  Sparkles,
  Star,
  TrendingDown,
  TrendingUp,
  X,
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
import { useAuth } from "@/context/AuthContext";
import {
  createUserWatchlist,
  deleteUserWatchlist,
  getUserWatchlists,
} from "@/lib/api";
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

const CATEGORY_TABS = [
  { id: "ALL", label: "Tất cả cổ phiếu" },
  { id: "WATCHLIST", label: "★ Theo dõi" },
  { id: "VN30", label: "VN30" },
  { id: "BANK", label: "Ngân hàng" },
  { id: "REAL_ESTATE", label: "Bất động sản" },
  { id: "TECH", label: "Công nghệ" },
  { id: "RETAIL", label: "Bán lẻ & Tiêu dùng" },
  { id: "STEEL", label: "Thép & Vật liệu" },
  { id: "FINANCE", label: "Dịch vụ tài chính" },
  { id: "ENERGY", label: "Năng lượng & Dầu khí" },
];

const EXCHANGE_TABS = [
  { id: "ALL", label: "Tất cả sàn" },
  { id: "HOSE", label: "HOSE" },
  { id: "HNX", label: "HNX" },
  { id: "UPCOM", label: "UPCOM" },
];

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
  const [selectedExchange, setSelectedExchange] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isSearchDropdownOpen, setIsSearchDropdownOpen] = useState<boolean>(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Trạng thái ghim mã cổ phiếu vào Danh mục theo dõi (Watchlist)
  const { user, isAuthenticated } = useAuth();
  const [pinnedSymbols, setPinnedSymbols] = useState<string[]>([]);
  const [userWatchlistId, setUserWatchlistId] = useState<string | null>(null);

  // Tải danh mục theo dõi từ CSDL hoặc localStorage
  useEffect(() => {
    let ignore = false;

    async function loadWatchlist() {
      if (isAuthenticated) {
        try {
          const lists = await getUserWatchlists();
          if (!ignore) {
            if (lists && lists.length > 0) {
              setUserWatchlistId(lists[0].id);
              setPinnedSymbols(lists[0].symbols || []);
            } else {
              setUserWatchlistId(null);
              setPinnedSymbols([]);
            }
            return;
          }
        } catch (err) {
          console.warn("Không thể tải danh mục theo dõi từ API:", err);
        }
      }

      // Fallback về localStorage nếu chưa đăng nhập hoặc offline
      if (typeof window !== "undefined") {
        try {
          const localSaved = localStorage.getItem("stockpulse_watchlist_symbols");
          if (localSaved && !ignore) {
            const parsed = JSON.parse(localSaved);
            if (Array.isArray(parsed)) {
              setPinnedSymbols(parsed);
            }
          }
        } catch {
          // Bỏ qua lỗi parse
        }
      }
    }

    loadWatchlist();
    return () => {
      ignore = true;
    };
  }, [isAuthenticated, user?.id]);

  const togglePinSymbol = async (targetSymbol: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const cleanSym = targetSymbol.toUpperCase();
    const isPinned = pinnedSymbols.includes(cleanSym);
    const nextSymbols = isPinned
      ? pinnedSymbols.filter((s) => s !== cleanSym)
      : [...pinnedSymbols, cleanSym];

    setPinnedSymbols(nextSymbols);

    if (typeof window !== "undefined") {
      localStorage.setItem(
        "stockpulse_watchlist_symbols",
        JSON.stringify(nextSymbols)
      );
    }

    if (isAuthenticated) {
      try {
        if (userWatchlistId) {
          await deleteUserWatchlist(userWatchlistId);
        }
        if (nextSymbols.length > 0) {
          const newWl = await createUserWatchlist("Mục theo dõi", nextSymbols);
          setUserWatchlistId(newWl.id);
        } else {
          setUserWatchlistId(null);
        }
      } catch (err) {
        console.warn("Lỗi đồng bộ danh mục theo dõi:", err);
      }
    }
  };

  // Đóng dropdown tìm kiếm khi click ra ngoài
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(event.target as Node)
      ) {
        setIsSearchDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Danh sách gợi ý tìm kiếm theo mã hoặc tên công ty
  const stocks = marketBoard?.stocks;
  const searchSuggestions = useMemo(() => {
    if (!searchQuery.trim() || !stocks) return [];
    const q = searchQuery.trim().toUpperCase();
    return stocks
      .filter(
        (s) => s.symbol.toUpperCase().includes(q) || s.name.toUpperCase().includes(q)
      )
      .slice(0, 8);
  }, [searchQuery, stocks]);

  const handleSelectSearchedSymbol = (sym: string) => {
    const cleanSym = sym.trim().toUpperCase();
    if (cleanSym) {
      onSelectSymbol?.(cleanSym);
      setSearchQuery("");
      setIsSearchDropdownOpen(false);
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const q = searchQuery.trim().toUpperCase();
      if (!q) return;

      // 1. Kiểm tra nếu có mã trùng khớp chính xác trong bảng giá
      const exact = marketBoard?.stocks?.find((s) => s.symbol.toUpperCase() === q);
      if (exact) {
        handleSelectSearchedSymbol(exact.symbol);
        return;
      }

      // 2. Nếu có danh sách gợi ý, chọn mục đầu tiên
      if (searchSuggestions.length > 0) {
        handleSelectSearchedSymbol(searchSuggestions[0].symbol);
        return;
      }

      // 3. Cho phép kích hoạt tra cứu trực tiếp mã do người dùng gõ
      handleSelectSearchedSymbol(q);
    } else if (e.key === "Escape") {
      setIsSearchDropdownOpen(false);
    }
  };

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

  // Lọc danh sách cổ phiếu theo Category, Exchange & Search Query
  const filteredStocks = useMemo(() => {
    if (!marketBoard || !marketBoard.stocks) return [];
    let list = marketBoard.stocks;

    // Lọc theo sàn giao dịch (Exchange)
    if (selectedExchange !== "ALL") {
      list = list.filter((s) => s.exchange?.toUpperCase() === selectedExchange);
    }

    // Lọc theo nhóm ngành / rổ (Category)
    if (selectedCategory === "WATCHLIST") {
      const pinnedSet = new Set(pinnedSymbols.map((s) => s.toUpperCase()));
      list = list.filter((s) => pinnedSet.has(s.symbol.toUpperCase()));
    } else if (selectedCategory === "VN30" || selectedCategory === "CORE") {
      const vn30Set = new Set([
        "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
        "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
        "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
      ]);
      list = list.filter((s) => vn30Set.has(s.symbol.toUpperCase()));
    } else if (selectedCategory === "BANK") {
      list = list.filter((s) => s.sector?.includes("Ngân hàng"));
    } else if (selectedCategory === "REAL_ESTATE") {
      list = list.filter((s) => s.sector?.includes("Bất động sản"));
    } else if (selectedCategory === "TECH") {
      list = list.filter((s) => s.sector?.includes("Công nghệ"));
    } else if (selectedCategory === "RETAIL") {
      list = list.filter(
        (s) =>
          s.sector?.includes("Bán lẻ") ||
          s.sector?.includes("tiêu dùng") ||
          s.sector?.includes("Đồ uống") ||
          s.sector?.includes("Vận tải") ||
          s.sector?.includes("Hàng không")
      );
    } else if (selectedCategory === "STEEL") {
      list = list.filter(
        (s) =>
          s.sector?.includes("Thép") ||
          s.sector?.includes("Vật liệu") ||
          s.sector?.includes("Tài nguyên")
      );
    } else if (selectedCategory === "FINANCE") {
      list = list.filter(
        (s) =>
          s.sector?.includes("Chứng khoán") ||
          s.sector?.includes("tài chính") ||
          s.sector?.includes("Tài chính") ||
          s.sector?.includes("Bảo hiểm")
      );
    } else if (selectedCategory === "ENERGY") {
      list = list.filter(
        (s) =>
          s.sector?.includes("Dầu khí") ||
          s.sector?.includes("Năng lượng") ||
          s.sector?.includes("Khí")
      );
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toUpperCase();
      list = list.filter(
        (s) => s.symbol.toUpperCase().includes(q) || s.name.toUpperCase().includes(q)
      );
    }

    return list;
  }, [marketBoard, selectedCategory, selectedExchange, searchQuery, pinnedSymbols]);

  // Thống kê độ rộng thị trường (Market Breadth) chuẩn phong cách DNSE
  const breadthStats = useMemo(() => {
    if (marketBoard?.breadth) {
      return marketBoard.breadth;
    }
    const stocks = marketBoard?.stocks || [];
    let ceiling = 0;
    let advancing = 0;
    let unchanged = 0;
    let declining = 0;
    let floor = 0;

    for (const s of stocks) {
      if (s.ceiling && s.close >= s.ceiling) {
        ceiling++;
      } else if (s.floor && s.close <= s.floor) {
        floor++;
      } else if (s.change > 0) {
        advancing++;
      } else if (s.change < 0) {
        declining++;
      } else {
        unchanged++;
      }
    }

    return { ceiling, advancing, unchanged, declining, floor };
  }, [marketBoard]);

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
      {/* 2. SUB-NAV PHÂN LOẠI DANH MỤC & THANH ĐIỀU KHIỂN CHUẨN PHONG CÁCH DNSE    */}
      {/* ========================================================================= */}
      <div className="space-y-2">
        {/* Tier 1: Sub-Nav Tab Strip (Phân loại danh mục nằm ngang phẳng mịn chuẩn DNSE) */}
        <div className="border-b border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar px-1">
            {CATEGORY_TABS.map((cat) => {
              const isActive = selectedCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`group relative whitespace-nowrap px-3.5 py-2.5 text-xs font-semibold transition-all ${isActive
                      ? "text-emerald-400 font-bold"
                      : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  <span>{cat.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tier 2: Action Toolbar (Tìm kiếm, Sàn giao dịch, Thống kê biến động & Chế độ xem) */}
        <div className="flex flex-col gap-2.5 py-1 sm:flex-row sm:items-center sm:justify-between">
          {/* Bên trái: Ô tìm kiếm + Bộ lọc Sàn giao dịch */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Ô tìm kiếm mã cổ phiếu thông minh phong cách Terminal */}
            <div ref={searchContainerRef} className="relative flex items-center">
              <Search className="pointer-events-none absolute left-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Tìm mã CP, tên cty..."
                value={searchQuery}
                onFocus={() => {
                  if (searchQuery.trim()) setIsSearchDropdownOpen(true);
                }}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchDropdownOpen(true);
                }}
                onKeyDown={handleSearchKeyDown}
                className="h-8 w-44 rounded-lg border border-slate-800 bg-slate-900/90 pl-8 pr-7 text-xs text-slate-100 placeholder:text-slate-500 focus:border-emerald-500/60 focus:bg-slate-900 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 sm:w-52 transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery("");
                    setIsSearchDropdownOpen(false);
                  }}
                  className="absolute right-2 text-slate-500 hover:text-slate-300"
                  title="Xóa tìm kiếm"
                >
                  <X className="h-3 w-3" />
                </button>
              )}

              {/* Dropdown Popover gợi ý mã cổ phiếu tức thì */}
              {isSearchDropdownOpen && searchQuery.trim() && (
                <div className="absolute left-0 top-full z-50 mt-1 w-80 rounded-xl border border-slate-800 bg-slate-950/95 p-1.5 shadow-2xl backdrop-blur-md">
                  <div className="flex items-center justify-between px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                    <span>Gợi ý cổ phiếu ({searchSuggestions.length})</span>
                    <span className="text-[9px] lowercase text-emerald-400">Nhấn Enter để mở</span>
                  </div>
                  <div className="max-h-64 overflow-y-auto divide-y divide-slate-800/40">
                    {searchSuggestions.length > 0 ? (
                      searchSuggestions.map((stk) => {
                        const isUp = stk.change >= 0;
                        return (
                          <button
                            key={stk.symbol}
                            type="button"
                            onClick={() => handleSelectSearchedSymbol(stk.symbol)}
                            className="flex w-full items-center justify-between px-2.5 py-2 text-left hover:bg-slate-800/70 rounded-lg transition-colors group"
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-100 group-hover:text-emerald-400 transition-colors">
                                {stk.symbol}
                              </span>
                              <span className="rounded bg-slate-800 px-1 py-0.5 text-[9px] text-slate-400 font-medium">
                                {stk.exchange}
                              </span>
                              <span className="truncate text-xs text-slate-400 max-w-[120px]">
                                {stk.name}
                              </span>
                            </div>
                            <div className="text-right whitespace-nowrap">
                              <div className="text-xs font-semibold text-slate-200">
                                {stk.close.toFixed(2)}
                              </div>
                              <div
                                className={`text-[10px] font-bold ${isUp ? "text-emerald-400" : "text-rose-400"
                                  }`}
                              >
                                {isUp ? "+" : ""}
                                {stk.change_pct.toFixed(2)}%
                              </div>
                            </div>
                          </button>
                        );
                      })
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleSelectSearchedSymbol(searchQuery)}
                        className="flex w-full items-center justify-between px-2.5 py-2 text-left hover:bg-slate-800/70 rounded-lg text-xs text-emerald-400 font-medium"
                      >
                        <span>Mở phân tích kỹ thuật mã &quot;{searchQuery.trim().toUpperCase()}&quot; (Nhấn Enter)</span>
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Bộ chọn Sàn giao dịch phong cách DNSE */}
            <div className="flex items-center gap-1">
              {EXCHANGE_TABS.map((exch) => {
                const isActive = selectedExchange === exch.id;
                return (
                  <button
                    key={exch.id}
                    onClick={() => setSelectedExchange(exch.id)}
                    className={`h-8 rounded-lg px-2.5 text-xs font-semibold transition-all border ${isActive
                        ? "bg-slate-800 text-emerald-400 border-emerald-500/40 shadow-sm"
                        : "bg-slate-900/70 text-slate-400 border-slate-800/80 hover:bg-slate-800 hover:text-slate-200"
                      }`}
                  >
                    {exch.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bên phải: Thống kê biến động chuẩn DNSE + Chế độ xem */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Thống kê biến động */}
            <div className="flex items-center gap-1.5">
              <span className="hidden text-xs font-medium text-slate-400 sm:inline whitespace-nowrap">
                Thống kê biến động:
              </span>

              <div className="flex items-center gap-1 text-xs font-bold">
                {/* Trần */}
                <div
                  title="Số mã chạm giá Trần (Ceiling)"
                  className="flex items-center gap-1 rounded-md border border-purple-500/30 bg-purple-950/40 px-2 py-1 text-purple-400 shadow-sm"
                >
                  <ArrowUpRight className="h-3 w-3" />
                  <span>{breadthStats.ceiling}</span>
                </div>

                {/* Tăng */}
                <div
                  title="Số mã Tăng giá (Advancing)"
                  className="flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-950/40 px-2 py-1 text-emerald-400 shadow-sm"
                >
                  <TrendingUp className="h-3 w-3" />
                  <span>{breadthStats.advancing}</span>
                </div>

                {/* Tham chiếu */}
                <div
                  title="Số mã Đứng giá / Tham chiếu (Unchanged)"
                  className="flex items-center gap-1 rounded-md border border-amber-500/30 bg-amber-950/40 px-2 py-1 text-amber-400 shadow-sm"
                >
                  <Minus className="h-3 w-3" />
                  <span>{breadthStats.unchanged}</span>
                </div>

                {/* Giảm */}
                <div
                  title="Số mã Giảm giá (Declining)"
                  className="flex items-center gap-1 rounded-md border border-rose-500/30 bg-rose-950/40 px-2 py-1 text-rose-400 shadow-sm"
                >
                  <TrendingDown className="h-3 w-3" />
                  <span>{breadthStats.declining}</span>
                </div>

                {/* Sàn */}
                <div
                  title="Số mã chạm giá Sàn (Floor)"
                  className="flex items-center gap-1 rounded-md border border-cyan-500/30 bg-cyan-950/40 px-2 py-1 text-cyan-400 shadow-sm"
                >
                  <ArrowDownRight className="h-3 w-3" />
                  <span>{breadthStats.floor}</span>
                </div>
              </div>
            </div>

            {/* Chế độ hiển thị (View Mode Switcher) */}
            <div className="flex items-center rounded-lg border border-slate-800 bg-slate-900/90 p-0.5 shadow-inner">
              <button
                onClick={() => setViewMode("split")}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${viewMode === "split"
                    ? "bg-slate-800 text-emerald-400 shadow-sm border border-emerald-500/30"
                    : "text-slate-400 hover:text-slate-200"
                  }`}
                title="Chế độ Kết hợp Bảng giá & Biểu đồ"
              >
                Kết hợp
              </button>
              <button
                onClick={() => setViewMode("board")}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${viewMode === "board"
                    ? "bg-slate-800 text-emerald-400 shadow-sm border border-emerald-500/30"
                    : "text-slate-400 hover:text-slate-200"
                  }`}
                title="Chỉ Bảng giá Điện tử"
              >
                Bảng giá
              </button>
              <button
                onClick={() => setViewMode("chart")}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${viewMode === "chart"
                    ? "bg-slate-800 text-emerald-400 shadow-sm border border-emerald-500/30"
                    : "text-slate-400 hover:text-slate-200"
                  }`}
                title="Chuyên sâu Biểu đồ nến kỹ thuật"
              >
                Biểu đồ
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. BẢNG GIÁ CHỨNG KHOÁN HIỆN ĐẠI & PHÂN HỆ PHỤ BÊN PHẢI (DNSE LAYOUT)     */}
      {/* ========================================================================= */}
      {viewMode !== "chart" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* CỘT TRÁI: BẢNG GIÁ ĐIỆN TỬ (70% - 75% CHIỀU RỘNG, GIỚI HẠN 10 DÒNG KÈM THANH CUỘN DỌC) */}
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg backdrop-blur-sm lg:col-span-8 xl:col-span-9">
            <div className="overflow-x-auto max-h-[530px] overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/95 backdrop-blur-md text-[11px] font-bold text-slate-400">
                  <tr>
                    <th className="py-2.5 pl-4 pr-3">MÃ CHỨNG KHOÁN</th>
                    <th className="px-3 py-2.5 text-right">GIÁ KHỚP</th>
                    <th className="px-3 py-2.5 text-right">BIẾN ĐỘNG</th>
                    <th className="px-3 py-2.5 text-right">KLGD</th>
                    <th className="px-3 py-2.5 text-center">BIỂU ĐỒ 10P</th>
                    <th className="px-3 py-2.5 text-center">LỰC MUA / BÁN</th>
                    <th className="py-2.5 pl-3 pr-4 text-center">AI BIAS</th>
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
                        onClick={() => {
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
                        title={`Nhấn để mở biểu đồ nến chi tiết của ${stock.symbol}`}
                        className={`group cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-emerald-500/10 hover:bg-emerald-500/15"
                            : "hover:bg-slate-800/60"
                        }`}
                      >
                        {/* 1. Mã chứng khoán & Logo */}
                        <td className="py-2 pl-4 pr-3">
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={(e) => togglePinSymbol(stock.symbol, e)}
                              title={
                                pinnedSymbols.includes(stock.symbol.toUpperCase())
                                  ? "Bỏ ghim khỏi danh mục theo dõi"
                                  : "Ghim vào danh mục theo dõi"
                              }
                              className="p-1 rounded hover:bg-slate-700/60 transition-colors shrink-0"
                            >
                              <Star
                                className={`h-3.5 w-3.5 ${
                                  pinnedSymbols.includes(stock.symbol.toUpperCase())
                                    ? "fill-amber-400 text-amber-400"
                                    : "text-slate-600 hover:text-amber-400"
                                }`}
                              />
                            </button>
                            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 font-black text-slate-200 ring-1 ring-slate-700/60 group-hover:ring-emerald-500/50 transition-all">
                              {stock.symbol.slice(0, 2)}
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className="font-extrabold tracking-tight text-slate-100 group-hover:text-emerald-400 transition-colors">
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
                        <td className="py-2 pl-3 pr-4 text-center">
                          <span
                            className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${
                              stock.ai_bias === "TĂNG"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : stock.ai_bias === "GIẢM"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                : "bg-slate-800 text-slate-300 border border-slate-700/50"
                            }`}
                          >
                            {stock.ai_bias}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {filteredStocks.length === 0 && (
                <div className="py-12 text-center text-xs text-slate-400">
                  {selectedCategory === "WATCHLIST" ? (
                    <div className="flex flex-col items-center gap-2">
                      <Star className="h-8 w-8 text-amber-400/40" />
                      <p className="font-semibold text-slate-300">
                        Danh mục theo dõi của bạn đang trống
                      </p>
                      <p className="max-w-md text-slate-500 text-[11px]">
                        Nhấn biểu tượng ★ bên cạnh bất kỳ mã cổ phiếu nào trong bảng giá để ghim vào danh mục theo dõi cá nhân của bạn.
                      </p>
                    </div>
                  ) : (
                    <p>Không tìm thấy mã cổ phiếu phù hợp với bộ lọc hiện tại.</p>
                  )}
                </div>
              )}
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
                    className={`flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-bold ${isPriceUp
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
                  className={`rounded px-2.5 py-1 text-xs font-semibold transition-all ${timeframe === tf
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
                  className={`text-sm font-bold ${(summary?.sma_20_dev ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
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
                  className={`text-sm font-bold ${(summary?.sma_50_dev ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
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
                  className={`text-sm font-bold ${(latestInd?.vol_ratio ?? 1) >= 1.2
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
                  className={`text-sm font-bold ${(latestInd?.vnindex_return_1d ?? 0) >= 0
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
          } catch { }
        }}
      />
    </div>
  );
};
