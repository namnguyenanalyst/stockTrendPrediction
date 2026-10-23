"use client";

import React from "react";
import { ArrowUpRight, ArrowDownRight, Radio } from "lucide-react";
import { RecentSignalItem } from "@/lib/types";

interface RecentSignalsSidebarProps {
  signals: RecentSignalItem[];
  onSelectSymbol?: (symbol: string) => void;
}

export const RecentSignalsSidebar: React.FC<RecentSignalsSidebarProps> = ({
  signals,
  onSelectSymbol,
}) => {
  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      {/* Header Panel */}
      <div className="mb-3 flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <span>Tín hiệu mới</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-300">
              {signals.length}
            </span>
          </h3>
        </div>
        <span className="text-[10px] text-slate-400">Near-realtime</span>
      </div>

      {/* Danh sách các tín hiệu */}
      <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
        {signals.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            <Radio className="mx-auto h-8 w-8 text-slate-600 mb-2 animate-pulse" />
            <p>Chưa có tín hiệu mới phát sinh</p>
          </div>
        ) : (
          signals.map((sig) => {
            const isBuy = sig.action === "BUY";
            const isSell = sig.action === "SELL";

            return (
              <div
                key={sig.signal_id}
                onClick={() => onSelectSymbol?.(sig.symbol)}
                className="group cursor-pointer rounded-lg border border-slate-800/80 bg-slate-950/60 p-2.5 transition-all hover:border-emerald-500/40 hover:bg-slate-950"
              >
                {/* Dòng 1: Mã CP, Action badge, Thời gian */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-slate-100 group-hover:text-emerald-400 transition-colors">
                      {sig.symbol}
                    </span>
                    <span
                      className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                        isBuy
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : isSell
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          : "bg-slate-800 text-slate-300 border border-slate-700"
                      }`}
                    >
                      {isBuy && <ArrowUpRight className="h-3 w-3 stroke-[2.5]" />}
                      {isSell && <ArrowDownRight className="h-3 w-3 stroke-[2.5]" />}
                      {sig.action}
                    </span>
                  </div>

                  <span className="text-[10px] text-slate-400 font-mono">
                    {sig.timestamp}
                  </span>
                </div>

                {/* Dòng 2: Tên chiến thuật */}
                <p className="mt-1 text-[11px] font-medium text-slate-300 line-clamp-1">
                  {sig.strategy_name}
                </p>

                {/* Dòng 3: Giá khuyến nghị & Độ tin cậy AI */}
                <div className="mt-2 flex items-center justify-between border-t border-slate-800/60 pt-1.5 text-[10px]">
                  <div>
                    <span className="text-slate-400">Giá: </span>
                    <strong className="text-slate-200">
                      {(sig.price).toLocaleString("vi-VN")} đ
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Mục tiêu: </span>
                    <strong className="text-emerald-400">
                      {(sig.target_price).toLocaleString("vi-VN")} đ
                    </strong>
                  </div>
                </div>

                {/* Dòng 4: Status badge */}
                <div className="mt-1.5 flex items-center justify-between text-[10px]">
                  <span className="text-slate-400">
                    Cắt lỗ: <strong className="text-rose-400">{(sig.stop_price).toLocaleString("vi-VN")} đ</strong>
                  </span>
                  <span className="rounded bg-slate-800/90 px-1.5 py-0.5 text-[9px] font-semibold text-slate-300">
                    {sig.status}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
