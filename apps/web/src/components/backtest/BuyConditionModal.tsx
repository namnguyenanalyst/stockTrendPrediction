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
      // Đồng bộ các flag tương thích ngược
      foreign_net_buy: Boolean(local.foreign_net_val || local.foreign_net_buy),
      prop_net_buy: Boolean(local.prop_net_val || local.prop_net_buy),
      max_pe: local.use_pe ? (local.max_pe || 18.0) : null,
      max_pb: local.use_pb ? (local.max_pb || 2.5) : null,
      min_roe: local.use_roe ? (local.min_roe || 12.0) : null,
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
