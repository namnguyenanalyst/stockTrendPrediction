"use client";

import React from "react";
import { Copy, ShieldCheck, Zap, Sparkles, TrendingUp } from "lucide-react";
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
              Các chiến thuật định lượng đã kiểm định lịch sử, kết hợp chỉ báo kỹ thuật, dòng tiền và bộ quy tắc quản trị rủi ro tự động.
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
            1-Click Áp dụng
          </span>
        </div>
      </div>

      {/* Lưới các thẻ Card Chiến thuật mẫu (3 cột chuẩn responsive) */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {presets.map((preset) => {
          const winRate = preset.win_rate_pct;

          return (
            <div
              key={preset.id}
              className="group flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/70 p-4 transition-all duration-200 hover:border-emerald-500/40 hover:bg-slate-900/90 hover:shadow-xl hover:shadow-emerald-950/20"
            >
              <div>
                {/* 1. Header Card: Tiêu đề & Category */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="inline-block rounded bg-purple-500/10 px-2 py-0.5 text-[10px] font-semibold text-purple-300 border border-purple-500/20 mb-1.5">
                      {preset.category}
                    </span>
                    <h4 className="text-sm font-bold text-slate-100 group-hover:text-emerald-400 transition-colors line-clamp-1" title={preset.name}>
                      {preset.name}
                    </h4>
                  </div>
                </div>

                {/* 2. Điều kiện tóm tắt */}
                <div className="mt-2.5 rounded-lg border border-slate-800/90 bg-slate-950/60 p-2 text-[11px] text-slate-300">
                  <p className="line-clamp-2 leading-relaxed" title={preset.conditions_summary}>
                    {preset.conditions_summary}
                  </p>
                </div>

                {/* 3. Phần chỉ số định lượng: Donut Win Rate, Lãi lũy kế, Tỷ lệ R/R */}
                <div className="mt-4 flex items-center justify-between border-y border-slate-800/80 py-3">
                  {/* Gauge Donut Chart tỷ lệ thắng */}
                  <div className="flex items-center gap-2.5">
                    <div className="relative flex h-14 w-14 items-center justify-center">
                      <svg className="h-14 w-14 -rotate-90 transform">
                        {/* Background circle */}
                        <circle
                          cx="28"
                          cy="28"
                          r="22"
                          stroke="currentColor"
                          strokeWidth="4"
                          className="text-rose-500/25"
                          fill="transparent"
                        />
                        {/* Progress circle */}
                        <circle
                          cx="28"
                          cy="28"
                          r="22"
                          stroke="currentColor"
                          strokeWidth="4.5"
                          strokeDasharray={2 * Math.PI * 22}
                          strokeDashoffset={2 * Math.PI * 22 * (1 - winRate / 100)}
                          strokeLinecap="round"
                          className="text-emerald-400 transition-all duration-700"
                          fill="transparent"
                        />
                      </svg>
                      <div className="absolute text-center">
                        <span className="text-[10px] font-extrabold text-slate-100">
                          {winRate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div>
                      <span className="block text-[10px] font-medium text-slate-400">Tỷ lệ thắng</span>
                      <span className="text-xs font-bold text-emerald-400">
                        {winRate >= 60 ? "Cao" : "Ổn định"}
                      </span>
                    </div>
                  </div>

                  {/* Lãi lũy kế & Tỷ lệ Rủi ro/Lợi nhuận */}
                  <div className="text-right space-y-1">
                    <div>
                      <span className="block text-[10px] text-slate-400">Lãi/lỗ luỹ kế</span>
                      <span className="text-sm font-black text-emerald-400">
                        +{preset.cumulative_pnl_pct.toFixed(2)}%
                      </span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-400">Tỷ lệ rủi ro / LN</span>
                      <span className="text-[11px] font-semibold text-slate-200">
                        {preset.risk_reward_ratio}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 4. Quy tắc Chốt lời / Cắt lỗ đi kèm */}
                <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Chốt lời: <strong className="text-emerald-400">+{Math.round(preset.take_profit_pct * 100)}%</strong></span>
                  <span>Cắt lỗ: <strong className="text-rose-400">-{Math.round(preset.stop_loss_pct * 100)}%</strong></span>
                  {preset.trailing_stop_pct > 0 && (
                    <span>Trailing: <strong className="text-amber-400">{Math.round(preset.trailing_stop_pct * 100)}%</strong></span>
                  )}
                </div>
              </div>

              {/* 5. Footer Card: Nhóm cổ phiếu, Lượt sao chép & Nút hành động */}
              <div className="mt-4 pt-3 border-t border-slate-800/60">
                <div className="mb-2.5 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="truncate max-w-[150px]">
                    Nhóm CP: <strong className="text-slate-200">{preset.target_symbols.slice(0, 3).join(", ")}</strong>
                  </span>
                  <span className="flex items-center gap-1 font-mono text-slate-400">
                    <Copy className="h-3 w-3 text-slate-500" />
                    {preset.copy_count} lượt
                  </span>
                </div>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => onApplyPreset(preset)}
                  className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-emerald-500/10 py-2 text-xs font-bold text-emerald-400 border border-emerald-500/30 transition-all hover:bg-emerald-500 hover:text-slate-950 active:scale-95 disabled:opacity-50"
                >
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>Áp dụng &amp; Kiểm thử ngay</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
