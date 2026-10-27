import {
  BacktestConditionFilter,
  BacktestScopeType,
  SavedStrategyItem,
  StrategyPresetItem,
} from "./types";

export const STRATEGY_STORAGE_KEY = "stockpulse_saved_strategies_v1";

export interface StrategyMetricsSummary {
  roi_pct: number;
  bh_roi_pct: number;
  excess_pct: number;
  sharpe: number;
  mdd_pct: number;
  win_rate_pct: number;
  trades: number;
  max_gain_pct?: number;
  max_loss_pct?: number;
  reward_risk_ratio?: string | number;
}

export interface SaveStrategyInput {
  name: string;
  status: "active" | "draft";
  overwriteExistingId?: string;
  scope_type: BacktestScopeType;
  symbol?: string;
  index_name?: string;
  sector_name?: string;
  portfolio_symbols?: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  model_type: "lightgbm" | "lstm" | "none";
  slippage_rate?: number;
  use_advanced_settings?: boolean;
  buy_conditions: BacktestConditionFilter;
  sell_conditions: BacktestConditionFilter;
  metrics?: StrategyMetricsSummary;
}

export interface AppliedPresetConfig {
  scope_type: BacktestScopeType;
  symbol?: string;
  index_name?: string;
  sector_name?: string;
  portfolio_symbols?: string[];
  buy_conditions: BacktestConditionFilter;
  sell_conditions: BacktestConditionFilter;
}

/**
 * Sinh ID duy nhất cho chiến lược
 */
export function generateStrategyId(prefix = "strat"): string {
  return `${prefix}-${Date.now()}`;
}

/**
 * Lấy chuỗi ngày giờ theo định dạng vi-VN
 */
