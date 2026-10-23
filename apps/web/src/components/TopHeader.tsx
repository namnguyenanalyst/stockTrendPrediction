"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Clock,
  History,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  getMarketSyncStatus,
  getStockSymbols,
  triggerMarketSync,
} from "@/lib/api";
import { MarketSyncStatusResponse, StockSymbolInfo } from "@/lib/types";

interface TopHeaderProps {
  activeTab: "market" | "prediction" | "backtest";
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
}

const QUICK_SYMBOLS = ["VIC", "HPG", "FPT", "VNM", "MWG", "VHM", "SSI"];

const TAB_TITLES = {
  market: {
    title: "Thị trường & Bảng giá Điện tử",
    subtitle: "Bối cảnh thị trường & phân tích kỹ thuật",
    icon: BarChart3,
  },
  prediction: {
    title: "Tín hiệu dự báo xu hướng của mô hình",
    subtitle: "Dự báo xác suất 3 lớp (Tăng/Giữ/Giảm) qua LightGBM & PyTorch LSTM",
    icon: BrainCircuit,
  },
  backtest: {
    title: "Kiểm thử chiến lược",
    subtitle: "Mô phỏng vi cấu trúc HOSE/HNX, trừ phí thuế và đo lường Sharpe, MDD",
    icon: History,
  },
};

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeTab,
  selectedSymbol,
  setSelectedSymbol,
}) => {
  const currentTabInfo = TAB_TITLES[activeTab];
  const Icon = currentTabInfo.icon;

  // Trạng thái phiên thị trường và đồng bộ
  const [syncStatus, setSyncStatus] = useState<MarketSyncStatusResponse | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);

  // Danh sách mã cổ phiếu và tìm kiếm linh hoạt
  const [availableSymbols, setAvailableSymbols] = useState<StockSymbolInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Tải trạng thái phiên và danh mục mã khi mount
  useEffect(() => {
    let ignore = false;

    async function loadInitialStatus() {
      try {
        const [statusData, symbolsData] = await Promise.allSettled([
          getMarketSyncStatus(),
          getStockSymbols(),
        ]);
        if (!ignore) {
          if (statusData.status === "fulfilled") {
            setSyncStatus(statusData.value);
          }
          if (symbolsData.status === "fulfilled") {
            setAvailableSymbols(symbolsData.value);
          }
        }
      } catch (err) {
        console.warn("Không thể tải trạng thái đồng bộ ban đầu:", err);
      }
    }

    loadInitialStatus();
    // Tự động làm mới trạng thái phiên sau mỗi 60 giây
    const interval = setInterval(loadInitialStatus, 60000);
    return () => {
      ignore = true;
      clearInterval(interval);
    };
  }, []);

  // Xử lý đóng dropdown tìm kiếm khi click ngoài
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Kích hoạt đồng bộ nến thị trường từ SSI
  const handleTriggerSync = async () => {
    try {
      setIsSyncing(true);
      setSyncFeedback(null);
      await triggerMarketSync();
      const updatedStatus = await getMarketSyncStatus();
      setSyncStatus(updatedStatus);
      setSyncFeedback(`Đã cập nhật dữ liệu phiên ${updatedStatus.target_date}`);
      setTimeout(() => setSyncFeedback(null), 4000);
    } catch (err) {
      console.error("Lỗi khi đồng bộ dữ liệu:", err);
      setSyncFeedback("Lỗi khi kết nối SSI");
      setTimeout(() => setSyncFeedback(null), 4000);
    } finally {
      setIsSyncing(false);
    }
  };

  // Lọc danh sách mã theo từ khóa
  const filteredSymbols = availableSymbols.filter(
    (item) =>
      item.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectSymbol = (sym: string) => {
    const cleanSym = sym.trim().toUpperCase();
    if (cleanSym) {
      setSelectedSymbol(cleanSym);
      setSearchQuery("");
      setIsSearchOpen(false);
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      handleSelectSymbol(searchQuery);
    }
  };

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/85 backdrop-blur-md">
      <div className="mx-auto flex w-full flex-col gap-2.5 px-4 py-2.5 sm:px-6 md:flex-row md:items-center md:justify-between">
        {/* Bên Trái: Tiêu đề Tab & Badge Phiên giao dịch */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold tracking-tight text-slate-100 sm:text-base">
                  {currentTabInfo.title}
                </h1>
              </div>
              <p className="hidden text-[11px] text-slate-400 md:block">
                {currentTabInfo.subtitle}
              </p>
            </div>
          </div>

          {/* Badge Trạng thái Phiên Thị Trường & Đồng Bộ Nến (Ẩn ở Tab 1 Thị Trường) */}
          {activeTab !== "market" && (
            <div className="flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/90 px-2.5 py-1 text-xs">
              {syncStatus ? (
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span
                      className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                        syncStatus.is_market_closed ? "bg-emerald-400" : "bg-amber-400"
                      }`}
                    />
                    <span
                      className={`relative inline-flex h-2 w-2 rounded-full ${
                        syncStatus.is_market_closed ? "bg-emerald-500" : "bg-amber-500"
                      }`}
                    />
                  </span>
                  <span className="font-semibold text-slate-200">
                    {syncStatus.session_name}:
                  </span>
                  <span
                    className={`font-mono font-bold ${
                      syncStatus.is_market_closed ? "text-emerald-400" : "text-amber-400"
                    }`}
                  >
                    {syncStatus.target_date}
                  </span>
                  <span className="hidden text-[10px] text-slate-400 lg:inline">
                    ({syncStatus.status_label})
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-slate-400">
                  <Clock className="h-3 w-3 animate-spin text-slate-400" />
                  <span>Đang kiểm tra phiên...</span>
                </div>
              )}

              {/* Nút Kích hoạt Đồng bộ Thủ công */}
              <button
                onClick={handleTriggerSync}
                disabled={isSyncing}
                title="Đồng bộ nến mới nhất từ SSI FC-Data"
                className="ml-1 flex h-5 w-5 items-center justify-center rounded-md text-slate-400 transition hover:bg-slate-800 hover:text-emerald-400 disabled:opacity-50"
              >
                <RefreshCw
                  className={`h-3 w-3 ${isSyncing ? "animate-spin text-emerald-400" : ""}`}
                />
              </button>

              {syncFeedback && (
                <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400 animate-fade-in">
                  <CheckCircle2 className="h-3 w-3" />
                  {syncFeedback}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Bên Phải: Bộ chọn mã cổ phiếu toàn diện (Ẩn ở Tab 1 Thị Trường vì bảng giá đã có bộ lọc và chọn mã riêng) */}
        {activeTab !== "market" && (
          <div className="flex flex-wrap items-center gap-2">
          {/* Ô Tìm Kiếm Mã Cổ Phiếu / Chỉ Số Mở Rộng */}
          <div ref={searchRef} className="relative">
            <div className="relative flex items-center">
              <Search className="pointer-events-none absolute left-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                onFocus={() => setIsSearchOpen(true)}
                onKeyDown={handleSearchKeyDown}
                placeholder={`🔍 Nhập mã CP (${selectedSymbol})...`}
                className="h-8 w-36 rounded-lg border border-slate-800 bg-slate-900/90 pl-8 pr-7 text-xs font-bold uppercase text-slate-100 placeholder:text-slate-500 placeholder:font-normal focus:border-emerald-500/60 focus:bg-slate-900 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 sm:w-48 transition-all"
              />
              <button
                type="button"
                onClick={() => setIsSearchOpen(!isSearchOpen)}
                className="absolute right-2 text-slate-400 hover:text-slate-200"
              >
                <ChevronDown className="h-3 w-3" />
              </button>
            </div>

            {/* Dropdown gợi ý mã cổ phiếu & chỉ số */}
            {isSearchOpen && (
              <div className="absolute right-0 mt-1 max-h-64 w-64 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-1.5 shadow-2xl backdrop-blur-xl z-50">
                <div className="px-2 py-1 text-[10px] font-semibold text-slate-400 border-b border-slate-800/80 mb-1 flex items-center justify-between">
                  <span>Gợi ý mã giao dịch</span>
                  <span className="text-emerald-400">Enter để chọn bất kỳ</span>
                </div>
                {filteredSymbols.length > 0 ? (
                  filteredSymbols.slice(0, 15).map((item) => (
                    <button
                      key={item.symbol}
                      onClick={() => handleSelectSymbol(item.symbol)}
                      className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-xs transition ${
                        selectedSymbol === item.symbol
                          ? "bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30"
                          : "text-slate-300 hover:bg-slate-900 hover:text-white"
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-slate-100">{item.symbol}</span>
                        <span className="text-[10px] text-slate-400 truncate max-w-[120px]">
                          {item.name}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">
                        {item.exchange}
                      </span>
                    </button>
                  ))
                ) : (
                  <div className="p-2 text-center text-xs text-slate-400">
                    <p>Nhấn <strong>Enter</strong> để nạp mã:</p>
                    <span className="font-bold text-emerald-400 uppercase mt-0.5 inline-block">
                      &quot;{searchQuery}&quot;
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Các nút ghim nhanh mã trọng tâm */}
          <div className="flex items-center gap-1 rounded-xl border border-slate-800 bg-slate-900/90 p-1 shadow-inner">
            {QUICK_SYMBOLS.map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`rounded-lg px-2 py-1 text-xs font-bold transition-all ${
                  selectedSymbol === sym
                    ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/40 scale-105"
                    : "text-slate-300 hover:bg-slate-800 hover:text-slate-100"
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
        )}
      </div>
    </header>
  );
};

