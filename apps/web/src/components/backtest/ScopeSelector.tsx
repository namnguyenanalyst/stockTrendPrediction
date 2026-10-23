"use client";

import React from "react";
import { Crown, Layers, PieChart, TrendingUp, X } from "lucide-react";
import { BacktestScopeType, SectorItem, StockSymbolInfo } from "@/lib/types";

interface ScopeSelectorProps {
  scopeType: BacktestScopeType;
  onChangeScopeType: (scope: BacktestScopeType) => void;
  selectedSymbol: string;
  onChangeSymbol: (symbol: string) => void;
  selectedIndex: string;
  onChangeIndex: (index: string) => void;
  selectedSector: string;
  onChangeSector: (sector: string) => void;
  portfolioSymbols: string[];
  onChangePortfolioSymbols: (symbols: string[]) => void;
  symbols: StockSymbolInfo[];
  sectors: SectorItem[];
}

export const ScopeSelector: React.FC<ScopeSelectorProps> = ({
  scopeType,
  onChangeScopeType,
  selectedSymbol,
  onChangeSymbol,
  selectedIndex,
  onChangeIndex,
  selectedSector,
  onChangeSector,
  portfolioSymbols,
  onChangePortfolioSymbols,
  symbols,
  sectors,
}) => {
  const togglePortfolioSymbol = (sym: string) => {
    if (portfolioSymbols.includes(sym)) {
      if (portfolioSymbols.length > 1) {
        onChangePortfolioSymbols(portfolioSymbols.filter((s) => s !== sym));
      }
    } else {
      onChangePortfolioSymbols([...portfolioSymbols, sym]);
    }
  };

  return (
    <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
      {/* 4 Radio buttons chuẩn DNSE */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {/* 1. Rổ chỉ số */}
        <label
          className={`flex items-center gap-2 cursor-pointer rounded-lg border px-3 py-2 text-xs font-semibold transition-all ${
            scopeType === "index"
              ? "border-emerald-500 bg-emerald-500/10 text-emerald-400 shadow-sm shadow-emerald-500/10"
              : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <input
            type="radio"
            name="scope_type"
            checked={scopeType === "index"}
            onChange={() => onChangeScopeType("index")}
            className="accent-emerald-500 h-3.5 w-3.5 cursor-pointer"
          />
          <Layers className="h-3.5 w-3.5 text-emerald-400" />
          <span>Rổ chỉ số</span>
        </label>

        {/* 2. Cổ phiếu */}
        <label
          className={`flex items-center gap-2 cursor-pointer rounded-lg border px-3 py-2 text-xs font-semibold transition-all ${
            scopeType === "stock"
              ? "border-emerald-500 bg-emerald-500/10 text-emerald-400 shadow-sm shadow-emerald-500/10"
              : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <input
            type="radio"
            name="scope_type"
            checked={scopeType === "stock"}
            onChange={() => onChangeScopeType("stock")}
            className="accent-emerald-500 h-3.5 w-3.5 cursor-pointer"
          />
          <TrendingUp className="h-3.5 w-3.5 text-cyan-400" />
          <span>Cổ phiếu</span>
        </label>

        {/* 3. Danh mục */}
        <label
          className={`flex items-center gap-2 cursor-pointer rounded-lg border px-3 py-2 text-xs font-semibold transition-all ${
            scopeType === "portfolio"
              ? "border-emerald-500 bg-emerald-500/10 text-emerald-400 shadow-sm shadow-emerald-500/10"
              : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <input
            type="radio"
            name="scope_type"
            checked={scopeType === "portfolio"}
            onChange={() => onChangeScopeType("portfolio")}
            className="accent-emerald-500 h-3.5 w-3.5 cursor-pointer"
          />
          <PieChart className="h-3.5 w-3.5 text-purple-400" />
          <span>Danh mục</span>
        </label>

        {/* 4. Ngành (Vương miện DNSE) */}
        <label
          className={`flex items-center gap-2 cursor-pointer rounded-lg border px-3 py-2 text-xs font-semibold transition-all ${
            scopeType === "sector"
              ? "border-amber-500 bg-amber-500/10 text-amber-400 shadow-sm shadow-amber-500/10"
              : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <input
            type="radio"
            name="scope_type"
            checked={scopeType === "sector"}
            onChange={() => onChangeScopeType("sector")}
            className="accent-amber-500 h-3.5 w-3.5 cursor-pointer"
          />
          <Crown className="h-3.5 w-3.5 text-amber-400" />
          <span>Ngành</span>
        </label>
      </div>

      {/* Input / Dropdown tương ứng cho từng lựa chọn Scope */}
      <div className="pt-1">
        {scopeType === "index" && (
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">
              Chọn rổ chỉ số mục tiêu
            </label>
            <select
              value={selectedIndex}
              onChange={(e) => onChangeIndex(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
            >
              <option value="VN30">VN30 (Rổ 30 cổ phiếu vốn hóa lớn nhất)</option>
              <option value="VN100">VN100 (Rổ 100 cổ phiếu hàng đầu HSX)</option>
              <option value="VNINDEX">VN-Index (Toàn sàn HoSE)</option>
            </select>
          </div>
        )}

        {scopeType === "stock" && (
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">
              Chọn cổ phiếu kiểm thử ({symbols.length} mã có sẵn)
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => onChangeSymbol(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
            >
              {symbols.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol} - {s.name} ({s.sector || "HOSE"})
                </option>
              ))}
            </select>
          </div>
        )}

        {scopeType === "sector" && (
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">
              Chọn nhóm ngành nghề
            </label>
            <select
              value={selectedSector}
              onChange={(e) => onChangeSector(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-amber-500 focus:outline-none"
            >
              {sectors.map((sec) => (
                <option key={sec.sector} value={sec.sector}>
                  {sec.sector} ({sec.count} cổ phiếu: {sec.symbols.slice(0, 5).join(", ")}
                  {sec.symbols.length > 5 ? "..." : ""})
                </option>
              ))}
            </select>
          </div>
        )}

        {scopeType === "portfolio" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-medium text-slate-400">
                Các mã trong danh mục ({portfolioSymbols.length} mã đã chọn):
              </label>
              <span className="text-[10px] text-slate-500">Tích chọn để thêm/bớt</span>
            </div>
            
            {/* Badges các mã đang chọn */}
            <div className="flex flex-wrap gap-1.5 p-2 rounded-lg bg-slate-950 border border-slate-800 min-h-[38px]">
              {portfolioSymbols.map((sym) => (
                <span
                  key={sym}
                  className="inline-flex items-center gap-1 rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-bold text-emerald-400 border border-emerald-500/30"
                >
                  {sym}
                  <button
                    type="button"
                    onClick={() => togglePortfolioSymbol(sym)}
                    className="hover:text-rose-400 text-slate-400 ml-0.5"
                    title="Xóa khỏi danh mục"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>

            {/* Quick Picker Buttons */}
            <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto pt-1">
              {symbols.map((s) => {
                const isSelected = portfolioSymbols.includes(s.symbol);
                return (
                  <button
                    key={s.symbol}
                    type="button"
                    onClick={() => togglePortfolioSymbol(s.symbol)}
                    className={`rounded px-2 py-0.5 text-[11px] font-semibold border transition-all ${
                      isSelected
                        ? "bg-slate-800 text-slate-500 border-slate-700 line-through opacity-60"
                        : "bg-slate-900 text-slate-300 border-slate-800 hover:border-emerald-500/50 hover:text-emerald-400"
                    }`}
                  >
                    + {s.symbol}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
