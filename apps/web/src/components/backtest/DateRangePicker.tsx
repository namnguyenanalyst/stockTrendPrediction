"use client";

import React, { useMemo } from "react";
import { Calendar, AlertCircle } from "lucide-react";

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onChangeStartDate: (date: string) => void;
  onChangeEndDate: (date: string) => void;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onChangeStartDate,
  onChangeEndDate,
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
    <div className="flex flex-wrap items-center gap-3">
      {/* Date Range Inputs Box */}
      <div className="relative flex items-center rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 shadow-inner">
        <Calendar className="mr-2 h-4 w-4 text-emerald-400 shrink-0" />
        
        <input
          type="date"
          value={startDate}
          onChange={(e) => onChangeStartDate(e.target.value)}
          className="bg-transparent text-slate-100 font-semibold focus:outline-none focus:text-emerald-400 cursor-pointer"
          title="Ngày bắt đầu"
        />
        
        <span className="mx-2 text-slate-500 font-bold">-</span>
        
        <input
          type="date"
          value={endDate}
          onChange={(e) => onChangeEndDate(e.target.value)}
          className="bg-transparent text-slate-100 font-semibold focus:outline-none focus:text-emerald-400 cursor-pointer"
          title="Ngày kết thúc"
        />

        {/* Tooltip / Cảnh báo chuẩn DNSE khi chọn quá 1 năm */}
        {isExceeded && (
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1.5 whitespace-nowrap rounded-md bg-amber-500/90 px-2.5 py-1 text-[11px] font-bold text-slate-950 shadow-lg animate-fade-in backdrop-blur-sm">
            <AlertCircle className="h-3 w-3" />
            <span>Khoảng thời gian chọn không quá 1 năm</span>
          </div>
        )}
      </div>

      {/* Badge Thời gian nến */}
      <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-2.5 py-1.5 text-[11px] font-medium text-slate-400">
        <span>Thời gian nến:</span>
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
