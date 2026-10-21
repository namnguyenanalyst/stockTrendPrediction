"use client";

import React from "react";
import {
  ChevronDown,
  ChevronUp,
  Plus,
} from "lucide-react";
import { IndexOverview, StockBoardItem } from "@/lib/types";

// Component Sparkline mini SVG
const MiniSparkline: React.FC<{ data: number[]; isUp: boolean }> = ({ data, isUp }) => {
  if (!data || data.length < 2) {
    return <div className="h-6 w-20 rounded bg-slate-900/40" />;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 80;
  const height = 24;

  const points = data
    .map((val, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const color = isUp ? "#10b981" : "#ef4444";

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

export interface DisplayRibbonCard {
  symbol: string;
  name: string;
  value: number;
  change: number;
  changePct: number;
  volumeStr: string;
  valueStr: string;
  advancing?: number;
  ceiling?: number;
  unchanged?: number;
  declining?: number;
  floor?: number;
  sparkline: number[];
  isStock?: boolean;
}

interface IndexRibbonProps {
  indices: IndexOverview[];
  stocks?: StockBoardItem[];
  activeSymbols: string[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onOpenManageModal: () => void;
  onSelectCard: (card: DisplayRibbonCard) => void;
}

export const IndexRibbon: React.FC<IndexRibbonProps> = ({
  indices,
  stocks = [],
  activeSymbols,
  isCollapsed,
  onToggleCollapse,
  onOpenManageModal,
  onSelectCard,
}) => {
  // Bản đồ tra cứu index
  const indexMap = new Map<string, IndexOverview>();
  indices.forEach((idx) => indexMap.set(idx.symbol.toUpperCase(), idx));

  // Bản đồ tra cứu stock
  const stockMap = new Map<string, StockBoardItem>();
  stocks.forEach((stk) => stockMap.set(stk.symbol.toUpperCase(), stk));

const DEFAULT_FALLBACK_CARDS: Record<string, DisplayRibbonCard> = {
  VNINDEX: {
    symbol: "VNINDEX",
    name: "VN-INDEX",
    value: 1738.67,
    change: 46.7,
    changePct: 2.76,
    volumeStr: "947.79 Triệu CP",
    valueStr: "20,290.59 Tỷ",
    advancing: 246,
    ceiling: 16,
    unchanged: 54,
    declining: 78,
    floor: 3,
    sparkline: [1710, 1715, 1720, 1738.67],
    isStock: false,
  },
  VN30: {
    symbol: "VN30",
    name: "VN30",
    value: 1880.55,
    change: 50.52,
    changePct: 2.76,
    volumeStr: "333.31 Triệu CP",
    valueStr: "10,350.85 Tỷ",
    advancing: 25,
    ceiling: 3,
    unchanged: 4,
    declining: 1,
    floor: 0,
    sparkline: [1850, 1860, 1870, 1880.55],
    isStock: false,
  },
  HNX: {
    symbol: "HNX",
    name: "HNX-INDEX",
    value: 248.28,
    change: 6.67,
    changePct: 2.76,
    volumeStr: "85.20 Triệu CP",
    valueStr: "1,450.20 Tỷ",
    advancing: 112,
    ceiling: 8,
    unchanged: 58,
    declining: 65,
    floor: 2,
    sparkline: [242, 244, 246, 248.28],
    isStock: false,
  },
  HNX30: {
    symbol: "HNX30",
    name: "HNX30",
    value: 443.71,
    change: 11.92,
    changePct: 2.76,
    volumeStr: "61.51 Triệu CP",
    valueStr: "954.83 Tỷ",
    advancing: 16,
    ceiling: 0,
    unchanged: 4,
    declining: 9,
    floor: 0,
    sparkline: [433, 436, 440, 443.71],
    isStock: false,
  },
  VN100: {
    symbol: "VN100",
    name: "VN100",
    value: 1829.08,
    change: 49.13,
    changePct: 2.76,
    volumeStr: "520.45 Triệu CP",
    valueStr: "15,820.40 Tỷ",
    advancing: 72,
    ceiling: 6,
    unchanged: 10,
    declining: 18,
    floor: 1,
    sparkline: [1790, 1805, 1820, 1829.08],
    isStock: false,
  },
  UPCOM: {
    symbol: "UPCOM",
    name: "UPCOM-INDEX",
    value: 99.10,
    change: 2.66,
    changePct: 2.76,
    volumeStr: "45.10 Triệu CP",
    valueStr: "620.50 Tỷ",
    advancing: 150,
    ceiling: 12,
    unchanged: 90,
    declining: 85,
    floor: 4,
    sparkline: [97, 97.5, 98.2, 99.1],
    isStock: false,
  },
  VN30F1M: {
    symbol: "VN30F1M",
    name: "VN30F1M",
    value: 1892.02,
    change: 50.82,
    changePct: 2.76,
    volumeStr: "237,641 HĐ",
    valueStr: "44,428.87 Tỷ",
    advancing: 1,
    ceiling: 0,
    unchanged: 0,
    declining: 0,
    floor: 0,
    sparkline: [1860, 1875, 1885, 1892.02],
    isStock: false,
  },
};

  // Tạo danh sách các card hiển thị theo thứ tự activeSymbols
  const displayCards: DisplayRibbonCard[] = activeSymbols
    .map((sym): DisplayRibbonCard => {
      const sUpper = sym.toUpperCase();
      if (indexMap.has(sUpper)) {
        const idx = indexMap.get(sUpper)!;
        return {
          symbol: idx.symbol,
          name: idx.name,
          value: idx.value,
          change: idx.change,
          changePct: idx.change_pct,
          volumeStr: idx.volume_str,
          valueStr: idx.value_str,
          advancing: idx.advancing,
          ceiling: idx.ceiling,
          unchanged: idx.unchanged,
          declining: idx.declining,
          floor: idx.floor,
          sparkline: idx.sparkline,
          isStock: false,
        };
      } else if (stockMap.has(sUpper)) {
        const stk = stockMap.get(sUpper)!;
        return {
          symbol: stk.symbol,
          name: stk.name,
          value: stk.close,
          change: stk.change,
          changePct: stk.change_pct,
          volumeStr: `${(stk.volume / 1000).toLocaleString("vi-VN")}k CP`,
          valueStr: stk.sector,
          sparkline: stk.sparkline,
          isStock: true,
        };
      } else if (DEFAULT_FALLBACK_CARDS[sUpper]) {
        return DEFAULT_FALLBACK_CARDS[sUpper];
      }

      // Fallback cho mã bất kỳ chưa có trong danh mục
      return {
        symbol: sUpper,
        name: sUpper,
        value: 20.0,
        change: 0.0,
        changePct: 0.0,
        volumeStr: "---",
        valueStr: "HOSE",
        sparkline: [20.0, 20.0],
        isStock: true,
      };
    });

  // Nếu đang ở trạng thái thu gọn ("Đóng") - Hiển thị dải ngang chỉ số rút gọn chuẩn DNSE
  if (isCollapsed) {
    return (
      <div className="flex h-9 items-center justify-between rounded-xl border border-slate-800/80 bg-slate-900/80 px-2 shadow-md backdrop-blur-sm transition-all">
        {/* Dải các chỉ số / cổ phiếu thu gọn xếp theo hàng ngang */}
        <div className="flex flex-1 items-center gap-1.5 overflow-x-auto py-1 pr-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {displayCards.map((card, idx) => {
            const isUp = card.change >= 0;
            return (
              <React.Fragment key={card.symbol}>
                <div
                  onClick={() => onSelectCard(card)}
                  className="group flex flex-shrink-0 cursor-pointer items-center gap-1.5 rounded-md px-2 py-0.5 text-xs transition-colors hover:bg-slate-800/80"
                  title={`Nhấp để xem biểu đồ kỹ thuật ${card.symbol}`}
                >
                  <span className="font-bold tracking-tight text-slate-300 group-hover:text-emerald-400 transition-colors">
                    {card.symbol}
                  </span>
                  <span
                    className={`font-black ${
                      isUp ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {card.value.toLocaleString("vi-VN", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>
                  <span
                    className={`flex items-center text-[11px] font-semibold ${
                      isUp ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isUp ? "▲" : "▼"} {isUp ? "+" : ""}
                    {card.change.toFixed(2)} ({isUp ? "+" : ""}
                    {card.changePct.toFixed(2)}%)
                  </span>
                </div>

                {idx < displayCards.length - 1 && (
                  <div className="h-3.5 w-px flex-shrink-0 bg-slate-800/80" />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Cụm điều khiển bên phải: Nút "+" và Nút "Mở" */}
        <div className="flex flex-shrink-0 items-center gap-1.5 border-l border-slate-800/80 pl-2">
          <button
            onClick={onOpenManageModal}
            className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-700 bg-slate-800/90 text-slate-300 shadow-sm transition-all hover:scale-105 hover:border-emerald-500 hover:bg-emerald-500/10 hover:text-emerald-400 active:scale-95"
            title="Thêm / Quản lý biểu đồ hiển thị"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={onToggleCollapse}
            className="flex items-center gap-0.5 rounded-lg px-2 py-1 text-xs font-bold text-slate-400 transition-colors hover:text-slate-100"
            title="Mở rộng băng chuyền đầy đủ"
          >
            <ChevronDown className="h-3.5 w-3.5" />
            <span>Mở</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex items-stretch gap-2 transition-all">
      {/* KHỐI 1: DANH SÁCH CÁC CARD CHỈ SỐ (CUỘN NGANG HOẶC CO GIÃN) */}
      <div className="flex-1 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5">
        {displayCards.map((card) => {
          const isUp = card.change >= 0;
          return (
            <div
              key={card.symbol}
              onClick={() => onSelectCard(card)}
              className="group relative flex cursor-pointer flex-col justify-between overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/70 p-3 shadow-md backdrop-blur-sm transition-all hover:border-emerald-500/50 hover:bg-slate-900/90 hover:shadow-emerald-500/10"
              title={`Nhấp để mở biểu đồ nến chi tiết của ${card.symbol}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold tracking-tight text-slate-200 group-hover:text-emerald-400 transition-colors">
                    {card.name}
                  </span>
                  {card.symbol === "VNINDEX" && (
                    <span className="rounded bg-emerald-500/10 px-1.5 py-0.2 text-[9px] font-bold text-emerald-400">
                      HOSE
                    </span>
                  )}
                  {card.isStock && (
                    <span className="rounded bg-slate-800 px-1 py-0.2 text-[8px] font-bold text-slate-400">
                      CP
                    </span>
                  )}
                </div>
                <span
                  className={`flex items-center text-xs font-bold ${
                    isUp ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {isUp ? "+" : ""}
                  {card.changePct.toFixed(2)}%
                </span>
              </div>

              <div className="mt-1 flex items-baseline justify-between">
                <div>
                  <span
                    className={`text-lg font-black tracking-tight ${
                      isUp ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {card.value.toLocaleString("vi-VN", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>
                  <span
                    className={`ml-1 text-[11px] font-medium ${
                      isUp ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {isUp ? "+" : ""}
                    {card.change.toFixed(2)}
                  </span>
                </div>

                {/* Sparkline mini */}
                <div className="opacity-90 transition-opacity group-hover:opacity-100">
                  <MiniSparkline data={card.sparkline} isUp={isUp} />
                </div>
              </div>

              {/* Khối lượng & Giá trị giao dịch */}
              <div className="mt-1.5 flex items-center justify-between border-t border-slate-800/60 pt-1 text-[10px] text-slate-400">
                <span>{card.volumeStr}</span>
                <span className="font-semibold text-slate-300">{card.valueStr}</span>
              </div>

              {/* Thống kê độ rộng thị trường mini (với chỉ số sàn) */}
              {card.advancing !== undefined && card.advancing > 0 && (
                <div className="mt-1 flex items-center gap-1 text-[9px]">
                  <span className="flex items-center gap-0.5 text-emerald-400 font-medium">
                    ▲{card.advancing}
                    {card.ceiling ? (
                      <span className="text-purple-400 font-bold">({card.ceiling})</span>
                    ) : null}
                  </span>
                  <span className="text-amber-400 font-medium">■{card.unchanged}</span>
                  <span className="flex items-center gap-0.5 text-rose-400 font-medium">
                    ▼{card.declining}
                    {card.floor ? (
                      <span className="text-cyan-400 font-bold">({card.floor})</span>
                    ) : null}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* KHỐI 2: CỤM ĐIỀU KHIỂN BÊN PHẢI (NÚT "ĐÓNG" + NÚT "+") - CHUẨN SCREENSHOT 2 */}
      <div className="flex w-[52px] flex-col items-center justify-between rounded-xl border border-slate-800/80 bg-slate-900/60 p-2 shadow-md backdrop-blur-sm">
        {/* Nút "Đóng" kèm icon thu gọn */}
        <button
          onClick={onToggleCollapse}
          className="group flex flex-col items-center gap-0.5 text-slate-400 transition-colors hover:text-slate-100"
          title="Thu gọn băng chuyền"
        >
          <ChevronUp className="h-3.5 w-3.5 transition-transform group-hover:-translate-y-0.5" />
          <span className="text-[10px] font-bold">Đóng</span>
        </button>

        {/* Nút tròn dấu cộng "+" để thêm/bớt biểu đồ */}
        <button
          onClick={onOpenManageModal}
          className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-700 bg-slate-800/90 text-slate-300 shadow-inner transition-all hover:scale-105 hover:border-emerald-500 hover:bg-emerald-500/10 hover:text-emerald-400 active:scale-95"
          title="Thêm / Quản lý biểu đồ hiển thị"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
