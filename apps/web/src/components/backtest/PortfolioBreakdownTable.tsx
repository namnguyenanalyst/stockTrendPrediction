"use client";

import React, { useState } from "react";
import { ArrowUpDown, ChevronRight, Eye } from "lucide-react";
import { SymbolBreakdownItem } from "@/lib/types";

interface PortfolioBreakdownTableProps {
  items: SymbolBreakdownItem[];
  selectedSymbol?: string | null;
  onSelectSymbol: (symbol: string) => void;
}

export const PortfolioBreakdownTable: React.FC<PortfolioBreakdownTableProps> = ({
  items,
  selectedSymbol,
  onSelectSymbol,
}) => {
  const [sortField, setSortField] = useState<keyof SymbolBreakdownItem>("roi_pct");
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const handleSort = (field: keyof SymbolBreakdownItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedItems = [...items].sort((a, b) => {
    const valA = a[sortField];
    const valB = b[sortField];
    if (typeof valA === "number" && typeof valB === "number") {
      return sortAsc ? valA - valB : valB - valA;
    }
    return sortAsc
      ? String(valA).localeCompare(String(valB))
      : String(valB).localeCompare(String(valA));
  });

  return (
    <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-emerald-400" />
          <h4 className="text-sm font-bold text-slate-100">
            Bảng phân rã chi tiết hiệu quả từng cổ phiếu ({items.length} mã)
          </h4>
        </div>
        <span className="text-[11px] text-slate-400">
          Nhấn vào từng dòng để xem biểu đồ và nhật ký lệnh riêng
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/70">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-800 bg-slate-900/90 text-slate-400">
            <tr>
              <th
                onClick={() => handleSort("symbol")}
                className="cursor-pointer px-3 py-2.5 font-bold hover:text-slate-200"
              >
                <div className="flex items-center gap-1">
                  <span>Mã CP</span>
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="px-3 py-2.5 font-medium hidden md:table-cell">Tên công ty</th>
              <th className="px-3 py-2.5 font-medium hidden sm:table-cell">Ngành</th>
              <th
                onClick={() => handleSort("roi_pct")}
                className="cursor-pointer px-3 py-2.5 text-right font-bold hover:text-slate-200"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>ROI</span>
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort("bh_roi_pct")}
                className="cursor-pointer px-3 py-2.5 text-right font-medium hover:text-slate-200 hidden lg:table-cell"
              >
                <span>B&H ROI</span>
              </th>
              <th
                onClick={() => handleSort("excess_pct")}
                className="cursor-pointer px-3 py-2.5 text-right font-bold hover:text-slate-200"
              >
                <span>Alpha</span>
              </th>
              <th
                onClick={() => handleSort("sharpe")}
                className="cursor-pointer px-3 py-2.5 text-right font-medium hover:text-slate-200 hidden sm:table-cell"
              >
                <span>Sharpe</span>
              </th>
              <th
                onClick={() => handleSort("mdd_pct")}
                className="cursor-pointer px-3 py-2.5 text-right font-medium hover:text-slate-200 hidden sm:table-cell"
              >
                <span>MDD</span>
              </th>
              <th
                onClick={() => handleSort("win_rate_pct")}
                className="cursor-pointer px-3 py-2.5 text-right font-medium hover:text-slate-200"
              >
                <span>Win Rate</span>
              </th>
              <th className="px-3 py-2.5 text-right font-medium">Lệnh</th>
              <th className="px-2 py-2.5 text-center">Chi tiết</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {sortedItems.map((item) => {
              const isSelected = selectedSymbol === item.symbol;
              const isPositive = item.roi_pct >= 0;
              const isAlphaPos = item.excess_pct >= 0;

              return (
                <tr
                  key={item.symbol}
                  onClick={() => onSelectSymbol(item.symbol)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-emerald-500/10 border-l-2 border-emerald-500 text-slate-100"
                      : "hover:bg-slate-800/50 text-slate-300"
                  }`}
                >
                  <td className="px-3 py-2.5 font-bold text-slate-100">
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-emerald-400">
                      {item.symbol}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-slate-400 hidden md:table-cell max-w-[160px] truncate">
                    {item.name}
                  </td>
                  <td className="px-3 py-2.5 text-slate-400 hidden sm:table-cell">
                    <span className="rounded bg-slate-900 px-2 py-0.5 text-[11px] border border-slate-800">
                      {item.sector}
                    </span>
                  </td>
                  <td
                    className={`px-3 py-2.5 text-right font-bold ${
                      isPositive ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isPositive ? "+" : ""}
                    {item.roi_pct.toFixed(2)}%
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-400 hidden lg:table-cell">
                    {item.bh_roi_pct >= 0 ? "+" : ""}
                    {item.bh_roi_pct.toFixed(2)}%
                  </td>
                  <td
                    className={`px-3 py-2.5 text-right font-bold ${
                      isAlphaPos ? "text-cyan-400" : "text-slate-400"
                    }`}
                  >
                    {isAlphaPos ? "+" : ""}
                    {item.excess_pct.toFixed(2)}%
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-300 hidden sm:table-cell">
                    {item.sharpe.toFixed(2)}
                  </td>
                  <td className="px-3 py-2.5 text-right text-rose-400 hidden sm:table-cell">
                    -{Math.abs(item.mdd_pct).toFixed(2)}%
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-200">
                    {item.win_rate_pct.toFixed(1)}%
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-400">{item.trades}</td>
                  <td className="px-2 py-2.5 text-center text-slate-500">
                    <ChevronRight className="inline h-4 w-4 text-slate-500 hover:text-emerald-400" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
