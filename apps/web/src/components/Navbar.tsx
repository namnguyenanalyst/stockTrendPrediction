"use client";

import React from "react";
import {
  BarChart3,
  BrainCircuit,
  History,
  TrendingUp,
  Wifi,
  WifiOff,
} from "lucide-react";

interface NavbarProps {
  activeTab: "market" | "prediction" | "backtest";
  setActiveTab: (tab: "market" | "prediction" | "backtest") => void;
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
  apiConnected: boolean;
  onRefreshHealth: () => void;
}

const CORE_SYMBOLS = ["VIC", "VHM", "VNM", "HPG", "SSI"];

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  selectedSymbol,
  setSelectedSymbol,
  apiConnected,
  onRefreshHealth,
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

        {/* Quick Symbol Switcher */}
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/90 p-1">
          <span className="hidden px-2 text-xs font-medium text-slate-400 md:inline">
            Mã CP:
          </span>
          {CORE_SYMBOLS.map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                selectedSymbol === sym
                  ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/40"
                  : "text-slate-300 hover:bg-slate-800 hover:text-slate-100"
              }`}
            >
              {sym}
            </button>
          ))}
        </div>

        {/* API Health Indicator */}
        <div className="flex items-center gap-2">
          <button
            onClick={onRefreshHealth}
            title={apiConnected ? "Backend API Online (FastAPI: 8000)" : "Mất kết nối API (Bấm để thử lại)"}
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
              apiConnected
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-rose-500/30 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20"
            }`}
          >
            {apiConnected ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                </span>
                <Wifi className="h-3.5 w-3.5" />
                <span className="hidden md:inline">API Online</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5" />
                <span>API Offline</span>
              </>
            )}
          </button>
        </div>
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
            <span>Thị trường & Kỹ thuật</span>
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
            <span>Tín hiệu AI & Mô hình</span>
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
            <span>Giả lập Backtest T+2</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
