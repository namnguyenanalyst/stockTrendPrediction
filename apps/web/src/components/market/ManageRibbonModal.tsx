"use client";

import React, { useMemo, useState } from "react";
import { Search, X, Activity } from "lucide-react";
import { MarketBoardResponse } from "@/lib/types";

export interface RibbonItemMeta {
  symbol: string;
  name: string;
  category: "index" | "top_search" | "top_volume";
  desc: string;
  price?: number;
  change?: number;
  changePct?: number;
}

// Fallback tĩnh phòng trường hợp API chưa phản hồi kịp
const FALLBACK_ITEMS: RibbonItemMeta[] = [
  // 1. Chỉ số
  { symbol: "VNINDEX", name: "VN-INDEX", category: "index", desc: "Chỉ số toàn bộ cổ phiếu niêm yết trên HSX", price: 1738.67, change: 46.7, changePct: 2.76 },
  { symbol: "VN30", name: "VN30", category: "index", desc: "Chỉ số 30 cổ phiếu vốn hoá lớn nhất trên HSX", price: 1880.55, change: 50.52, changePct: 2.76 },
  { symbol: "HNX", name: "HNX-INDEX", category: "index", desc: "Chỉ số toàn bộ cổ phiếu niêm yết trên HNX", price: 248.28, change: 6.67, changePct: 2.76 },
  { symbol: "HNX30", name: "HNX30", category: "index", desc: "Chỉ số 30 cổ phiếu thanh khoản lớn nhất HNX", price: 443.71, change: 11.92, changePct: 2.76 },
  { symbol: "VN100", name: "VN100", category: "index", desc: "Chỉ số 100 cổ phiếu vốn hoá lớn nhất HSX", price: 1829.08, change: 49.13, changePct: 2.76 },
  { symbol: "UPCOM", name: "UPCOM-INDEX", category: "index", desc: "Chỉ số thị trường cổ phiếu UPCOM", price: 99.10, change: 2.66, changePct: 2.76 },
  { symbol: "VN30F1M", name: "VN30F1M", category: "index", desc: "Hợp đồng tương lai VN30 kỳ hạn gần nhất", price: 1892.02, change: 50.82, changePct: 2.76 },

  // 2. Top tìm kiếm (10 cổ phiếu)
  { symbol: "VIC", name: "Tập đoàn Vingroup", category: "top_search", desc: "Bất động sản & Dịch vụ", price: 45.2, change: 2.9, changePct: 6.99 },
  { symbol: "HPG", name: "Tập đoàn Hòa Phát", category: "top_search", desc: "Thép xây dựng & Công nghiệp", price: 28.1, change: 0.8, changePct: 2.93 },
  { symbol: "FPT", name: "CTCP FPT", category: "top_search", desc: "Công nghệ thông tin & Viễn thông", price: 135.5, change: 1.5, changePct: 1.12 },
  { symbol: "VHM", name: "CTCP Vinhomes", category: "top_search", desc: "Bất động sản nhà ở hàng đầu", price: 42.5, change: 0.7, changePct: 1.67 },
  { symbol: "SSI", name: "Chứng khoán SSI", category: "top_search", desc: "Dịch vụ tài chính & Môi giới", price: 28.5, change: 0.4, changePct: 1.42 },
  { symbol: "VPB", name: "VPBank", category: "top_search", desc: "Ngân hàng TMCP Việt Nam Thịnh Vượng", price: 19.8, change: 0.3, changePct: 1.54 },
  { symbol: "TCB", name: "Techcombank", category: "top_search", desc: "Ngân hàng Kỹ Thương", price: 23.5, change: 0.3, changePct: 1.29 },
  { symbol: "MBB", name: "Ngân hàng Quân Đội", category: "top_search", desc: "Ngân hàng TMCP Quân Đội", price: 24.8, change: 0.2, changePct: 0.81 },
  { symbol: "CTG", name: "VietinBank", category: "top_search", desc: "Ngân hàng Công Thương", price: 30.5, change: 0.05, changePct: 0.16 },
  { symbol: "ACB", name: "Ngân hàng Á Châu", category: "top_search", desc: "Ngân hàng TMCP Á Châu", price: 20.4, change: 0.15, changePct: 0.74 },

  // 3. Top KLGD (10 cổ phiếu)
  { symbol: "HPG", name: "Tập đoàn Hòa Phát", category: "top_volume", desc: "KLGD: 26,155,300 CP", price: 28.1, change: 0.8, changePct: 2.93 },
  { symbol: "VPB", name: "VPBank", category: "top_volume", desc: "KLGD: 18,300,000 CP", price: 19.8, change: 0.3, changePct: 1.54 },
  { symbol: "TCB", name: "Techcombank", category: "top_volume", desc: "KLGD: 15,200,000 CP", price: 23.5, change: 0.3, changePct: 1.29 },
  { symbol: "SSI", name: "Chứng khoán SSI", category: "top_volume", desc: "KLGD: 14,900,000 CP", price: 28.5, change: 0.4, changePct: 1.42 },
  { symbol: "MBB", name: "Ngân hàng Quân Đội", category: "top_volume", desc: "KLGD: 12,850,000 CP", price: 24.8, change: 0.2, changePct: 0.81 },
  { symbol: "VHM", name: "CTCP Vinhomes", category: "top_volume", desc: "KLGD: 11,200,000 CP", price: 42.5, change: 0.7, changePct: 1.67 },
  { symbol: "FPT", name: "CTCP FPT", category: "top_volume", desc: "KLGD: 8,771,500 CP", price: 135.5, change: 1.5, changePct: 1.12 },
  { symbol: "CTG", name: "VietinBank", category: "top_volume", desc: "KLGD: 8,417,200 CP", price: 30.5, change: 0.05, changePct: 0.16 },
  { symbol: "ACB", name: "Ngân hàng Á Châu", category: "top_volume", desc: "KLGD: 8,202,000 CP", price: 20.4, change: 0.15, changePct: 0.74 },
  { symbol: "BID", name: "BIDV", category: "top_volume", desc: "KLGD: 3,246,000 CP", price: 34.1, change: 0.45, changePct: 1.34 },
];

