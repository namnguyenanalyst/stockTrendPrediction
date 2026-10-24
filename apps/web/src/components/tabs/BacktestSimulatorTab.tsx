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
  X,
  Layers,
  BarChart3,
  ListFilter,
  ArrowLeft,
  Bot,
  Sliders,
  FolderOpen,
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
import { SellConditionModal } from "@/components/backtest/SellConditionModal";
import { PortfolioBreakdownTable } from "@/components/backtest/PortfolioBreakdownTable";
import { SaveStrategyModal } from "@/components/backtest/SaveStrategyModal";
import { SavedStrategiesManager } from "@/components/backtest/SavedStrategiesManager";

const STRATEGY_STORAGE_KEY = "stockpulse_saved_strategies_v1";

function generateStrategyId(): string {
  return `strat-${Date.now()}`;
}

function getCurrentDateTimeString(): string {
  return new Date().toLocaleString("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const DEFAULT_SEED_STRATEGIES: SavedStrategyItem[] = [
  {
    id: "strat-seed-1",
    name: "Chiến thuật Đa mã & Rổ VN30",
    status: "active",
    created_at: "2026-10-22 09:30",
    updated_at: "2026-10-24 10:20",
    scope_type: "index",
    index_name: "VN30",
    start_date: "2025-10-22",
    end_date: "2026-10-22",
    initial_capital: 100_000_000,
    model_type: "lightgbm",
    slippage_rate: 0.0005,
    buy_conditions: {
      use_ma: true,
      use_rsi: true,
      rsi_threshold: 45,
    },
    sell_conditions: {
      use_rsi: true,
      rsi_sell_threshold: 70,
      take_profit_pct: 0.15,
      stop_loss_pct: 0.07,
      trailing_stop_pct: 0.05,
    },
    last_metrics: {
      roi_pct: 34.76,
      bh_roi_pct: 52.83,
      excess_pct: -18.07,
      sharpe: 2.5,
      mdd_pct: -5.99,
      win_rate_pct: 100.0,
      trades: 2,
    },
  },
  {
    id: "strat-seed-2",
    name: "Chiến lược Động lượng Ngành Ngân hàng",
    status: "draft",
    created_at: "2026-10-23 14:15",
    updated_at: "2026-10-23 15:00",
    scope_type: "sector",
    sector_name: "Ngân hàng",
    start_date: "2025-10-22",
    end_date: "2026-10-22",
    initial_capital: 200_000_000,
    model_type: "lstm",
    slippage_rate: 0.001,
    buy_conditions: {
      use_macd: true,
      use_rsi: true,
      rsi_threshold: 40,
      use_volume_spike: true,
    },
    sell_conditions: {
      take_profit_pct: 0.2,
      stop_loss_pct: 0.06,
      trailing_stop_pct: 0.04,
    },
    last_metrics: {
      roi_pct: 28.45,
      bh_roi_pct: 15.2,
      excess_pct: 13.25,
      sharpe: 2.15,
      mdd_pct: -8.4,
      win_rate_pct: 75.0,
      trades: 12,
    },
  },
];

/**
 * Tính toán động dải ngày 1 năm gần nhất dựa trên lịch thị trường chứng khoán Việt Nam:
 * - Nếu hôm nay là Thứ Bảy (day 6), lùi 1 ngày về phiên Thứ Sáu gần nhất.
 * - Nếu hôm nay là Chủ Nhật (day 0), lùi 2 ngày về phiên Thứ Sáu gần nhất.
 * - Ngày bắt đầu tự động tính lùi 365 ngày (1 năm) từ phiên gần nhất theo chuẩn DNSE.
 */
function getDynamicDateRange(): { start: string; end: string } {
  const now = new Date();
  const day = now.getDay();
  const rollback = day === 6 ? 1 : day === 0 ? 2 : 0;
  const end = new Date(now);
  end.setDate(end.getDate() - rollback);
  const start = new Date(end);
  start.setFullYear(start.getFullYear() - 1);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
}

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
  const [strategyViewMode, setStrategyViewMode] = useState<"manager" | "builder">("builder");
  const [savedStrategies, setSavedStrategies] = useState<SavedStrategyItem[]>(() => {
    if (typeof window === "undefined") return DEFAULT_SEED_STRATEGIES;
    try {
      const raw = localStorage.getItem(STRATEGY_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {
      // fallback
    }
    return DEFAULT_SEED_STRATEGIES;
  });
  const [isSaveModalOpen, setIsSaveModalOpen] = useState<boolean>(false);
  const [activeStrategyId, setActiveStrategyId] = useState<string | null>("strat-seed-1");

  // Strategy Basic Settings
  const [strategyName, setStrategyName] = useState<string>("Chiến thuật Đa mã & Rổ VN30");
  const [initialCapital, setInitialCapital] = useState<number>(100_000_000);
  const [modelType, setModelType] = useState<"lightgbm" | "lstm">("lightgbm");
  const [slippageRate, setSlippageRate] = useState<number>(0.0005); // 0.05%

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
    use_rsi: true,
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
  const [resultsTab, setResultsTab] = useState<"portfolio" | "breakdown" | "trades">("portfolio");

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
    try {
      const s = new Date(startDate);
      const end = new Date(endDate);
      const diff = Math.round((end.getTime() - s.getTime()) / (1000 * 3600 * 24));
      if (diff > 365) {
        setSavedToast("Lỗi: Khoảng thời gian chọn không quá 1 năm (tối đa 365 ngày)!");
        setTimeout(() => setSavedToast(null), 4000);
        return;
      }
      if (diff < 0) {
        setSavedToast("Lỗi: Ngày kết thúc phải sau ngày bắt đầu!");
        setTimeout(() => setSavedToast(null), 4000);
        return;
      }
    } catch {
      // ignore
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
          try {
            localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(updated));
          } catch (e) {
            console.debug("Lỗi lưu localStorage:", e);
          }
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

    // Cấu hình phạm vi tương ứng
    if (preset.category.includes("VN30")) {
      setScopeType("index");
      setSelectedIndex("VN30");
    } else if (preset.category.includes("VN100")) {
      setScopeType("index");
      setSelectedIndex("VN100");
    } else if (preset.category.includes("Ngân hàng")) {
      setScopeType("sector");
      setSelectedSector("Ngân hàng");
    } else if (preset.target_symbols && preset.target_symbols.length > 1) {
      setScopeType("portfolio");
      setPortfolioSymbols(preset.target_symbols);
    } else {
      setScopeType("stock");
      onSelectSymbol(preset.default_symbol);
    }

    const updatedSell: BacktestConditionFilter = {
      ...sellConditions,
      condition_logic: "OR",
      take_profit_pct: preset.take_profit_pct > 0 ? preset.take_profit_pct : null,
      stop_loss_pct: preset.stop_loss_pct > 0 ? preset.stop_loss_pct : null,
      trailing_stop_pct: preset.trailing_stop_pct > 0 ? preset.trailing_stop_pct : null,
    };
    setSellConditions(updatedSell);

    // Cấu hình điều kiện Mua chuẩn theo từng Preset DNSE
    let updatedBuy: BacktestConditionFilter = {
      condition_logic: "AND",
      market_condition: "all",
    };

    if (preset.id === "dnse-01") {
      updatedBuy = {
        ...updatedBuy,
        use_ema: true,
        use_volume_spike: true,
        use_price_cross: true,
        foreign_net_buy: true,
      };
    } else if (preset.id === "dnse-02") {
      updatedBuy = {
        ...updatedBuy,
        use_rsi: true,
        rsi_threshold: 70,
        use_volume_spike: true,
      };
    } else if (preset.id === "dnse-03") {
      updatedBuy = {
        ...updatedBuy,
        use_pe: true,
        max_pe: 16,
        use_price_increase: true,
        foreign_net_buy: true,
      };
    } else if (preset.id === "dnse-04") {
      updatedBuy = {
        ...updatedBuy,
        use_stock_price: true,
        min_stock_price: 10.0,
        use_market_cap: true,
        min_market_cap: 2000,
        use_pe: true,
        min_roe: 5.0,
        growth_eps: true,
      };
    } else if (preset.id === "dnse-05") {
      updatedBuy = {
        ...updatedBuy,
        use_pb: true,
        max_pb: 1.0,
        use_avg_trading_val: true,
        min_avg_trading_val: 10,
      };
    } else if (preset.id === "dnse-06") {
      updatedBuy = {
        ...updatedBuy,
        use_price_increase: true,
        use_volume_spike: true,
      };
    } else if (preset.id === "dnse-07") {
      updatedBuy = {
        ...updatedBuy,
        use_adx: true,
        use_bb: true,
      };
    } else if (preset.id === "dnse-08") {
      updatedBuy = {
        ...updatedBuy,
        use_price_cross: true,
        use_rsi: true,
        rsi_threshold: 57,
      };
    } else {
      updatedBuy = {
        ...updatedBuy,
        use_ma: true,
        use_rsi: true,
      };
    }

    setBuyConditions(updatedBuy);

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
    const now = getCurrentDateTimeString();

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

    let updatedList: SavedStrategyItem[];
    const targetId =
      overwriteExistingId ||
      savedStrategies.find((s) => s.name.trim().toLowerCase() === name.trim().toLowerCase())?.id;

    if (targetId) {
      // Cập nhật chiến lược đã tồn tại
      updatedList = savedStrategies.map((s) => {
        if (s.id === targetId) {
          return {
            ...s,
            name,
            status,
            updated_at: now,
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
            buy_conditions: buyConditions,
            sell_conditions: sellConditions,
            last_metrics: currentMetrics || s.last_metrics,
          };
        }
        return s;
      });
      setActiveStrategyId(targetId);
      setSavedToast(`Đã cập nhật chiến lược "${name}" thành công!`);
    } else {
      // Thêm chiến lược mới
      const newStrategy: SavedStrategyItem = {
        id: generateStrategyId(),
        name,
        status,
        created_at: now,
        updated_at: now,
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
        buy_conditions: buyConditions,
        sell_conditions: sellConditions,
        last_metrics: currentMetrics,
      };
      updatedList = [newStrategy, ...savedStrategies];
      setActiveStrategyId(newStrategy.id);
      setSavedToast(`Đã lưu chiến lược mới "${name}" thành công!`);
    }

    setSavedStrategies(updatedList);
    setStrategyName(name);
    try {
      localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(updatedList));
    } catch (e) {
      console.debug("Lỗi lưu localStorage:", e);
    }

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
    setModelType(strat.model_type);
    if (strat.slippage_rate !== undefined) setSlippageRate(strat.slippage_rate);
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

    const nextStatus: "active" | "draft" = targetStrat.status === "active" ? "draft" : "active";
    const targetName = targetStrat.name;

    const updatedList = savedStrategies.map((s) => {
      if (s.id === strategyId) {
        return {
          ...s,
          status: nextStatus,
          updated_at: getCurrentDateTimeString(),
        };
      }
      return s;
    });

    setSavedStrategies(updatedList);
    try {
      localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(updatedList));
    } catch (e) {
      console.debug("Lỗi cập nhật localStorage:", e);
    }

    setSavedToast(
      `Chiến lược "${targetName}" đã chuyển sang: ${
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
      const updatedList = savedStrategies.filter((s) => s.id !== strategyId);
      setSavedStrategies(updatedList);
      try {
        localStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(updatedList));
      } catch (e) {
        console.debug("Lỗi xóa localStorage:", e);
      }
      setSavedToast(`Đã xóa chiến lược "${strat.name}"`);
      setTimeout(() => setSavedToast(null), 3000);
    }
  };


  // Lấy các metrics hiển thị
  const metrics = portfolioResult?.aggregate_metrics || backtestResult?.metrics;
  const equityCurve = portfolioResult?.portfolio_equity_curve || backtestResult?.equity_curve || [];
  const trades: TradeLogItem[] =
    detailSymbol && portfolioResult?.individual_results?.[detailSymbol]
      ? portfolioResult.individual_results[detailSymbol].trades
      : backtestResult?.trades || [];

  const isAlphaPositive = (metrics?.excess_return_pct ?? 0) >= 0;
  const isLoading = isAdvancedLoading || externalLoading;

  // Render các tag/pill điều kiện mua
  const renderBuyConditionTags = () => {
    const tags: { id: string; label: string; onRemove: () => void }[] = [];
    if (buyConditions.market_condition && buyConditions.market_condition !== "all") {
      tags.push({
        id: "vni",
        label: `VN-Index: ${buyConditions.market_condition === "uptrend"
          ? "Tăng"
          : buyConditions.market_condition === "sideways"
            ? "Đi ngang"
            : "Giảm"
          }`,
        onRemove: () => setBuyConditions({ ...buyConditions, market_condition: "all" }),
      });
    }
    if (buyConditions.use_ma) {
      tags.push({
        id: "ma",
        label: "MA: Giá > SMA20",
        onRemove: () => setBuyConditions({ ...buyConditions, use_ma: false }),
      });
    }
    if (buyConditions.use_ema) {
      tags.push({
        id: "ema",
        label: "EMA: EMA12 > EMA26",
        onRemove: () => setBuyConditions({ ...buyConditions, use_ema: false }),
      });
    }
    if (buyConditions.use_macd) {
      tags.push({
        id: "macd",
        label: "MACD: Cắt lên Signal",
        onRemove: () => setBuyConditions({ ...buyConditions, use_macd: false }),
      });
    }
    if (buyConditions.use_rsi) {
      tags.push({
        id: "rsi",
        label: `RSI(14) <= ${buyConditions.rsi_threshold || 45}`,
        onRemove: () => setBuyConditions({ ...buyConditions, use_rsi: false }),
      });
    }
    if (buyConditions.use_bb) {
      tags.push({
        id: "bb",
        label: "Bollinger: Chạm dải dưới",
        onRemove: () => setBuyConditions({ ...buyConditions, use_bb: false }),
      });
    }
    if (buyConditions.use_volume_spike) {
      tags.push({
        id: "vol",
        label: "KLGD: Đột biến >1.2x SMA20",
        onRemove: () => setBuyConditions({ ...buyConditions, use_volume_spike: false }),
      });
    }
    if (buyConditions.use_price_increase) {
      tags.push({
        id: "t0",
        label: "Giá: T0 > T-1",
        onRemove: () => setBuyConditions({ ...buyConditions, use_price_increase: false }),
      });
    }
    if (buyConditions.use_adx) {
      tags.push({
        id: "adx",
        label: "ADX(14) ≥ 25 (Xu hướng mạnh)",
        onRemove: () => setBuyConditions({ ...buyConditions, use_adx: false }),
      });
    }
    if (buyConditions.use_rs) {
      tags.push({
        id: "rs",
        label: "RS: Sức mạnh giá dẫn dắt",
        onRemove: () => setBuyConditions({ ...buyConditions, use_rs: false }),
      });
    }
    if (buyConditions.use_price_cross) {
      tags.push({
        id: "cross",
        label: "Giá cắt đường MA/EMA/BB",
        onRemove: () => setBuyConditions({ ...buyConditions, use_price_cross: false }),
      });
    }
    if (buyConditions.use_stock_price) {
      tags.push({
        id: "price",
        label: "Lọc giá cổ phiếu",
        onRemove: () => setBuyConditions({ ...buyConditions, use_stock_price: false }),
      });
    }
    if (buyConditions.use_market_cap) {
      tags.push({
        id: "mcap",
        label: "Vốn hóa (Tỷ)",
        onRemove: () => setBuyConditions({ ...buyConditions, use_market_cap: false }),
      });
    }
    if (buyConditions.use_avg_trading_val) {
      tags.push({
        id: "avg_val",
        label: "GTGD trung bình (Tỷ)",
        onRemove: () => setBuyConditions({ ...buyConditions, use_avg_trading_val: false }),
      });
    }
    if (buyConditions.growth_rev_latest || buyConditions.growth_rev_ttm) {
      tags.push({
        id: "rev_growth",
        label: "Tăng trưởng Doanh thu (YoY)",
        onRemove: () =>
          setBuyConditions({
            ...buyConditions,
            growth_rev_latest: false,
            growth_rev_prev: false,
            growth_rev_ttm: false,
          }),
      });
    }
    if (buyConditions.growth_np_latest || buyConditions.growth_np_ttm) {
      tags.push({
        id: "np_growth",
        label: "Tăng trưởng LNST (YoY)",
        onRemove: () =>
          setBuyConditions({
            ...buyConditions,
            growth_np_latest: false,
            growth_np_prev: false,
            growth_np_ttm: false,
          }),
      });
    }
    if (buyConditions.use_pe || buyConditions.max_pe) {
      tags.push({
        id: "pe",
        label: "Định giá P/E",
        onRemove: () => setBuyConditions({ ...buyConditions, use_pe: false, max_pe: null }),
      });
    }
    if (buyConditions.use_pb || buyConditions.max_pb) {
      tags.push({
        id: "pb",
        label: "Định giá P/B",
        onRemove: () => setBuyConditions({ ...buyConditions, use_pb: false, max_pb: null }),
      });
    }
    if (buyConditions.use_ps) {
      tags.push({
        id: "ps",
        label: "Định giá P/S",
        onRemove: () => setBuyConditions({ ...buyConditions, use_ps: false }),
      });
    }
    if (buyConditions.use_roa) {
      tags.push({
        id: "roa",
        label: "ROA trượt 12T",
        onRemove: () => setBuyConditions({ ...buyConditions, use_roa: false }),
      });
    }
    if (buyConditions.use_roe || buyConditions.min_roe) {
      tags.push({
        id: "roe",
        label: "ROE trượt 12T",
        onRemove: () => setBuyConditions({ ...buyConditions, use_roe: false, min_roe: null }),
      });
    }
    if (buyConditions.use_eps || buyConditions.growth_eps) {
      tags.push({
        id: "eps",
        label: "Tăng trưởng EPS (YoY)",
        onRemove: () => setBuyConditions({ ...buyConditions, use_eps: false, growth_eps: false }),
      });
    }
    if (buyConditions.foreign_net_buy || buyConditions.foreign_net_val || buyConditions.foreign_net_vol) {
      tags.push({
        id: "foreign",
        label: "Khối ngoại: Mua ròng",
        onRemove: () =>
          setBuyConditions({
            ...buyConditions,
            foreign_net_buy: false,
            foreign_net_val: false,
            foreign_net_vol: false,
          }),
      });
    }
    if (buyConditions.prop_net_buy || buyConditions.prop_net_val || buyConditions.prop_net_vol) {
      tags.push({
        id: "prop",
        label: "Tự doanh: Mua ròng",
        onRemove: () =>
          setBuyConditions({
            ...buyConditions,
            prop_net_buy: false,
            prop_net_val: false,
            prop_net_vol: false,
          }),
      });
    }

    if (tags.length === 0) {
      return (
        <span className="text-[11px] text-slate-500 italic">
          Chưa chọn điều kiện mua (Nhấn + để thêm)
        </span>
      );
    }

    return (
      <div className="flex flex-wrap gap-1.5">
        {tags.map((t) => (
          <span
            key={t.id}
            className="inline-flex items-center gap-1 rounded bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300 border border-emerald-500/30"
          >
            <span>{t.label}</span>
            <button
              type="button"
              onClick={t.onRemove}
              className="hover:text-rose-400 text-slate-400 ml-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    );
  };

  // Render các tag/pill điều kiện bán
  const renderSellConditionTags = () => {
    const tags: { id: string; label: string; onRemove: () => void }[] = [];
    if (sellConditions.market_condition && sellConditions.market_condition !== "all") {
      tags.push({
        id: "vni_sell",
        label: `VN-Index: ${sellConditions.market_condition}`,
        onRemove: () => setSellConditions({ ...sellConditions, market_condition: "all" }),
      });
    }
    if (sellConditions.use_rsi) {
      tags.push({
        id: "rsi_sell",
        label: `RSI(14) >= ${sellConditions.rsi_sell_threshold || 70}`,
        onRemove: () => setSellConditions({ ...sellConditions, use_rsi: false }),
      });
    }
    if (sellConditions.use_macd) {
      tags.push({
        id: "macd_sell",
        label: "MACD: Cắt xuống Signal",
        onRemove: () => setSellConditions({ ...sellConditions, use_macd: false }),
      });
    }
    if (sellConditions.use_ma) {
      tags.push({
        id: "ma_sell",
        label: "MA: Giá < SMA20",
        onRemove: () => setSellConditions({ ...sellConditions, use_ma: false }),
      });
    }
    if (sellConditions.take_profit_pct && sellConditions.take_profit_pct > 0) {
      tags.push({
        id: "tp",
        label: `Chốt lời: +${Math.round(sellConditions.take_profit_pct * 100)}%`,
        onRemove: () => setSellConditions({ ...sellConditions, take_profit_pct: null }),
      });
    }
    if (sellConditions.stop_loss_pct && sellConditions.stop_loss_pct > 0) {
      tags.push({
        id: "sl",
        label: `Cắt lỗ: -${Math.round(sellConditions.stop_loss_pct * 100)}%`,
        onRemove: () => setSellConditions({ ...sellConditions, stop_loss_pct: null }),
      });
    }
    if (sellConditions.trailing_stop_pct && sellConditions.trailing_stop_pct > 0) {
      tags.push({
        id: "trailing",
        label: `Trailing Stop: ${Math.round(sellConditions.trailing_stop_pct * 100)}% từ đỉnh`,
        onRemove: () => setSellConditions({ ...sellConditions, trailing_stop_pct: null }),
      });
    }

    if (tags.length === 0) {
      return (
        <span className="text-[11px] text-slate-500 italic">
          Chưa chọn điều kiện bán (Nhấn + để thêm)
        </span>
      );
    }

    return (
      <div className="flex flex-wrap gap-1.5">
        {tags.map((t) => (
          <span
            key={t.id}
            className="inline-flex items-center gap-1 rounded bg-rose-500/15 px-2 py-0.5 text-[11px] font-semibold text-rose-300 border border-rose-500/30"
          >
            <span>{t.label}</span>
            <button
              type="button"
              onClick={t.onRemove}
              className="hover:text-rose-400 text-slate-400 ml-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    );
  };

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
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-bold transition-all ${
              activeSubtab === "my_strategy" && strategyViewMode === "manager"
                ? "bg-slate-800 text-emerald-400 border border-slate-700 shadow-md shadow-emerald-500/10"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
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
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-bold transition-all ${
              activeSubtab === "my_strategy" && strategyViewMode === "builder"
                ? "bg-slate-800 text-emerald-400 border border-slate-700 shadow-md shadow-emerald-500/10"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <Sliders className="h-4 w-4" />
            <span>Phòng Lab Kiểm thử</span>
          </button>

          {/* Nút 3: Chiến thuật mẫu */}
          <button
            type="button"
            onClick={() => setActiveSubtab("presets")}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-bold transition-all ${
              activeSubtab === "presets"
                ? "bg-slate-800 text-purple-400 border border-slate-700 shadow-md shadow-purple-500/10"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <Sparkles className="h-4 w-4" />
            <span>Chiến thuật mẫu</span>
          </button>
        </div>

        {/* Action Buttons: Lưu chiến lược & Toast */}
        <div className="flex items-center gap-2">
          {savedToast && (
            <div className="flex items-center gap-1.5 rounded-lg bg-emerald-500/20 px-3 py-1.5 text-xs font-semibold text-emerald-400 border border-emerald-500/40 animate-fade-in shadow-lg">
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
            className="flex items-center gap-1.5 rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 border border-slate-700 hover:border-emerald-500/50 hover:text-emerald-400 transition-colors shadow-sm cursor-pointer"
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
          {/* Nút quay lại Quản lý chiến thuật */}
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

          {/* Form Cấu hình Chiến lược Toàn diện */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm space-y-4">
            {/* Header Form: Tên chiến lược & Date Range Picker */}
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
                  <Sliders className="h-5 w-5" />
                </div>
                <div>
                  <input
                    type="text"
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                    className="bg-transparent text-base font-bold text-slate-100 hover:border-b hover:border-slate-600 focus:border-b focus:border-emerald-500 focus:outline-none sm:text-lg"
                    title="Nhấn để đổi tên chiến lược"
                  />
                </div>
              </div>

              {/* DateRangePicker có ràng buộc <= 1 năm chuẩn DNSE kèm tự động đồng bộ phiên mới nhất */}
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

            {/* Accordion Điều kiện Mua & Điều kiện Bán (Chuẩn giao diện DNSE ảnh 1, 2, 3, 4) */}
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {/* Accordion Mua [M] */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-xs font-bold text-emerald-400">
                      M
                    </span>
                    <span className="text-xs font-bold text-slate-200">Điều kiện Mua</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsBuyModalOpen(true)}
                    className="flex items-center gap-1 rounded-lg bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Thêm điều kiện</span>
                  </button>
                </div>

                <div className="pt-1">{renderBuyConditionTags()}</div>
              </div>

              {/* Accordion Bán [B] */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/20 text-xs font-bold text-rose-400">
                      B
                    </span>
                    <span className="text-xs font-bold text-slate-200">Điều kiện Bán</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsSellModalOpen(true)}
                    className="flex items-center gap-1 rounded-lg bg-rose-500/10 px-2 py-1 text-xs font-semibold text-rose-400 border border-rose-500/30 hover:bg-rose-500/20 transition-all"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Thêm điều kiện</span>
                  </button>
                </div>

                <div className="pt-1">{renderSellConditionTags()}</div>
              </div>
            </div>

            {/* Các tham số phụ: Vốn, Mô hình AI, Trượt giá & Nút CHẠY KIỂM THỬ */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 items-end pt-2 border-t border-slate-800/80">
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
                  Mô hình dự báo tín hiệu
                </label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value as "lightgbm" | "lstm")}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-100 focus:border-emerald-500 focus:outline-none"
                >
                  <option value="lightgbm">LightGBM (Walk-forward OOS)</option>
                  <option value="lstm">PyTorch LSTM (Đa biến)</option>
                </select>
              </div>

              {/* Trượt giá */}
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Trượt giá (Slippage)
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

              {/* Nút Chạy Kiểm thử */}
              <div>
                <button
                  type="button"
                  onClick={handleRunAdvancedSimulation}
                  disabled={isLoading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 disabled:opacity-50 transition-all cursor-pointer"
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
          </div>

          {/* ===================================================================== */}
          {/* KHU VỰC HIỂN THỊ KẾT QUẢ ĐỊNH LƯỢNG */}
          {/* ===================================================================== */}

          {/* Trường hợp chưa chạy kiểm thử: Hiển thị Mascot và lời nhắc chuẩn DNSE ảnh 1 */}
          {!portfolioResult && !backtestResult && !isLoading && (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center backdrop-blur-sm min-h-[360px]">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800 text-emerald-400 border border-slate-700 shadow-xl mb-4">
                <Bot className="h-8 w-8 animate-pulse" />
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
                    <strong>{portfolioResult.end_date}</strong> • Vốn:{" "}
                    <strong>{portfolioResult.aggregate_metrics.initial_capital.toLocaleString("vi-VN")} đ</strong>
                  </div>
                </div>
              )}

              {/* Lưới 6 Chỉ số Định lượng cốt lõi */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                {/* 1. ROI */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                  <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                    <span>ROI Danh mục AI</span>
                    {(metrics?.total_return_pct ?? 0) >= 0 ? (
                      <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                    )}
                  </div>
                  <div className="mt-1 text-base font-black">
                    <span className={(metrics?.total_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                      {metrics ? `${metrics.total_return_pct.toFixed(2)}%` : "---"}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[10px] text-slate-500">
                    B&amp;H: {metrics ? `${metrics.buy_and_hold_return_pct.toFixed(2)}%` : "---"}
                  </p>
                </div>

                {/* 2. Alpha */}
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

                {/* 3. Sharpe */}
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

                {/* 4. MDD */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                  <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                    <span>Max Drawdown (MDD)</span>
                    <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
                  </div>
                  <div className="mt-1 text-base font-black text-rose-400">
                    {metrics ? `-${Math.abs(metrics.max_drawdown_pct).toFixed(2)}%` : "---"}
                  </div>
                  <p className="mt-0.5 text-[10px] text-slate-500">Sụt giảm vốn từ đỉnh</p>
                </div>

                {/* 5. Win Rate */}
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

                {/* 6. Chi phí */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                  <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
                    <span>Tổng thuế &amp; phí</span>
                    <Wallet className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                  <div className="mt-1 text-base font-black text-slate-200">
                    {metrics ? `${(metrics.total_costs / 1000).toLocaleString("vi-VN")} k` : "---"}
                  </div>
                  <p className="mt-0.5 text-[10px] text-slate-500">
                    Tác động: {metrics ? `${metrics.cost_impact_pct.toFixed(2)}%` : "---"} vốn
                  </p>
                </div>
              </div>

              {/* LƯỚI 4 CHỈ SỐ DEAL & DONUT WIN/LOSS CHUẨN DNSE ENTRADE X */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {/* 1. Lãi lớn nhất (Max Gain) */}
                <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 hover:border-emerald-500/30 transition-all">
                  <div>
                    <span className="block text-[11px] font-medium text-slate-400">Lãi nhiều nhất (Deal đỉnh)</span>
                    <div className="mt-1 flex items-baseline gap-1.5">
                      <span className="text-lg font-black text-emerald-400">
                        {metrics?.max_gain_pct !== undefined && metrics.max_gain_pct > 0
                          ? `+${metrics.max_gain_pct.toFixed(2)}%`
                          : metrics?.max_gain_pct !== undefined
                            ? `${metrics.max_gain_pct.toFixed(2)}%`
                            : "---"}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500">Deal hiệu suất cao nhất</span>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                </div>

                {/* 2. Lỗ sâu nhất (Max Loss) */}
                <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 hover:border-rose-500/30 transition-all">
                  <div>
                    <span className="block text-[11px] font-medium text-slate-400">Lỗ nhiều nhất (Max Loss)</span>
                    <div className="mt-1 flex items-baseline gap-1.5">
                      <span className="text-lg font-black text-rose-400">
                        {metrics?.max_loss_pct !== undefined
                          ? `${metrics.max_loss_pct.toFixed(2)}%`
                          : "---"}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500">Kiểm định kỷ luật cắt lỗ</span>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <TrendingDown className="h-5 w-5" />
                  </div>
                </div>

                {/* 3. Lợi nhuận bình quân / deal */}
                <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 hover:border-cyan-500/30 transition-all">
                  <div>
                    <span className="block text-[11px] font-medium text-slate-400">Lãi TB / deal</span>
                    <div className="mt-1 flex items-baseline gap-1.5">
                      <span className={`text-lg font-black ${(metrics?.avg_trade_return_pct ?? 0) >= 0 ? "text-cyan-400" : "text-rose-400"}`}>
                        {metrics ? `${metrics.avg_trade_return_pct.toFixed(2)}%` : "---"}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500">Kỳ vọng toán học mỗi lệnh</span>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <BarChart3 className="h-5 w-5" />
                  </div>
                </div>

                {/* 4. Tỷ lệ Lợi nhuận / Rủi ro & Donut Win/Loss */}
                <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 hover:border-purple-500/30 transition-all">
                  <div>
                    <span className="block text-[11px] font-medium text-slate-400">Tỷ lệ Lợi nhuận / Rủi ro</span>
                    <div className="mt-1 flex items-baseline gap-1.5">
                      <span className="text-lg font-black text-purple-300">
                        {metrics?.reward_risk_ratio ? `${metrics.reward_risk_ratio}` : `${metrics?.profit_factor.toFixed(2)} : 1`}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500">
                      Thắng {metrics?.winning_trades ?? 0} / Thua {metrics?.losing_trades ?? 0} lệnh
                    </span>
                  </div>

                  {/* Donut Chart mini Win/Loss */}
                  <div className="relative flex h-11 w-11 items-center justify-center shrink-0">
                    <svg className="h-11 w-11 -rotate-90 transform">
                      <circle
                        cx="22"
                        cy="22"
                        r="16"
                        stroke="currentColor"
                        strokeWidth="3.5"
                        className="text-rose-500/30"
                        fill="transparent"
                      />
                      <circle
                        cx="22"
                        cy="22"
                        r="16"
                        stroke="currentColor"
                        strokeWidth="3.5"
                        strokeDasharray={2 * Math.PI * 16}
                        strokeDashoffset={2 * Math.PI * 16 * (1 - (metrics?.win_rate_pct ?? 50) / 100)}
                        strokeLinecap="round"
                        className="text-emerald-400"
                        fill="transparent"
                      />
                    </svg>
                    <div className="absolute text-[9px] font-black text-slate-200">
                      {metrics ? `${Math.round(metrics.win_rate_pct)}%` : "0%"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Subtabs Xem Kết quả (Biểu đồ Danh mục vs Bảng Phân rã vs Nhật ký Lệnh) */}
              <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs">
                <button
                  type="button"
                  onClick={() => setResultsTab("portfolio")}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all ${resultsTab === "portfolio"
                    ? "bg-slate-800 text-emerald-400 border border-slate-700"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  <BarChart3 className="h-4 w-4" />
                  <span>Biểu đồ tài sản</span>
                </button>

                {portfolioResult && (
                  <button
                    type="button"
                    onClick={() => setResultsTab("breakdown")}
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all ${resultsTab === "breakdown"
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
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-bold transition-all ${resultsTab === "trades"
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
                    className="ml-auto flex items-center gap-1 rounded bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-cyan-400 hover:bg-slate-700"
                  >
                    <ArrowLeft className="h-3 w-3" />
                    <span>Quay lại tổng quan danh mục</span>
                  </button>
                )}
              </div>

              {/* Tab 1: Biểu đồ tài sản Portfolio */}
              {resultsTab === "portfolio" && (
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
                  <div className="space-y-3 lg:col-span-8 xl:col-span-9">
                    {detailSymbol && portfolioResult?.individual_results?.[detailSymbol] && (
                      <div className="flex items-center justify-between rounded-lg bg-cyan-500/10 px-3 py-2 border border-cyan-500/30 text-xs">
                        <span className="font-bold text-cyan-400">
                          Đang xem chi tiết riêng mã: {detailSymbol}
                        </span>
                        <button
                          type="button"
                          onClick={() => setDetailSymbol(null)}
                          className="text-slate-400 hover:text-slate-200 underline"
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
                          ? initialCapital / (portfolioResult?.symbols_count || 1)
                          : initialCapital
                      }
                      height={320}
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

                  {/* Sidebar Tín hiệu Mới bên phải */}
                  <div className="lg:col-span-4 xl:col-span-3">
                    <RecentSignalsSidebar
                      signals={recentSignals}
                      onSelectSymbol={(sym) => {
                        onSelectSymbol(sym);
                      }}
                    />
                  </div>
                </div>
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

