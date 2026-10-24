"use client";

import React, { useCallback, useId } from "react";

interface DualRangeSliderProps {
  min: number;
  max: number;
  step?: number;
  valueMin: number;
  valueMax: number;
  onChange: (newMin: number, newMax: number) => void;
  formatValue?: (val: number) => string;
  unit?: string;
  className?: string;
}

export const DualRangeSlider: React.FC<DualRangeSliderProps> = ({
  min,
  max,
  step = 1,
  valueMin,
  valueMax,
  onChange,
  formatValue,
  unit,
  className = "",
}) => {
  const sliderId = useId();

  // Đảm bảo giá trị nằm trong giới hạn [min, max] và min <= max
  const safeMin = Math.max(min, Math.min(valueMin, max));
  const safeMax = Math.max(min, Math.min(valueMax, max));

  // Tính toán phần trăm vị trí để hiển thị thanh đỏ
  const range = max - min || 1;
  const leftPercent = Math.min(100, Math.max(0, ((safeMin - min) / range) * 100));
  const rightPercent = Math.min(100, Math.max(0, ((safeMax - min) / range) * 100));

  const handleMinChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = Math.min(Number(e.target.value), safeMax);
      onChange(val, safeMax);
    },
    [safeMax, onChange]
  );

  const handleMaxChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = Math.max(Number(e.target.value), safeMin);
      onChange(safeMin, val);
    },
    [safeMin, onChange]
  );

  const renderFormatted = (val: number) => {
    if (formatValue) return formatValue(val);
    if (unit) return `${val.toLocaleString("en-US")} ${unit}`;
    return val.toLocaleString("en-US");
  };

  return (
    <div className={`space-y-2 py-1 select-none ${className}`}>
      {/* 2 Giá trị hiển thị ở 2 đầu: Trái (Min) & Phải (Max) */}
      <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
        <span className="font-mono text-slate-300 bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800/80">
          {renderFormatted(safeMin)}
        </span>
        <span className="font-mono text-slate-300 bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800/80">
          {renderFormatted(safeMax)}
        </span>
      </div>

      {/* Vùng thanh trượt Dual Thumbs */}
      <div className="relative flex items-center h-5 w-full">
        {/* Track nền xám đen */}
        <div className="absolute inset-x-0 h-1 rounded-full bg-slate-800" />

        {/* Thanh Highlight màu Đỏ/Coral chuẩn DNSE (#e04f44) */}
        <div
          className="absolute h-1 rounded-full bg-[#e04f44]"
          style={{
            left: `${leftPercent}%`,
            width: `${Math.max(0, rightPercent - leftPercent)}%`,
          }}
        />

        {/* Slider 1: Điều khiển Giá trị Min */}
        <input
          id={`${sliderId}-min`}
          type="range"
          min={min}
          max={max}
          step={step}
          value={safeMin}
          onChange={handleMinChange}
          className="pointer-events-none absolute inset-x-0 h-5 w-full appearance-none bg-transparent 
            [&::-webkit-slider-thumb]:pointer-events-auto 
            [&::-webkit-slider-thumb]:h-4 
            [&::-webkit-slider-thumb]:w-4 
            [&::-webkit-slider-thumb]:appearance-none 
            [&::-webkit-slider-thumb]:rounded-full 
            [&::-webkit-slider-thumb]:bg-white 
            [&::-webkit-slider-thumb]:shadow-md 
            [&::-webkit-slider-thumb]:shadow-black/50 
            [&::-webkit-slider-thumb]:cursor-pointer 
            [&::-webkit-slider-thumb]:border 
            [&::-webkit-slider-thumb]:border-slate-300 
            [&::-webkit-slider-thumb]:active:scale-110 
            [&::-webkit-slider-thumb]:transition-transform
            [&::-moz-range-thumb]:pointer-events-auto 
            [&::-moz-range-thumb]:h-4 
            [&::-moz-range-thumb]:w-4 
            [&::-moz-range-thumb]:rounded-full 
            [&::-moz-range-thumb]:bg-white 
            [&::-moz-range-thumb]:cursor-pointer 
            [&::-moz-range-thumb]:border-none"
        />

        {/* Slider 2: Điều khiển Giá trị Max */}
        <input
          id={`${sliderId}-max`}
          type="range"
          min={min}
          max={max}
          step={step}
          value={safeMax}
          onChange={handleMaxChange}
          className="pointer-events-none absolute inset-x-0 h-5 w-full appearance-none bg-transparent 
            [&::-webkit-slider-thumb]:pointer-events-auto 
            [&::-webkit-slider-thumb]:h-4 
            [&::-webkit-slider-thumb]:w-4 
            [&::-webkit-slider-thumb]:appearance-none 
            [&::-webkit-slider-thumb]:rounded-full 
            [&::-webkit-slider-thumb]:bg-white 
            [&::-webkit-slider-thumb]:shadow-md 
            [&::-webkit-slider-thumb]:shadow-black/50 
            [&::-webkit-slider-thumb]:cursor-pointer 
            [&::-webkit-slider-thumb]:border 
            [&::-webkit-slider-thumb]:border-slate-300 
            [&::-webkit-slider-thumb]:active:scale-110 
            [&::-webkit-slider-thumb]:transition-transform
            [&::-moz-range-thumb]:pointer-events-auto 
            [&::-moz-range-thumb]:h-4 
            [&::-moz-range-thumb]:w-4 
            [&::-moz-range-thumb]:rounded-full 
            [&::-moz-range-thumb]:bg-white 
            [&::-moz-range-thumb]:cursor-pointer 
            [&::-moz-range-thumb]:border-none"
        />
      </div>
    </div>
  );
};
