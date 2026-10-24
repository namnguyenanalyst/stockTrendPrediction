"use client";

import React from "react";
import { Trash2, Copy, Plus, ChevronDown } from "lucide-react";
import { BacktestConditionFilter } from "@/lib/types";
import { DualRangeSlider } from "./DualRangeSlider";

interface SellConditionAdjusterProps {
  conditions: BacktestConditionFilter;
  onChange: (updated: BacktestConditionFilter) => void;
  onOpenAddModal: () => void;
  onDuplicateCondition?: (conditionKey: string) => void;
}

export const SellConditionAdjuster: React.FC<SellConditionAdjusterProps> = ({
  conditions,
  onChange,
  onOpenAddModal,
  onDuplicateCondition,
}) => {
  // Logic kết nối điều kiện bán: OR (mặc định cho bán bảo vệ vốn) hoặc AND
  const logic = conditions.condition_logic || "OR";

  const handleLogicChange = (newLogic: "AND" | "OR") => {
    onChange({ ...conditions, condition_logic: newLogic });
  };

  // 1. Kiểm tra các điều kiện cổ phiếu đang hoạt động
  const stockConditionKeys: string[] = [];
  if (conditions.use_ma) stockConditionKeys.push("ma");
  if (conditions.use_price_cross) stockConditionKeys.push("price_cross");
  if (conditions.use_rsi) stockConditionKeys.push("rsi");
  if (conditions.foreign_net_sell_val) stockConditionKeys.push("foreign_sell_val");
  if (conditions.prop_net_sell_vol) stockConditionKeys.push("prop_sell_vol");
  if (conditions.use_adx) stockConditionKeys.push("adx");
  if (conditions.use_ema) stockConditionKeys.push("ema");
  if (conditions.foreign_net_sell_vol) stockConditionKeys.push("foreign_sell_vol");
  if (conditions.use_rs) stockConditionKeys.push("rs");
  if (conditions.use_macd) stockConditionKeys.push("macd");
  if (conditions.prop_net_sell_val) stockConditionKeys.push("prop_sell_val");

  // 2. Kiểm tra các điều kiện quản trị rủi ro
  const riskConditionKeys: string[] = [];
  if (conditions.take_profit_pct !== null && conditions.take_profit_pct !== undefined && conditions.take_profit_pct > 0) {
    riskConditionKeys.push("take_profit");
  }
  if (conditions.stop_loss_pct !== null && conditions.stop_loss_pct !== undefined && conditions.stop_loss_pct > 0) {
    riskConditionKeys.push("stop_loss");
  }
  if (conditions.trailing_stop_pct !== null && conditions.trailing_stop_pct !== undefined && conditions.trailing_stop_pct > 0) {
    riskConditionKeys.push("trailing_stop");
  }

  const totalActive = stockConditionKeys.length + riskConditionKeys.length;

  return (
    <div className="space-y-4">
      {/* 1. TIÊU ĐỀ PHÂN NHÓM: ĐIỀU KIỆN CỔ PHIẾU */}
      <div className="space-y-2">
        <div className="text-[13px] font-bold text-slate-200">Điều kiện cổ phiếu</div>

        {/* Thanh chọn logic Và / Hoặc chuẩn DNSE */}
        <div className="flex items-center gap-6 px-1 pt-1 pb-1">
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
      </div>

      {/* 2. DANH SÁCH THẺ ĐIỀU KIỆN CỔ PHIẾU */}
      <div className="space-y-3">
        {/* 1. MA */}
        {conditions.use_ma && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2.5 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">MA</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("ma")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản điều kiện MA"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_ma: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa điều kiện MA"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="relative">
                <select
                  value={conditions.ma_left || "MA 10"}
                  onChange={(e) => onChange({ ...conditions, ma_left: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="MA 10">MA 10</option>
                  <option value="MA 20">MA 20</option>
                  <option value="MA 50">MA 50</option>
                  <option value="MA 100">MA 100</option>
                  <option value="MA 200">MA 200</option>
                  <option value="Giá đóng cửa">Giá đóng cửa</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>

              <div className="relative">
                <select
                  value={conditions.ma_operator || "Cắt lên"}
                  onChange={(e) => onChange({ ...conditions, ma_operator: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="Cắt lên">Cắt lên</option>
                  <option value="Cắt xuống">Cắt xuống</option>
                  <option value="Nằm trên">Nằm trên</option>
                  <option value="Nằm dưới">Nằm dưới</option>
                  <option value=">">&gt;</option>
                  <option value="<">&lt;</option>
                  <option value="=">=</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>

              <div className="relative">
                <select
                  value={conditions.ma_right || "MA 10"}
                  onChange={(e) => onChange({ ...conditions, ma_right: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="MA 10">MA 10</option>
                  <option value="MA 20">MA 20</option>
                  <option value="MA 50">MA 50</option>
                  <option value="MA 100">MA 100</option>
                  <option value="MA 200">MA 200</option>
                  <option value="Giá đóng cửa">Giá đóng cửa</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>
            </div>
          </div>
        )}

        {/* 2. GIÁ CẮT ĐƯỜNG MA/EMA/BB */}
        {conditions.use_price_cross && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2.5 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">Giá cắt đường MA/EMA/BB</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("price_cross")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_price_cross: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="relative">
                <select
                  value={conditions.price_cross_operator || "Cắt lên"}
                  onChange={(e) => onChange({ ...conditions, price_cross_operator: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="Cắt lên">Cắt lên</option>
                  <option value="Cắt xuống">Cắt xuống</option>
                  <option value="Nằm trên">Nằm trên</option>
                  <option value="Nằm dưới">Nằm dưới</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>

              <div className="relative">
                <select
                  value={conditions.price_cross_target || "MA 10"}
                  onChange={(e) => onChange({ ...conditions, price_cross_target: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="MA 10">MA 10</option>
                  <option value="MA 20">MA 20</option>
                  <option value="MA 50">MA 50</option>
                  <option value="EMA 10">EMA 10</option>
                  <option value="EMA 20">EMA 20</option>
                  <option value="BB Trên">BB Trên</option>
                  <option value="BB Dưới">BB Dưới</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>
            </div>
          </div>
        )}

        {/* 3. RSI (14) */}
        {conditions.use_rsi && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">RSI (14)</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("rsi")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_rsi: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <DualRangeSlider
              min={0}
              max={100}
              step={0.1}
              valueMin={conditions.rsi_min !== undefined && conditions.rsi_min !== null ? conditions.rsi_min : 0.0}
              valueMax={conditions.rsi_max !== undefined && conditions.rsi_max !== null ? conditions.rsi_max : 100.0}
              formatValue={(val) => val.toFixed(2)}
              onChange={(low, high) => onChange({ ...conditions, rsi_min: low, rsi_max: high })}
            />
          </div>
        )}

        {/* 4. GTGD NƯỚC NGOÀI BÁN RÒNG (TỶ) */}
        {conditions.foreign_net_sell_val && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">GTGD nước ngoài bán ròng (Tỷ)</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, foreign_net_sell_val: false })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={9817}
              step={1}
              valueMin={conditions.min_foreign_sell_val ?? 0}
              valueMax={conditions.max_foreign_sell_val ?? 9817}
              formatValue={(val) => Math.round(val).toLocaleString()}
              onChange={(low, high) => onChange({ ...conditions, min_foreign_sell_val: low, max_foreign_sell_val: high })}
            />
          </div>
        )}

        {/* 5. KLGD TỰ DOANH BÁN RÒNG */}
        {conditions.prop_net_sell_vol && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">KLGD tự doanh bán ròng</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, prop_net_sell_vol: false })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={50}
              step={0.1}
              valueMin={conditions.min_prop_sell_vol ?? 0}
              valueMax={conditions.max_prop_sell_vol ?? 50.0}
              formatValue={(val) => (val === 0 ? "0" : `${val.toFixed(1)} triệu`)}
              onChange={(low, high) => onChange({ ...conditions, min_prop_sell_vol: low, max_prop_sell_vol: high })}
            />
          </div>
        )}

        {/* 6. ADX (14) */}
        {conditions.use_adx && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">ADX (14)</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("adx")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_adx: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <DualRangeSlider
              min={0}
              max={100}
              step={0.1}
              valueMin={conditions.min_adx ?? 0.0}
              valueMax={conditions.max_adx ?? 100.0}
              formatValue={(val) => val.toFixed(2)}
              onChange={(low, high) => onChange({ ...conditions, min_adx: low, max_adx: high })}
            />
          </div>
        )}

        {/* 7. EMA */}
        {conditions.use_ema && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2.5 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">EMA</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("ema")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_ema: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="relative">
                <select
                  value={conditions.ema_left || "EMA 10"}
                  onChange={(e) => onChange({ ...conditions, ema_left: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="EMA 10">EMA 10</option>
                  <option value="EMA 12">EMA 12</option>
                  <option value="EMA 20">EMA 20</option>
                  <option value="EMA 26">EMA 26</option>
                  <option value="EMA 50">EMA 50</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>

              <div className="relative">
                <select
                  value={conditions.ema_operator || "Cắt lên"}
                  onChange={(e) => onChange({ ...conditions, ema_operator: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="Cắt lên">Cắt lên</option>
                  <option value="Cắt xuống">Cắt xuống</option>
                  <option value="Nằm trên">Nằm trên</option>
                  <option value="Nằm dưới">Nằm dưới</option>
                  <option value=">">&gt;</option>
                  <option value="<">&lt;</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>

              <div className="relative">
                <select
                  value={conditions.ema_right || "EMA 10"}
                  onChange={(e) => onChange({ ...conditions, ema_right: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="EMA 10">EMA 10</option>
                  <option value="EMA 20">EMA 20</option>
                  <option value="EMA 50">EMA 50</option>
                  <option value="Giá đóng cửa">Giá đóng cửa</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>
            </div>
          </div>
        )}

        {/* 8. KLGD NƯỚC NGOÀI BÁN RÒNG */}
        {conditions.foreign_net_sell_vol && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">KLGD nước ngoài bán ròng</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, foreign_net_sell_vol: false })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={300}
              step={0.5}
              valueMin={conditions.min_foreign_sell_vol ?? 0}
              valueMax={conditions.max_foreign_sell_vol ?? 300.0}
              formatValue={(val) => (val === 0 ? "0" : `${val.toFixed(1)} triệu`)}
              onChange={(low, high) => onChange({ ...conditions, min_foreign_sell_vol: low, max_foreign_sell_vol: high })}
            />
          </div>
        )}

        {/* 9. RS */}
        {conditions.use_rs && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">RS</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("rs")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_rs: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <DualRangeSlider
              min={0}
              max={99.93}
              step={0.1}
              valueMin={conditions.min_rs ?? 0.0}
              valueMax={conditions.max_rs ?? 99.93}
              formatValue={(val) => val.toFixed(2)}
              onChange={(low, high) => onChange({ ...conditions, min_rs: low, max_rs: high })}
            />
          </div>
        )}

        {/* 10. MACD (12,26,9) */}
        {conditions.use_macd && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2.5 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">MACD (12,26,9)</span>
              <div className="flex items-center gap-2 text-slate-400">
                <button
                  type="button"
                  onClick={() => onDuplicateCondition?.("macd")}
                  className="p-1 hover:text-slate-200 transition-colors cursor-pointer"
                  title="Nhân bản"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ ...conditions, use_macd: false })}
                  className="p-1 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="relative">
                <select
                  value={conditions.macd_operator || "Cắt lên"}
                  onChange={(e) => onChange({ ...conditions, macd_operator: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="Cắt lên">Cắt lên</option>
                  <option value="Cắt xuống">Cắt xuống</option>
                  <option value="Nằm trên">Nằm trên</option>
                  <option value="Nằm dưới">Nằm dưới</option>
                  <option value=">">&gt;</option>
                  <option value="<">&lt;</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>

              <div className="relative">
                <select
                  value={conditions.macd_target || "Đường tín hiệu"}
                  onChange={(e) => onChange({ ...conditions, macd_target: e.target.value })}
                  className="w-full appearance-none rounded-lg border border-slate-800 bg-[#1e222d] px-2.5 py-1.5 text-xs text-slate-200 focus:border-[#e04f44] focus:outline-none pr-6 cursor-pointer"
                >
                  <option value="Đường tín hiệu">Đường tín hiệu</option>
                  <option value="Số 0">Số 0</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3 w-3 text-slate-400" />
              </div>
            </div>
          </div>
        )}

        {/* 11. GTGD TỰ DOANH BÁN RÒNG (TỶ) */}
        {conditions.prop_net_sell_val && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">GTGD tự doanh bán ròng (Tỷ)</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, prop_net_sell_val: false })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <DualRangeSlider
              min={0}
              max={48633}
              step={1}
              valueMin={conditions.min_prop_sell_val ?? 0}
              valueMax={conditions.max_prop_sell_val ?? 48633}
              formatValue={(val) => Math.round(val).toLocaleString()}
              onChange={(low, high) => onChange({ ...conditions, min_prop_sell_val: low, max_prop_sell_val: high })}
            />
          </div>
        )}
      </div>

      {/* 3. TIÊU ĐỀ PHÂN NHÓM: QUẢN TRỊ RỦI RO */}
      <div className="space-y-3 pt-2">
        <div className="text-[13px] font-bold text-slate-200">Quản trị rủi ro</div>

        {/* 12. CHỐT LỜI */}
        {conditions.take_profit_pct !== null && conditions.take_profit_pct !== undefined && conditions.take_profit_pct > 0 && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">Chốt lời</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, take_profit_pct: null })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa điều kiện chốt lời"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="relative flex items-center justify-between rounded-lg border border-slate-700/80 bg-[#1e222d] px-3 py-2 text-xs text-slate-300 focus-within:border-white transition-colors">
              <span className="text-slate-400">Chốt lời (%)</span>
              <input
                type="number"
                min="1"
                max="100"
                step="1"
                value={
                  conditions.take_profit_pct > 1
                    ? conditions.take_profit_pct
                    : Math.round(conditions.take_profit_pct * 100)
                }
                onChange={(e) => {
                  const val = Number(e.target.value);
                  onChange({ ...conditions, take_profit_pct: val > 0 ? val / 100 : null });
                }}
                className="w-16 bg-transparent text-right font-bold text-slate-100 focus:outline-none"
              />
            </div>
          </div>
        )}

        {/* 13. CẮT LỖ */}
        {conditions.stop_loss_pct !== null && conditions.stop_loss_pct !== undefined && conditions.stop_loss_pct > 0 && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">Cắt lỗ</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, stop_loss_pct: null })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa điều kiện cắt lỗ"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="relative flex items-center justify-between rounded-lg border border-slate-700/80 bg-[#1e222d] px-3 py-2 text-xs text-slate-300 focus-within:border-white transition-colors">
              <span className="text-slate-400">Cắt lỗ (%)</span>
              <input
                type="number"
                min="1"
                max="50"
                step="1"
                value={
                  conditions.stop_loss_pct > 1
                    ? conditions.stop_loss_pct
                    : Math.round(conditions.stop_loss_pct * 100)
                }
                onChange={(e) => {
                  const val = Number(e.target.value);
                  onChange({ ...conditions, stop_loss_pct: val > 0 ? val / 100 : null });
                }}
                className="w-16 bg-transparent text-right font-bold text-slate-100 focus:outline-none"
              />
            </div>
          </div>
        )}

        {/* 14. TRAILING STOP */}
        {conditions.trailing_stop_pct !== null && conditions.trailing_stop_pct !== undefined && conditions.trailing_stop_pct > 0 && (
          <div className="rounded-xl border border-slate-800 bg-[#16181e] p-3.5 space-y-2 transition-all hover:border-slate-700/80">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">Trailing Stop</span>
              <button
                type="button"
                onClick={() => onChange({ ...conditions, trailing_stop_pct: null })}
                className="p-1 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                title="Xóa điều kiện trailing stop"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="relative flex items-center justify-between rounded-lg border border-slate-700/80 bg-[#1e222d] px-3 py-2 text-xs text-slate-300 focus-within:border-white transition-colors">
              <span className="text-slate-400">Trailing Stop (%)</span>
              <input
                type="number"
                min="1"
                max="30"
                step="1"
                value={
                  conditions.trailing_stop_pct > 1
                    ? conditions.trailing_stop_pct
                    : Math.round(conditions.trailing_stop_pct * 100)
                }
                onChange={(e) => {
                  const val = Number(e.target.value);
                  onChange({ ...conditions, trailing_stop_pct: val > 0 ? val / 100 : null });
                }}
                className="w-16 bg-transparent text-right font-bold text-slate-100 focus:outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* 4. TRẠNG THÁI RỖNG (KHI CHƯA CHỌN ĐIỀU KIỆN NÀO) */}
      {totalActive === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-[#12141a]/60 py-8 px-4 text-center">
          <p className="text-xs text-slate-400">Chưa có điều kiện bán nào được thiết lập.</p>
          <p className="text-[11px] text-slate-500 mt-1">
            Bấm nút &quot;Thêm điều kiện&quot; để cấu hình tín hiệu kỹ thuật hoặc quản trị rủi ro.
          </p>
          <button
            type="button"
            onClick={onOpenAddModal}
            className="mt-3.5 flex items-center gap-1.5 rounded-lg bg-[#e04f44]/15 px-3.5 py-1.5 text-xs font-semibold text-[#e04f44] border border-[#e04f44]/30 hover:bg-[#e04f44]/25 transition-all cursor-pointer"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Thêm điều kiện bán</span>
          </button>
        </div>
      )}
    </div>
  );
};