interface ManageRibbonModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeSymbols: string[];
  onUpdateActiveSymbols: (symbols: string[]) => void;
  marketBoard?: MarketBoardResponse | null;
}

export const ManageRibbonModal: React.FC<ManageRibbonModalProps> = ({
  isOpen,
  onClose,
  activeSymbols,
  onUpdateActiveSymbols,
  marketBoard,
}) => {
  const [activeTab, setActiveTab] = useState<"index" | "top_search" | "top_volume">("index");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const activeSet = useMemo(() => new Set(activeSymbols.map((s) => s.toUpperCase())), [activeSymbols]);

  // Xây dựng danh sách mục tự động cập nhật động theo dữ liệu thời gian thực từ Backend
  const dynamicItems = useMemo((): RibbonItemMeta[] => {
    if (!marketBoard) return FALLBACK_ITEMS;

    const items: RibbonItemMeta[] = [];

    // 1. Sub-tab Chỉ số (Toàn bộ 7 chỉ số thị trường cập nhật theo thời gian)
    if (marketBoard.indices && marketBoard.indices.length > 0) {
      marketBoard.indices.forEach((idx) => {
        items.push({
          symbol: idx.symbol,
          name: idx.name,
          category: "index",
          price: idx.value,
          change: idx.change,
          changePct: idx.change_pct,
          desc: `${idx.volume_str} | ${idx.value_str}`,
        });
      });
    }

    // 2. Sub-tab Top tìm kiếm (Top 10 cổ phiếu được quan tâm nhất từ dữ liệu)
    if (marketBoard.top_search && marketBoard.top_search.length > 0) {
      marketBoard.top_search.slice(0, 10).forEach((stk) => {
        const valMil = ((stk.close * stk.volume) / 1_000_000_000).toFixed(1);
        items.push({
          symbol: stk.symbol,
          name: stk.name,
          category: "top_search",
          price: stk.close,
          change: stk.change,
          changePct: stk.change_pct,
          desc: `Ngành: ${stk.sector} • GTGD: ~${valMil} Tỷ VNĐ`,
        });
      });
    }

    // 3. Sub-tab Top KLGD (Top 10 cổ phiếu có khối lượng giao dịch lớn nhất từ dữ liệu)
    if (marketBoard.top_volume && marketBoard.top_volume.length > 0) {
      marketBoard.top_volume.slice(0, 10).forEach((stk) => {
        const volStr = stk.volume.toLocaleString("vi-VN");
        const valMil = ((stk.close * stk.volume) / 1_000_000_000).toFixed(1);
        items.push({
          symbol: stk.symbol,
          name: stk.name,
          category: "top_volume",
          price: stk.close,
          change: stk.change,
          changePct: stk.change_pct,
          desc: `KLGD: ${volStr} CP • ${valMil} Tỷ`,
        });
      });
    }

    // Nếu API trả về chưa đủ 3 category thì bổ sung từ fallback
    if (items.length === 0) return FALLBACK_ITEMS;
    return items;
  }, [marketBoard]);

  const handleToggle = (symbol: string) => {
    const sUpper = symbol.toUpperCase();
    if (activeSet.has(sUpper)) {
      if (activeSymbols.length <= 1) return; // Giữ tối thiểu 1 biểu đồ
      onUpdateActiveSymbols(activeSymbols.filter((s) => s.toUpperCase() !== sUpper));
    } else {
      if (activeSymbols.length >= 12) return; // Tối đa 12 biểu đồ
      onUpdateActiveSymbols([...activeSymbols, sUpper]);
    }
  };

  const handleRemove = (symbol: string) => {
    if (activeSymbols.length <= 1) return;
    const sUpper = symbol.toUpperCase();
    onUpdateActiveSymbols(activeSymbols.filter((s) => s.toUpperCase() !== sUpper));
  };

  const filteredItems = useMemo(() => {
    return dynamicItems.filter((item) => {
      const matchTab = item.category === activeTab;
      if (!matchTab) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.trim().toUpperCase();
      return item.symbol.toUpperCase().includes(q) || item.name.toUpperCase().includes(q);
    });
  }, [dynamicItems, activeTab, searchQuery]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative flex max-h-[85vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl overflow-hidden">
        {/* Header Modal */}
        <div className="flex items-center justify-between border-b border-slate-800/80 px-5 py-3.5">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100">Thêm biểu đồ</h2>
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              <span>Realtime</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Ô tìm kiếm */}
        <div className="border-b border-slate-800/60 p-4">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Tìm mã để thêm chart..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full rounded-xl border border-slate-800 bg-slate-900/90 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Nội dung 2 cột: Cột trái (Đang hiển thị) & Cột phải (Danh sách chọn) */}
        <div className="grid flex-1 grid-cols-1 overflow-hidden sm:grid-cols-12">
          {/* CỘT TRÁI: Biểu đồ đang hiển thị (X/12) */}
          <div className="border-b border-slate-800/80 p-4 sm:col-span-5 sm:border-b-0 sm:border-r overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-300">
                Biểu đồ đang hiển thị
              </span>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-bold text-slate-400">
                {activeSymbols.length}/12
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {activeSymbols.map((sym) => (
                <div
                  key={sym}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700/80 bg-slate-900 px-2.5 py-1 text-xs font-bold text-slate-200 shadow-sm transition-all hover:border-rose-500/50"
                >
                  <span>{sym}</span>
                  <button
                    onClick={() => handleRemove(sym)}
                    className="text-slate-400 hover:text-rose-400"
                    title={`Xóa ${sym}`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
            {activeSymbols.length >= 12 && (
              <p className="mt-3 text-[11px] text-amber-400">
                Đã đạt giới hạn tối đa 12 biểu đồ trên băng chuyền.
              </p>
            )}
          </div>

          {/* CỘT PHẢI: Tabs & Danh sách Thêm / Xóa */}
          <div className="flex flex-col sm:col-span-7 overflow-hidden">
            {/* 3 Sub-tabs (Chỉ số, Top tìm kiếm, Top KLGD) */}
            <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-900/50 px-3 pt-2">
              <div className="flex">
                {[
                  { id: "index" as const, label: "Chỉ số (7)" },
                  { id: "top_search" as const, label: "Top tìm kiếm (10)" },
                  { id: "top_volume" as const, label: "Top KLGD (10)" },
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setActiveTab(t.id)}
                    className={`px-3 py-2 text-xs font-bold border-b-2 transition-all ${
                      activeTab === t.id
                        ? "border-emerald-500 text-emerald-400"
                        : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {marketBoard?.updated_at && (
                <span className="text-[10px] text-slate-500 pr-2">
                  {marketBoard.updated_at.split(" ")[0]}
                </span>
              )}
            </div>

            {/* Danh sách mục của tab đang active */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-[380px]">
              {filteredItems.map((item) => {
                const isAdded = activeSet.has(item.symbol.toUpperCase());
                const isUp = (item.change ?? 0) >= 0;

                return (
                  <div
                    key={`${item.category}-${item.symbol}`}
                    className="flex items-center justify-between rounded-xl border border-slate-800/70 bg-slate-900/40 p-2.5 transition-all hover:border-slate-700 hover:bg-slate-900/80"
                  >
                    <div className="pr-3 flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-xs text-slate-100">
                            {item.symbol}
                          </span>
                          <span className="text-[11px] text-slate-400 font-medium truncate max-w-[150px]">
                            {item.name}
                          </span>
                        </div>

                        {item.price !== undefined && (
                          <div className="flex items-baseline gap-1 text-[11px]">
                            <span className={`font-bold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                              {item.price.toLocaleString("vi-VN", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </span>
                            {item.changePct !== undefined && (
                              <span className={`text-[10px] ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                                ({isUp ? "+" : ""}{item.changePct.toFixed(2)}%)
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <p className="mt-1 text-[10px] text-slate-500 line-clamp-1">
                        {item.desc}
                      </p>
                    </div>

                    <button
                      onClick={() => handleToggle(item.symbol)}
                      className={`ml-2 min-w-[64px] rounded-lg px-3 py-1 text-xs font-bold transition-all ${
                        isAdded
                          ? "border border-rose-500/40 text-rose-400 hover:bg-rose-500/10"
                          : "border border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10"
                      }`}
                    >
                      {isAdded ? "Xóa" : "Thêm"}
                    </button>
                  </div>
                );
              })}

              {filteredItems.length === 0 && (
                <div className="py-8 text-center text-xs text-slate-500">
                  Không tìm thấy mục nào phù hợp với từ khóa.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Modal */}
        <div className="flex items-center justify-between border-t border-slate-800/80 bg-slate-950 px-5 py-3 text-xs text-slate-400">
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <Activity className="h-3.5 w-3.5 text-emerald-400" />
            <span>Tự động cập nhật theo chu kỳ 10s</span>
          </div>

          <button
            onClick={onClose}
            className="rounded-xl bg-emerald-500 px-5 py-1.5 text-xs font-bold text-slate-950 shadow-md shadow-emerald-500/20 hover:bg-emerald-400"
          >
            Hoàn tất
          </button>
        </div>
      </div>
    </div>
  );
};
