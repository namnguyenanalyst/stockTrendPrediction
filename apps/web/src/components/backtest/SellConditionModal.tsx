"use client";

import React, { useState } from "react";
import { Check, TrendingDown, TrendingUp, Minus, Sliders, X, ShieldAlert } from "lucide-react";
import { BacktestConditionFilter } from "@/lib/types";

interface SellConditionModalProps {
  isOpen: boolean;
  onClose: () => void;
  conditions: BacktestConditionFilter;
  onApplyConditions: (conditions: BacktestConditionFilter) => void;
}

export const SellConditionModal: React.FC<SellConditionModalProps> = ({
  isOpen,
  onClose,
  conditions,
  onApplyConditions,
}) => {
  const [local, setLocal] = useState<BacktestConditionFilter>({ ...conditions });

  if (!isOpen) return null;

  // Đếm số lượng điều kiện đang được chọn
  let count = 0;
  if (local.market_condition && local.market_condition !== "all") count++;
  if (local.use_ma) count++;
  if (local.use_macd) count++;
  if (local.use_rsi) count++;
  if (local.use_bb) count++;
  if (local.foreign_net_sell) count++;
  if (local.take_profit_pct !== null && local.take_profit_pct !== undefined && local.take_profit_pct > 0) count++;
  if (local.stop_loss_pct !== null && local.stop_loss_pct !== undefined && local.stop_loss_pct > 0) count++;
  if (local.trailing_stop_pct !== null && local.trailing_stop_pct !== undefined && local.trailing_stop_pct > 0) count++;

  const handleApply = () => {
    onApplyConditions(local);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative flex max-h-[90vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-rose-500/20 text-xs font-bold text-rose-400">
              B
            </span>
            <h3 className="text-base font-bold text-slate-100">Thêm điều kiện Bán</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body (Scrollable) */}
        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-4 text-xs text-slate-300">
          {/* Thanh chọn logic kết nối điều kiện Bán: HOẶC (OR - mặc định) vs VÀ (AND) */}
          <div className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-950/80 p-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-200">Logic kết nối điều kiện Bán:</span>
              <span className="text-[11px] text-slate-400">
                {local.condition_logic === "AND"
                  ? "Bán khi thỏa mãn ĐỒNG THỜI tất cả điều kiện"
                  : "Bán ngay khi vi phạm BẤT KỲ điều kiện nào (Khuyến nghị)"}
              </span>
            </div>
            <div className="flex items-center gap-1 rounded-lg bg-slate-900 p-1 border border-slate-800">
              <button
                type="button"
                onClick={() => setLocal({ ...local, condition_logic: "OR" })}
                className={`rounded-md px-3 py-1 text-xs font-bold transition-all ${
                  (!local.condition_logic || local.condition_logic === "OR")
                    ? "bg-rose-500 text-slate-100 shadow-md shadow-rose-500/20"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                HOẶC (OR)
              </button>
              <button
                type="button"
                onClick={() => setLocal({ ...local, condition_logic: "AND" })}
                className={`rounded-md px-3 py-1 text-xs font-bold transition-all ${
                  local.condition_logic === "AND"
                    ? "bg-amber-400 text-slate-950 shadow-md shadow-amber-400/20"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                VÀ (AND)
              </button>
            </div>
          </div>

          {/* 1. Chọn điều kiện VNIndex (Không bắt buộc) */}
          <div className="space-y-2">
            <h4 className="font-semibold text-slate-200">
              Chọn điều kiện VNIndex (Không bắt buộc)
            </h4>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <button
                type="button"
                onClick={() =>
                  setLocal({
                    ...local,
                    market_condition: local.market_condition === "uptrend" ? "all" : "uptrend",
                  })
                }
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all ${
                  local.market_condition === "uptrend"
                    ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                }`}
              >
                <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                <span>Tăng</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setLocal({
                    ...local,
                    market_condition: local.market_condition === "sideways" ? "all" : "sideways",
                  })
                }
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all ${
                  local.market_condition === "sideways"
                    ? "border-amber-500 bg-amber-500/20 text-amber-400"
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Minus className="h-3.5 w-3.5 text-amber-400" />
                <span>Đi ngang</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setLocal({
                    ...local,
                    market_condition: local.market_condition === "downtrend" ? "all" : "downtrend",
                  })
                }
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all ${
                  local.market_condition === "downtrend"
                    ? "border-rose-500 bg-rose-500/20 text-rose-400"
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                }`}
              >
                <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                <span>Giảm</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setLocal({
                    ...local,
                    market_condition: "all",
                  })
                }
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all ${
                  !local.market_condition || local.market_condition === "all"
                    ? "border-cyan-500 bg-cyan-500/20 text-cyan-400"
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Sliders className="h-3.5 w-3.5" />
                <span>Tất cả</span>
              </button>
            </div>
          </div>

          {/* 2. Điều kiện Cổ phiếu */}
          <div className="space-y-4">
            <h4 className="font-bold text-slate-100 text-sm">Điều kiện Cổ phiếu</h4>

            {/* Chỉ số kỹ thuật Cổ phiếu */}
            <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Chỉ số kỹ thuật Cổ phiếu
              </span>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_ma || false}
                    onChange={(e) => setLocal({ ...local, use_ma: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5"
                  />
                  <span>MA (Giá cắt xuống SMA20)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_macd || false}
                    onChange={(e) => setLocal({ ...local, use_macd: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5"
                  />
                  <span>MACD (12, 26, 9) cắt xuống Signal</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_rsi || false}
                    onChange={(e) => setLocal({ ...local, use_rsi: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5"
                  />
                  <span>RSI (14) Quá mua (&ge;70) quay đầu</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_bb || false}
                    onChange={(e) => setLocal({ ...local, use_bb: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5"
                  />
                  <span>Giá chạm dải trên Bollinger Bands</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.foreign_net_sell || false}
                    onChange={(e) => setLocal({ ...local, foreign_net_sell: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5"
                  />
                  <span>Khối ngoại bán ròng đột biến</span>
                </label>
              </div>
            </div>

            {/* Quản trị rủi ro (Take Profit, Stop Loss, Trailing Stop) */}
            <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-emerald-400" />
                <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                  Quản trị rủi ro tự động (DNSE Risk Guard)
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* Chốt lời */}
                <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-semibold text-xs">
                    <input
                      type="checkbox"
                      checked={Boolean(local.take_profit_pct && local.take_profit_pct > 0)}
                      onChange={(e) =>
                        setLocal({
                          ...local,
                          take_profit_pct: e.target.checked ? 0.15 : null,
                        })
                      }
                      className="accent-emerald-500 rounded h-3.5 w-3.5"
                    />
                    <span>Chốt lời (Take Profit)</span>
                  </label>
                  {Boolean(local.take_profit_pct && local.take_profit_pct > 0) && (
                    <div className="flex items-center gap-1.5 pt-1">
                      <input
                        type="number"
                        step="1"
                        min="1"
                        max="100"
                        value={Math.round((local.take_profit_pct || 0.15) * 100)}
                        onChange={(e) =>
                          setLocal({
                            ...local,
                            take_profit_pct: Number(e.target.value) / 100,
                          })
                        }
                        className="w-16 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs font-bold text-emerald-400 focus:outline-none"
                      />
                      <span className="text-slate-400 text-xs">%</span>
                    </div>
                  )}
                </div>

                {/* Cắt lỗ */}
                <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-semibold text-xs">
                    <input
                      type="checkbox"
                      checked={Boolean(local.stop_loss_pct && local.stop_loss_pct > 0)}
                      onChange={(e) =>
                        setLocal({
                          ...local,
                          stop_loss_pct: e.target.checked ? 0.07 : null,
                        })
                      }
                      className="accent-rose-500 rounded h-3.5 w-3.5"
                    />
                    <span>Cắt lỗ (Stop Loss)</span>
                  </label>
                  {Boolean(local.stop_loss_pct && local.stop_loss_pct > 0) && (
                    <div className="flex items-center gap-1.5 pt-1">
                      <input
                        type="number"
                        step="1"
                        min="1"
                        max="50"
                        value={Math.round((local.stop_loss_pct || 0.07) * 100)}
                        onChange={(e) =>
                          setLocal({
                            ...local,
                            stop_loss_pct: Number(e.target.value) / 100,
                          })
                        }
                        className="w-16 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs font-bold text-rose-400 focus:outline-none"
                      />
                      <span className="text-slate-400 text-xs">%</span>
                    </div>
                  )}
                </div>

                {/* Trailing Stop */}
                <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-semibold text-xs">
                    <input
                      type="checkbox"
                      checked={Boolean(local.trailing_stop_pct && local.trailing_stop_pct > 0)}
                      onChange={(e) =>
                        setLocal({
                          ...local,
                          trailing_stop_pct: e.target.checked ? 0.05 : null,
                        })
                      }
                      className="accent-amber-500 rounded h-3.5 w-3.5"
                    />
                    <span>Trailing Stop</span>
                  </label>
                  {Boolean(local.trailing_stop_pct && local.trailing_stop_pct > 0) && (
                    <div className="flex items-center gap-1.5 pt-1">
                      <input
                        type="number"
                        step="1"
                        min="1"
                        max="30"
                        value={Math.round((local.trailing_stop_pct || 0.05) * 100)}
                        onChange={(e) =>
                          setLocal({
                            ...local,
                            trailing_stop_pct: Number(e.target.value) / 100,
                          })
                        }
                        className="w-16 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs font-bold text-amber-400 focus:outline-none"
                      />
                      <span className="text-slate-400 text-xs">% từ đỉnh</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t border-slate-800 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleApply}
            className="flex items-center gap-2 rounded-lg bg-rose-500 px-5 py-2 text-xs font-bold text-white hover:bg-rose-600 shadow-lg shadow-rose-500/20 transition-all"
          >
            <Check className="h-4 w-4" />
            <span>Áp dụng điều kiện Bán ({count})</span>
          </button>
        </div>
      </div>
    </div>
  );
};
