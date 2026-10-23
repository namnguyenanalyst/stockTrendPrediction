"use client";

import React, { useState } from "react";
import { Check, TrendingDown, TrendingUp, Minus, Sliders, X } from "lucide-react";
import { BacktestConditionFilter } from "@/lib/types";

interface BuyConditionModalProps {
  isOpen: boolean;
  onClose: () => void;
  conditions: BacktestConditionFilter;
  onApplyConditions: (conditions: BacktestConditionFilter) => void;
}

export const BuyConditionModal: React.FC<BuyConditionModalProps> = ({
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
  if (local.use_ema) count++;
  if (local.use_macd) count++;
  if (local.use_rsi) count++;
  if (local.use_bb) count++;
  if (local.use_volume_spike) count++;
  if (local.use_price_increase) count++;
  if (local.max_pe) count++;
  if (local.max_pb) count++;
  if (local.min_roe) count++;
  if (local.foreign_net_buy) count++;
  if (local.prop_net_buy) count++;

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
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-xs font-bold text-emerald-400">
              M
            </span>
            <h3 className="text-base font-bold text-slate-100">Thêm điều kiện Mua</h3>
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
        <div className="flex-1 space-y-6 overflow-y-auto px-6 py-4 text-xs text-slate-300">
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

            {/* Thông tin Cổ phiếu */}
            <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Thông tin Cổ phiếu
              </span>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_price_increase || false}
                    onChange={(e) => setLocal({ ...local, use_price_increase: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>Giá T0 so với giá T-1 (Tăng)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_volume_spike || false}
                    onChange={(e) => setLocal({ ...local, use_volume_spike: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>%KLGD đột biến (&gt;1.2x SMA20)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={Boolean(local.max_pe)}
                    onChange={(e) => setLocal({ ...local, max_pe: e.target.checked ? 18.0 : null })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>Định giá P/E hấp dẫn (&le;18)</span>
                </label>
              </div>
            </div>

            {/* Chỉ số kỹ thuật Cổ phiếu */}
            <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Chỉ số kỹ thuật Cổ phiếu
              </span>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_ma || false}
                    onChange={(e) => setLocal({ ...local, use_ma: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>MA (Giá &gt; SMA20)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_ema || false}
                    onChange={(e) => setLocal({ ...local, use_ema: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>EMA (EMA12 cắt lên EMA26)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_macd || false}
                    onChange={(e) => setLocal({ ...local, use_macd: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>MACD (12, 26, 9) cắt lên Signal</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_rsi || false}
                    onChange={(e) => setLocal({ ...local, use_rsi: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>RSI (14) Quá bán (&le;45) hồi phục</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_bb || false}
                    onChange={(e) => setLocal({ ...local, use_bb: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>Giá chạm dải dưới Bollinger Bands</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={Boolean(local.max_pb)}
                    onChange={(e) => setLocal({ ...local, max_pb: e.target.checked ? 2.5 : null })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>P/B hợp lý (&le;2.5)</span>
                </label>
              </div>
            </div>

            {/* Dòng tiền Cổ phiếu */}
            <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Dòng tiền Cổ phiếu
              </span>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.foreign_net_buy || false}
                    onChange={(e) => setLocal({ ...local, foreign_net_buy: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>GTGD nước ngoài mua ròng (Tỷ)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.prop_net_buy || false}
                    onChange={(e) => setLocal({ ...local, prop_net_buy: e.target.checked })}
                    className="accent-emerald-500 rounded h-3.5 w-3.5"
                  />
                  <span>GTGD tự doanh mua ròng (Tỷ)</span>
                </label>
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
            className="flex items-center gap-2 rounded-lg bg-emerald-500 px-5 py-2 text-xs font-bold text-slate-950 hover:bg-emerald-400 shadow-lg shadow-emerald-500/20 transition-all"
          >
            <Check className="h-4 w-4" />
            <span>Áp dụng điều kiện Mua ({count})</span>
          </button>
        </div>
      </div>
    </div>
  );
};
