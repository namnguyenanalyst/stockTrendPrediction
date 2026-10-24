"use client";

import React from "react";
import { Trash2, Copy, Plus, ChevronDown } from "lucide-react";
import { BacktestConditionFilter } from "@/lib/types";
import { DualRangeSlider } from "./DualRangeSlider";

interface BuyConditionAdjusterProps {
  conditions: BacktestConditionFilter;
  onChange: (updated: BacktestConditionFilter) => void;
  onOpenAddModal: () => void;
  onDuplicateCondition?: (conditionKey: string) => void;
}

export const BuyConditionAdjuster: React.FC<BuyConditionAdjusterProps> = ({
  conditions,
  onChange,
  onOpenAddModal,
  onDuplicateCondition,
}) => {
  const logic = conditions.condition_logic || "AND";

  const handleLogicChange = (newLogic: "AND" | "OR") => {
    onChange({ ...conditions, condition_logic: newLogic });
  };

  // Đếm các điều kiện đang được kích hoạt
  const activeKeys: string[] = [];
  if (conditions.use_volume_spike) activeKeys.push("vol_spike");
  if (conditions.use_pb) activeKeys.push("pb");
  if (conditions.use_stock_price) activeKeys.push("stock_price");
  if (conditions.use_market_cap) activeKeys.push("market_cap");
  if (conditions.use_avg_trading_val) activeKeys.push("avg_val");
  if (conditions.use_ma) activeKeys.push("ma");
  if (conditions.use_rsi) activeKeys.push("rsi");
  if (conditions.use_price_increase) activeKeys.push("price_t0");
  if (conditions.growth_rev_latest) activeKeys.push("rev_latest");
  if (conditions.growth_np_latest) activeKeys.push("np_latest");
  if (conditions.use_pe) activeKeys.push("pe");
  if (conditions.use_roa) activeKeys.push("roa");
  if (conditions.growth_eps) activeKeys.push("eps_growth");
  if (conditions.foreign_net_val || conditions.foreign_net_buy) activeKeys.push("foreign_val");
  if (conditions.prop_net_vol) activeKeys.push("prop_vol");
  if (conditions.foreign_net_vol) activeKeys.push("foreign_vol");
  if (conditions.use_roe) activeKeys.push("roe");
  if (conditions.growth_np_prev) activeKeys.push("np_prev");
  if (conditions.growth_rev_prev) activeKeys.push("rev_prev");
  if (conditions.use_adx) activeKeys.push("adx");
  if (conditions.use_ema) activeKeys.push("ema");
  if (conditions.use_macd) activeKeys.push("macd");
  if (conditions.use_rs) activeKeys.push("rs");
  if (conditions.growth_rev_ttm) activeKeys.push("rev_ttm");
  if (conditions.growth_np_ttm) activeKeys.push("np_ttm");
  if (conditions.use_ps) activeKeys.push("ps");
  if (conditions.use_eps) activeKeys.push("eps");
  if (conditions.prop_net_val || conditions.prop_net_buy) activeKeys.push("prop_val");
  if (conditions.use_price_cross) activeKeys.push("price_cross");
  if (conditions.use_bb) activeKeys.push("bb");

  const totalActive = activeKeys.length;

  return (
    <div className="space-y-3.5">
      {/* 1. THANH CHỌN TOÁN TỬ LOGIC VÀ / HOẶC CHUẨN DNSE */}
      <div className="flex items-center gap-6 px-1">
        {/* Nút radio VÀ */}
        <label
          onClick={() => handleLogicChange("AND")}
          className="flex items-center gap-2 cursor-pointer group select-none"
        >
          <div className="relative flex h-4 w-4 items-center justify-center rounded-full border border-slate-600 bg-slate-900 transition-colors group-hover:border-slate-500">
            {logic === "AND" && (
              <div className="h-2 w-2 rounded-full bg-[#e04f44] ring-2 ring-[#e04f44]/30" />
            )}
          </div>
          <span
            className={`text-xs font-semibold transition-colors ${
              logic === "AND" ? "text-slate-100" : "text-slate-400 group-hover:text-slate-300"
            }`}
          >
            Và
          </span>
        </label>

        {/* Nút radio HOẶC */}
        <label
          onClick={() => handleLogicChange("OR")}
          className="flex items-center gap-2 cursor-pointer group select-none"
        >
          <div className="relative flex h-4 w-4 items-center justify-center rounded-full border border-slate-600 bg-slate-900 transition-colors group-hover:border-slate-500">
            {logic === "OR" && (
              <div className="h-2 w-2 rounded-full bg-[#e04f44] ring-2 ring-[#e04f44]/30" />
            )}
          </div>
          <span
            className={`text-xs font-semibold transition-colors ${
              logic === "OR" ? "text-slate-100" : "text-slate-400 group-hover:text-slate-300"
            }`}
          >
            Hoặc
          </span>
        </label>
      </div>

      {/* 2. NẾU CHƯA CÓ ĐIỀU KIỆN NÀO ĐƯỢC CHỌN */}
      {totalActive === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30 p-6 text-center">
          <p className="text-xs text-slate-400">
            Chưa có chỉ số nào được chọn trong điều kiện Mua.
          </p>
          <button
            type="button"
            onClick={onOpenAddModal}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all cursor-pointer"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>+ Thêm điều kiện Mua</span>
          </button>
        </div>
      )}

      {/* 3. DANH SÁCH THẺ TINH CHỈNH THÔNG SỐ CHUẨN DNSE */}
      <div className="space-y-2.5">
        {/* CARD: %KLGD đột biến */}
        {conditions.use_volume_spike && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-200">%KLGD đột biến</span>
                {/* Dropdown chu kỳ phiên */}
                <div className="relative inline-flex items-center">
                  <select
                    value={conditions.vol_spike_period || 10}
                    onChange={(e) =>
                      onChange({ ...conditions, vol_spike_period: Number(e.target.value) })
                    }
                    className="appearance-none bg-transparent text-[11px] font-semibold text-[#e04f44] pr-4 cursor-pointer focus:outline-none"
                  >
                    <option value={5} className="bg-slate-900 text-slate-200">5 phiên gần nhất</option>
                    <option value={10} className="bg-slate-900 text-slate-200">10 phiên gần nhất</option>
                    <option value={20} className="bg-slate-900 text-slate-200">20 phiên gần nhất</option>
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-0 h-3 w-3 text-[#e04f44]" />
                </div>
              </div>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_volume_spike: false })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-100}
              max={19900}
              step={10}
              valueMin={conditions.min_vol_spike_pct ?? -100}
              valueMax={conditions.max_vol_spike_pct ?? 19900}
              onChange={(min, max) =>
                onChange({ ...conditions, min_vol_spike_pct: min, max_vol_spike_pct: max })
              }
              formatValue={(v) => `${v.toLocaleString()}%`}
            />
          </div>
        )}

        {/* CARD: P/B */}
        {conditions.use_pb && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">P/B</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_pb: false, min_pb: null, max_pb: null })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0.0}
              max={10.0}
              step={0.01}
              valueMin={conditions.min_pb ?? 0.11}
              valueMax={conditions.max_pb ?? 1.07}
              onChange={(min, max) => onChange({ ...conditions, min_pb: min, max_pb: max })}
              formatValue={(v) => v.toFixed(2)}
            />
          </div>
        )}

        {/* CARD: Giá cổ phiếu */}
        {conditions.use_stock_price && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Giá cổ phiếu (nghìn đồng)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, use_stock_price: false, min_stock_price: undefined, max_stock_price: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0.0}
              max={1358.7}
              step={0.5}
              valueMin={conditions.min_stock_price ?? 0.0}
              valueMax={conditions.max_stock_price ?? 1358.7}
              onChange={(min, max) =>
                onChange({ ...conditions, min_stock_price: min, max_stock_price: max })
              }
              formatValue={(v) => v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            />
          </div>
        )}

        {/* CARD: Vốn hóa (Tỷ) */}
        {conditions.use_market_cap && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Vốn hóa (Tỷ)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, use_market_cap: false, min_market_cap: undefined, max_market_cap: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={500000}
              step={500}
              valueMin={conditions.min_market_cap ?? 0}
              valueMax={conditions.max_market_cap ?? 500000}
              onChange={(min, max) =>
                onChange({ ...conditions, min_market_cap: min, max_market_cap: max })
              }
              formatValue={(v) => (v >= 500000 ? "Tối đa" : v.toLocaleString())}
            />
          </div>
        )}

        {/* CARD: GTGD trung bình (Tỷ) */}
        {conditions.use_avg_trading_val && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-200">GTGD trung bình (Tỷ)</span>
                <div className="relative inline-flex items-center">
                  <select
                    value={conditions.avg_trading_val_period || 10}
                    onChange={(e) =>
                      onChange({ ...conditions, avg_trading_val_period: Number(e.target.value) })
                    }
                    className="appearance-none bg-transparent text-[11px] font-semibold text-[#e04f44] pr-4 cursor-pointer focus:outline-none"
                  >
                    <option value={5} className="bg-slate-900 text-slate-200">5 phiên gần nhất</option>
                    <option value={10} className="bg-slate-900 text-slate-200">10 phiên gần nhất</option>
                    <option value={20} className="bg-slate-900 text-slate-200">20 phiên gần nhất</option>
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-0 h-3 w-3 text-[#e04f44]" />
                </div>
              </div>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, use_avg_trading_val: false, min_avg_trading_val: undefined, max_avg_trading_val: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={10000}
              step={10}
              valueMin={conditions.min_avg_trading_val ?? 0}
              valueMax={conditions.max_avg_trading_val ?? 7028}
              onChange={(min, max) =>
                onChange({ ...conditions, min_avg_trading_val: min, max_avg_trading_val: max })
              }
              formatValue={(v) => v.toLocaleString()}
            />
          </div>
        )}

        {/* CARD: MA (Comparison Dropdowns) */}
        {conditions.use_ma && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">MA</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("ma")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_ma: false })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            {/* Bộ 3 dropdowns MA: Left - Operator - Right */}
            <div className="grid grid-cols-3 gap-2">
              <select
                value={conditions.ma_left || "MA 10"}
                onChange={(e) => onChange({ ...conditions, ma_left: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="MA 5">MA 5</option>
                <option value="MA 10">MA 10</option>
                <option value="MA 20">MA 20</option>
                <option value="MA 50">MA 50</option>
                <option value="MA 100">MA 100</option>
                <option value="MA 200">MA 200</option>
                <option value="Giá đóng cửa">Giá đóng cửa</option>
              </select>

              <select
                value={conditions.ma_operator || "Cắt lên"}
                onChange={(e) => onChange({ ...conditions, ma_operator: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Cắt lên">Cắt lên</option>
                <option value="Cắt xuống">Cắt xuống</option>
                <option value="Nằm trên">Nằm trên</option>
                <option value="Nằm dưới">Nằm dưới</option>
              </select>

              <select
                value={conditions.ma_right || "MA 20"}
                onChange={(e) => onChange({ ...conditions, ma_right: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="MA 10">MA 10</option>
                <option value="MA 20">MA 20</option>
                <option value="MA 50">MA 50</option>
                <option value="MA 100">MA 100</option>
                <option value="MA 200">MA 200</option>
                <option value="Giá đóng cửa">Giá đóng cửa</option>
              </select>
            </div>
          </div>
        )}

        {/* CARD: RSI (14) */}
        {conditions.use_rsi && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">RSI (14)</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("rsi")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_rsi: false, rsi_min: undefined, rsi_max: undefined })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <DualRangeSlider
              min={0.0}
              max={100.0}
              step={1}
              valueMin={conditions.rsi_min ?? 0.0}
              valueMax={conditions.rsi_max ?? 100.0}
              onChange={(min, max) => onChange({ ...conditions, rsi_min: min, rsi_max: max, rsi_threshold: max })}
              formatValue={(v) => v.toFixed(2)}
            />
          </div>
        )}

        {/* CARD: Giá T0 so với giá T-1 */}
        {conditions.use_price_increase && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Giá T0 so với giá T-1</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("price_t0")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_price_increase: false })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <select
                value={conditions.price_t0_field || "Giá đóng cửa T0"}
                onChange={(e) => onChange({ ...conditions, price_t0_field: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Giá đóng cửa T0">Giá đóng cửa T0</option>
                <option value="Giá mở cửa T0">Giá mở cửa T0</option>
                <option value="Giá cao nhất T0">Giá cao nhất T0</option>
                <option value="Giá thấp nhất T0">Giá thấp nhất T0</option>
              </select>

              <select
                value={conditions.price_t0_operator || ">"}
                onChange={(e) => onChange({ ...conditions, price_t0_operator: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer text-center font-bold"
              >
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
                <option value="=">=</option>
                <option value=">=">&gt;=</option>
                <option value="<=">&lt;=</option>
              </select>

              <select
                value={conditions.price_t1_field || "Giá đóng cửa T-1"}
                onChange={(e) => onChange({ ...conditions, price_t1_field: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Giá đóng cửa T-1">Giá đóng cửa T-1</option>
                <option value="Giá mở cửa T-1">Giá mở cửa T-1</option>
                <option value="Giá cao nhất T-1">Giá cao nhất T-1</option>
                <option value="Giá tham chiếu T-1">Giá tham chiếu T-1</option>
              </select>
            </div>
          </div>
        )}

        {/* CARD: Tăng trưởng doanh thu quý gần nhất (YoY) */}
        {conditions.growth_rev_latest && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng doanh thu quý gần nhất (YoY)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_rev_latest: false, min_growth_rev_latest: undefined, max_growth_rev_latest: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-100}
              max={500}
              step={1}
              valueMin={conditions.min_growth_rev_latest ?? -67}
              valueMax={conditions.max_growth_rev_latest ?? 175}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_rev_latest: min, max_growth_rev_latest: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: Tăng trưởng LNST quý gần nhất (YoY) */}
        {conditions.growth_np_latest && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng LNST quý gần nhất (YoY)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_np_latest: false, min_growth_np_latest: undefined, max_growth_np_latest: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-500}
              max={1000}
              step={1}
              valueMin={conditions.min_growth_np_latest ?? -307}
              valueMax={conditions.max_growth_np_latest ?? 628}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_np_latest: min, max_growth_np_latest: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: P/E */}
        {conditions.use_pe && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">P/E</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_pe: false, min_pe: null, max_pe: null })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-50.0}
              max={150.0}
              step={0.1}
              valueMin={conditions.min_pe ?? -13.11}
              valueMax={conditions.max_pe ?? 96.53}
              onChange={(min, max) => onChange({ ...conditions, min_pe: min, max_pe: max })}
              formatValue={(v) => v.toFixed(2)}
            />
          </div>
        )}

        {/* CARD: ROA (Trượt 12 tháng) */}
        {conditions.use_roa && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">ROA (Trượt 12 tháng)</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_roa: false, min_roa: null, max_roa: null })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-30.0}
              max={50.0}
              step={0.1}
              valueMin={conditions.min_roa ?? -5.74}
              valueMax={conditions.max_roa ?? 18.7}
              onChange={(min, max) => onChange({ ...conditions, min_roa: min, max_roa: max })}
              formatValue={(v) => `${v.toFixed(2)}%`}
            />
          </div>
        )}

        {/* CARD: Tăng trưởng EPS (YoY) */}
        {conditions.growth_eps && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng EPS (YoY)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_eps: false, min_growth_eps: null, max_growth_eps: null })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-400}
              max={500}
              step={1}
              valueMin={conditions.min_growth_eps ?? -255}
              valueMax={conditions.max_growth_eps ?? 311}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_eps: min, max_growth_eps: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: GTGD nước ngoài mua ròng (Tỷ) */}
        {(conditions.foreign_net_val || conditions.foreign_net_buy) && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">GTGD nước ngoài mua ròng (Tỷ)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, foreign_net_val: false, foreign_net_buy: false, min_foreign_val: undefined, max_foreign_val: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={20000}
              step={10}
              valueMin={conditions.min_foreign_val ?? 0}
              valueMax={conditions.max_foreign_val ?? 9817}
              onChange={(min, max) =>
                onChange({ ...conditions, min_foreign_val: min, max_foreign_val: max, foreign_net_buy: true, foreign_net_val: true })
              }
              formatValue={(v) => v.toLocaleString()}
            />
          </div>
        )}

        {/* CARD: KLGD tự doanh mua ròng */}
        {conditions.prop_net_vol && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">KLGD tự doanh mua ròng</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, prop_net_vol: false, min_prop_vol: undefined, max_prop_vol: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={100}
              step={0.5}
              valueMin={conditions.min_prop_vol ?? 0}
              valueMax={conditions.max_prop_vol ?? 50.0}
              onChange={(min, max) => onChange({ ...conditions, min_prop_vol: min, max_prop_vol: max })}
              formatValue={(v) => `${v.toFixed(1)} triệu`}
            />
          </div>
        )}

        {/* CARD: KLGD nước ngoài mua ròng */}
        {conditions.foreign_net_vol && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">KLGD nước ngoài mua ròng</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, foreign_net_vol: false, min_foreign_vol: undefined, max_foreign_vol: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={500}
              step={1}
              valueMin={conditions.min_foreign_vol ?? 0}
              valueMax={conditions.max_foreign_vol ?? 300.0}
              onChange={(min, max) =>
                onChange({ ...conditions, min_foreign_vol: min, max_foreign_vol: max })
              }
              formatValue={(v) => `${v.toFixed(1)} triệu`}
            />
          </div>
        )}

        {/* CARD: ROE (Trượt 12 tháng) */}
        {conditions.use_roe && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">ROE (Trượt 12 tháng)</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_roe: false, min_roe: null, max_roe: null })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-50.0}
              max={60.0}
              step={0.1}
              valueMin={conditions.min_roe ?? -11.04}
              valueMax={conditions.max_roe ?? 33.38}
              onChange={(min, max) => onChange({ ...conditions, min_roe: min, max_roe: max })}
              formatValue={(v) => `${v.toFixed(2)}%`}
            />
          </div>
        )}

        {/* CARD: Tăng trưởng LNST quý liền trước (YoY) */}
        {conditions.growth_np_prev && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng LNST quý liền trước (YoY)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_np_prev: false, min_growth_np_prev: undefined, max_growth_np_prev: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-500}
              max={1000}
              step={1}
              valueMin={conditions.min_growth_np_prev ?? -307}
              valueMax={conditions.max_growth_np_prev ?? 628}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_np_prev: min, max_growth_np_prev: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: Tăng trưởng doanh thu quý liền trước (YoY) */}
        {conditions.growth_rev_prev && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng doanh thu quý liền trước (YoY)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_rev_prev: false, min_growth_rev_prev: undefined, max_growth_rev_prev: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-100}
              max={500}
              step={1}
              valueMin={conditions.min_growth_rev_prev ?? -67}
              valueMax={conditions.max_growth_rev_prev ?? 175}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_rev_prev: min, max_growth_rev_prev: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: ADX (14) */}
        {conditions.use_adx && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">ADX (14)</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("adx")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_adx: false, min_adx: undefined, max_adx: undefined })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <DualRangeSlider
              min={0.0}
              max={100.0}
              step={1}
              valueMin={conditions.min_adx ?? 0.0}
              valueMax={conditions.max_adx ?? 100.0}
              onChange={(min, max) => onChange({ ...conditions, min_adx: min, max_adx: max })}
              formatValue={(v) => v.toFixed(2)}
            />
          </div>
        )}

        {/* CARD: EMA (Comparison Dropdowns) */}
        {conditions.use_ema && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">EMA</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("ema")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_ema: false })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <select
                value={conditions.ema_left || "EMA 10"}
                onChange={(e) => onChange({ ...conditions, ema_left: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="EMA 5">EMA 5</option>
                <option value="EMA 10">EMA 10</option>
                <option value="EMA 12">EMA 12</option>
                <option value="EMA 20">EMA 20</option>
                <option value="EMA 26">EMA 26</option>
                <option value="EMA 50">EMA 50</option>
                <option value="Giá đóng cửa">Giá đóng cửa</option>
              </select>

              <select
                value={conditions.ema_operator || "Cắt lên"}
                onChange={(e) => onChange({ ...conditions, ema_operator: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Cắt lên">Cắt lên</option>
                <option value="Cắt xuống">Cắt xuống</option>
                <option value="Nằm trên">Nằm trên</option>
                <option value="Nằm dưới">Nằm dưới</option>
              </select>

              <select
                value={conditions.ema_right || "EMA 20"}
                onChange={(e) => onChange({ ...conditions, ema_right: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="EMA 10">EMA 10</option>
                <option value="EMA 20">EMA 20</option>
                <option value="EMA 50">EMA 50</option>
                <option value="EMA 100">EMA 100</option>
                <option value="EMA 200">EMA 200</option>
                <option value="Giá đóng cửa">Giá đóng cửa</option>
              </select>
            </div>
          </div>
        )}

        {/* CARD: MACD (12,26,9) */}
        {conditions.use_macd && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">MACD (12,26,9)</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("macd")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_macd: false })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={conditions.macd_operator || "Cắt lên"}
                onChange={(e) => onChange({ ...conditions, macd_operator: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Cắt lên">Cắt lên</option>
                <option value="Cắt xuống">Cắt xuống</option>
                <option value="Nằm trên">Nằm trên</option>
                <option value="Nằm dưới">Nằm dưới</option>
              </select>

              <select
                value={conditions.macd_target || "Đường tín hiệu"}
                onChange={(e) => onChange({ ...conditions, macd_target: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Đường tín hiệu">Đường tín hiệu</option>
                <option value="Đường 0">Đường 0</option>
              </select>
            </div>
          </div>
        )}

        {/* CARD: RS (Sức mạnh giá Relative Strength) */}
        {conditions.use_rs && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">RS</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("rs")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_rs: false, min_rs: undefined, max_rs: undefined })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <DualRangeSlider
              min={0.0}
              max={99.93}
              step={0.5}
              valueMin={conditions.min_rs ?? 0.0}
              valueMax={conditions.max_rs ?? 99.93}
              onChange={(min, max) => onChange({ ...conditions, min_rs: min, max_rs: max })}
              formatValue={(v) => v.toFixed(2)}
            />
          </div>
        )}

        {/* CARD: Tăng trưởng doanh thu quý trượt 12 tháng (YoY) */}
        {conditions.growth_rev_ttm && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng doanh thu quý trượt 12 tháng</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_rev_ttm: false, min_growth_rev_ttm: undefined, max_growth_rev_ttm: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-100}
              max={300}
              step={1}
              valueMin={conditions.min_growth_rev_ttm ?? -53}
              valueMax={conditions.max_growth_rev_ttm ?? 102}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_rev_ttm: min, max_growth_rev_ttm: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: Tăng trưởng LNST quý trượt 12 tháng (YoY) */}
        {conditions.growth_np_ttm && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Tăng trưởng LNST quý trượt 12 tháng (YoY)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, growth_np_ttm: false, min_growth_np_ttm: undefined, max_growth_np_ttm: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-400}
              max={500}
              step={1}
              valueMin={conditions.min_growth_np_ttm ?? -263}
              valueMax={conditions.max_growth_np_ttm ?? 351}
              onChange={(min, max) =>
                onChange({ ...conditions, min_growth_np_ttm: min, max_growth_np_ttm: max })
              }
              formatValue={(v) => `${v > 0 ? "+" : ""}${v}%`}
            />
          </div>
        )}

        {/* CARD: P/S */}
        {conditions.use_ps && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">P/S</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_ps: false, min_ps: null, max_ps: null })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0.0}
              max={20.0}
              step={0.01}
              valueMin={conditions.min_ps ?? 0.08}
              valueMax={conditions.max_ps ?? 7.54}
              onChange={(min, max) => onChange({ ...conditions, min_ps: min, max_ps: max })}
              formatValue={(v) => v.toFixed(2)}
            />
          </div>
        )}

        {/* CARD: EPS (Trượt 12 tháng) */}
        {conditions.use_eps && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">EPS (Trượt 12 tháng)</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_eps: false, min_eps: null, max_eps: null })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={-5000}
              max={15000}
              step={50}
              valueMin={conditions.min_eps ?? -1274}
              valueMax={conditions.max_eps ?? 6743}
              onChange={(min, max) => onChange({ ...conditions, min_eps: min, max_eps: max })}
              formatValue={(v) => v.toLocaleString()}
            />
          </div>
        )}

        {/* CARD: GTGD tự doanh mua ròng (Tỷ) */}
        {(conditions.prop_net_val || conditions.prop_net_buy) && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">GTGD tự doanh mua ròng (Tỷ)</span>
              <button
                type="button"
                onClick={() =>
                  onChange({ ...conditions, prop_net_val: false, prop_net_buy: false, min_prop_val: undefined, max_prop_val: undefined })
                }
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={60000}
              step={50}
              valueMin={conditions.min_prop_val ?? 0}
              valueMax={conditions.max_prop_val ?? 48633}
              onChange={(min, max) =>
                onChange({ ...conditions, min_prop_val: min, max_prop_val: max, prop_net_val: true, prop_net_buy: true })
              }
              formatValue={(v) => v.toLocaleString()}
            />
          </div>
        )}

        {/* CARD: Giá cắt đường MA/EMA/BB */}
        {conditions.use_price_cross && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2.5 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Giá cắt đường MA/EMA/BB</span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("price_cross")}
                  className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                  title="Sao chép điều kiện"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_price_cross: false })}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Xóa điều kiện"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={conditions.price_cross_operator || "Cắt lên"}
                onChange={(e) => onChange({ ...conditions, price_cross_operator: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="Cắt lên">Cắt lên</option>
                <option value="Cắt xuống">Cắt xuống</option>
                <option value="Nằm trên">Nằm trên</option>
                <option value="Nằm dưới">Nằm dưới</option>
              </select>

              <select
                value={conditions.price_cross_target || "MA 10"}
                onChange={(e) => onChange({ ...conditions, price_cross_target: e.target.value })}
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs font-medium text-slate-200 focus:border-emerald-500 focus:outline-none cursor-pointer"
              >
                <option value="MA 10">MA 10</option>
                <option value="MA 20">MA 20</option>
                <option value="MA 50">MA 50</option>
                <option value="EMA 20">EMA 20</option>
                <option value="EMA 50">EMA 50</option>
                <option value="BB Trên">BB Trên</option>
                <option value="BB Dưới">BB Dưới</option>
              </select>
            </div>
          </div>
        )}

        {/* CARD: Bollinger Bands */}
        {conditions.use_bb && (
          <div className="rounded-xl border border-slate-800/90 bg-slate-950/70 p-3.5 space-y-2 shadow-sm transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">Bollinger Bands (20, 2)</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, use_bb: false })}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Xóa điều kiện"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <p className="text-[11px] text-slate-400">
              Điều kiện: Giá chạm dải dưới (BB Lower) hoặc bật tăng từ biên dưới Bollinger Bands.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
