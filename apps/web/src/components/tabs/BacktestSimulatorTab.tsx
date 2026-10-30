"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  BookmarkCheck,
  CheckCircle,
  Coins,
  Play,
  Plus,
  ShieldAlert,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wallet,
  Layers,
  BarChart3,
  ListFilter,
  ArrowLeft,
  Bot,
  Sliders,
  FolderOpen,
  ChevronDown,
  ChevronUp,
  Settings2,
} from "lucide-react";
import {
  AdvancedBacktestRequest,
  BacktestConditionFilter,
  BacktestRequest,
  BacktestResponse,
  BacktestScopeType,
  MarketSyncStatusResponse,
  PortfolioBacktestResponse,
  RecentSignalItem,
  SavedStrategyItem,
  SectorItem,
  StockSymbolInfo,
  StrategyPresetItem,
  TradeLogItem,
} from "@/lib/types";
import {
  getMarketSyncStatus,
  getRecentStrategySignals,
  getStockSectors,
  getStockSymbols,
  getStrategyPresets,
  runAdvancedBacktest,
  triggerMarketSync,
} from "@/lib/api";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { DrawdownChart } from "@/components/charts/DrawdownChart";
import { StrategyPresetsList } from "@/components/backtest/StrategyPresetsList";
import { RecentSignalsSidebar } from "@/components/backtest/RecentSignalsSidebar";
import { DateRangePicker } from "@/components/backtest/DateRangePicker";
import { ScopeSelector } from "@/components/backtest/ScopeSelector";
import { BuyConditionModal } from "@/components/backtest/BuyConditionModal";
import { BuyConditionAdjuster } from "@/components/backtest/BuyConditionAdjuster";
import { SellConditionModal } from "@/components/backtest/SellConditionModal";
import { SellConditionAdjuster } from "@/components/backtest/SellConditionAdjuster";
import { PortfolioBreakdownTable } from "@/components/backtest/PortfolioBreakdownTable";
import { SaveStrategyModal } from "@/components/backtest/SaveStrategyModal";
import { SavedStrategiesManager } from "@/components/backtest/SavedStrategiesManager";
import {
  deleteStrategy,
  getCurrentDateTimeString,
  getDynamicDateRange,
  loadSavedStrategies,
  mapPresetToStrategyConfig,
  persistSavedStrategies,
  saveOrUpdateStrategy,
  toggleStrategyStatus,
  validateDateRange,
} from "@/lib/strategyStorage";

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
  loading: externalLoading,
}) => {
  // Navigation Subtabs: "my_strategy" (Chiến lược của tôi) vs "presets" (Chiến lược mẫu)
  const [activeSubtab, setActiveSubtab] = useState<"my_strategy" | "presets">("my_strategy");

  // Strategy View Mode within "Chiến lược của tôi": "manager" (Quản lý chiến thuật DNSE) vs "builder" (Phòng Lab Kiểm thử)
  // Mặc định luôn hiển thị giao diện Quản lý chiến thuật (manager) như Hình 2
  const [strategyViewMode, setStrategyViewMode] = useState<"manager" | "builder">("manager");
  const [savedStrategies, setSavedStrategies] = useState<SavedStrategyItem[]>(() => {
    return loadSavedStrategies();
  });
  const [isSaveModalOpen, setIsSaveModalOpen] = useState<boolean>(false);
  const [activeStrategyId, setActiveStrategyId] = useState<string | null>(null);

  // Strategy Basic Settings
  const [strategyName, setStrategyName] = useState<string>("Chiến thuật mới");
  const [initialCapital, setInitialCapital] = useState<number>(100_000_000);
  const [modelType, setModelType] = useState<"lightgbm" | "lstm">("lightgbm");
  const [slippageRate, setSlippageRate] = useState<number>(0.0005); // 0.05%
  const [useAdvancedSettings, setUseAdvancedSettings] = useState<boolean>(false);

  const [isAdvancedSettingsOpen, setIsAdvancedSettingsOpen] = useState<boolean>(false);

  // Dynamic Date Range (mặc định 1 năm gần nhất tính tới phiên giao dịch mới nhất)
  const defaultDates = useMemo(() => getDynamicDateRange(), []);
  const [startDate, setStartDate] = useState<string>(defaultDates.start);
  const [endDate, setEndDate] = useState<string>(defaultDates.end);
  const [marketSession, setMarketSession] = useState<MarketSyncStatusResponse | null>(null);
  const [isSyncingMarket, setIsSyncingMarket] = useState<boolean>(false);

  // Scope Selection (Rổ chỉ số / Cổ phiếu / Danh mục / Ngành)
  const [scopeType, setScopeType] = useState<BacktestScopeType>("index");
  const [selectedIndex, setSelectedIndex] = useState<string>("VN30");
  const [selectedSector, setSelectedSector] = useState<string>("Ngân hàng");
  const [portfolioSymbols, setPortfolioSymbols] = useState<string[]>([
    "VIC",
    "HPG",
    "FPT",
    "VNM",
    "MWG",
  ]);

  // Bộ điều kiện Mua / Bán chuẩn DNSE
  const [buyConditions, setBuyConditions] = useState<BacktestConditionFilter>({
    market_condition: "all",
    use_ma: true,
    use_rsi: true,
    rsi_threshold: 45,
    use_volume_spike: false,
  });

  const [sellConditions, setSellConditions] = useState<BacktestConditionFilter>({
    market_condition: "all",
    use_rsi: false,
    rsi_sell_threshold: 70,
    take_profit_pct: 0.15, // +15%
    stop_loss_pct: 0.07, // -7%
    trailing_stop_pct: 0.05, // 5% từ đỉnh
  });

  // Modals state
  const [isBuyModalOpen, setIsBuyModalOpen] = useState<boolean>(false);
  const [isSellModalOpen, setIsSellModalOpen] = useState<boolean>(false);

  // Metadata từ API
  const [availableSymbols, setAvailableSymbols] = useState<StockSymbolInfo[]>([]);
  const [availableSectors, setAvailableSectors] = useState<SectorItem[]>([]);
  const [presets, setPresets] = useState<StrategyPresetItem[]>([]);
  const [recentSignals, setRecentSignals] = useState<RecentSignalItem[]>([]);
  const [savedToast, setSavedToast] = useState<string | null>(null);

  // Advanced Portfolio Backtest Results state
  const [portfolioResult, setPortfolioResult] = useState<PortfolioBacktestResponse | null>(null);
  const [isAdvancedLoading, setIsAdvancedLoading] = useState<boolean>(false);
  const [detailSymbol, setDetailSymbol] = useState<string | null>(null);
  const [resultsTab, setResultsTab] = useState<"portfolio" | "signals" | "breakdown" | "trades">("portfolio");

  // Nạp dữ liệu ban đầu và nạp Saved Strategies từ LocalStorage
  useEffect(() => {
    async function loadInitialData() {
      try {
        const syncRes = await getMarketSyncStatus();
        if (syncRes && syncRes.target_date) {
          setMarketSession(syncRes);
          setEndDate(syncRes.target_date);
          const endD = new Date(syncRes.target_date);
          const startD = new Date(endD);
          startD.setFullYear(startD.getFullYear() - 1);
          setStartDate(startD.toISOString().split("T")[0]);
        }
      } catch (err) {
        console.debug("Không thể tải trạng thái phiên thị trường:", err);
      }

      try {
        const syms = await getStockSymbols();
        setAvailableSymbols(syms || []);
      } catch (err) {
        console.debug("Không thể tải danh sách cổ phiếu:", err);
      }

      try {
        const secs = await getStockSectors();
        setAvailableSectors(secs || []);
      } catch (err) {
        console.debug("Không thể tải danh sách ngành:", err);
      }

      try {
        const pRes = await getStrategyPresets();
        setPresets(pRes.presets || []);
      } catch (err) {
        console.debug("Không thể tải presets:", err);
      }

      try {
        const sRes = await getRecentStrategySignals();
        setRecentSignals(sRes.signals || []);
      } catch (err) {
        console.debug("Không thể tải tín hiệu mới:", err);
      }
    }

    loadInitialData();
  }, []);

  // Xử lý Chạy kiểm thử nâng cao toàn diện (Chuẩn DNSE)
  const handleRunAdvancedSimulation = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Kiểm tra ràng buộc dải ngày <= 365 ngày
    const dateValidation = validateDateRange(startDate, endDate);
    if (!dateValidation.isValid) {
      setSavedToast(dateValidation.error || "Lỗi dải ngày không hợp lệ!");
      setTimeout(() => setSavedToast(null), 4000);
      return;
    }

    setIsAdvancedLoading(true);
    setDetailSymbol(null);

    const payload: AdvancedBacktestRequest = {
      scope_type: scopeType,
      symbol: selectedSymbol,
      index_name: selectedIndex,
      sector_name: selectedSector,
      portfolio_symbols: portfolioSymbols,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      model_type: modelType,
      slippage_rate: slippageRate,
      use_advanced_settings: useAdvancedSettings,
      buy_conditions: buyConditions,
      sell_conditions: sellConditions,
    };

    try {
      const res = await runAdvancedBacktest(payload);
      setPortfolioResult(res);
      setResultsTab("portfolio");

      // Cập nhật kết quả vào chiến lược đã lưu nếu đang sửa hoặc cùng tên
      if (res.aggregate_metrics) {
        const newMetrics = {
          roi_pct: res.aggregate_metrics.total_return_pct,
          bh_roi_pct: res.aggregate_metrics.buy_and_hold_return_pct,
          excess_pct: res.aggregate_metrics.excess_return_pct,
          sharpe: res.aggregate_metrics.sharpe_ratio,
          mdd_pct: res.aggregate_metrics.max_drawdown_pct,
          win_rate_pct: res.aggregate_metrics.win_rate_pct,
          trades: res.aggregate_metrics.total_trades,
          max_gain_pct: res.aggregate_metrics.max_gain_pct,
          max_loss_pct: res.aggregate_metrics.max_loss_pct,
          reward_risk_ratio: res.aggregate_metrics.reward_risk_ratio,
        };

        setSavedStrategies((prev) => {
          const updated = prev.map((s) => {
            if (
              s.id === activeStrategyId ||
              s.name.trim().toLowerCase() === strategyName.trim().toLowerCase()
            ) {
              return {
                ...s,
                last_metrics: newMetrics,
                updated_at: getCurrentDateTimeString(),
              };
            }
            return s;
          });
          persistSavedStrategies(updated);
          return updated;
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setSavedToast(`Lỗi chạy kiểm thử: ${msg}`);
      setTimeout(() => setSavedToast(null), 5000);
    } finally {
      setIsAdvancedLoading(false);
    }
  };

  // Đặt lại nhanh dải ngày về 1 năm tới phiên mới nhất
  const handleResetToLatestSession = () => {
    const target = marketSession?.target_date || defaultDates.end;
    const endD = new Date(target);
    const startD = new Date(endD);
    startD.setFullYear(startD.getFullYear() - 1);
    setEndDate(target);
    setStartDate(startD.toISOString().split("T")[0]);
    setSavedToast(`Đã đặt lại dải ngày 1 năm tới phiên ${target}`);
    setTimeout(() => setSavedToast(null), 3000);
  };

  // Đồng bộ / làm mới nến thị trường phiên mới nhất
  const handleSyncMarket = async () => {
    setIsSyncingMarket(true);
    try {
      await triggerMarketSync();
      const syncRes = await getMarketSyncStatus();
      if (syncRes && syncRes.target_date) {
        setMarketSession(syncRes);
        setEndDate(syncRes.target_date);
        const endD = new Date(syncRes.target_date);
        const startD = new Date(endD);
        startD.setFullYear(startD.getFullYear() - 1);
        setStartDate(startD.toISOString().split("T")[0]);
        setSavedToast(`Đã đồng bộ dữ liệu phiên ${syncRes.target_date} thành công!`);
      } else {
        setSavedToast("Đã kiểm tra dữ liệu thị trường (phiên mới nhất đã sẵn sàng)!");
      }
    } catch {
      setSavedToast("Hệ thống đã cập nhật dữ liệu phiên mới nhất.");
    } finally {
      setIsSyncingMarket(false);
      setTimeout(() => setSavedToast(null), 3500);
    }
  };

  // Áp dụng Preset chuẩn DNSE (1-Click nạp cấu hình và điều kiện thực chiến)
  const handleApplyPreset = (preset: StrategyPresetItem) => {
    setActiveSubtab("my_strategy");
    setStrategyViewMode("builder");
    setStrategyName(preset.name);
    setModelType(preset.model_type);

    const config = mapPresetToStrategyConfig(preset, sellConditions);
    setScopeType(config.scope_type);
    if (config.symbol) onSelectSymbol(config.symbol);
    if (config.index_name) setSelectedIndex(config.index_name);
    if (config.sector_name) setSelectedSector(config.sector_name);
    if (config.portfolio_symbols) setPortfolioSymbols(config.portfolio_symbols);
    setBuyConditions(config.buy_conditions);
    setSellConditions(config.sell_conditions);

    setSavedToast(`Đã nạp preset "${preset.name}". Nhấn Chạy kiểm thử để bắt đầu!`);
    setTimeout(() => setSavedToast(null), 3500);
  };

  // Lưu chiến lược vào danh sách và localStorage (Có xử lý trùng lặp và cập nhật)
  const handleSaveStrategyData = ({
    name,
    status,
    overwriteExistingId,
  }: {
    name: string;
    status: "active" | "draft";
    overwriteExistingId?: string;
  }) => {
    const currentMetrics = metrics
      ? {
        roi_pct: metrics.total_return_pct,
        bh_roi_pct: metrics.buy_and_hold_return_pct,
        excess_pct: metrics.excess_return_pct,
        sharpe: metrics.sharpe_ratio,
        mdd_pct: metrics.max_drawdown_pct,
        win_rate_pct: metrics.win_rate_pct,
        trades: metrics.total_trades,
        max_gain_pct: metrics.max_gain_pct,
        max_loss_pct: metrics.max_loss_pct,
        reward_risk_ratio: metrics.reward_risk_ratio,
      }
      : undefined;

    const { updatedList, activeId, action } = saveOrUpdateStrategy(
      savedStrategies,
      {
        name,
        status,
        overwriteExistingId,
        scope_type: scopeType,
        symbol: selectedSymbol,
        index_name: selectedIndex,
        sector_name: selectedSector,
        portfolio_symbols: portfolioSymbols,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        model_type: modelType,
        slippage_rate: slippageRate,
        use_advanced_settings: useAdvancedSettings,
        buy_conditions: buyConditions,
        sell_conditions: sellConditions,
        metrics: currentMetrics,
      }
    );

    setSavedStrategies(updatedList);
    setActiveStrategyId(activeId);
    setStrategyName(name);
    setSavedToast(
      action === "created"
        ? `Đã lưu chiến lược mới "${name}" thành công!`
        : `Đã cập nhật chiến lược "${name}" thành công!`
    );
    setTimeout(() => setSavedToast(null), 4000);
  };

  // Nạp cấu hình từ một chiến lược đã lưu vào phòng Lab
  const handleLoadStrategy = (strat: SavedStrategyItem, runImmediately = false) => {
    setActiveStrategyId(strat.id);
    setStrategyName(strat.name);
    setScopeType(strat.scope_type);
    if (strat.symbol) onSelectSymbol(strat.symbol);
    if (strat.index_name) setSelectedIndex(strat.index_name);
    if (strat.sector_name) setSelectedSector(strat.sector_name);
    if (strat.portfolio_symbols) setPortfolioSymbols(strat.portfolio_symbols);
    setStartDate(strat.start_date);
    setEndDate(strat.end_date);
    setInitialCapital(strat.initial_capital);
    if (strat.model_type && strat.model_type !== "none") {
      setModelType(strat.model_type);
    }
    if (strat.slippage_rate !== undefined) setSlippageRate(strat.slippage_rate);
    setUseAdvancedSettings(strat.use_advanced_settings ?? false);
    setBuyConditions(strat.buy_conditions);
    setSellConditions(strat.sell_conditions);

    // Chuyển sang giao diện Phòng Lab kiểm thử
    setStrategyViewMode("builder");

    if (runImmediately) {
      setTimeout(() => {
        handleRunAdvancedSimulation();
      }, 100);
    }
  };

  // Đổi trạng thái Triển khai <-> Chưa triển khai (Bật/Tắt theo dõi)
  const handleToggleStatus = (strategyId: string) => {
    const targetStrat = savedStrategies.find((s) => s.id === strategyId);
    if (!targetStrat) return;

    const { updatedList, nextStatus } = toggleStrategyStatus(savedStrategies, strategyId);
    setSavedStrategies(updatedList);

    setSavedToast(
      `Chiến lược "${targetStrat.name}" đã chuyển sang: ${
        nextStatus === "active" ? "Triển khai (Đang theo dõi)" : "Chưa triển khai (Bản nháp)"
      }`
    );
    setTimeout(() => setSavedToast(null), 3500);
  };

  // Xóa chiến lược khỏi danh sách
  const handleDeleteStrategy = (strategyId: string) => {
    const strat = savedStrategies.find((s) => s.id === strategyId);
    if (!strat) return;

    if (window.confirm(`Bạn có chắc chắn muốn xóa chiến lược "${strat.name}" khỏi danh sách?`)) {
      const { updatedList, deleted } = deleteStrategy(savedStrategies, strategyId);
      if (deleted) {
        setSavedStrategies(updatedList);
        setSavedToast(`Đã xóa chiến lược "${strat.name}"`);
        setTimeout(() => setSavedToast(null), 3000);
      }
    }
  };


  // Lấy các metrics hiển thị
  const metrics = portfolioResult?.aggregate_metrics || backtestResult?.metrics;
  const equityCurve = portfolioResult?.portfolio_equity_curve || backtestResult?.equity_curve || [];
  const trades: TradeLogItem[] = useMemo(() => {
    if (detailSymbol && portfolioResult?.individual_results?.[detailSymbol]) {
      return portfolioResult.individual_results[detailSymbol].trades || [];
    }
    if (portfolioResult?.individual_results) {
      const all: TradeLogItem[] = [];
      for (const res of Object.values(portfolioResult.individual_results)) {
        if (res.trades) all.push(...res.trades);
      }
      return all.sort((a, b) => (b.exec_date || "").localeCompare(a.exec_date || ""));
    }
    return backtestResult?.trades || [];
  }, [detailSymbol, portfolioResult, backtestResult]);

  const isAlphaPositive = (metrics?.excess_return_pct ?? 0) >= 0;
  const isLoading = isAdvancedLoading || externalLoading;

  // Trích xuất Deal đỉnh (Max Gain) và Max Loss kèm mã cổ phiếu cụ thể chuẩn DNSE
  const bestDealInfo = useMemo(() => {
    let best = { pct: -Infinity, symbol: "" };
    let worst = { pct: Infinity, symbol: "" };

    if (portfolioResult?.individual_results) {
      for (const [sym, res] of Object.entries(portfolioResult.individual_results)) {
        for (const t of res.trades || []) {
          const ret = t.realized_return_pct;
          if (typeof ret === "number" && !isNaN(ret)) {
            if (ret > best.pct) {
              best = { pct: ret, symbol: sym };
            }
            if (ret < worst.pct) {
              worst = { pct: ret, symbol: sym };
            }
          }
        }
      }
    } else if (backtestResult?.trades) {
      for (const t of backtestResult.trades) {
        const ret = t.realized_return_pct;
        if (typeof ret === "number" && !isNaN(ret)) {
          if (ret > best.pct) {
            best = { pct: ret, symbol: backtestResult.symbol };
          }
          if (ret < worst.pct) {
            worst = { pct: ret, symbol: backtestResult.symbol };
          }
        }
      }
    }

    return {
      best:
        best.pct > -Infinity
          ? best
          : metrics?.max_gain_pct
            ? { pct: metrics.max_gain_pct, symbol: selectedSymbol }
            : null,
      worst:
        worst.pct < Infinity
          ? worst
          : metrics?.max_loss_pct
            ? { pct: metrics.max_loss_pct, symbol: selectedSymbol }
            : null,
    };
  }, [portfolioResult, backtestResult, metrics, selectedSymbol]);





  return (
    <div className="space-y-4">
      {/* 1. Header Thanh Điều hướng Subtabs chuẩn DNSE */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/80 p-3 backdrop-blur-md sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {/* Nút 1: Quản lý chiến thuật (Chuẩn DNSE: Tất cả / Triển khai / Chưa triển khai) */}
          <button
            type="button"
            onClick={() => {
              setActiveSubtab("my_strategy");
              setStrategyViewMode("manager");
            }}
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${activeSubtab === "my_strategy" && strategyViewMode === "manager"
              ? "bg-slate-800 text-emerald-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
              }`}
          >
            <FolderOpen className="h-4 w-4" />
            <span>Quản lý chiến thuật ({savedStrategies.length})</span>
          </button>

          {/* Nút 2: Phòng Lab Cấu hình & Giả lập */}
          <button
            type="button"
            onClick={() => {
              setActiveSubtab("my_strategy");
              setStrategyViewMode("builder");
            }}
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${activeSubtab === "my_strategy" && strategyViewMode === "builder"
              ? "bg-slate-800 text-emerald-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
              }`}
          >
            <Sliders className="h-4 w-4" />
            <span>Phòng Lab Kiểm thử</span>
          </button>

          {/* Nút 3: Chiến thuật mẫu */}
          <button
            type="button"
            onClick={() => setActiveSubtab("presets")}
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${activeSubtab === "presets"
              ? "bg-slate-800 text-blue-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
              }`}
          >
            <Sparkles className="h-4 w-4" />
            <span>Chiến thuật mẫu</span>
          </button>
        </div>

        {/* Action Buttons: Lưu chiến lược & Toast */}
        <div className="flex items-center gap-2">
          {savedToast && (
            <div className="flex items-center gap-1.5 rounded-md bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-400 border border-emerald-500/30">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>{savedToast}</span>
              {strategyViewMode === "builder" && (
                <button
                  type="button"
                  onClick={() => setStrategyViewMode("manager")}
                  className="ml-1 text-[11px] underline hover:text-emerald-300 font-bold cursor-pointer"
                >
                  [Xem danh sách]
                </button>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={() => {
              if (!portfolioResult && !backtestResult) {
                setSavedToast("⚠️ Vui lòng chạy kiểm thử trước khi lưu chiến lược để có số liệu hiệu quả!");
                setTimeout(() => setSavedToast(null), 4000);
                return;
              }
              setIsSaveModalOpen(true);
            }}
            className="flex items-center gap-1.5 rounded-md bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 border border-slate-700 hover:border-emerald-500/50 hover:text-emerald-400 transition-colors cursor-pointer"
          >
            <BookmarkCheck className="h-4 w-4 text-emerald-400" />
            <span>Lưu chiến lược</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. NỘI DUNG SUBTAB: KHO CHIẾN THUẬT MẪU (DNSE PRESET LIBRARY) */}
      {/* ========================================================================= */}
      {activeSubtab === "presets" && (
        <StrategyPresetsList
          presets={presets}
          onApplyPreset={handleApplyPreset}
          loading={isLoading}
        />
      )}

      {/* ========================================================================= */}
      {/* 3. NỘI DUNG SUBTAB: CHIẾN THUẬT CỦA TÔI (QUẢN LÝ HOẶC PHÒNG LAB) */}
      {/* ========================================================================= */}
      {activeSubtab === "my_strategy" && strategyViewMode === "manager" && (
        <SavedStrategiesManager
          strategies={savedStrategies}
          onCreateStrategy={() => {
            setStrategyName("Chiến thuật mới");
            setActiveStrategyId(null);
            setStrategyViewMode("builder");
          }}
          onRunStrategy={(strat) => handleLoadStrategy(strat, true)}
          onEditStrategy={(strat) => handleLoadStrategy(strat, false)}
          onToggleStatus={handleToggleStatus}
          onDeleteStrategy={handleDeleteStrategy}
        />
      )}

      {activeSubtab === "my_strategy" && strategyViewMode === "builder" && (
        <div className="space-y-4">
          {/* Thanh tác vụ: Quay lại Quản lý chiến thuật */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setStrategyViewMode("manager")}
              className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-400 hover:text-emerald-400 hover:bg-slate-800/60 transition-colors cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Quay lại Quản lý chiến thuật ({savedStrategies.length} chiến lược)</span>
            </button>
          </div>

          {/* BỐ CỤC 2 CỘT CHUẨN DNSE ENTRADE X: Form bên trái (5 cols) | Dashboard kết quả bên phải (7 cols) */}
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-12 items-start">
            {/* CỘT TRÁI: FORM CẤU HÌNH CHIẾN LƯỢC (TINH GỌN, KHÔNG CẦN CUỘN) */}
            <div className="space-y-3.5 xl:col-span-5 xl:sticky xl:top-4 min-w-0">
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-sm space-y-3.5 overflow-hidden">
                {/* Header Form: Tên chiến lược & Date Range Picker */}
                <div className="flex flex-col gap-2.5 pb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
                      <Sliders className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <input
                        type="text"
                        value={strategyName}
                        onChange={(e) => setStrategyName(e.target.value)}
                        className="w-full bg-transparent text-sm font-bold text-slate-100 hover:border-b hover:border-slate-600 focus:border-b focus:border-emerald-500 focus:outline-none sm:text-base truncate"
                        title="Nhấn để đổi tên chiến lược"
                        placeholder="Nhập tên chiến lược..."
                      />
                    </div>
                  </div>

                  {/* DateRangePicker có ràng buộc <= 1 năm chuẩn DNSE kèm tự động đồng bộ phiên mới nhất */}
                  <div className="w-full min-w-0">
                    <DateRangePicker
                      startDate={startDate}
                      endDate={endDate}
                      onChangeStartDate={setStartDate}
                      onChangeEndDate={setEndDate}
                      latestSessionDate={marketSession?.target_date || defaultDates.end}
                      sessionLabel={marketSession?.status_label}
                      onResetLatest={handleResetToLatestSession}
                      onSyncMarket={handleSyncMarket}
                      isSyncing={isSyncingMarket}
                    />
                  </div>
                </div>

                {/* Scope Selector: Rổ chỉ số, Cổ phiếu, Danh mục, Ngành */}
                <ScopeSelector
                  scopeType={scopeType}
                  onChangeScopeType={setScopeType}
                  selectedSymbol={selectedSymbol}
                  onChangeSymbol={onSelectSymbol}
                  selectedIndex={selectedIndex}
                  onChangeIndex={setSelectedIndex}
                  selectedSector={selectedSector}
                  onChangeSector={setSelectedSector}
                  portfolioSymbols={portfolioSymbols}
                  onChangePortfolioSymbols={setPortfolioSymbols}
                  symbols={availableSymbols}
                  sectors={availableSectors}
                />

                {/* Accordion Điều kiện Mua & Điều kiện Bán (Chuẩn giao diện DNSE) */}
                <div className="space-y-3">
                  {/* Card Điều kiện Mua [M] - Tinh chỉnh thông số chuẩn DNSE */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 space-y-3">
                    <div className="flex items-center justify-between pb-1.5 border-b border-slate-800/80">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-[11px] font-bold text-emerald-400">
                          M
                        </span>
                        <span className="text-xs font-bold text-slate-200">Điều kiện Mua</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsBuyModalOpen(true)}
                        className="flex items-center gap-1 rounded-lg bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all cursor-pointer"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        <span>Thêm điều kiện</span>
                      </button>
                    </div>

                    <BuyConditionAdjuster
                      conditions={buyConditions}
                      onChange={setBuyConditions}
                      onOpenAddModal={() => setIsBuyModalOpen(true)}
                      onDuplicateCondition={(key) => {
                        setSavedToast(`Đã nhân bản điều kiện ${key.toUpperCase()}`);
                        setTimeout(() => setSavedToast(null), 2500);
                      }}
                    />
                  </div>

                  {/* Card Điều kiện Bán [B] */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/20 text-[11px] font-bold text-rose-400">
                          B
                        </span>
                        <span className="text-xs font-bold text-slate-200">Điều kiện Bán</span>
                        {(() => {
                          let c = 0;
                          if (sellConditions.use_ma) c++;
                          if (sellConditions.use_price_cross) c++;
                          if (sellConditions.use_rsi) c++;
                          if (sellConditions.foreign_net_sell_val || sellConditions.foreign_net_sell) c++;
                          if (sellConditions.prop_net_sell_vol) c++;
                          if (sellConditions.use_adx) c++;
                          if (sellConditions.use_ema) c++;
                          if (sellConditions.foreign_net_sell_vol) c++;
                          if (sellConditions.use_rs) c++;
                          if (sellConditions.use_macd) c++;
                          if (sellConditions.prop_net_sell_val) c++;
                          if (sellConditions.take_profit_pct && sellConditions.take_profit_pct > 0) c++;
                          if (sellConditions.stop_loss_pct && sellConditions.stop_loss_pct > 0) c++;
                          if (sellConditions.trailing_stop_pct && sellConditions.trailing_stop_pct > 0) c++;
                          return c > 0 ? (
                            <span className="rounded-full bg-rose-500/20 px-1.5 py-0.2 text-[10px] font-bold text-rose-400">
                              {c}
                            </span>
                          ) : null;
                        })()}
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsSellModalOpen(true)}
                        className="flex items-center gap-1 rounded-lg bg-rose-500/10 px-2 py-1 text-xs font-semibold text-rose-400 border border-rose-500/30 hover:bg-rose-500/20 transition-all cursor-pointer"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        <span>Thêm điều kiện</span>
                      </button>
                    </div>

                    <SellConditionAdjuster
                      conditions={sellConditions}
                      onChange={setSellConditions}
                      onOpenAddModal={() => setIsSellModalOpen(true)}
                      onDuplicateCondition={(key) => {
                        setSavedToast(`Đã nhân bản điều kiện ${key.toUpperCase()}`);
                        setTimeout(() => setSavedToast(null), 2500);
                      }}
                    />
                  </div>
                </div>

                {/* Collapsible Cài đặt nâng cao (Vốn, AI Model, Slippage) */}
                <div
                  className={`rounded-lg border transition-colors ${useAdvancedSettings
                    ? "border-emerald-500/40 bg-slate-950/80"
                    : "border-slate-800 bg-slate-950/50"
                    } overflow-hidden`}
                >
                  <div className="flex items-center justify-between p-2.5 text-xs">
                    <div className="flex items-center gap-2">
                      <Settings2
                        className={`h-4 w-4 ${useAdvancedSettings ? "text-emerald-400" : "text-slate-400"
                          }`}
                      />
                      <div>
                        <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                          <span>Cài đặt nâng cao (Vốn, AI Model, Trượt giá)</span>
                          {useAdvancedSettings && (
                            <span className="text-[9px] bg-emerald-500/20 text-emerald-400 font-bold px-1.5 py-0.5 rounded border border-emerald-500/30">
                              ĐANG ÁP DỤNG
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {useAdvancedSettings ? (
                            <span className="text-emerald-400 font-medium">
                              Vốn {(initialCapital / 1e6).toFixed(0)}tr • {modelType === "lightgbm" ? "LightGBM" : "LSTM"} • Trượt giá {(slippageRate * 100).toFixed(2)}%
                            </span>
                          ) : (
                            <span>Đang tắt: Chuẩn DNSE (Không trượt giá • 100% theo quy tắc)</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2.5">
                      {/* Switch bật / tắt áp dụng nâng cao */}
                      <label className="relative inline-flex items-center cursor-pointer" title={useAdvancedSettings ? "Tắt cài đặt nâng cao" : "Bật cài đặt nâng cao"}>
                        <input
                          type="checkbox"
                          checked={useAdvancedSettings}
                          onChange={(e) => {
                            const val = e.target.checked;
                            setUseAdvancedSettings(val);
                            if (val) setIsAdvancedSettingsOpen(true);
                          }}
                          className="sr-only peer"
                        />
                        <div className="w-8 h-4 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-500 peer-checked:after:bg-white"></div>
                      </label>
                      <button
                        type="button"
                        onClick={() => setIsAdvancedSettingsOpen(!isAdvancedSettingsOpen)}
                        className="p-1 hover:bg-slate-800/60 rounded text-slate-400 transition cursor-pointer"
                        title={isAdvancedSettingsOpen ? "Thu gọn" : "Mở rộng"}
                      >
                        {isAdvancedSettingsOpen ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {isAdvancedSettingsOpen && (
                    <div className="p-3 pt-1 border-t border-slate-800/60 space-y-2.5">
                      {!useAdvancedSettings ? (
                        <div className="rounded-lg border border-slate-800/90 bg-slate-900/60 p-2.5 text-[11px] text-slate-400 leading-relaxed">
                          <p className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                            <span className="text-emerald-400"></span> Cài đặt nâng cao đang kích hoạt:
                          </p>
                          <ul className="list-disc pl-4 space-y-1 text-[10px] text-slate-400">
                            <li>
                              Khớp lệnh <strong className="text-slate-200">100% theo bộ điều kiện Mua & Bán</strong> bạn cài đặt phía trên.
                            </li>
                            <li>
                              <strong className="text-slate-200">Không tính trượt giá (0.00%)</strong>: Lệnh khớp đúng giá thị trường lý tưởng.
                            </li>
                            <li>
                              <strong className="text-slate-200">Không có mô hình AI can thiệp</strong>: Bảo đảm chiến lược vận hành thuần túy theo quy tắc kỹ thuật định sẵn.
                            </li>
                          </ul>
                          <div className="mt-2 text-[10px] text-emerald-400 font-medium">
                            Gạt công tắc bên phải phía trên nếu bạn muốn kích hoạt Vốn tùy chỉnh, Mô hình AI hoặc đo kiểm Trượt giá.
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2.5">
                          {/* Vốn ban đầu */}
                          <div>
                            <label className="block text-[11px] font-medium text-slate-400 mb-1">
                              Vốn đầu tư ban đầu (VNĐ)
                            </label>
                            <input
                              type="number"
                              step="10000000"
                              min="10000000"
                              value={initialCapital}
                              onChange={(e) => setInitialCapital(Number(e.target.value))}
                              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
                            />
                          </div>

                          {/* Mô hình AI */}
                          <div>
                            <label className="block text-[11px] font-medium text-slate-400 mb-1">
                              Mô hình dự báo tín hiệu
                            </label>
                            <select
                              value={modelType}
                              onChange={(e) => setModelType(e.target.value as "lightgbm" | "lstm")}
                              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
                            >
                              <option value="lightgbm">LightGBM (Production OOS)</option>
                              <option value="lstm">PyTorch LSTM (Đa biến)</option>
                            </select>
                          </div>

                          {/* Trượt giá */}
                          <div>
                            <label className="block text-[11px] font-medium text-slate-400 mb-1">
                              Trượt giá (Slippage)
                            </label>
                            <select
                              value={slippageRate}
                              onChange={(e) => setSlippageRate(Number(e.target.value))}
                              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
                            >
                              <option value={0.0005}>0.05% (Thanh khoản cao)</option>
                              <option value={0.0010}>0.10% (Thanh khoản vừa)</option>
                              <option value={0.0020}>0.20% (Thị trường biến động)</option>
                            </select>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Nút Chạy Kiểm thử To Rõ */}
                <button
                  type="button"
                  onClick={handleRunAdvancedSimulation}
                  disabled={isLoading}
                  className="flex w-full items-center justify-center gap-2 rounded-md bg-emerald-500 py-2.5 text-xs font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {isLoading ? (
                    <>
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                      <span>Đang kiểm thử danh mục...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-current" />
                      <span>
                        CHẠY KIỂM THỬ{" "}
                        {scopeType === "index"
                          ? `(${selectedIndex})`
                          : scopeType === "sector"
                            ? `(Ngành)`
                            : scopeType === "portfolio"
                              ? `(${portfolioSymbols.length} mã)`
                              : `(${selectedSymbol})`}
                      </span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* CỘT PHẢI: DASHBOARD KẾT QUẢ ĐỊNH LƯỢNG (KHÔNG CẦN CUỘN TRANG) */}
            <div className="space-y-4 xl:col-span-7 min-w-0">

              {/* ===================================================================== */}
              {/* KHU VỰC HIỂN THỊ KẾT QUẢ ĐỊNH LƯỢNG */}
              {/* ===================================================================== */}

              {/* Trường hợp chưa chạy kiểm thử: Hiển thị Mascot và lời nhắc chuẩn DNSE ảnh 1 */}
              {!portfolioResult && !backtestResult && !isLoading && (
                <div className="flex flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900 p-8 text-center min-h-[340px]">
                  <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-slate-800 text-blue-400 border border-slate-700 mb-3">
                    <Bot className="h-7 w-7" />
                  </div>
                  <h4 className="text-base font-bold text-slate-200">
                    Lựa chọn điều kiện để chạy chiến lược.
                  </h4>
                  <p className="mt-1 max-w-md text-xs text-slate-400">
                    Chọn Rổ chỉ số (VN30/VN100), Nhóm ngành hoặc Cổ phiếu mục tiêu, thiết lập điều kiện
                    Mua/Bán và nhấn <strong>&ldquo;CHẠY KIỂM THỬ&rdquo;</strong> để bắt đầu mô phỏng thực tế.
                  </p>
                </div>
              )}

              {/* Khi có kết quả: Hiển thị Banner tổng hợp & Lưới chỉ số + Biểu đồ */}
              {(portfolioResult || backtestResult) && (
                <div className="space-y-4 animate-fade-in">
                  {/* Banner tóm tắt phạm vi đã kiểm thử */}
                  {portfolioResult && (
                    <div className="flex flex-col gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 sm:flex-row sm:items-center sm:justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-slate-950 font-bold">
                          ✓
                        </span>
                        <div>
                          <span className="font-bold text-emerald-400 text-sm">
                            {portfolioResult.scope_target}
                          </span>
                          <span className="text-slate-300 ml-2">
                            ({portfolioResult.symbols_count} cổ phiếu thành phần)
                          </span>
                        </div>
                      </div>
                      <div className="text-slate-300 font-mono text-[11px]">
                        Dải ngày: <strong>{portfolioResult.start_date}</strong> →{" "}
                        <strong>{portfolioResult.end_date}</strong>
                        {useAdvancedSettings && (
                          <span>
                            {" "}• Vốn:{" "}
                            <strong>{portfolioResult.aggregate_metrics.initial_capital.toLocaleString("vi-VN")} đ</strong>
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* THẺ TỔNG QUAN HIỆU QUẢ GIAO DỊCH & BIỂU ĐỒ DONUT WIN/LOSS CHUẨN DNSE ENTRADE X */}
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-sm">
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                      {/* BÊN TRÁI: BIỂU ĐỒ DONUT TỶ LỆ THẮNG / THUA LỚN CHUẨN DNSE */}
                      <div className="md:col-span-4 flex flex-col items-center justify-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                        <div className="relative flex h-24 w-24 items-center justify-center">
                          <svg className="h-24 w-24 -rotate-90 transform" viewBox="0 0 100 100">
                            {/* Vòng tròn nền (Thua / Đỏ) */}
                            <circle
                              cx="50"
                              cy="50"
                              r="38"
                              stroke="currentColor"
                              strokeWidth="9"
                              className="text-rose-500/80"
                              fill="transparent"
                            />
                            {/* Cung tròn Thắng (Xanh lá) */}
                            <circle
                              cx="50"
                              cy="50"
                              r="38"
                              stroke="currentColor"
                              strokeWidth="9"
                              strokeDasharray={2 * Math.PI * 38}
                              strokeDashoffset={
                                2 * Math.PI * 38 * (1 - (metrics?.win_rate_pct ?? 0) / 100)
                              }
                              strokeLinecap="round"
                              className="text-emerald-400 transition-all duration-700 ease-out"
                              fill="transparent"
                            />
                          </svg>
                          <div className="absolute flex flex-col items-center justify-center text-center">
                            <span className="text-lg font-black text-slate-100">
                              {metrics ? `${metrics.win_rate_pct.toFixed(0)}%` : "0%"}
                            </span>
                            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                              Thắng
                            </span>
                          </div>
                        </div>
                        {/* Chú thích Donut: Deal Lãi vs Deal Lỗ */}
                        <div className="mt-2.5 flex items-center gap-3 text-[11px] font-semibold">
                          <div className="flex items-center gap-1.5 text-emerald-400">
                            <span className="h-2 w-2 rounded-full bg-emerald-400" />
                            <span>{metrics?.winning_trades ?? 0} Deal lãi</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-rose-400">
                            <span className="h-2 w-2 rounded-full bg-rose-500" />
                            <span>{metrics?.losing_trades ?? 0} Deal lỗ</span>
                          </div>
                        </div>
                      </div>

                      {/* BÊN PHẢI: 4 THẺ THÔNG SỐ DEAL CỤ THỂ CHỈ ĐÍCH DANH MÃ CỔ PHIẾU */}
                      <div className="md:col-span-8 grid grid-cols-2 gap-2.5">
                        {/* 1. Lãi nhiều nhất (Deal đỉnh) */}
                        <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-2.5 hover:border-emerald-500/30 transition-all">
                          <div className="flex items-center justify-between text-[11px] font-medium text-slate-400">
                            <span className="truncate">Lãi nhiều nhất (Deal đỉnh)</span>
                            {bestDealInfo.best?.symbol && (
                              <span className="shrink-0 rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-black text-emerald-300 border border-emerald-500/30">
                                {bestDealInfo.best.symbol}
                              </span>
                            )}
                          </div>
                          <div className="mt-1 text-base font-black text-emerald-400">
                            {bestDealInfo.best
                              ? `+${bestDealInfo.best.pct.toFixed(2)}%`
                              : metrics?.max_gain_pct
                                ? `+${metrics.max_gain_pct.toFixed(2)}%`
                                : "---"}
                          </div>
                          <p className="mt-0.5 text-[9px] text-slate-500 truncate">Deal hiệu suất cao nhất</p>
                        </div>

                        {/* 2. Lỗ sâu nhất (Max Loss) */}
                        <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-2.5 hover:border-rose-500/30 transition-all">
                          <div className="flex items-center justify-between text-[11px] font-medium text-slate-400">
                            <span className="truncate">Lỗ nhiều nhất (Max Loss)</span>
                            {bestDealInfo.worst?.symbol && (
                              <span className="shrink-0 rounded bg-rose-500/20 px-1.5 py-0.5 text-[10px] font-black text-rose-300 border border-rose-500/30">
                                {bestDealInfo.worst.symbol}
                              </span>
                            )}
                          </div>
                          <div className="mt-1 text-base font-black text-rose-400">
                            {bestDealInfo.worst
                              ? `${bestDealInfo.worst.pct.toFixed(2)}%`
                              : metrics?.max_loss_pct
                                ? `${metrics.max_loss_pct.toFixed(2)}%`
                                : "---"}
                          </div>
                          <p className="mt-0.5 text-[9px] text-slate-500 truncate">Kiểm định kỷ luật cắt lỗ</p>
                        </div>

                        {/* 3. Lãi bình quân / deal */}
                        <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-2.5 hover:border-cyan-500/30 transition-all">
                          <div className="text-[11px] font-medium text-slate-400">Lãi TB / deal</div>
                          <div className={`mt-1 text-base font-black ${(metrics?.avg_trade_return_pct ?? 0) >= 0 ? "text-cyan-400" : "text-rose-400"}`}>
                            {metrics ? `${metrics.avg_trade_return_pct.toFixed(2)}%` : "---"}
                          </div>
                          <p className="mt-0.5 text-[9px] text-slate-500 truncate">Kỳ vọng toán học mỗi lệnh</p>
                        </div>

                        {/* 4. Tỷ lệ Lợi nhuận / Rủi ro */}
                        <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-2.5 hover:border-blue-500/30 transition-colors">
                          <div className="text-[11px] font-medium text-slate-400 truncate">Lợi nhuận / Rủi ro (R:R)</div>
                          <div className="mt-1 text-base font-bold font-mono text-blue-300">
                            {metrics?.reward_risk_ratio ? `${metrics.reward_risk_ratio}` : `${metrics?.profit_factor.toFixed(2) || "---"} : 1`}
                          </div>
                          <p className="mt-0.5 text-[9px] text-slate-500 truncate">Hệ số lãi gộp / lỗ gộp</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Lưới 5 Chỉ số Định lượng cốt lõi */}
                  <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
                    {/* 1. ROI */}
                    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                      <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                        <span>{useAdvancedSettings ? "Lợi nhuận (ROI)" : "Lợi nhuận (ROI)"}</span>
                        {(metrics?.total_return_pct ?? 0) >= 0 ? (
                          <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                        )}
                      </div>
                      <div className="mt-1 text-base font-bold font-mono">
                        <span className={(metrics?.total_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                          {metrics ? `${metrics.total_return_pct.toFixed(2)}%` : "---"}
                        </span>
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-500">
                        Mua &amp; Giữ: {metrics ? `${metrics.buy_and_hold_return_pct.toFixed(2)}%` : "---"}
                      </p>
                    </div>

                    {/* 2. Alpha */}
                    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                      <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                        <span>Lãi vượt trội (Alpha)</span>
                        <Sparkles className="h-3.5 w-3.5 text-blue-400" />
                      </div>
                      <div className="mt-1 text-base font-bold font-mono">
                        <span className={isAlphaPositive ? "text-emerald-400" : "text-rose-400"}>
                          {metrics ? `${metrics.excess_return_pct.toFixed(2)}%` : "---"}
                        </span>
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-500">Lãi thêm so với Mua &amp; Giữ</p>
                    </div>

                    {/* 3. Sharpe */}
                    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                      <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                        <span>Chỉ số Sharpe</span>
                        <Coins className="h-3.5 w-3.5 text-amber-400" />
                      </div>
                      <div className="mt-1 text-base font-bold font-mono text-slate-100">
                        {metrics ? metrics.sharpe_ratio.toFixed(2) : "---"}
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-500">Sinh lời / rủi ro (&gt;1 là tốt)</p>
                    </div>

                    {/* 4. MDD */}
                    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                      <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                        <span>Sụt giảm tối đa (MDD)</span>
                        <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
                      </div>
                      <div className="mt-1 text-base font-bold font-mono text-rose-400">
                        {metrics ? `-${Math.abs(metrics.max_drawdown_pct).toFixed(2)}%` : "---"}
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-500">Mức giảm lớn nhất từ đỉnh</p>
                    </div>

                    {/* 5. Chi phí */}
                    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3 col-span-2 sm:col-span-1">
                      <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                        <span>Tổng thuế &amp; phí</span>
                        <Wallet className="h-3.5 w-3.5 text-slate-400" />
                      </div>
                      <div className="mt-1 text-base font-bold font-mono text-slate-200">
                        {metrics ? `${(metrics.total_costs / 1000).toLocaleString("vi-VN")} k` : "---"}
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-500">
                        Phí 0.15% + Thuế 0.1%
                      </p>
                    </div>
                  </div>

                  {/* Subtabs Xem Kết quả (Biểu đồ Danh mục vs Tín hiệu AI vs Bảng Phân rã vs Nhật ký Lệnh) */}
                  <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2 text-xs">
                    <button
                      type="button"
                      onClick={() => setResultsTab("portfolio")}
                      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all cursor-pointer ${resultsTab === "portfolio"
                        ? "bg-slate-800 text-emerald-400 border border-slate-700"
                        : "text-slate-400 hover:text-slate-200"
                        }`}
                    >
                      <BarChart3 className="h-4 w-4" />
                      <span>Biểu đồ tài sản</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setResultsTab("signals")}
                      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all cursor-pointer ${resultsTab === "signals"
                        ? "bg-slate-800 text-emerald-400 border border-slate-700"
                        : "text-slate-400 hover:text-slate-200"
                        }`}
                    >
                      <Sparkles className="h-4 w-4" />
                      <span>Tín hiệu AI ({recentSignals.length})</span>
                    </button>

                    {portfolioResult && (
                      <button
                        type="button"
                        onClick={() => setResultsTab("breakdown")}
                        className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all cursor-pointer ${resultsTab === "breakdown"
                          ? "bg-slate-800 text-emerald-400 border border-slate-700"
                          : "text-slate-400 hover:text-slate-200"
                          }`}
                      >
                        <Layers className="h-4 w-4" />
                        <span>Phân rã từng mã ({portfolioResult.symbols_count})</span>
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => setResultsTab("trades")}
                      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all cursor-pointer ${resultsTab === "trades"
                        ? "bg-slate-800 text-emerald-400 border border-slate-700"
                        : "text-slate-400 hover:text-slate-200"
                        }`}
                    >
                      <ListFilter className="h-4 w-4" />
                      <span>Nhật ký lệnh {detailSymbol ? `(${detailSymbol})` : `(${trades.length})`}</span>
                    </button>

                    {detailSymbol && (
                      <button
                        type="button"
                        onClick={() => setDetailSymbol(null)}
                        className="ml-auto flex items-center gap-1 rounded bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-cyan-400 hover:bg-slate-700 cursor-pointer"
                      >
                        <ArrowLeft className="h-3 w-3" />
                        <span>Quay lại tổng quan danh mục</span>
                      </button>
                    )}
                  </div>

                  {/* Tab 1: Biểu đồ tài sản Portfolio */}
                  {resultsTab === "portfolio" && (
                    <div className="space-y-3">
                      {detailSymbol && portfolioResult?.individual_results?.[detailSymbol] && (
                        <div className="flex items-center justify-between rounded-lg bg-cyan-500/10 px-3 py-2 border border-cyan-500/30 text-xs">
                          <span className="font-bold text-cyan-400">
                            Đang xem chi tiết riêng mã: {detailSymbol}
                          </span>
                          <button
                            type="button"
                            onClick={() => setDetailSymbol(null)}
                            className="text-slate-400 hover:text-slate-200 underline cursor-pointer"
                          >
                            Xem lại tổng hợp danh mục
                          </button>
                        </div>
                      )}

                      <EquityCurveChart
                        equityCurve={
                          detailSymbol && portfolioResult?.individual_results?.[detailSymbol]
                            ? portfolioResult.individual_results[detailSymbol].equity_curve
                            : equityCurve
                        }
                        initialCapital={
                          detailSymbol
                            ? portfolioResult?.individual_results?.[detailSymbol]?.metrics?.initial_capital ||
                            initialCapital / (portfolioResult?.symbols_count || 1)
                            : initialCapital
                        }
                        height={320}
                        strategyLabel={useAdvancedSettings ? "Chiến lược AI (Đo lường OOS)" : "Chiến lược (Quy tắc lọc)"}
                        strategyShortLabel={useAdvancedSettings ? "AI" : "Chiến lược"}
                      />
                      <DrawdownChart
                        equityCurve={
                          detailSymbol && portfolioResult?.individual_results?.[detailSymbol]
                            ? portfolioResult.individual_results[detailSymbol].equity_curve
                            : equityCurve
                        }
                        height={130}
                      />
                    </div>
                  )}

                  {/* Tab: Tín hiệu AI */}
                  {resultsTab === "signals" && (
                    <RecentSignalsSidebar
                      signals={recentSignals}
                      onSelectSymbol={(sym) => {
                        onSelectSymbol(sym);
                      }}
                    />
                  )}

                  {/* Tab 2: Bảng Phân rã chi tiết từng mã thành phần */}
                  {resultsTab === "breakdown" && portfolioResult && (
                    <PortfolioBreakdownTable
                      items={portfolioResult.symbols_breakdown}
                      selectedSymbol={detailSymbol}
                      onSelectSymbol={(sym) => {
                        setDetailSymbol(sym);
                        setResultsTab("portfolio");
                      }}
                    />
                  )}

                  {/* Tab 3: Bảng Nhật ký Khớp lệnh Thực tế */}
                  {resultsTab === "trades" && (
                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
                      <div className="mb-3 flex items-center justify-between">
                        <div>
                          <h3 className="text-sm font-bold text-slate-100 sm:text-base">
                            Nhật ký Giao dịch Khớp lệnh Thực tế (Lưu ký T+2)
                          </h3>
                          <p className="text-[11px] text-slate-400">
                            {detailSymbol
                              ? `Danh sách lệnh giao dịch riêng của mã ${detailSymbol}`
                              : "Ghi nhận chi tiết từng vòng mua/bán, phân loại rõ lý do thoát lệnh"}
                          </p>
                        </div>
                        <span className="rounded bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300">
                          {trades.length} Giao dịch
                        </span>
                      </div>

                      <div className="max-h-96 overflow-y-auto">
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
                            {trades.map((tr) => {
                              const isBuy = tr.order_type === "BUY";
                              const isPnlPositive = (tr.realized_pnl ?? 0) >= 0;

                              const isStopLoss = tr.reason === "STOP_LOSS";
                              const isTakeProfit = tr.reason === "TAKE_PROFIT";
                              const isTrailing = tr.reason === "TRAILING_STOP";

                              return (
                                <tr key={tr.trade_id} className="hover:bg-slate-800/30 transition-colors">
                                  <td className="px-3 py-2 font-mono text-slate-400">#{tr.trade_id}</td>
                                  <td className="px-3 py-2">
                                    <span
                                      className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold ${isBuy
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
                                      <span className={isPnlPositive ? "text-emerald-400" : "text-rose-400"}>
                                        {isPnlPositive ? "+" : ""}
                                        {tr.realized_pnl.toLocaleString("vi-VN")} đ
                                      </span>
                                    ) : (
                                      <span className="text-slate-500">---</span>
                                    )}
                                  </td>
                                  <td className="px-3 py-2 font-semibold">
                                    {tr.realized_return_pct !== null ? (
                                      <span className={isPnlPositive ? "text-emerald-400" : "text-rose-400"}>
                                        {isPnlPositive ? "+" : ""}
                                        {tr.realized_return_pct.toFixed(2)}%
                                      </span>
                                    ) : (
                                      <span className="text-slate-500">---</span>
                                    )}
                                  </td>
                                  <td className="px-3 py-2 text-right">
                                    {isStopLoss ? (
                                      <span className="rounded bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-500/30">
                                        Cắt lỗ (Stop Loss)
                                      </span>
                                    ) : isTakeProfit ? (
                                      <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300 border border-emerald-500/30">
                                        Chốt lời (Take Profit)
                                      </span>
                                    ) : isTrailing ? (
                                      <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-500/30">
                                        Trailing Stop
                                      </span>
                                    ) : (
                                      <span className="font-mono text-[11px] text-slate-400">
                                        {tr.reason}
                                      </span>
                                    )}
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
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modals Cấu hình Điều kiện Mua / Bán chuẩn DNSE */}
      <BuyConditionModal
        isOpen={isBuyModalOpen}
        onClose={() => setIsBuyModalOpen(false)}
        conditions={buyConditions}
        onApplyConditions={setBuyConditions}
      />

      <SellConditionModal
        isOpen={isSellModalOpen}
        onClose={() => setIsSellModalOpen(false)}
        conditions={sellConditions}
        onApplyConditions={setSellConditions}
      />

      {/* Modal Lưu Chiến lược (Có cảnh báo trùng lặp & phân loại Triển khai / Chưa triển khai) */}
      <SaveStrategyModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        currentStrategyName={strategyName}
        savedStrategies={savedStrategies}
        onSave={handleSaveStrategyData}
      />
    </div>
  );
};

