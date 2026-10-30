"use client";

import React from "react";
import { ShieldCheck, Zap, Sparkles, TrendingUp } from "lucide-react";
import { StrategyPresetItem } from "@/lib/types";

interface StrategyPresetsListProps {
  presets: StrategyPresetItem[];
  onApplyPreset: (preset: StrategyPresetItem) => void;
  loading: boolean;
}

export const StrategyPresetsList: React.FC<StrategyPresetsListProps> = ({
  presets,
  onApplyPreset,
  loading,
}) => {
  return (
    <div className="space-y-4">
      {/* Header giới thiệu kho chiến thuật mẫu */}
      <div className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/20 text-purple-400">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100 sm:text-lg">
                Kho Thư viện 8 Chiến thuật Mẫu Thực chiến
              </h3>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                Chuẩn DNSE Entrade X
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Các kịch bản định lượng mẫu kết hợp chỉ báo kỹ thuật, dòng tiền và quy tắc quản trị rủi ro tự động.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="flex items-center gap-1 rounded bg-slate-800/80 px-2.5 py-1 border border-slate-700">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            Có sẵn Take Profit &amp; Stop Loss
          </span>
          <span className="flex items-center gap-1 rounded bg-slate-800/80 px-2.5 py-1 border border-slate-700">
            <Zap className="h-3.5 w-3.5 text-amber-400" />
            1-Click Nạp &amp; Chạy thử
          </span>
        </div>
      </div>

      {/* Lưới các thẻ Card Chiến thuật mẫu (Clean & Streamlined) */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {presets.map((preset) => {
          const conditions = preset.conditions_summary
            .split("•")
            .map((c) => c.trim())
            .filter(Boolean);

          return (
            <div
              key={preset.id}
              className="group flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/70 p-4 transition-all duration-200 hover:border-emerald-500/40 hover:bg-slate-900/90 hover:shadow-xl hover:shadow-emerald-950/20"
            >
              <div>
                {/* 1. Header Card: Tiêu đề & Category */}
                <div className="mb-2">
                  <span className="inline-block rounded bg-purple-500/10 px-2 py-0.5 text-[10px] font-semibold text-purple-300 border border-purple-500/20">
                    {preset.category}
                  </span>
                </div>

                <h4
                  className="text-sm font-bold text-slate-100 group-hover:text-emerald-400 transition-colors line-clamp-1"
                  title={preset.name}
                >
                  {preset.name}
                </h4>

                {/* 2. Điều kiện kích hoạt dạng Bulletin nổi bật */}
                <div className="mt-3 rounded-lg border border-slate-800/90 bg-slate-950/80 p-2.5 min-h-[96px] flex flex-col justify-center">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    <span>Điều kiện kích hoạt</span>
                  </div>
                  <ul className="space-y-1.5 text-[11px]">
                    {conditions.map((cond, cIdx) => (
                      <li key={cIdx} className="flex items-start gap-2 text-slate-200">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-400/90 shrink-0 shadow-sm shadow-emerald-400/40" />
                        <span className="leading-tight font-medium">{cond}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 3. Quy tắc Quản trị rủi ro & Chốt lời / Cắt lỗ */}
                <div className="mt-3 rounded-lg border border-slate-800/60 bg-slate-900/40 p-2.5 text-xs">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Quản trị rủi ro
                  </div>
                  <div className="flex items-center justify-between font-mono text-[11px]">
                    <span>
                      Chốt lời: <strong className="text-emerald-400">+{Math.round(preset.take_profit_pct * 100)}%</strong>
                    </span>
                    <span>
                      Cắt lỗ: <strong className="text-rose-400">-{Math.round(preset.stop_loss_pct * 100)}%</strong>
                    </span>
                    {preset.trailing_stop_pct > 0 && (
                      <span>
                        Trailing: <strong className="text-amber-400">{Math.round(preset.trailing_stop_pct * 100)}%</strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* 4. Footer Card: Cổ phiếu áp dụng & Nút nạp vào phòng Lab */}
              <div className="mt-4 pt-3 border-t border-slate-800/60">
                <div className="mb-2.5 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="truncate">
                    Áp dụng: <strong className="text-slate-200">{preset.target_symbols.slice(0, 4).join(", ")}</strong>
                  </span>
                </div>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => onApplyPreset(preset)}
                  className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-emerald-500/10 py-2 text-xs font-bold text-emerald-400 border border-emerald-500/30 transition-all hover:bg-emerald-500 hover:text-slate-950 active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>Nạp vào Phòng Lab &amp; Kiểm thử</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
