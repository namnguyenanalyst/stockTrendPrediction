"use client";

import React, { useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  Clock,
  Eye,
  History,
  LineChart,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { UserBacktestHistory } from "@/lib/types";

interface BacktestHistoryTableProps {
  histories: UserBacktestHistory[];
  isLoading: boolean;
  onSelectHistory?: (item: UserBacktestHistory) => void;
  selectedHistoryId?: string | null;
  onRefresh?: () => void;
  onDeleteHistories?: (ids: string[]) => Promise<void> | void;
}

export const BacktestHistoryTable: React.FC<BacktestHistoryTableProps> = ({
  histories,
  isLoading,
  onSelectHistory,
  selectedHistoryId,
  onRefresh,
  onDeleteHistories,
}) => {
  const [activePreview, setActivePreview] = useState<UserBacktestHistory | null>(
    null
  );
  const [isSelectionMode, setIsSelectionMode] = useState<boolean>(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const handleToggleSelectOne = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleToggleSelectAll = () => {
    if (selectedIds.size === histories.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(histories.map((h) => h.id)));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0 || !onDeleteHistories) return;
    const count = selectedIds.size;
    const confirmed = window.confirm(
      `Bạn có chắc chắn muốn xóa ${count} bản ghi nhật ký kiểm thử đã chọn không?`
    );
    if (!confirmed) return;

    setIsDeleting(true);
    try {
      await onDeleteHistories(Array.from(selectedIds));
      if (activePreview && selectedIds.has(activePreview.id)) {
        setActivePreview(null);
      }
      setSelectedIds(new Set());
      setIsSelectionMode(false);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRowClick = (item: UserBacktestHistory) => {
    if (isSelectionMode) {
      handleToggleSelectOne(item.id);
    } else {
      setActivePreview(item);
      onSelectHistory?.(item);
    }
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

        <div className="flex items-center gap-2">
          {/* Nút bật chế độ Chọn để xóa */}
          {histories.length > 0 && (
            <>
              {isSelectionMode ? (
                <div className="flex items-center gap-1.5 animate-fade-in">
                  <button
                    type="button"
                    onClick={handleToggleSelectAll}
                    className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-200 hover:text-white transition-all cursor-pointer"
                  >
                    <span>
                      {selectedIds.size === histories.length
                        ? "Bỏ chọn tất cả"
                        : "Chọn tất cả"}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={handleDeleteSelected}
                    disabled={selectedIds.size === 0 || isDeleting}
                    className="flex items-center gap-1.5 rounded-lg border border-rose-500/40 bg-rose-500/15 px-2.5 py-1 text-xs font-semibold text-rose-300 hover:bg-rose-500 hover:text-white transition-all disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>
                      {isDeleting
                        ? "Đang xóa..."
                        : `Xóa (${selectedIds.size})`}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setIsSelectionMode(false);
                      setSelectedIds(new Set());
                    }}
                    className="rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200 transition-all cursor-pointer"
                  >
                    Hủy
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsSelectionMode(true)}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-800/80 px-2.5 py-1 text-xs font-medium text-slate-300 hover:border-rose-500/40 hover:text-rose-300 hover:bg-rose-500/10 transition-all cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Xóa bản ghi</span>
                </button>
              )}
            </>
          )}

          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isLoading}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1 text-xs text-slate-300 hover:border-slate-700 hover:text-white transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>Làm mới</span>
            </button>
          )}
        </div>
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
            Khi bạn chạy kiểm thử chiến lược tại Phòng Lab, hệ thống sẽ tự động ghi nhận
            kết quả và đường cong vốn vào đây để bạn tiện theo dõi và so sánh hiệu quả qua các lần thử nghiệm.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg backdrop-blur-sm">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-bold text-slate-400">
              <tr>
                {isSelectionMode && (
                  <th className="py-2.5 pl-3 pr-1 w-9 text-center">
                    <button
                      type="button"
                      onClick={handleToggleSelectAll}
                      className="cursor-pointer inline-flex items-center justify-center p-0.5 rounded text-slate-400 hover:text-white"
                      title={selectedIds.size === histories.length ? "Bỏ chọn tất cả" : "Chọn tất cả"}
                    >
                      <div
                        className={`h-4 w-4 rounded-full border transition-all flex items-center justify-center ${
                          selectedIds.size === histories.length && histories.length > 0
                            ? "border-rose-500 bg-rose-500 text-white"
                            : selectedIds.size > 0
                            ? "border-rose-400 bg-rose-500/30 text-rose-300"
                            : "border-slate-600 hover:border-slate-400"
                        }`}
                      >
                        {selectedIds.size > 0 && <Check className="h-2.5 w-2.5 stroke-[3]" />}
                      </div>
                    </button>
                  </th>
                )}
                <th className={`py-2.5 pr-2 ${isSelectionMode ? "pl-2" : "pl-4"}`}>THỜI GIAN THỰC THI</th>
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
                const isChecked = selectedIds.has(item.id);
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
                      isChecked
                        ? "bg-rose-500/10 hover:bg-rose-500/15"
                        : isSelected
                        ? "bg-emerald-500/15 hover:bg-emerald-500/20"
                        : "hover:bg-slate-800/60"
                    }`}
                  >
                    {isSelectionMode && (
                      <td
                        className="py-2.5 pl-3 pr-1 text-center"
                        onClick={(e) => handleToggleSelectOne(item.id, e)}
                      >
                        <div
                          className={`mx-auto h-4 w-4 rounded-full border transition-all flex items-center justify-center cursor-pointer ${
                            isChecked
                              ? "border-rose-500 bg-rose-500 text-white shadow-sm shadow-rose-500/40"
                              : "border-slate-600 group-hover:border-slate-400 bg-slate-900"
                          }`}
                        >
                          {isChecked && <Check className="h-2.5 w-2.5 stroke-[3]" />}
                        </div>
                      </td>
                    )}

                    <td className={`py-2.5 pr-2 text-slate-400 ${isSelectionMode ? "pl-2" : "pl-4"}`}>
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
