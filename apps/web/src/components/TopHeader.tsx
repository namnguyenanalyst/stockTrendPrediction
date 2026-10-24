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

  // Lọc danh mục mã theo nhóm phân loại
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const categoryFiltered = availableSymbols.filter((item) => {
    if (selectedCategory === "VN30") return !!item.is_vn30;
    if (selectedCategory === "INDEX") return item.exchange === "INDEX";
    if (selectedCategory === "BANK") return item.sector?.includes("Ngân hàng");
    if (selectedCategory === "REALESTATE") return item.sector?.includes("Bất động sản");
    if (selectedCategory === "STEEL") return item.sector?.includes("Thép");
    if (selectedCategory === "RETAIL_TECH")
      return (
        item.sector?.includes("Công nghệ") ||
        item.sector?.includes("Bán lẻ") ||
        item.sector?.includes("Tiêu dùng")
      );
    return true;
  });

  // Lọc danh sách mã theo từ khóa
  const filteredSymbols = categoryFiltered.filter(
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

  const CATEGORY_TABS = [
    { id: "ALL", label: "Tất cả" },
    { id: "VN30", label: "VN30" },
    { id: "INDEX", label: "Chỉ số" },
    { id: "BANK", label: "Ngân hàng" },
    { id: "REALESTATE", label: "BĐS" },
    { id: "STEEL", label: "Thép" },
    { id: "RETAIL_TECH", label: "Bán lẻ/CN" },
  ];

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
              <div className="absolute right-0 mt-1 max-h-80 w-80 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-2 shadow-2xl backdrop-blur-xl z-50">
                {/* Header gợi ý */}
                <div className="px-1.5 py-1 text-[10px] font-semibold text-slate-400 border-b border-slate-800/80 mb-1.5">
                  <span>Gợi ý mã giao dịch</span>
                </div>

                {/* Thanh phân loại Category Chips */}
                <div className="flex items-center gap-1 overflow-x-auto pb-1.5 mb-1.5 border-b border-slate-800/80 scrollbar-none">
                  {CATEGORY_TABS.map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedCategory(cat.id);
                      }}
                      className={`rounded-md px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap transition-colors ${
                        selectedCategory === cat.id
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>

                {filteredSymbols.length > 0 ? (
                  <div className="space-y-0.5">
                    {filteredSymbols.slice(0, 30).map((item) => (
                      <button
                        key={item.symbol}
                        onClick={() => handleSelectSymbol(item.symbol)}
                        className={`flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs transition ${
                          selectedSymbol === item.symbol
                            ? "bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30"
                            : "text-slate-300 hover:bg-slate-900 hover:text-white"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span className="font-bold text-slate-100">{item.symbol}</span>
                          {item.exchange === "INDEX" && (
                            <span className="rounded bg-sky-500/15 border border-sky-500/30 px-1 py-0.2 text-[9px] font-bold text-sky-400">
                              CHỈ SỐ
                            </span>
                          )}
                          <span className="text-[10px] text-slate-400 truncate max-w-[130px]">
                            {item.name}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500 shrink-0">
                          {item.exchange}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 text-center text-xs text-slate-400">
                    <p>Không thấy trong danh mục đã lưu.</p>
                    <p className="mt-1">Nhấn <strong>Enter</strong> để tải nến SSI trực tuyến:</p>
                    <span className="font-bold text-emerald-400 uppercase mt-1 inline-block">
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

