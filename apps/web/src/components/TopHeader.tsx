"use client";

import React from "react";
import {
  BarChart3,
  BrainCircuit,
  History,
} from "lucide-react";

interface TopHeaderProps {
  activeTab: "market" | "prediction" | "backtest";
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
}

const CORE_SYMBOLS = ["VIC", "HPG", "FPT", "VNM", "MWG"];

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

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex w-full items-center justify-between px-4 py-3 sm:px-6">
        {/* Bên Trái: Tiêu đề Tab hiện tại */}
        <div className="flex items-center gap-3">

          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight text-slate-100 sm:text-base">
                {currentTabInfo.title}
              </h1>
              <p className="hidden text-[11px] text-slate-400 md:block">
                {currentTabInfo.subtitle}
              </p>
            </div>
          </div>
        </div>

        {/* Bên Phải: Bộ chọn mã cổ phiếu nhanh (Chỉ hiển thị ở Tab 2 Dự báo và Tab 3 Kiểm thử, ẩn ở Tab 1 Tổng quan thị trường) */}
        {activeTab !== "market" && (
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/90 p-1 shadow-inner">
            <span className="hidden px-2 text-xs font-medium text-slate-400 sm:inline">
              Mã CP:
            </span>
            {CORE_SYMBOLS.map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`rounded-lg px-2.5 py-1 text-xs font-bold transition-all ${
                  selectedSymbol === sym
                    ? "bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/40 scale-105"
                    : "text-slate-300 hover:bg-slate-800 hover:text-slate-100"
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
};
