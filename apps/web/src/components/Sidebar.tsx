"use client";

import React, { useEffect } from "react";
import {
  BarChart3,
  BrainCircuit,
  History,
  TrendingUp,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

export interface SidebarProps {
  activeTab: "market" | "prediction" | "backtest";
  setActiveTab: (tab: "market" | "prediction" | "backtest") => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
}

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
      className={`sticky top-0 h-screen flex flex-col border-r border-slate-800 bg-slate-950/95 backdrop-blur-md z-40 transition-all duration-300 ease-in-out shrink-0 select-none ${
        isCollapsed ? "w-20" : "w-64"
      }`}
    >
      {/* 1. Phần Đầu: Branding & Nút Đóng/Mở Xổ ra vào */}
      <div
        className={`flex items-center border-b border-slate-800/80 h-[73px] transition-all duration-300 ${
          isCollapsed ? "justify-center px-2" : "justify-between px-4"
        }`}
      >
        {!isCollapsed ? (
          <>
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20">
                <TrendingUp className="h-6 w-6 stroke-[2.5]" />
              </div>
              <div className="flex flex-col overflow-hidden transition-opacity duration-300">
                <span className="text-base font-extrabold tracking-tight text-slate-100 whitespace-nowrap">
                  STOCK<span className="text-emerald-400">PULSE</span>
                </span>
                <span className="text-[10px] text-slate-400 font-medium whitespace-nowrap truncate">
                  AI Stock Prediction
                </span>
              </div>
            </div>

            <button
              onClick={() => setIsCollapsed(true)}
              title="Thu gọn thanh điều hướng"
              aria-label="Thu gọn thanh điều hướng"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-400 hover:border-slate-700 hover:bg-slate-800 hover:text-slate-100 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </>
        ) : (
          <button
            onClick={() => setIsCollapsed(false)}
            title="Mở rộng thanh điều hướng"
            aria-label="Mở rộng thanh điều hướng"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/80 text-slate-300 hover:border-emerald-500/50 hover:bg-slate-800 hover:text-emerald-400 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <PanelLeftOpen className="h-5 w-5 text-emerald-400" />
          </button>
        )}
      </div>

      {/* 2. Danh sách Menu Tabs (Dạng Cột Dọc) */}
      <div className="flex-1 px-3 py-4 overflow-y-auto">
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
    </aside>
  );
};
