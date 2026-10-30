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
  if (local.use_price_cross) count++;
  if (local.use_rsi) count++;
  if (local.foreign_net_sell_val || local.foreign_net_sell) count++;
  if (local.prop_net_sell_vol) count++;
  if (local.use_adx) count++;
  if (local.use_ema) count++;
  if (local.foreign_net_sell_vol) count++;
  if (local.use_rs) count++;
  if (local.use_macd) count++;
  if (local.prop_net_sell_val) count++;
  if (local.take_profit_pct !== null && local.take_profit_pct !== undefined && local.take_profit_pct > 0) count++;
  if (local.stop_loss_pct !== null && local.stop_loss_pct !== undefined && local.stop_loss_pct > 0) count++;
  if (local.trailing_stop_pct !== null && local.trailing_stop_pct !== undefined && local.trailing_stop_pct > 0) count++;

  const handleApply = () => {
    const updated: BacktestConditionFilter = { ...local };

    // Điền giá trị mặc định chuẩn DNSE cho các điều kiện vừa kích hoạt
    if (updated.use_ma) {
      if (!updated.ma_left) updated.ma_left = "MA 10";
      if (!updated.ma_operator) updated.ma_operator = "Cắt lên";
      if (!updated.ma_right) updated.ma_right = "MA 10";
    }

    if (updated.use_price_cross) {
      if (!updated.price_cross_operator) updated.price_cross_operator = "Cắt lên";
      if (!updated.price_cross_target) updated.price_cross_target = "MA 10";
    }

    if (updated.use_rsi) {
      if (updated.rsi_min === undefined || updated.rsi_min === null) updated.rsi_min = 0.0;
      if (updated.rsi_max === undefined || updated.rsi_max === null) updated.rsi_max = 100.0;
    }

    if (updated.foreign_net_sell_val) {
      if (updated.min_foreign_sell_val === undefined || updated.min_foreign_sell_val === null) updated.min_foreign_sell_val = 0;
      if (updated.max_foreign_sell_val === undefined || updated.max_foreign_sell_val === null) updated.max_foreign_sell_val = 9817;
    }

    if (updated.prop_net_sell_vol) {
      if (updated.min_prop_sell_vol === undefined || updated.min_prop_sell_vol === null) updated.min_prop_sell_vol = 0;
      if (updated.max_prop_sell_vol === undefined || updated.max_prop_sell_vol === null) updated.max_prop_sell_vol = 50.0;
    }

    if (updated.use_adx) {
      if (updated.min_adx === undefined || updated.min_adx === null) updated.min_adx = 0.0;
      if (updated.max_adx === undefined || updated.max_adx === null) updated.max_adx = 100.0;
    }

    if (updated.use_ema) {
      if (!updated.ema_left) updated.ema_left = "EMA 10";
      if (!updated.ema_operator) updated.ema_operator = "Cắt lên";
      if (!updated.ema_right) updated.ema_right = "EMA 10";
    }

    if (updated.foreign_net_sell_vol) {
      if (updated.min_foreign_sell_vol === undefined || updated.min_foreign_sell_vol === null) updated.min_foreign_sell_vol = 0;
      if (updated.max_foreign_sell_vol === undefined || updated.max_foreign_sell_vol === null) updated.max_foreign_sell_vol = 300.0;
    }

    if (updated.use_rs) {
      if (updated.min_rs === undefined || updated.min_rs === null) updated.min_rs = 0.0;
      if (updated.max_rs === undefined || updated.max_rs === null) updated.max_rs = 99.93;
    }

    if (updated.use_macd) {
      if (!updated.macd_operator) updated.macd_operator = "Cắt lên";
      if (!updated.macd_target) updated.macd_target = "Đường tín hiệu";
    }

    if (updated.prop_net_sell_val) {
      if (updated.min_prop_sell_val === undefined || updated.min_prop_sell_val === null) updated.min_prop_sell_val = 0;
      if (updated.max_prop_sell_val === undefined || updated.max_prop_sell_val === null) updated.max_prop_sell_val = 48633;
    }

    onApplyConditions(updated);
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
            <h3 className="text-base font-bold text-slate-100">Thêm điều kiện Bán ({count})</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors cursor-pointer"
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
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors cursor-pointer ${
                  (!local.condition_logic || local.condition_logic === "OR")
                    ? "bg-rose-600 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                HOẶC (OR)
              </button>
              <button
                type="button"
                onClick={() => setLocal({ ...local, condition_logic: "AND" })}
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors cursor-pointer ${
                  local.condition_logic === "AND"
                    ? "bg-amber-500 text-slate-950"
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
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all cursor-pointer ${
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
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all cursor-pointer ${
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
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all cursor-pointer ${
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
                className={`flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-semibold transition-all cursor-pointer ${
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

          {/* 2. Điều kiện Cổ phiếu (11 tiêu chí chuẩn DNSE) */}
          <div className="space-y-4">
            <h4 className="font-bold text-slate-100 text-sm">Điều kiện Cổ phiếu (11 chỉ báo)</h4>

            <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Chỉ số kỹ thuật & Dòng tiền
              </span>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {/* 1. MA */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_ma || false}
                    onChange={(e) => setLocal({ ...local, use_ma: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>MA (Đường trung bình động)</span>
                </label>

                {/* 2. Giá cắt đường MA/EMA/BB */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_price_cross || false}
                    onChange={(e) => setLocal({ ...local, use_price_cross: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>Giá cắt đường MA/EMA/BB</span>
                </label>

                {/* 3. RSI (14) */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_rsi || false}
                    onChange={(e) => setLocal({ ...local, use_rsi: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>RSI (14)</span>
                </label>

                {/* 4. GTGD nước ngoài bán ròng (Tỷ) */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.foreign_net_sell_val || false}
                    onChange={(e) => setLocal({ ...local, foreign_net_sell_val: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>GTGD nước ngoài bán ròng (Tỷ)</span>
                </label>

                {/* 5. KLGD tự doanh bán ròng */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.prop_net_sell_vol || false}
                    onChange={(e) => setLocal({ ...local, prop_net_sell_vol: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>KLGD tự doanh bán ròng</span>
                </label>

                {/* 6. ADX (14) */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_adx || false}
                    onChange={(e) => setLocal({ ...local, use_adx: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>ADX (14)</span>
                </label>

                {/* 7. EMA */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_ema || false}
                    onChange={(e) => setLocal({ ...local, use_ema: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>EMA (Đường trung bình hàm mũ)</span>
                </label>

                {/* 8. KLGD nước ngoài bán ròng */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.foreign_net_sell_vol || false}
                    onChange={(e) => setLocal({ ...local, foreign_net_sell_vol: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>KLGD nước ngoài bán ròng</span>
                </label>

                {/* 9. RS */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_rs || false}
                    onChange={(e) => setLocal({ ...local, use_rs: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>RS (Sức mạnh giá tương đối)</span>
                </label>

                {/* 10. MACD (12,26,9) */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.use_macd || false}
                    onChange={(e) => setLocal({ ...local, use_macd: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>MACD (12,26,9)</span>
                </label>

                {/* 11. GTGD tự doanh bán ròng (Tỷ) */}
                <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-slate-100">
                  <input
                    type="checkbox"
                    checked={local.prop_net_sell_val || false}
                    onChange={(e) => setLocal({ ...local, prop_net_sell_val: e.target.checked })}
                    className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                  />
                  <span>GTGD tự doanh bán ròng (Tỷ)</span>
                </label>
              </div>
            </div>

            {/* 3. Quản trị rủi ro (3 tiêu chí chuẩn DNSE) */}
            <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-emerald-400" />
                <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                  Quản trị rủi ro tự động (DNSE Risk Guard)
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* 12. Chốt lời */}
                <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-semibold text-xs">
                    <input
                      type="checkbox"
                      checked={Boolean(local.take_profit_pct && local.take_profit_pct > 0)}
                      onChange={(e) =>
                        setLocal({
                          ...local,
                          take_profit_pct: e.target.checked ? (local.take_profit_pct || 0.15) : null,
                        })
                      }
                      className="accent-emerald-500 rounded h-3.5 w-3.5 cursor-pointer"
                    />
                    <span>Chốt lời (Take Profit)</span>
                  </label>
                </div>

                {/* 13. Cắt lỗ */}
                <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-semibold text-xs">
                    <input
                      type="checkbox"
                      checked={Boolean(local.stop_loss_pct && local.stop_loss_pct > 0)}
                      onChange={(e) =>
                        setLocal({
                          ...local,
                          stop_loss_pct: e.target.checked ? (local.stop_loss_pct || 0.07) : null,
                        })
                      }
                      className="accent-rose-500 rounded h-3.5 w-3.5 cursor-pointer"
                    />
                    <span>Cắt lỗ (Stop Loss)</span>
                  </label>
                </div>

                {/* 14. Trailing Stop */}
                <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
                  <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-semibold text-xs">
                    <input
                      type="checkbox"
                      checked={Boolean(local.trailing_stop_pct && local.trailing_stop_pct > 0)}
                      onChange={(e) =>
                        setLocal({
                          ...local,
                          trailing_stop_pct: e.target.checked ? (local.trailing_stop_pct || 0.07) : null,
                        })
                      }
                      className="accent-amber-500 rounded h-3.5 w-3.5 cursor-pointer"
                    />
                    <span>Trailing Stop</span>
                  </label>
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
            className="rounded-lg px-4 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-slate-200 cursor-pointer"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleApply}
            className="flex items-center gap-2 rounded-md bg-rose-600 px-5 py-2 text-xs font-semibold text-white hover:bg-rose-500 transition-colors cursor-pointer"
          >
            <Check className="h-4 w-4" />
            <span>Áp dụng điều kiện Bán ({count})</span>
          </button>
        </div>
      </div>
    </div>
  );
};
