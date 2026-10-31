"use client";

import React, { useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  Clock,
  Eye,
  History,
  LineChart,
  RefreshCw,
} from "lucide-react";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { UserBacktestHistory } from "@/lib/types";

interface BacktestHistoryTableProps {
  histories: UserBacktestHistory[];
  isLoading: boolean;
  onSelectHistory?: (item: UserBacktestHistory) => void;
  selectedHistoryId?: string | null;
  onRefresh?: () => void;
}

export const BacktestHistoryTable: React.FC<BacktestHistoryTableProps> = ({
  histories,
  isLoading,
  onSelectHistory,
  selectedHistoryId,
  onRefresh,
}) => {
  const [activePreview, setActivePreview] = useState<UserBacktestHistory | null>(
    null
  );

  const handleRowClick = (item: UserBacktestHistory) => {
    setActivePreview(item);
    onSelectHistory?.(item);
  };

  return (
    <div className="space-y-4">
      {/* Header thanh công cụ */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-3 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
            <History className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-100">
              Sổ nhật ký kiểm thử ({histories.length})
            </h3>
            <p className="text-[10px] text-slate-400">
              Lưu trữ kết quả kiểm thử, chỉ số tài chính và đường cong vốn vào tài khoản
            </p>
          </div>
        </div>

        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1 text-xs text-slate-300 hover:border-slate-700 hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Làm mới</span>
          </button>
        )}
      </div>

      {/* Preview Biểu đồ Equity Curve khi chọn dòng */}
      {activePreview && activePreview.equity_curve && activePreview.equity_curve.length > 0 && (
        <div className="rounded-xl border border-emerald-500/30 bg-slate-900/90 p-4 shadow-xl backdrop-blur-md animate-in fade-in">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800/80 pb-3 mb-3">
            <div className="flex items-center gap-2">
              <LineChart className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-bold text-slate-100">
                Đường cong vốn (Equity Curve):{" "}
                <span className="text-emerald-400">{activePreview.strategy_name}</span>{" "}
                ({activePreview.symbol})
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="text-slate-400">
                ROI:{" "}
                <strong
                  className={
                    activePreview.total_return >= 0
                      ? "text-emerald-400"
                      : "text-rose-400"
                  }
                >
                  {activePreview.total_return >= 0 ? "+" : ""}
                  {activePreview.total_return.toFixed(2)}%
                </strong>
              </span>
              <span className="text-slate-400">
                Sharpe:{" "}
                <strong className="text-slate-200">
                  {activePreview.sharpe_ratio.toFixed(2)}
                </strong>
              </span>
              <span className="text-slate-400">
                MDD:{" "}
                <strong className="text-rose-400">
                  {activePreview.max_drawdown.toFixed(2)}%
                </strong>
              </span>
              <button
                type="button"
                onClick={() => setActivePreview(null)}
                className="text-xs text-slate-500 hover:text-slate-300 ml-2"
              >
                Đóng xem nhanh
              </button>
            </div>
          </div>

          <div className="h-64 w-full">
            <EquityCurveChart
              equityCurve={activePreview.equity_curve}
              height={256}
              initialCapital={activePreview.initial_capital}
            />
          </div>
        </div>
      )}

      {/* Bảng danh sách nhật ký */}
      {isLoading ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs text-slate-500 animate-pulse">
          Đang tải dữ liệu nhật ký kiểm thử...
        </div>
      ) : histories.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center text-xs text-slate-400">
          <History className="mx-auto h-8 w-8 text-slate-600 mb-2" />
          <p className="font-semibold text-slate-300">
            Sổ nhật ký kiểm thử đang trống
          </p>
          <p className="mt-1 text-slate-500 max-w-md mx-auto text-[11px]">
            Chạy kiểm thử chiến lược định lượng tại Phòng Lab, sau đó nhấn nút &quot;Lưu vào
            sổ nhật ký&quot; để ghi nhận kết quả và so sánh đường cong vốn.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg backdrop-blur-sm">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-bold text-slate-400">
              <tr>
                <th className="py-2.5 pl-4 pr-2">THỜI GIAN THỰC THI</th>
                <th className="px-3 py-2.5">MÃ / CHIẾN LƯỢC</th>
                <th className="px-3 py-2.5">GIAI ĐOẠN</th>
                <th className="px-3 py-2.5 text-right">VỐN ĐẦU TƯ</th>
                <th className="px-3 py-2.5 text-right">TỔNG LỢI NHUẬN</th>
                <th className="px-3 py-2.5 text-right">SHARPE</th>
                <th className="px-3 py-2.5 text-right">MAX DRAWDOWN</th>
                <th className="px-3 py-2.5 text-right">WIN RATE</th>
                <th className="py-2.5 pl-2 pr-4 text-center">BIỂU ĐỒ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {histories.map((item) => {
                const isSelected =
                  selectedHistoryId === item.id || activePreview?.id === item.id;
                const isUp = item.total_return >= 0;
                const dateStr = item.executed_at
                  ? new Date(item.executed_at).toLocaleString("vi-VN", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "N/A";

                return (
                  <tr
                    key={item.id}
                    onClick={() => handleRowClick(item)}
                    className={`group cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-emerald-500/15 hover:bg-emerald-500/20"
                        : "hover:bg-slate-800/60"
                    }`}
                  >
                    <td className="py-2.5 pl-4 pr-2 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-slate-500" />
                        <span className="font-mono text-[11px]">{dateStr}</span>
                      </div>
                    </td>

                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-emerald-400">
                          {item.symbol}
                        </span>
                        <div className="flex flex-col">
                          <span className="font-medium text-slate-100 group-hover:text-emerald-300">
                            {item.strategy_name}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {item.strategy_type}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-3 py-2.5 text-slate-400 text-[11px]">
                      {item.start_date} &rarr; {item.end_date}
                    </td>

                    <td className="px-3 py-2.5 text-right font-mono text-slate-300">
                      {item.initial_capital.toLocaleString("vi-VN")} đ
                    </td>

                    <td className="px-3 py-2.5 text-right font-bold">
                      <span
                        className={`inline-flex items-center gap-0.5 ${
                          isUp ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {isUp ? (
                          <ArrowUpRight className="h-3 w-3 stroke-[2.5]" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3 stroke-[2.5]" />
                        )}
                        <span>
                          {isUp ? "+" : ""}
                          {item.total_return.toFixed(2)}%
                        </span>
                      </span>
                    </td>

                    <td className="px-3 py-2.5 text-right font-mono text-slate-200">
                      {item.sharpe_ratio.toFixed(2)}
                    </td>

                    <td className="px-3 py-2.5 text-right font-mono text-rose-400">
                      {item.max_drawdown.toFixed(2)}%
                    </td>

                    <td className="px-3 py-2.5 text-right font-mono text-slate-200">
                      {item.win_rate.toFixed(2)}%
                    </td>

                    <td className="py-2.5 pl-2 pr-4 text-center">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(item);
                        }}
                        title="Xem đường cong vốn"
                        className="inline-flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-[11px] font-semibold text-slate-300 hover:border-emerald-500/50 hover:bg-slate-850 hover:text-emerald-400 transition-all"
                      >
                        <Eye className="h-3 w-3" />
                        <span>Xem</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
