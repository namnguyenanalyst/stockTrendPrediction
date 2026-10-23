"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  BarChart3,
  BrainCircuit,
  ChevronDown,
  History,
  Search,
} from "lucide-react";
import { getStockSymbols } from "@/lib/api";
import { StockSymbolInfo } from "@/lib/types";

interface TopHeaderProps {
  activeTab: "market" | "prediction" | "backtest";
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
}

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

  // Danh sách mã cổ phiếu và tìm kiếm linh hoạt
  const [availableSymbols, setAvailableSymbols] = useState<StockSymbolInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Tải danh mục mã khi mount
  useEffect(() => {
    let ignore = false;

    async function loadSymbols() {
      try {
        const symbols = await getStockSymbols();
        if (!ignore && symbols) {
          setAvailableSymbols(symbols);
        }
      } catch (err) {
        console.warn("Không thể tải danh mục mã:", err);
      }
    }

    loadSymbols();
    return () => {
      ignore = true;
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

        </div>

        {/* Bên Phải: Bộ chọn mã cổ phiếu toàn diện (Chỉ hiển thị ở Tab 2 Dự báo AI; ẩn ở Tab 1 Thị trường và Tab 3 Kiểm thử vì đã có bộ chọn chuyên biệt) */}
        {activeTab === "prediction" && (
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
                placeholder={`Nhập mã CP (${selectedSymbol})...`}
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

        </div>
        )}
      </div>
    </header>
  );
};

