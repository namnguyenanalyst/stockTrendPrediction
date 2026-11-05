"use client";

import React from "react";
import { Loader2 } from "lucide-react";

export const BacktestResultSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 animate-fade-in">
      {/* Banner thông báo trạng thái đang chạy kiểm thử */}
      <div className="flex flex-col gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 sm:flex-row sm:items-center sm:justify-between text-xs animate-pulse">
        <div className="flex items-center gap-2.5">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-400 shrink-0" />
          <span className="font-semibold text-emerald-300">
            Đang phân tích vi cấu trúc lệnh, trượt giá và tính toán PnL qua từng phiên giao dịch...
          </span>
        </div>
        <span className="text-[11px] font-mono text-emerald-400/80">Vui lòng đợi giây lát</span>
      </div>

      {/* THẺ TỔNG QUAN HIỆU QUẢ GIAO DỊCH & BIỂU ĐỒ DONUT WIN/LOSS SKELETON */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-sm">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* BÊN TRÁI: KHUNG TRÒN DONUT SKELETON */}
          <div className="md:col-span-4 flex flex-col items-center justify-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="relative flex h-24 w-24 items-center justify-center">
              <div className="h-22 w-22 rounded-full border-4 border-slate-800 border-t-emerald-500/60 animate-spin" />
              <div className="absolute flex flex-col items-center justify-center text-center">
                <div className="h-4 w-10 bg-slate-800 rounded animate-pulse mb-1" />
                <div className="h-2 w-12 bg-slate-800/70 rounded animate-pulse" />
              </div>
            </div>
            {/* Chú thích Donut skeleton */}
            <div className="mt-2.5 flex items-center gap-3">
              <div className="h-3 w-16 bg-slate-800 rounded animate-pulse" />
              <div className="h-3 w-16 bg-slate-800 rounded animate-pulse" />
            </div>
          </div>

          {/* BÊN PHẢI: 4 THẺ THÔNG SỐ GIAO DỊCH SKELETON */}
          <div className="md:col-span-8 grid grid-cols-2 gap-2.5">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-800 bg-slate-950/80 p-2.5 space-y-2 animate-pulse"
              >
                <div className="flex items-center justify-between">
                  <div className="h-3 w-20 bg-slate-800 rounded" />
                  <div className="h-3 w-8 bg-slate-800/60 rounded" />
                </div>
                <div className="h-6 w-24 bg-slate-800/90 rounded" />
                <div className="h-2.5 w-32 bg-slate-800/50 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* LƯỚI 5 CHỈ SỐ ĐỊNH LƯỢNG CỐT LÕI SKELETON */}
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-800 bg-slate-900/80 p-3 space-y-2 animate-pulse"
          >
            <div className="flex items-center justify-between">
              <div className="h-3 w-16 bg-slate-800 rounded" />
              <div className="h-3.5 w-3.5 bg-slate-800 rounded-full" />
            </div>
            <div className="h-5 w-20 bg-slate-800/90 rounded" />
            <div className="h-2.5 w-24 bg-slate-800/60 rounded" />
          </div>
        ))}
      </div>

      {/* BIỂU ĐỒ ĐƯỜNG CONG TÀI SẢN SKELETON */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3.5">
        {/* Header tabs skeleton */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <div className="h-7 w-28 bg-slate-800 rounded-lg animate-pulse" />
            <div className="h-7 w-28 bg-slate-800/60 rounded-lg animate-pulse" />
            <div className="h-7 w-28 bg-slate-800/60 rounded-lg animate-pulse" />
          </div>
          <div className="h-3 w-24 bg-slate-800/50 rounded animate-pulse" />
        </div>

        {/* Khung vẽ biểu đồ lớn skeleton */}
        <div className="relative h-[280px] w-full rounded-lg bg-slate-950/60 border border-slate-800/80 p-4 flex flex-col justify-between overflow-hidden">
          <div className="flex justify-between items-center text-xs text-slate-600">
            <div className="h-3 w-16 bg-slate-800/60 rounded animate-pulse" />
            <div className="h-3 w-40 bg-slate-800/60 rounded animate-pulse" />
          </div>

          {/* Sóng đường nét mô phỏng nhấp nháy */}
          <div className="w-full flex items-end justify-between gap-1.5 h-36 px-2 opacity-30">
            {[40, 65, 50, 70, 85, 60, 75, 90, 80, 95, 88, 100].map((h, idx) => (
              <div
                key={idx}
                className="w-full bg-slate-700 rounded-t animate-pulse"
                style={{ height: `${h}%`, animationDelay: `${idx * 80}ms` }}
              />
            ))}
          </div>

          <div className="flex justify-between items-center text-xs text-slate-600 border-t border-slate-800/60 pt-2">
            <div className="h-2.5 w-16 bg-slate-800/50 rounded animate-pulse" />
            <div className="h-2.5 w-16 bg-slate-800/50 rounded animate-pulse" />
            <div className="h-2.5 w-16 bg-slate-800/50 rounded animate-pulse" />
          </div>
        </div>

        {/* Khung vẽ biểu đồ Drawdown nhỏ skeleton */}
        <div className="h-[90px] w-full rounded-lg bg-slate-950/60 border border-slate-800/80 p-3 flex flex-col justify-between">
          <div className="flex justify-between items-center text-[11px] text-slate-500">
            <div className="h-2.5 w-32 bg-slate-800/60 rounded animate-pulse" />
            <div className="h-2.5 w-20 bg-slate-800/60 rounded animate-pulse" />
          </div>
          <div className="h-10 w-full bg-rose-500/10 border-b border-rose-500/20 rounded animate-pulse" />
        </div>
      </div>
    </div>
  );
};
