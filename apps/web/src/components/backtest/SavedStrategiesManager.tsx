"use client";

import React, { useState } from "react";
import {
  Plus,
  Play,
  Edit3,
  Trash2,
  Sparkles,
  Search,
  LayoutGrid,
  List,
  Bot,
  Activity,
} from "lucide-react";
import { SavedStrategyItem } from "@/lib/types";

interface SavedStrategiesManagerProps {
  strategies: SavedStrategyItem[];
  onCreateStrategy: () => void;
  onRunStrategy: (strategy: SavedStrategyItem) => void;
  onEditStrategy: (strategy: SavedStrategyItem) => void;
  onToggleStatus: (strategyId: string) => void;
  onDeleteStrategy: (strategyId: string) => void;
}

export const SavedStrategiesManager: React.FC<SavedStrategiesManagerProps> = ({
  strategies,
  onCreateStrategy,
  onRunStrategy,
  onEditStrategy,
  onToggleStatus,
  onDeleteStrategy,
}) => {
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "draft">("all");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Đếm số lượng theo trạng thái
  const allCount = strategies.length;
  const activeCount = strategies.filter((s) => s.status === "active").length;
  const draftCount = strategies.filter((s) => s.status === "draft").length;

  // Lọc danh sách chiến lược
  const filteredStrategies = strategies.filter((s) => {
    // Lọc theo tab trạng thái
    if (filterStatus === "active" && s.status !== "active") return false;
    if (filterStatus === "draft" && s.status !== "draft") return false;

    // Lọc theo từ khóa tìm kiếm
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = s.name.toLowerCase().includes(q);
      const matchScope =
        (s.symbol && s.symbol.toLowerCase().includes(q)) ||
        (s.index_name && s.index_name.toLowerCase().includes(q)) ||
        (s.sector_name && s.sector_name.toLowerCase().includes(q)) ||
        (s.portfolio_symbols && s.portfolio_symbols.some((sym) => sym.toLowerCase().includes(q)));
      return matchName || matchScope;
    }
    return true;
  });

  return (
    <div className="space-y-4 animate-fade-in">
      {/* 1. THANH ĐIỀU HƯỚNG BỘ LỌC CHUẨN DNSE: TẤT CẢ / TRIỂN KHAI / CHƯA TRIỂN KHAI */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/80 p-3 sm:flex-row sm:items-center sm:justify-between backdrop-blur-md">
        {/* Bộ ba nút Pills: Tất cả, Triển khai, Chưa triển khai */}
        <div className="flex items-center gap-2">
          {/* Tất cả */}
          <button
            type="button"
            onClick={() => setFilterStatus("all")}
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all ${
              filterStatus === "all"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-md shadow-emerald-500/10"
                : "bg-slate-800/60 text-slate-400 border border-slate-700/60 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            <span>Tất cả</span>
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] font-extrabold ${
                filterStatus === "all"
                  ? "bg-emerald-500 text-slate-950"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {allCount}
            </span>
          </button>

          {/* Triển khai */}
          <button
            type="button"
            onClick={() => setFilterStatus("active")}
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all ${
              filterStatus === "active"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-md shadow-emerald-500/10"
                : "bg-slate-800/60 text-slate-400 border border-slate-700/60 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            <span>Triển khai</span>
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] font-extrabold ${
                filterStatus === "active"
                  ? "bg-emerald-500 text-slate-950"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {activeCount}
            </span>
          </button>

          {/* Chưa triển khai */}
          <button
            type="button"
            onClick={() => setFilterStatus("draft")}
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-all ${
              filterStatus === "draft"
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-md shadow-emerald-500/10"
                : "bg-slate-800/60 text-slate-400 border border-slate-700/60 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            <span>Chưa triển khai</span>
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] font-extrabold ${
                filterStatus === "draft"
                  ? "bg-emerald-500 text-slate-950"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {draftCount}
            </span>
          </button>
        </div>

        {/* Công cụ tìm kiếm, Chế độ xem & Nút Tạo chiến thuật */}
        <div className="flex items-center gap-2">
          {/* Ô tìm kiếm */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm chiến lược..."
              className="w-36 rounded-lg border border-slate-700 bg-slate-950 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:w-48 transition-all"
            />
          </div>

          {/* Switch Grid / Table View (chuẩn DNSE ảnh 2) */}
          <div className="flex items-center rounded-lg border border-slate-700 bg-slate-950 p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              className={`rounded p-1 transition-colors ${
                viewMode === "grid"
                  ? "bg-slate-800 text-emerald-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
              title="Xem dạng Lưới"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={`rounded p-1 transition-colors ${
                viewMode === "table"
                  ? "bg-slate-800 text-emerald-400"
                  : "text-slate-400 hover:text-slate-200"
              }`}
              title="Xem dạng Bảng"
            >
              <List className="h-4 w-4" />
            </button>
          </div>

          {/* Nút Tạo chiến thuật mới */}
          <button
            type="button"
            onClick={onCreateStrategy}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-slate-950 shadow-md shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo chiến thuật</span>
          </button>
        </div>
      </div>

      {/* 2. NỘI DUNG DANH SÁCH CHIẾN LƯỢC / EMPTY STATE */}
      {filteredStrategies.length === 0 ? (
        /* GIAO DIỆN EMPTY STATE CHUẨN DNSE VỚI MASCOT */
        <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center backdrop-blur-sm min-h-[420px]">
          {/* Mascot Animation / Illustration */}
          <div className="relative mb-6">
            <div className="flex h-24 w-24 items-center justify-center rounded-3xl border border-slate-700 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 shadow-2xl shadow-emerald-500/10">
              <div className="relative">
                <Bot className="h-12 w-12 text-emerald-400 animate-bounce" />
                <span className="absolute -right-2 -top-1 flex h-4 w-4">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex h-4 w-4 rounded-full bg-emerald-500"></span>
                </span>
              </div>
            </div>
            {/* Cây cảnh / Icon phụ họa bên cạnh giống ảnh DNSE */}
            <div className="absolute -bottom-2 -right-3 flex h-8 w-8 items-center justify-center rounded-xl bg-slate-800 border border-slate-700 text-emerald-400 shadow-md">
              <Sparkles className="h-4 w-4" />
            </div>
          </div>

          <h3 className="text-base font-bold text-slate-100 sm:text-lg">
            {searchQuery
              ? "Không tìm thấy chiến lược phù hợp với từ khóa"
              : filterStatus === "active"
              ? "Chưa có chiến lược nào đang được triển khai"
              : filterStatus === "draft"
              ? "Chưa có chiến lược nháp nào trong danh sách"
              : "Tạo chiến thuật đầu tiên để xây dựng và kiểm thử"}
          </h3>

          <p className="mt-2 max-w-md text-xs text-slate-400 leading-relaxed">
            {searchQuery
              ? `Thử thay đổi từ khóa tìm kiếm hoặc bấm nút "Tất cả" để xem toàn bộ chiến lược.`
              : `Xây dựng chiến thuật giao dịch định lượng kết hợp AI, tùy chỉnh các bộ lọc kỹ thuật (MA, RSI, MACD, Chốt lời, Cắt lỗ) và kiểm thử thực tế trên toàn bộ dữ liệu HOSE/HNX.`}
          </p>

          <button
            type="button"
            onClick={onCreateStrategy}
            className="mt-6 flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-xl shadow-emerald-500/25 hover:bg-emerald-400 active:scale-95 transition-all cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo chiến thuật</span>
          </button>
        </div>
      ) : viewMode === "grid" ? (
        /* DẠNG GRID (THẺ CHIẾN LƯỢC TRỰC QUAN) */
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredStrategies.map((strat) => {
            const isActive = strat.status === "active";
            const metrics = strat.last_metrics;

            // Phạm vi áp dụng
            let scopeLabel = "Cổ phiếu";
            if (strat.scope_type === "index") {
              scopeLabel = `Rổ chỉ số ${strat.index_name || "VN30"}`;
            } else if (strat.scope_type === "sector") {
              scopeLabel = `Ngành ${strat.sector_name || "Tài chính"}`;
            } else if (strat.scope_type === "portfolio") {
              scopeLabel = `Danh mục (${strat.portfolio_symbols?.length || 0} mã)`;
            } else {
              scopeLabel = `Mã ${strat.symbol || "FPT"}`;
            }

            return (
              <div
                key={strat.id}
                className="group flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/70 p-4 transition-all hover:border-slate-700 hover:shadow-xl hover:shadow-emerald-500/5 backdrop-blur-sm"
              >
                <div>
                  {/* Top: Status Badge & Action buttons */}
                  <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {/* Status Pill */}
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                            isActive
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : "bg-slate-800 text-slate-400 border border-slate-700"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              isActive ? "bg-emerald-400 animate-pulse" : "bg-slate-500"
                            }`}
                          />
                          {isActive ? "Triển khai" : "Chưa triển khai"}
                        </span>

                        <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-medium text-slate-400">
                          {strat.model_type === "lstm" ? "LSTM AI" : "LightGBM"}
                        </span>
                      </div>

                      {/* Tên chiến lược */}
                      <h4
                        onClick={() => onEditStrategy(strat)}
                        className="mt-2 text-sm font-bold text-slate-100 hover:text-emerald-400 cursor-pointer transition-colors line-clamp-1"
                        title={strat.name}
                      >
                        {strat.name}
                      </h4>
                    </div>

                    {/* Toggle Status Switch */}
                    <button
                      type="button"
                      onClick={() => onToggleStatus(strat.id)}
                      className={`rounded-lg px-2 py-1 text-[10px] font-bold border transition-colors ${
                        isActive
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-rose-500/10 hover:text-rose-400 hover:border-rose-500/30"
                          : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-emerald-500/10 hover:text-emerald-400 hover:border-emerald-500/30"
                      }`}
                      title={isActive ? "Bấm để tắt triển khai" : "Bấm để kích hoạt triển khai"}
                    >
                      {isActive ? "Đang chạy" : "Kích hoạt"}
                    </button>
                  </div>

                  {/* Phạm vi & Thời gian */}
                  <div className="mt-3 space-y-1.5 text-xs text-slate-400">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-500">Phạm vi:</span>
                      <span className="font-semibold text-slate-300">{scopeLabel}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-500">Khung thời gian:</span>
                      <span className="font-mono text-[11px] text-slate-400">
                        {strat.start_date} → {strat.end_date}
                      </span>
                    </div>
                  </div>

                  {/* Tóm tắt Điều kiện Mua / Bán */}
                  <div className="mt-3 rounded-lg border border-slate-800/80 bg-slate-950/60 p-2.5 space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/20 text-[9px] font-bold text-emerald-400">
                        M
                      </span>
                      <span className="text-[11px] text-slate-300 truncate">
                        {strat.buy_conditions.use_ma && "SMA20 • "}
                        {strat.buy_conditions.use_rsi && `RSI≤${strat.buy_conditions.rsi_threshold || 45} • `}
                        {strat.buy_conditions.use_macd && "MACD • "}
                        {strat.buy_conditions.use_volume_spike && "KLGD đột biến • "}
                        {!strat.buy_conditions.use_ma &&
                          !strat.buy_conditions.use_rsi &&
                          !strat.buy_conditions.use_macd &&
                          !strat.buy_conditions.use_volume_spike &&
                          "Điều kiện cơ bản"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-rose-500/20 text-[9px] font-bold text-rose-400">
                        B
                      </span>
                      <span className="text-[11px] text-slate-300 truncate">
                        {strat.sell_conditions.take_profit_pct
                          ? `Chốt lời +${Math.round(strat.sell_conditions.take_profit_pct * 100)}% • `
                          : ""}
                        {strat.sell_conditions.stop_loss_pct
                          ? `Cắt lỗ -${Math.round(strat.sell_conditions.stop_loss_pct * 100)}% • `
                          : ""}
                        {strat.sell_conditions.trailing_stop_pct
                          ? `Trailing ${Math.round(strat.sell_conditions.trailing_stop_pct * 100)}% • `
                          : ""}
                        {strat.sell_conditions.use_rsi
                          ? `RSI≥${strat.sell_conditions.rsi_sell_threshold || 70}`
                          : ""}
                      </span>
                    </div>
                  </div>

                  {/* Banner trạng thái Triển khai theo dõi tín hiệu Realtime */}
                  {isActive && (
                    <div className="mt-2.5 flex items-center justify-between rounded-lg bg-emerald-500/10 px-2.5 py-1.5 border border-emerald-500/20 text-[11px]">
                      <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                        <Activity className="h-3.5 w-3.5 animate-pulse" />
                        <span>Đang quét tín hiệu realtime</span>
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">Phiên hôm nay</span>
                    </div>
                  )}

                  {/* KPI Metrics nếu đã từng chạy kiểm định */}
                  {metrics ? (
                    <div className="mt-3 space-y-1.5 rounded-lg bg-slate-950/70 p-2.5 border border-slate-800/80">
                      <div className="grid grid-cols-3 gap-1.5 text-center">
                        <div>
                          <div className="text-[10px] text-slate-500">ROI AI</div>
                          <div
                            className={`text-xs font-bold ${
                              metrics.roi_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {metrics.roi_pct > 0 ? "+" : ""}
                            {metrics.roi_pct.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] text-slate-500">Sharpe</div>
                          <div className="text-xs font-bold text-slate-200">
                            {metrics.sharpe.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] text-slate-500">Thắng (Win)</div>
                          <div className="text-xs font-bold text-emerald-400">
                            {metrics.win_rate_pct.toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      {/* Hàng 2: Max Gain, Max Loss, R:R */}
                      {(metrics.max_gain_pct !== undefined || metrics.reward_risk_ratio !== undefined) && (
                        <div className="grid grid-cols-3 gap-1.5 border-t border-slate-800/60 pt-1.5 text-center text-[10px]">
                          <div>
                            <span className="text-slate-500 block">Lãi đỉnh</span>
                            <span className="font-semibold text-emerald-400">
                              {metrics.max_gain_pct !== undefined ? `+${metrics.max_gain_pct.toFixed(1)}%` : "---"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Lỗ sâu</span>
                            <span className="font-semibold text-rose-400">
                              {metrics.max_loss_pct !== undefined ? `${metrics.max_loss_pct.toFixed(1)}%` : "---"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Tỷ lệ R:R</span>
                            <span className="font-semibold text-purple-300">
                              {metrics.reward_risk_ratio ? `${metrics.reward_risk_ratio}` : "---"}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3 rounded-lg border border-dashed border-slate-800 p-2 text-center text-[10px] text-slate-500">
                      Chưa kiểm thử gần đây. Nhấn &ldquo;Chạy kiểm thử&rdquo; bên dưới.
                    </div>
                  )}
                </div>

                {/* Bottom Actions */}
                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3">
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => onEditStrategy(strat)}
                      className="flex items-center gap-1 rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-slate-100 transition-colors"
                      title="Chỉnh sửa cấu hình"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                      <span>Sửa</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeleteStrategy(strat.id)}
                      className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
                      title="Xóa chiến lược"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => onRunStrategy(strat)}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-500/20 px-3 py-1.5 text-xs font-bold text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500 hover:text-slate-950 transition-all cursor-pointer"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Chạy kiểm thử</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* DẠNG BẢNG (TABLE VIEW) */
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-950 text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Tên chiến lược</th>
                  <th className="px-3 py-3 font-semibold">Trạng thái</th>
                  <th className="px-3 py-3 font-semibold">Phạm vi</th>
                  <th className="px-3 py-3 font-semibold">Dải ngày</th>
                  <th className="px-3 py-3 font-semibold">Mô hình</th>
                  <th className="px-3 py-3 font-semibold text-right">ROI AI</th>
                  <th className="px-3 py-3 font-semibold text-right">Sharpe</th>
                  <th className="px-3 py-3 font-semibold text-right">Win Rate</th>
                  <th className="px-4 py-3 text-right font-semibold">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredStrategies.map((strat) => {
                  const isActive = strat.status === "active";
                  const metrics = strat.last_metrics;

                  let scopeLabel = strat.symbol || "FPT";
                  if (strat.scope_type === "index") scopeLabel = `Rổ ${strat.index_name || "VN30"}`;
                  else if (strat.scope_type === "sector") scopeLabel = `Ngành ${strat.sector_name}`;
                  else if (strat.scope_type === "portfolio")
                    scopeLabel = `${strat.portfolio_symbols?.length || 0} mã`;

                  return (
                    <tr key={strat.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-semibold text-slate-200">
                        <button
                          type="button"
                          onClick={() => onEditStrategy(strat)}
                          className="hover:text-emerald-400 font-bold transition-colors text-left"
                        >
                          {strat.name}
                        </button>
                      </td>
                      <td className="px-3 py-3">
                        <button
                          type="button"
                          onClick={() => onToggleStatus(strat.id)}
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-bold border transition-colors ${
                            isActive
                              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 hover:bg-rose-500/10 hover:text-rose-400"
                              : "bg-slate-800 text-slate-400 border-slate-700 hover:bg-emerald-500/10 hover:text-emerald-400"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              isActive ? "bg-emerald-400 animate-pulse" : "bg-slate-500"
                            }`}
                          />
                          {isActive ? "Triển khai" : "Chưa triển khai"}
                        </button>
                      </td>
                      <td className="px-3 py-3 text-slate-300 font-medium">{scopeLabel}</td>
                      <td className="px-3 py-3 font-mono text-[11px] text-slate-400">
                        {strat.start_date} → {strat.end_date}
                      </td>
                      <td className="px-3 py-3 text-slate-400">
                        {strat.model_type === "lstm" ? "LSTM AI" : "LightGBM"}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold">
                        {metrics ? (
                          <span
                            className={metrics.roi_pct >= 0 ? "text-emerald-400" : "text-rose-400"}
                          >
                            {metrics.roi_pct > 0 ? "+" : ""}
                            {metrics.roi_pct.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-slate-500">---</span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold text-slate-300">
                        {metrics ? metrics.sharpe.toFixed(2) : "---"}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold text-emerald-400">
                        {metrics ? `${metrics.win_rate_pct.toFixed(0)}%` : "---"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => onRunStrategy(strat)}
                            className="rounded-lg bg-emerald-500/20 px-2.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500 hover:text-slate-950 transition-all cursor-pointer"
                            title="Chạy kiểm thử"
                          >
                            <Play className="h-3 w-3 fill-current inline-block mr-1" />
                            Chạy
                          </button>
                          <button
                            type="button"
                            onClick={() => onEditStrategy(strat)}
                            className="rounded-lg bg-slate-800 p-1 text-slate-300 hover:text-slate-100 hover:bg-slate-700 transition-colors"
                            title="Chỉnh sửa"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => onDeleteStrategy(strat.id)}
                            className="rounded-lg p-1 text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
                            title="Xóa"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
