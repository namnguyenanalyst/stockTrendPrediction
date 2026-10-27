"use client";

import React from "react";
import {
  BarChart3,
  BrainCircuit,
  History,
  TrendingUp,
} from "lucide-react";

interface NavbarProps {
  activeTab: "market" | "prediction" | "backtest";
  setActiveTab: (tab: "market" | "prediction" | "backtest") => void;
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
}

const QUICK_SYMBOLS = ["VN30", "VNINDEX", "VIC", "HPG", "FPT", "VNM", "MWG", "TCB", "SSI"];

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  selectedSymbol,
  setSelectedSymbol,
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      {/* Top Banner: Branding & Status */}
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-slate-950 shadow-lg shadow-emerald-500/20">
            <TrendingUp className="h-6 w-6 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-slate-100 sm:text-lg">
                STOCK<span className="text-emerald-400">PULSE</span> VN
              </span>
              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-300">
                AI Quant
              </span>
            </div>
            <p className="hidden text-[11px] text-slate-400 sm:block">
              Hệ thống Dự báo Xu hướng & Đánh giá Chiến lược Đầu tư • HUMG
            </p>
          </div>
        </div>

        {/* Quick Symbol Switcher (Chỉ hiển thị khi không ở Tab 1) */}
        {activeTab !== "market" && (
          <div className="flex flex-wrap items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/90 p-1">
            <span className="hidden px-2 text-xs font-medium text-slate-400 md:inline">
              Mục tiêu:
            </span>
            {QUICK_SYMBOLS.map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`rounded-md px-2 py-1 text-xs font-semibold transition-all ${
                  selectedSymbol === sym
                    ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/40"
                    : "text-slate-300 hover:bg-slate-800 hover:text-slate-100"
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="mx-auto flex max-w-7xl border-t border-slate-800/80 px-4 sm:px-6">
        <nav className="flex space-x-1 sm:space-x-2">
          <button
            onClick={() => setActiveTab("market")}
            className={`flex items-center gap-2 border-b-2 px-3 py-3 text-xs font-semibold sm:text-sm transition-all ${
              activeTab === "market"
                ? "border-emerald-400 text-emerald-400 bg-emerald-500/5"
                : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200"
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            <span>Thị trường & Bảng giá</span>
          </button>

          <button
            onClick={() => setActiveTab("prediction")}
            className={`flex items-center gap-2 border-b-2 px-3 py-3 text-xs font-semibold sm:text-sm transition-all ${
              activeTab === "prediction"
                ? "border-emerald-400 text-emerald-400 bg-emerald-500/5"
                : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200"
            }`}
          >
            <BrainCircuit className="h-4 w-4" />
            <span>Tín hiệu dự báo xu hướng</span>
          </button>

          <button
            onClick={() => setActiveTab("backtest")}
            className={`flex items-center gap-2 border-b-2 px-3 py-3 text-xs font-semibold sm:text-sm transition-all ${
              activeTab === "backtest"
                ? "border-emerald-400 text-emerald-400 bg-emerald-500/5"
                : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200"
            }`}
          >
            <History className="h-4 w-4" />
            <span>Kiểm thử chiến lược</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
