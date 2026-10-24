"use client";

import React, { useState, useEffect } from "react";
import { Check, X } from "lucide-react";
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
  const [showRSTooltip, setShowRSTooltip] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        setLocal({ ...conditions });
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [isOpen, conditions]);

  if (!isOpen) return null;

  // Đếm số lượng điều kiện đang được chọn
  let count = 0;
  // Thông tin cổ phiếu
  if (local.use_stock_price) count++;
  if (local.use_market_cap) count++;
  if (local.use_avg_trading_val) count++;
  if (local.use_volume_spike) count++;

  // Chỉ số kỹ thuật
  if (local.use_ma) count++;
  if (local.use_adx) count++;
  if (local.use_rs) count++;
  if (local.use_rsi) count++;
  if (local.use_price_cross) count++;
  if (local.use_price_increase) count++;

  // Kết quả kinh doanh
  if (local.growth_rev_latest) count++;
  if (local.growth_rev_prev) count++;
  if (local.growth_rev_ttm) count++;
  if (local.growth_np_latest) count++;
  if (local.growth_np_prev) count++;
  if (local.growth_np_ttm) count++;

  // Định giá
  if (local.use_pe || local.max_pe) count++;
  if (local.use_pb || local.max_pb) count++;
  if (local.use_ps || local.max_ps) count++;
  if (local.use_roa || local.min_roa) count++;
  if (local.use_roe || local.min_roe) count++;
  if (local.use_eps || local.min_eps) count++;
  if (local.growth_eps) count++;

  // Dòng tiền cổ phiếu
  if (local.foreign_net_val || local.foreign_net_buy) count++;
  if (local.foreign_net_vol) count++;
  if (local.prop_net_val || local.prop_net_buy) count++;
  if (local.prop_net_vol) count++;

  const handleApply = () => {
    onApplyConditions({
      ...local,
      // Đồng bộ các flag tương thích ngược và khởi tạo giá trị dải chuẩn DNSE
      foreign_net_buy: Boolean(local.foreign_net_val || local.foreign_net_buy),
      prop_net_buy: Boolean(local.prop_net_val || local.prop_net_buy),
      vol_spike_period: local.vol_spike_period || 10,
      min_vol_spike_pct: local.min_vol_spike_pct ?? -100,
      max_vol_spike_pct: local.max_vol_spike_pct ?? 19900,
      min_pb: local.min_pb ?? (local.use_pb ? 0.11 : undefined),
      max_pb: local.max_pb ?? (local.use_pb ? 1.07 : (local.max_pb || 2.5)),
      min_pe: local.min_pe ?? (local.use_pe ? -13.11 : undefined),
      max_pe: local.max_pe ?? (local.use_pe ? 96.53 : (local.max_pe || 18.0)),
      min_stock_price: local.min_stock_price ?? (local.use_stock_price ? 0.0 : undefined),
      max_stock_price: local.max_stock_price ?? (local.use_stock_price ? 1358.7 : undefined),
      min_market_cap: local.min_market_cap ?? (local.use_market_cap ? 0 : undefined),
      max_market_cap: local.max_market_cap ?? (local.use_market_cap ? 500000 : undefined),
      avg_trading_val_period: local.avg_trading_val_period || 10,
      min_avg_trading_val: local.min_avg_trading_val ?? (local.use_avg_trading_val ? 0 : undefined),
      max_avg_trading_val: local.max_avg_trading_val ?? (local.use_avg_trading_val ? 7028 : undefined),
      ma_left: local.ma_left || "MA 10",
      ma_operator: local.ma_operator || "Cắt lên",
      ma_right: local.ma_right || "MA 20",
      rsi_min: local.rsi_min ?? (local.use_rsi ? 0.0 : undefined),
      rsi_max: local.rsi_max ?? (local.use_rsi ? 100.0 : (local.rsi_threshold || 45.0)),
      price_t0_field: local.price_t0_field || "Giá đóng cửa T0",
      price_t0_operator: local.price_t0_operator || ">",
      price_t1_field: local.price_t1_field || "Giá đóng cửa T-1",
      min_growth_rev_latest: local.min_growth_rev_latest ?? (local.growth_rev_latest ? -67 : undefined),
      max_growth_rev_latest: local.max_growth_rev_latest ?? (local.growth_rev_latest ? 175 : undefined),
      min_growth_np_latest: local.min_growth_np_latest ?? (local.growth_np_latest ? -307 : undefined),
      max_growth_np_latest: local.max_growth_np_latest ?? (local.growth_np_latest ? 628 : undefined),
      min_growth_eps: local.min_growth_eps ?? (local.growth_eps ? -255 : undefined),
      max_growth_eps: local.max_growth_eps ?? (local.growth_eps ? 311 : undefined),
      min_growth_np_prev: local.min_growth_np_prev ?? (local.growth_np_prev ? -307 : undefined),
      max_growth_np_prev: local.max_growth_np_prev ?? (local.growth_np_prev ? 628 : undefined),
      min_growth_rev_prev: local.min_growth_rev_prev ?? (local.growth_rev_prev ? -67 : undefined),
      max_growth_rev_prev: local.max_growth_rev_prev ?? (local.growth_rev_prev ? 175 : undefined),
      min_growth_rev_ttm: local.min_growth_rev_ttm ?? (local.growth_rev_ttm ? -53 : undefined),
      max_growth_rev_ttm: local.max_growth_rev_ttm ?? (local.growth_rev_ttm ? 102 : undefined),
      min_growth_np_ttm: local.min_growth_np_ttm ?? (local.growth_np_ttm ? -263 : undefined),
      max_growth_np_ttm: local.max_growth_np_ttm ?? (local.growth_np_ttm ? 351 : undefined),
      min_roa: local.min_roa ?? (local.use_roa ? -5.74 : undefined),
      max_roa: local.max_roa ?? (local.use_roa ? 18.7 : undefined),
      min_roe: local.min_roe ?? (local.use_roe ? -11.04 : (local.min_roe || 12.0)),
      max_roe: local.max_roe ?? (local.use_roe ? 33.38 : undefined),
      min_ps: local.min_ps ?? (local.use_ps ? 0.08 : undefined),
      max_ps: local.max_ps ?? (local.use_ps ? 7.54 : undefined),
      min_eps: local.min_eps ?? (local.use_eps ? -1274 : undefined),
      max_eps: local.max_eps ?? (local.use_eps ? 6743 : undefined),
      min_adx: local.min_adx ?? (local.use_adx ? 0.0 : undefined),
      max_adx: local.max_adx ?? (local.use_adx ? 100.0 : undefined),
      min_rs: local.min_rs ?? (local.use_rs ? 0.0 : undefined),
      max_rs: local.max_rs ?? (local.use_rs ? 99.93 : undefined),
      ema_left: local.ema_left || "EMA 10",
      ema_operator: local.ema_operator || "Cắt lên",
      ema_right: local.ema_right || "EMA 20",
      macd_operator: local.macd_operator || "Cắt lên",
      macd_target: local.macd_target || "Đường tín hiệu",
      price_cross_operator: local.price_cross_operator || "Cắt lên",
      price_cross_target: local.price_cross_target || "MA 10",
      min_foreign_val: local.min_foreign_val ?? (local.foreign_net_val ? 0 : undefined),
      max_foreign_val: local.max_foreign_val ?? (local.foreign_net_val ? 9817 : undefined),
      min_foreign_vol: local.min_foreign_vol ?? (local.foreign_net_vol ? 0 : undefined),
      max_foreign_vol: local.max_foreign_vol ?? (local.foreign_net_vol ? 300.0 : undefined),
      min_prop_val: local.min_prop_val ?? (local.prop_net_val ? 0 : undefined),
      max_prop_val: local.max_prop_val ?? (local.prop_net_val ? 48633 : undefined),
      min_prop_vol: local.min_prop_vol ?? (local.prop_net_vol ? 0 : undefined),
      max_prop_vol: local.max_prop_vol ?? (local.prop_net_vol ? 50.0 : undefined),
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-3 sm:p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative flex max-h-[92vh] w-full max-w-4xl flex-col rounded-2xl border border-slate-800 bg-[#0f172a] shadow-2xl overflow-hidden">
        {/* Header Chuẩn DNSE */}
        <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4 bg-slate-900/50">
          <h3 className="text-base font-bold text-slate-100">Thêm điều kiện Mua</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body: Chuẩn 5 nhóm điều kiện DNSE */}
        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5 text-xs text-slate-300">
          {/* Thanh chọn logic kết nối điều kiện: VÀ (AND) vs HOẶC (OR) chuẩn DNSE */}
          <div className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-950/80 p-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-200">Logic kết nối điều kiện:</span>
              <span className="text-[11px] text-slate-400">
                {local.condition_logic === "OR"
                  ? "Kích hoạt Mua khi thỏa mãn ÍT NHẤT 1 điều kiện"
                  : "Kích hoạt Mua khi thỏa mãn ĐỒNG THỜI tất cả điều kiện"}
              </span>
            </div>
            <div className="flex items-center gap-1 rounded-lg bg-slate-900 p-1 border border-slate-800">
              <button
                type="button"
                onClick={() => setLocal({ ...local, condition_logic: "AND" })}
                className={`rounded-md px-3 py-1 text-xs font-bold transition-all ${
                  (!local.condition_logic || local.condition_logic === "AND")
                    ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                VÀ (AND)
              </button>
              <button
                type="button"
                onClick={() => setLocal({ ...local, condition_logic: "OR" })}
                className={`rounded-md px-3 py-1 text-xs font-bold transition-all ${
                  local.condition_logic === "OR"
                    ? "bg-amber-400 text-slate-950 shadow-md shadow-amber-400/20"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                HOẶC (OR)
              </button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-bold text-slate-100 mb-4">Điều kiện Cổ phiếu</h4>

            {/* NHÓM 1: Thông tin Cổ phiếu */}
            <div className="mb-6 space-y-2.5">
              <h5 className="text-xs font-semibold text-slate-400">Thông tin Cổ phiếu</h5>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* 1. Giá cổ phiếu */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_stock_price || false}
                    onChange={(e) => setLocal({ ...local, use_stock_price: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Giá cổ phiếu</span>
                </label>

                {/* 2. Vốn hóa (Tỷ) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_market_cap || false}
                    onChange={(e) => setLocal({ ...local, use_market_cap: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Vốn hóa (Tỷ)</span>
                </label>

                {/* 3. GTGD trung bình (Tỷ) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_avg_trading_val || false}
                    onChange={(e) => setLocal({ ...local, use_avg_trading_val: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>GTGD trung bình (Tỷ)</span>
                </label>

                {/* 4. %KLGD đột biến */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_volume_spike || false}
                    onChange={(e) => setLocal({ ...local, use_volume_spike: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>%KLGD đột biến</span>
                </label>
              </div>
            </div>

            {/* NHÓM 2: Chỉ số kỹ thuật Cổ phiếu */}
            <div className="mb-6 space-y-2.5">
              <h5 className="text-xs font-semibold text-slate-400">Chỉ số kỹ thuật Cổ phiếu</h5>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* 1. MA */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_ma || false}
                    onChange={(e) => setLocal({ ...local, use_ma: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>MA</span>
                </label>

                {/* 2. ADX (14) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_adx || false}
                    onChange={(e) => setLocal({ ...local, use_adx: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>ADX (14)</span>
                </label>

                {/* 3. RS (với Tooltip chuẩn DNSE) */}
                <div className="relative">
                  <label
                    onMouseEnter={() => setShowRSTooltip(true)}
                    onMouseLeave={() => setShowRSTooltip(false)}
                    className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none"
                  >
                    <input
                      type="checkbox"
                      checked={local.use_rs || false}
                      onChange={(e) => setLocal({ ...local, use_rs: e.target.checked })}
                      className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                    />
                    <span className="border-b border-dotted border-slate-500">RS</span>
                  </label>

                  {/* Tooltip Popup chuẩn DNSE */}
                  {showRSTooltip && (
                    <div className="absolute left-0 bottom-full mb-1 z-30 w-72 rounded-lg border border-slate-700 bg-slate-950/95 p-2.5 text-[11px] text-slate-200 shadow-xl backdrop-blur-md animate-fade-in leading-relaxed">
                      RS (Relative Strength - sức mạnh giá) đo lường mức tăng/giảm của cổ phiếu so với
                      VN-Index. Giá trị càng lớn, cổ phiếu càng dẫn dắt.
                    </div>
                  )}
                </div>

                {/* 4. RSI (14) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_rsi || false}
                    onChange={(e) => setLocal({ ...local, use_rsi: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>RSI (14)</span>
                </label>

                {/* 5. Giá T0 so với giá T-1 */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_price_increase || false}
                    onChange={(e) => setLocal({ ...local, use_price_increase: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Giá T0 so với giá T-1</span>
                </label>

                {/* 6. Giá cắt đường MA/EMA/BB */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_price_cross || false}
                    onChange={(e) =>
                      setLocal({
                        ...local,
                        use_price_cross: e.target.checked,
                        use_bb: e.target.checked,
                        use_ema: e.target.checked,
                      })
                    }
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Giá cắt đường MA/EMA/BB</span>
                </label>
              </div>
            </div>

            {/* NHÓM 3: Kết quả kinh doanh */}
            <div className="mb-6 space-y-2.5">
              <h5 className="text-xs font-semibold text-slate-400">Kết quả kinh doanh</h5>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* 1. Tăng trưởng doanh thu quý gần nhất (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_rev_latest || false}
                    onChange={(e) => setLocal({ ...local, growth_rev_latest: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Tăng trưởng doanh thu quý gần nhất (YoY)</span>
                </label>

                {/* 2. Tăng trưởng doanh thu quý liền trước (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_rev_prev || false}
                    onChange={(e) => setLocal({ ...local, growth_rev_prev: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Tăng trưởng doanh thu quý liền trước (YoY)</span>
                </label>

                {/* 3. Tăng trưởng doanh thu quý trượt 12 tháng (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_rev_ttm || false}
                    onChange={(e) => setLocal({ ...local, growth_rev_ttm: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span className="border-b border-dotted border-slate-600">
                    Tăng trưởng doanh thu quý trượt 12 tháng (YoY)
                  </span>
                </label>

                {/* 4. Tăng trưởng LNST quý gần nhất (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_np_latest || false}
                    onChange={(e) => setLocal({ ...local, growth_np_latest: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Tăng trưởng LNST quý gần nhất (YoY)</span>
                </label>

                {/* 5. Tăng trưởng LNST quý liền trước (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_np_prev || false}
                    onChange={(e) => setLocal({ ...local, growth_np_prev: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Tăng trưởng LNST quý liền trước (YoY)</span>
                </label>

                {/* 6. Tăng trưởng LNST quý trượt 12 tháng (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_np_ttm || false}
                    onChange={(e) => setLocal({ ...local, growth_np_ttm: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span className="border-b border-dotted border-slate-600">
                    Tăng trưởng LNST quý trượt 12 tháng (YoY)
                  </span>
                </label>
              </div>
            </div>

            {/* NHÓM 4: Định giá */}
            <div className="mb-6 space-y-2.5">
              <h5 className="text-xs font-semibold text-slate-400">Định giá</h5>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* 1. P/E */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_pe || Boolean(local.max_pe)}
                    onChange={(e) =>
                      setLocal({
                        ...local,
                        use_pe: e.target.checked,
                        max_pe: e.target.checked ? 18.0 : null,
                      })
                    }
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>P/E</span>
                </label>

                {/* 2. P/B */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_pb || Boolean(local.max_pb)}
                    onChange={(e) =>
                      setLocal({
                        ...local,
                        use_pb: e.target.checked,
                        max_pb: e.target.checked ? 2.5 : null,
                      })
                    }
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>P/B</span>
                </label>

                {/* 3. P/S */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_ps || false}
                    onChange={(e) => setLocal({ ...local, use_ps: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>P/S</span>
                </label>

                {/* 4. ROA (Trượt 12 tháng) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_roa || false}
                    onChange={(e) => setLocal({ ...local, use_roa: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>ROA (Trượt 12 tháng)</span>
                </label>

                {/* 5. ROE (Trượt 12 tháng) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_roe || Boolean(local.min_roe)}
                    onChange={(e) =>
                      setLocal({
                        ...local,
                        use_roe: e.target.checked,
                        min_roe: e.target.checked ? 12.0 : null,
                      })
                    }
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>ROE (Trượt 12 tháng)</span>
                </label>

                {/* 6. EPS (Trượt 12 tháng) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.use_eps || false}
                    onChange={(e) => setLocal({ ...local, use_eps: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>EPS (Trượt 12 tháng)</span>
                </label>

                {/* 7. Tăng trưởng EPS (YoY) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.growth_eps || false}
                    onChange={(e) => setLocal({ ...local, growth_eps: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>Tăng trưởng EPS (YoY)</span>
                </label>
              </div>
            </div>

            {/* NHÓM 5: Dòng tiền Cổ phiếu */}
            <div className="mb-2 space-y-2.5">
              <h5 className="text-xs font-semibold text-slate-400">Dòng tiền Cổ phiếu</h5>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {/* 1. GTGD nước ngoài mua ròng (Tỷ) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.foreign_net_val || local.foreign_net_buy || false}
                    onChange={(e) =>
                      setLocal({
                        ...local,
                        foreign_net_val: e.target.checked,
                        foreign_net_buy: e.target.checked,
                      })
                    }
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>GTGD nước ngoài mua ròng (Tỷ)</span>
                </label>

                {/* 2. KLGD nước ngoài mua ròng */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.foreign_net_vol || false}
                    onChange={(e) => setLocal({ ...local, foreign_net_vol: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>KLGD nước ngoài mua ròng</span>
                </label>

                {/* 3. GTGD tự doanh mua ròng (Tỷ) */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.prop_net_val || local.prop_net_buy || false}
                    onChange={(e) =>
                      setLocal({
                        ...local,
                        prop_net_val: e.target.checked,
                        prop_net_buy: e.target.checked,
                      })
                    }
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>GTGD tự doanh mua ròng (Tỷ)</span>
                </label>

                {/* 4. KLGD tự doanh mua ròng */}
                <label className="flex items-center gap-2.5 cursor-pointer text-slate-300 hover:text-slate-100 select-none">
                  <input
                    type="checkbox"
                    checked={local.prop_net_vol || false}
                    onChange={(e) => setLocal({ ...local, prop_net_vol: e.target.checked })}
                    className="accent-emerald-500 rounded h-4 w-4 bg-slate-950 border-slate-700"
                  />
                  <span>KLGD tự doanh mua ròng</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Chuẩn DNSE: Nút xanh Áp dụng điều kiện Mua */}
        <div className="flex items-center justify-end gap-3 border-t border-slate-800/80 px-6 py-4 bg-slate-900/50">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            Đóng
          </button>
          <button
            type="button"
            onClick={handleApply}
            className="flex items-center gap-2 rounded-xl bg-emerald-500 px-6 py-2.5 text-xs font-bold text-slate-950 shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all cursor-pointer"
          >
            <Check className="h-4 w-4" />
            <span>Áp dụng điều kiện Mua{count > 0 ? ` (${count})` : ""}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