export function getCurrentDateTimeString(date = new Date()): string {
  return date.toLocaleString("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Tính toán động dải ngày 1 năm gần nhất dựa trên lịch thị trường chứng khoán Việt Nam:
 * - Thứ Bảy (day 6): lùi 1 ngày về Thứ Sáu
 * - Chủ Nhật (day 0): lùi 2 ngày về Thứ Sáu
 * - Bắt đầu lùi 365 ngày (1 năm) từ phiên gần nhất
 */
export function getDynamicDateRange(referenceDate = new Date()): { start: string; end: string } {
  const day = referenceDate.getDay();
  const rollback = day === 6 ? 1 : day === 0 ? 2 : 0;
  const end = new Date(referenceDate);
  end.setDate(end.getDate() - rollback);
  const start = new Date(end);
  start.setFullYear(start.getFullYear() - 1);

  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
}

/**
 * Kiểm định dải ngày chọn kiểm thử (tối đa 365 ngày, kết thúc >= bắt đầu)
 */
export function validateDateRange(
  startDate: string,
  endDate: string
): { isValid: boolean; error?: string; diffDays: number } {
  try {
    const s = new Date(startDate);
    const e = new Date(endDate);
    if (isNaN(s.getTime()) || isNaN(e.getTime())) {
      return { isValid: false, error: "Định dạng ngày không hợp lệ", diffDays: 0 };
    }
    const diffDays = Math.round((e.getTime() - s.getTime()) / (1000 * 3600 * 24));
    if (diffDays < 0) {
      return {
        isValid: false,
        error: "Lỗi: Ngày kết thúc phải sau ngày bắt đầu!",
        diffDays,
      };
    }
    if (diffDays > 365) {
      return {
        isValid: false,
        error: "Lỗi: Khoảng thời gian chọn không quá 1 năm (tối đa 365 ngày)!",
        diffDays,
      };
    }
    return { isValid: true, diffDays };
  } catch {
    return { isValid: false, error: "Lỗi tính toán dải ngày", diffDays: 0 };
  }
}

/**
 * Tải danh sách chiến lược từ Storage (lọc bỏ seed cũ, xử lý parse lỗi)
 */
export function loadSavedStrategies(storage?: Storage): SavedStrategyItem[] {
  const activeStorage =
    storage || (typeof window !== "undefined" ? window.localStorage : undefined);
  if (!activeStorage) return [];

  try {
    const raw = activeStorage.getItem(STRATEGY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    const userOnly = parsed.filter(
      (s: SavedStrategyItem) => s && s.id !== "strat-seed-1" && s.id !== "strat-seed-2"
    );
    if (userOnly.length !== parsed.length) {
      activeStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(userOnly));
    }
    return userOnly;
  } catch {
    return [];
  }
}

/**
 * Lưu danh sách chiến lược vào Storage an toàn
 */
export function persistSavedStrategies(
  strategies: SavedStrategyItem[],
  storage?: Storage
): boolean {
  const activeStorage =
    storage || (typeof window !== "undefined" ? window.localStorage : undefined);
  if (!activeStorage) return false;

  try {
    activeStorage.setItem(STRATEGY_STORAGE_KEY, JSON.stringify(strategies));
    return true;
  } catch {
    return false;
  }
}

/**
 * Thêm mới hoặc cập nhật/ghi đè chiến lược
 */
export function saveOrUpdateStrategy(
  currentList: SavedStrategyItem[],
  input: SaveStrategyInput,
  storage?: Storage
): { updatedList: SavedStrategyItem[]; activeId: string; action: "created" | "updated" } {
  const now = getCurrentDateTimeString();
  const trimmedName = input.name.trim();

  const targetId =
    input.overwriteExistingId ||
    currentList.find((s) => s.name.trim().toLowerCase() === trimmedName.toLowerCase())?.id;

  let updatedList: SavedStrategyItem[];
  let activeId: string;
  let action: "created" | "updated";

  if (targetId) {
    action = "updated";
    activeId = targetId;
    updatedList = currentList.map((s) => {
      if (s.id === targetId) {
        return {
          ...s,
          name: trimmedName,
          status: input.status,
          updated_at: now,
          scope_type: input.scope_type,
          symbol: input.symbol,
          index_name: input.index_name,
          sector_name: input.sector_name,
          portfolio_symbols: input.portfolio_symbols,
          start_date: input.start_date,
          end_date: input.end_date,
          initial_capital: input.initial_capital,
          model_type: input.model_type,
          slippage_rate: input.slippage_rate,
          use_advanced_settings: input.use_advanced_settings,
          buy_conditions: input.buy_conditions,
          sell_conditions: input.sell_conditions,
          last_metrics: input.metrics || s.last_metrics,
        };
      }
      return s;
    });
  } else {
    action = "created";
    const newId = generateStrategyId();
    activeId = newId;
    const newStrategy: SavedStrategyItem = {
      id: newId,
      name: trimmedName,
      status: input.status,
      created_at: now,
      updated_at: now,
      scope_type: input.scope_type,
      symbol: input.symbol,
      index_name: input.index_name,
      sector_name: input.sector_name,
      portfolio_symbols: input.portfolio_symbols,
      start_date: input.start_date,
      end_date: input.end_date,
      initial_capital: input.initial_capital,
      model_type: input.model_type,
      slippage_rate: input.slippage_rate,
      use_advanced_settings: input.use_advanced_settings,
      buy_conditions: input.buy_conditions,
      sell_conditions: input.sell_conditions,
      last_metrics: input.metrics,
    };
    updatedList = [newStrategy, ...currentList];
  }

  persistSavedStrategies(updatedList, storage);
  return { updatedList, activeId, action };
}

/**
 * Đổi trạng thái chiến lược giữa "active" (Triển khai) và "draft" (Chưa triển khai)
 */
export function toggleStrategyStatus(
  currentList: SavedStrategyItem[],
  strategyId: string,
  storage?: Storage
): { updatedList: SavedStrategyItem[]; nextStatus: "active" | "draft" | null } {
  const target = currentList.find((s) => s.id === strategyId);
  if (!target) {
    return { updatedList: currentList, nextStatus: null };
  }

  const nextStatus: "active" | "draft" = target.status === "active" ? "draft" : "active";
  const now = getCurrentDateTimeString();

  const updatedList = currentList.map((s) => {
    if (s.id === strategyId) {
      return {
        ...s,
        status: nextStatus,
        updated_at: now,
      };
    }
    return s;
  });

  persistSavedStrategies(updatedList, storage);
  return { updatedList, nextStatus };
}

/**
 * Xóa chiến lược khỏi danh sách và lưu vào storage
 */
export function deleteStrategy(
  currentList: SavedStrategyItem[],
  strategyId: string,
  storage?: Storage
): { updatedList: SavedStrategyItem[]; deleted: boolean } {
  const initialLength = currentList.length;
  const updatedList = currentList.filter((s) => s.id !== strategyId);
  const deleted = updatedList.length !== initialLength;

  if (deleted) {
    persistSavedStrategies(updatedList, storage);
  }
  return { updatedList, deleted };
}

/**
 * Lọc danh sách chiến lược theo trạng thái và tìm kiếm đa năng
 */
export function filterStrategies(
  strategies: SavedStrategyItem[],
  filterStatus: "all" | "active" | "draft",
  searchQuery: string
): SavedStrategyItem[] {
  return strategies.filter((s) => {
    if (filterStatus === "active" && s.status !== "active") return false;
    if (filterStatus === "draft" && s.status !== "draft") return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
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
}

/**
 * Tạo tên bản sao tự động khi lưu trùng lặp
 */
export function generateCopyStrategyName(
  baseName: string,
  existingList: SavedStrategyItem[]
): string {
  const trimmed = baseName.trim();
  let copyName = `${trimmed} (Bản sao)`;
  let counter = 2;
  while (existingList.some((s) => s.name.toLowerCase() === copyName.toLowerCase())) {
    copyName = `${trimmed} (Bản sao ${counter})`;
    counter++;
  }
  return copyName;
}

/**
 * Xử lý thêm/bớt mã trong danh mục kiểm thử, ngăn chặn danh mục rỗng
 */
export function togglePortfolioSymbolList(
  currentSymbols: string[],
  symbolToToggle: string
): string[] {
  if (currentSymbols.includes(symbolToToggle)) {
    if (currentSymbols.length > 1) {
      return currentSymbols.filter((s) => s !== symbolToToggle);
    }
    return currentSymbols;
  }
  return [...currentSymbols, symbolToToggle];
}

/**
 * Chuyển đổi Preset thực chiến thành cấu hình chiến lược tương thích
 */
export function mapPresetToStrategyConfig(
  preset: StrategyPresetItem,
  currentSellConditions?: BacktestConditionFilter
): AppliedPresetConfig {
  let scope_type: BacktestScopeType = "stock";
  let symbol: string | undefined = preset.default_symbol;
  let index_name: string | undefined = undefined;
  let sector_name: string | undefined = undefined;
  let portfolio_symbols: string[] | undefined = undefined;

  if (preset.category.includes("VN30")) {
    scope_type = "index";
    index_name = "VN30";
    symbol = undefined;
  } else if (preset.category.includes("VN100")) {
    scope_type = "index";
    index_name = "VN100";
    symbol = undefined;
  } else if (preset.category.includes("Ngân hàng")) {
    scope_type = "sector";
    sector_name = "Ngân hàng";
    symbol = undefined;
  } else if (preset.target_symbols && preset.target_symbols.length > 1) {
    scope_type = "portfolio";
    portfolio_symbols = preset.target_symbols;
    symbol = undefined;
  }

  const updatedSell: BacktestConditionFilter = {
    ...(currentSellConditions || {}),
    condition_logic: "OR",
    take_profit_pct: preset.take_profit_pct > 0 ? preset.take_profit_pct : null,
    stop_loss_pct: preset.stop_loss_pct > 0 ? preset.stop_loss_pct : null,
    trailing_stop_pct: preset.trailing_stop_pct > 0 ? preset.trailing_stop_pct : null,
  };

  let updatedBuy: BacktestConditionFilter = {
    condition_logic: "AND",
    market_condition: "all",
  };

  switch (preset.id) {
    case "dnse-01":
      updatedBuy = {
        ...updatedBuy,
        use_ema: true,
        use_volume_spike: true,
        use_price_cross: true,
        foreign_net_buy: true,
      };
      break;
    case "dnse-02":
      updatedBuy = {
        ...updatedBuy,
        use_rsi: true,
        rsi_threshold: 70,
        use_volume_spike: true,
      };
      break;
    case "dnse-03":
      updatedBuy = {
        ...updatedBuy,
        use_pe: true,
        max_pe: 16,
        use_price_increase: true,
        foreign_net_buy: true,
      };
      break;
    case "dnse-04":
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
      break;
    case "dnse-05":
      updatedBuy = {
        ...updatedBuy,
        use_pb: true,
        max_pb: 1.0,
        use_avg_trading_val: true,
        min_avg_trading_val: 10,
      };
      break;
    case "dnse-06":
      updatedBuy = {
        ...updatedBuy,
        use_price_increase: true,
        use_volume_spike: true,
      };
      break;
    case "dnse-07":
      updatedBuy = {
        ...updatedBuy,
        use_adx: true,
        use_bb: true,
      };
      break;
    case "dnse-08":
      updatedBuy = {
        ...updatedBuy,
        use_price_cross: true,
        use_rsi: true,
        rsi_threshold: 57,
      };
      break;
    default:
      updatedBuy = {
        ...updatedBuy,
        use_ma: true,
        use_rsi: true,
      };
      break;
  }

  return {
    scope_type,
    symbol,
    index_name,
    sector_name,
    portfolio_symbols,
    buy_conditions: updatedBuy,
    sell_conditions: updatedSell,
  };
}
