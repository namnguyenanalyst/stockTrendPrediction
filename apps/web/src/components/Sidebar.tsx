"use client";

import React, { useEffect } from "react";
import {
  BarChart3,
  BrainCircuit,
  History,
  TrendingUp,
  PanelLeftClose,
  PanelLeftOpen,
  GraduationCap,
} from "lucide-react";

export interface SidebarProps {
  activeTab: "market" | "prediction" | "backtest";
  setActiveTab: (tab: "market" | "prediction" | "backtest") => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
}

const CORE_SYMBOLS = ["VIC", "HPG", "FPT", "VNM", "MWG"];

const NAV_ITEMS = [
  {
    id: "market" as const,
    label: "Thị trường & Kỹ thuật",
    shortLabel: "Thị trường",
    description: "Nến OHLCV & RSI (14)",
    icon: BarChart3,
  },
  {
    id: "prediction" as const,
    label: "Tín hiệu AI & Mô hình",
    shortLabel: "Dự báo AI",
    description: "LightGBM & PyTorch LSTM",
    icon: BrainCircuit,
  },
  {
    id: "backtest" as const,
    label: "Giả lập Backtest T+2",
    shortLabel: "Backtest",
    description: "Kiểm định & Quản trị Rủi ro",
    icon: History,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
  selectedSymbol,
  setSelectedSymbol,
}) => {
  // Kích hoạt dispatch sự kiện resize để các biểu đồ Lightweight Charts tự động cập nhật độ rộng mượt mà
  useEffect(() => {
    window.dispatchEvent(new Event("resize"));
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 320);
    return () => clearTimeout(timer);
  }, [isCollapsed]);

  return (
    <aside
      aria-label="Thanh điều hướng chính"
      className={`sticky top-0 h-screen flex flex-col justify-between border-r border-slate-800 bg-slate-950/95 backdrop-blur-md z-40 transition-all duration-300 ease-in-out shrink-0 select-none ${
        isCollapsed ? "w-20" : "w-64"
      }`}
    >
      {/* 1. Phần Đầu: Branding & Nút Đóng/Mở Xổ ra vào */}
      <div>
        <div className="flex items-center justify-between border-b border-slate-800/80 px-4 py-4">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20">
              <TrendingUp className="h-6 w-6 stroke-[2.5]" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col overflow-hidden transition-opacity duration-300">
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-extrabold tracking-tight text-slate-100 whitespace-nowrap">
                    STOCK<span className="text-emerald-400">PULSE</span>
                  </span>
                  <span className="rounded bg-slate-800 px-1 py-0.2 text-[9px] font-semibold uppercase tracking-wider text-emerald-400">
                    QUANT
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-medium whitespace-nowrap truncate">
                  AI Stock Prediction
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"}
            aria-label={isCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng"}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 hover:border-slate-700 hover:bg-slate-800 hover:text-slate-100 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            {isCollapsed ? (
              <PanelLeftOpen className="h-4 w-4 text-emerald-400" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* 2. Danh sách Menu Tabs (Dạng Cột Dọc) */}
        <div className="px-3 py-4">
          <div className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            {!isCollapsed ? "Chức năng hệ thống" : "Menu"}
          </div>

          <nav className="flex flex-col space-y-1.5" role="tablist">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveTab(item.id)}
                  title={isCollapsed ? `${item.label} — ${item.description}` : undefined}
                  className={`group relative flex items-center gap-3 rounded-xl px-3 py-3 text-left transition-all ${
                    isActive
                      ? "bg-emerald-500/10 text-emerald-400 font-semibold shadow-sm shadow-emerald-500/5 border border-emerald-500/30"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent"
                  } ${isCollapsed ? "justify-center px-0" : ""}`}
                >
                  <Icon
                    className={`h-5 w-5 shrink-0 transition-transform group-hover:scale-110 ${
                      isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-slate-200"
                    }`}
                  />

                  {!isCollapsed && (
                    <div className="flex flex-col overflow-hidden">
                      <span className="text-xs font-medium leading-tight truncate">
                        {item.label}
                      </span>
                      <span className="text-[10px] text-slate-500 truncate mt-0.5">
                        {item.description}
                      </span>
                    </div>
                  )}

                  {/* Vạch chỉ báo kích hoạt (Active Indicator) */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-emerald-400" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* 3. Phần chọn Mã Cổ phiếu Nhanh trong Sidebar (hiển thị khi mở rộng) */}
        {!isCollapsed && (
          <div className="mx-3 mt-2 rounded-xl border border-slate-800/80 bg-slate-900/50 p-3">
            <div className="mb-2 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              <span>Mã CP Giám Sát</span>
              <span className="text-emerald-400 text-[10px]">{selectedSymbol}</span>
            </div>
            <div className="grid grid-cols-5 gap-1">
              {CORE_SYMBOLS.map((sym) => (
                <button
                  key={sym}
                  onClick={() => setSelectedSymbol(sym)}
                  className={`rounded-md py-1.5 text-xs font-bold transition-all ${
                    selectedSymbol === sym
                      ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/40"
                      : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 4. Phần Chân Sidebar: Thông tin Học thuật ĐATN */}
      <div className="border-t border-slate-800/80 p-3">
        {!isCollapsed ? (
          <div className="flex items-center gap-2.5 rounded-xl bg-slate-900/60 p-2.5 border border-slate-800/60">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
              <GraduationCap className="h-4 w-4" />
            </div>
            <div className="overflow-hidden">
              <div className="text-[11px] font-semibold text-slate-200 truncate">
                Đồ án Tốt nghiệp
              </div>
              <div className="text-[10px] text-slate-500 truncate">
                Tin học Kinh tế • HUMG
              </div>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="ĐATN Tin học Kinh tế - HUMG">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-slate-400 hover:text-emerald-400 transition-colors">
              <GraduationCap className="h-4 w-4" />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
