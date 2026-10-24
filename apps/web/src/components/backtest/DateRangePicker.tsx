"use client";

import React, { useMemo } from "react";
import { Calendar, AlertCircle, RefreshCw } from "lucide-react";

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChangeStartDate: (date: string) => void;
  onChangeEndDate: (date: string) => void;
  latestSessionDate?: string;
  sessionLabel?: string;
  onResetLatest?: () => void;
  onSyncMarket?: () => void;
  isSyncing?: boolean;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onChangeStartDate,
  onChangeEndDate,
  latestSessionDate,
  sessionLabel,
  onResetLatest,
  onSyncMarket,
  isSyncing = false,
}) => {
  // Tính khoảng cách giữa 2 ngày (ngày)
  const diffDays = useMemo(() => {
    try {
      const s = new Date(startDate);
      const e = new Date(endDate);
      const diff = Math.round((e.getTime() - s.getTime()) / (1000 * 3600 * 24));
      return isNaN(diff) ? 0 : diff;
    } catch {
      return 0;
    }
  }, [startDate, endDate]);

  const isExceeded = diffDays > 365;
  const isInvalid = diffDays < 0;

  return (
    <div className="w-full flex flex-wrap items-center gap-2">
      {/* Date Range Inputs Box */}
      <div className="relative flex items-center rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-200 shadow-inner max-w-full">
        <Calendar className="mr-1.5 h-3.5 w-3.5 text-emerald-400 shrink-0" />
        
        <input
          type="date"
          value={startDate}
          onChange={(e) => onChangeStartDate(e.target.value)}
          className="bg-transparent text-slate-100 font-semibold focus:outline-none focus:text-emerald-400 cursor-pointer text-xs w-[105px]"
          title="Ngày bắt đầu"
        />
        
        <span className="mx-1 text-slate-500 font-bold">-</span>
        
        <input
          type="date"
          value={endDate}
          onChange={(e) => onChangeEndDate(e.target.value)}
          className="bg-transparent text-slate-100 font-semibold focus:outline-none focus:text-emerald-400 cursor-pointer text-xs w-[105px]"
          title="Ngày kết thúc"
        />

        {/* Tooltip / Cảnh báo chuẩn DNSE khi chọn quá 1 năm */}
        {isExceeded && (
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1.5 whitespace-nowrap rounded-md bg-amber-500/90 px-2 py-0.5 text-[10px] font-bold text-slate-950 shadow-lg animate-fade-in backdrop-blur-sm">
            <AlertCircle className="h-3 w-3" />
            <span>Tối đa 1 năm</span>
          </div>
        )}
      </div>

      {/* Nút / Badge thông tin phiên mới nhất & Tự động đồng bộ */}
      {latestSessionDate && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={onResetLatest}
            title={sessionLabel || `Dữ liệu chốt phiên gần nhất: ${latestSessionDate}. Nhấn để đặt nhanh dải ngày 1 năm tới phiên này.`}
            className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[11px] font-medium transition-all cursor-pointer ${
              endDate === latestSessionDate
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-slate-700 bg-slate-900 text-slate-300 hover:border-emerald-500 hover:text-emerald-400"
            }`}
          >
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>Chốt phiên: <strong className="font-semibold text-white">{latestSessionDate}</strong></span>
          </button>

          {onSyncMarket && (
            <button
              type="button"
              onClick={onSyncMarket}
              disabled={isSyncing}
              title="Cập nhật / kiểm tra dữ liệu nến phiên mới nhất từ thị trường"
              className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900 px-2 py-1 text-[11px] text-slate-400 hover:border-emerald-500/50 hover:text-emerald-400 transition-colors disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`h-3 w-3 ${isSyncing ? "animate-spin text-emerald-400" : ""}`} />
              <span className="hidden sm:inline">{isSyncing ? "Đang đồng bộ..." : "Đồng bộ"}</span>
            </button>
          )}
        </div>
      )}

      {/* Badge Thời gian nến */}
      <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-2 py-1 text-[11px] font-medium text-slate-400">
        <span>Nến:</span>
        <span className="font-bold text-slate-200">1 ngày</span>
      </div>

      {isInvalid && (
        <span className="text-[11px] font-semibold text-rose-400 flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Ngày kết thúc phải sau ngày bắt đầu
        </span>
      )}
    </div>
  );
};
