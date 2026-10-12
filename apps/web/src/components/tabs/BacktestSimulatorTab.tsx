"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Coins,
  History,
  Play,
  ShieldAlert,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { DrawdownChart } from "@/components/charts/DrawdownChart";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { BacktestRequest, BacktestResponse } from "@/lib/types";

interface BacktestSimulatorTabProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  backtestResult: BacktestResponse | null;
  onRunBacktest: (params: BacktestRequest) => void;
  loading: boolean;
}

export const BacktestSimulatorTab: React.FC<BacktestSimulatorTabProps> = ({
  selectedSymbol,
  onSelectSymbol,
  backtestResult,
  onRunBacktest,
  loading,
}) => {
  // Local form state
  const [initialCapital, setInitialCapital] = useState<number>(100_000_000);
  const [modelType, setModelType] = useState<"lightgbm" | "lstm">("lightgbm");
  const [slippageRate, setSlippageRate] = useState<number>(0.0005); // 0.05%

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunBacktest({
      symbol: selectedSymbol,
      model_type: modelType,
      initial_capital: initialCapital,
      slippage_rate: slippageRate,
      fee_rate: 0.0015,
      tax_rate: 0.0010,
      lot_size: 100,
      settlement_delay: 2,
    });
  };

  const metrics = backtestResult?.metrics;
  const isAlphaPositive = (metrics?.excess_return_pct ?? 0) >= 0;

  return (
    <div className="space-y-4">
      {/* 1. Header & Bộ tham số mô phỏng tương tác */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
              <History className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 sm:text-xl">
                Phòng Giả lập Chiến lược & Quản trị Rủi ro (T+2)
              </h2>
              <p className="text-xs text-slate-400">
                Mô phỏng khớp lệnh thực tế sàn HOSE: Khớp tại Open T+1, nắm giữ tối thiểu T+2, trừ đủ thuế phí
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded bg-slate-800 px-2.5 py-1 text-slate-300 border border-slate-700">
              Phí GD: <strong>0.15%</strong>
            </span>
            <span className="rounded bg-slate-800 px-2.5 py-1 text-slate-300 border border-slate-700">
              Thuế bán: <strong>0.10%</strong>
            </span>
            <span className="rounded bg-slate-800 px-2.5 py-1 text-slate-300 border border-slate-700">
              Lô chẵn: <strong>100 CP</strong>
            </span>
            <span className="rounded bg-emerald-500/10 px-2.5 py-1 text-emerald-400 border border-emerald-500/30">
              Chu kỳ: <strong>T+2</strong>
            </span>
          </div>
        </div>

        {/* Form Tham số */}
        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5 items-end">
          {/* Mã cổ phiếu */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Mã kiểm thử
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => onSelectSymbol(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
            >
              <option value="VIC">VIC (Vingroup)</option>
              <option value="VHM">VHM (Vinhomes)</option>
              <option value="VNM">VNM (Vinamilk)</option>
              <option value="HPG">HPG (Hòa Phát)</option>
              <option value="SSI">SSI (Chứng khoán SSI)</option>
            </select>
          </div>

          {/* Vốn ban đầu */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Vốn đầu tư ban đầu (VNĐ)
            </label>
            <input
              type="number"
              step="10000000"
              min="10000000"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          {/* Mô hình AI */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Mô hình tạo tín hiệu
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value as "lightgbm" | "lstm")}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
            >
              <option value="lightgbm">LightGBM (Walk-forward)</option>
              <option value="lstm">PyTorch LSTM (Đa biến)</option>
            </select>
          </div>

          {/* Trượt giá (Slippage) */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Tỷ lệ trượt giá (Slippage)
            </label>
            <select
              value={slippageRate}
              onChange={(e) => setSlippageRate(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
            >
              <option value={0.0005}>0.05% (Thanh khoản cao)</option>
              <option value={0.0010}>0.10% (Thanh khoản vừa)</option>
              <option value={0.0020}>0.20% (Thị trường biến động)</option>
            </select>
          </div>

          {/* Nút hành động */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 py-2.5 text-xs font-bold text-slate-950 shadow-md shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 disabled:opacity-50 transition-all"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                  <span>Đang mô phỏng...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  <span>CHẠY KIỂM THỬ</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* 2. Biểu đồ Đường cong tài sản & Underwater Drawdown */}
      <div className="space-y-3">
        <EquityCurveChart
          equityCurve={backtestResult?.equity_curve || []}
          initialCapital={initialCapital}
          height={320}
        />
        <DrawdownChart
          equityCurve={backtestResult?.equity_curve || []}
          height={130}
        />
      </div>

      {/* 3. Lưới 12 Chỉ số Định lượng (Quantitative Risk Metrics Grid) */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {/* Metric 1: ROI */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>ROI Chiến lược AI</span>
            {(metrics?.total_return_pct ?? 0) >= 0 ? (
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
            )}
          </div>
          <div className="mt-1 text-base font-black">
            <span
              className={
                (metrics?.total_return_pct ?? 0) >= 0
                  ? "text-emerald-400"
                  : "text-rose-400"
              }
            >
              {metrics ? `${metrics.total_return_pct.toFixed(2)}%` : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">
            B&amp;H: {metrics ? `${metrics.buy_and_hold_return_pct.toFixed(2)}%` : "---"}
          </p>
        </div>

        {/* Metric 2: Alpha */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Alpha Vượt trội</span>
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
          </div>
          <div className="mt-1 text-base font-black">
            <span className={isAlphaPositive ? "text-emerald-400" : "text-rose-400"}>
              {metrics ? `${metrics.excess_return_pct.toFixed(2)}%` : "---"}
            </span>
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Chênh lệch so với B&amp;H</p>
        </div>

        {/* Metric 3: Sharpe Ratio */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Sharpe Ratio (Rf=4%)</span>
            <Coins className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="mt-1 text-base font-black text-slate-100">
            {metrics ? metrics.sharpe_ratio.toFixed(2) : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Lợi suất bù đắp rủi ro</p>
        </div>

        {/* Metric 4: Sortino Ratio */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Sortino Ratio</span>
            <Coins className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="mt-1 text-base font-black text-slate-100">
            {metrics ? metrics.sortino_ratio.toFixed(2) : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Rủi ro biến động giảm</p>
        </div>

        {/* Metric 5: Max Drawdown */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Max Drawdown (MDD)</span>
            <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
          </div>
          <div className="mt-1 text-base font-black text-rose-400">
            {metrics ? `${metrics.max_drawdown_pct.toFixed(2)}%` : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Sụt giảm vốn từ đỉnh</p>
        </div>

        {/* Metric 6: Calmar Ratio */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Calmar Ratio</span>
            <Coins className="h-3.5 w-3.5 text-teal-400" />
          </div>
          <div className="mt-1 text-base font-black text-slate-100">
            {metrics ? metrics.calmar_ratio.toFixed(2) : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">CAGR / Max Drawdown</p>
        </div>

        {/* Metric 7: Win Rate */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Tỷ lệ thắng (Win Rate)</span>
            <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="mt-1 text-base font-black text-emerald-400">
            {metrics ? `${metrics.win_rate_pct.toFixed(1)}%` : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">
            {metrics ? `${metrics.winning_trades} Thắng / ${metrics.total_trades} Lệnh` : "---"}
          </p>
        </div>

        {/* Metric 8: Profit Factor */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Profit Factor</span>
            <Wallet className="h-3.5 w-3.5 text-cyan-400" />
          </div>
          <div className="mt-1 text-base font-black text-slate-100">
            {metrics ? metrics.profit_factor.toFixed(2) : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Tổng lãi / Tổng lỗ gộp</p>
        </div>

        {/* Metric 9: VaR 95% */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Value-at-Risk (VaR 95%)</span>
            <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
          </div>
          <div className="mt-1 text-base font-black text-rose-400">
            {metrics ? `${metrics.var_95_pct.toFixed(2)}%` : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Rủi ro tối đa 1 phiên</p>
        </div>

        {/* Metric 10: CVaR 95% */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>CVaR 95% (Expected Shortfall)</span>
            <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
          </div>
          <div className="mt-1 text-base font-black text-rose-400">
            {metrics ? `${metrics.cvar_95_pct.toFixed(2)}%` : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Kỳ vọng tổn thất đuôi</p>
        </div>

        {/* Metric 11: Nắm giữ TB */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Thời gian nắm giữ TB</span>
            <History className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-1 text-base font-black text-slate-100">
            {metrics ? `${metrics.avg_holding_days.toFixed(1)} phiên` : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">Tuân thủ tối thiểu T+2</p>
        </div>

        {/* Metric 12: Tổng thuế phí */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
            <span>Tổng chi phí thuế phí</span>
            <Coins className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-1 text-base font-black text-slate-200">
            {metrics ? `${(metrics.total_costs / 1000).toLocaleString("vi-VN")} k` : "---"}
          </div>
          <p className="mt-0.5 text-[10px] text-slate-500">
            Tác động: {metrics ? `${metrics.cost_impact_pct.toFixed(2)}%` : "---"} vốn
          </p>
        </div>
      </div>

      {/* 4. Bảng Nhật ký Khớp lệnh Thực tế T+2 (Executed Trades Log) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 sm:text-base">
              Nhật ký Giao dịch Khớp lệnh Thực tế (Theo Chu kỳ T+2)
            </h3>
            <p className="text-[11px] text-slate-400">
              Chi tiết các vòng giao dịch đã thực hiện trong thời gian kiểm định Out-of-sample
            </p>
          </div>
          <span className="rounded bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300">
            {backtestResult?.trades?.length || 0} Giao dịch
          </span>
        </div>

        <div className="max-h-72 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 border-b border-slate-800 bg-slate-950 text-slate-400">
              <tr>
                <th className="px-3 py-2 font-semibold">Mã GD</th>
                <th className="px-3 py-2 font-semibold">Loại lệnh</th>
                <th className="px-3 py-2 font-semibold">Ngày khớp</th>
                <th className="px-3 py-2 font-semibold">Giá khớp</th>
                <th className="px-3 py-2 font-semibold">Khối lượng</th>
                <th className="px-3 py-2 font-semibold">Phí + Thuế</th>
                <th className="px-3 py-2 font-semibold">Lãi/Lỗ ròng</th>
                <th className="px-3 py-2 font-semibold">Hiệu suất (%)</th>
                <th className="px-3 py-2 text-right font-semibold">Lý do</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {backtestResult?.trades?.map((tr) => {
                const isBuy = tr.order_type === "BUY";
                const isPnlPositive = (tr.realized_pnl ?? 0) >= 0;

                return (
                  <tr key={tr.trade_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-3 py-2 font-mono text-slate-400">#{tr.trade_id}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold ${
                          isBuy
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-rose-500/10 text-rose-400"
                        }`}
                      >
                        {tr.order_type}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-300">{tr.exec_date}</td>
                    <td className="px-3 py-2 font-semibold text-slate-200">
                      {(tr.exec_price * 1000).toLocaleString("vi-VN")} đ
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-300">
                      {tr.shares.toLocaleString("vi-VN")} CP
                    </td>
                    <td className="px-3 py-2 text-slate-400">
                      {((tr.fee + tr.tax) / 1000).toLocaleString("vi-VN")} k
                    </td>
                    <td className="px-3 py-2 font-semibold">
                      {tr.realized_pnl !== null ? (
                        <span
                          className={isPnlPositive ? "text-emerald-400" : "text-rose-400"}
                        >
                          {isPnlPositive ? "+" : ""}
                          {tr.realized_pnl.toLocaleString("vi-VN")} đ
                        </span>
                      ) : (
                        <span className="text-slate-500">---</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-semibold">
                      {tr.realized_return_pct !== null ? (
                        <span
                          className={isPnlPositive ? "text-emerald-400" : "text-rose-400"}
                        >
                          {isPnlPositive ? "+" : ""}
                          {tr.realized_return_pct.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-slate-500">---</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-[11px] text-slate-400">
                      {tr.reason}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
