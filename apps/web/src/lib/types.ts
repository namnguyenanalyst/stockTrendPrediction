/**
 * TypeScript Interfaces cho Hệ thống Web Dashboard Dự báo Chứng khoán VN.
 * Đồng bộ 1:1 với Pydantic Schemas của FastAPI Backend (apps/api/app/models/schemas.py).
 */

export interface StockSymbolInfo {
  symbol: string;
  name: string;
  exchange: string;
  is_core: boolean;
  is_vn30?: boolean;
  sector?: string;
}

export interface StockBar {
  date: string; // YYYY-MM-DD
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockHistoryResponse {
  symbol: string;
  total_bars: number;
  bars: StockBar[];
}

export interface StockIndicatorBar {
  date: string;
  close: number;
  open_close_ratio: number;
  hl_ratio: number;
  sma_20_dev: number;
  sma_50_dev: number;
  sma_200_dev: number;
  cv_50: number;
  cv_200: number;
  rsi_14: number;
  return_1d: number;
  vol_ratio: number;
  vnindex_return_1d: number;
}

export interface StockIndicatorsResponse {
  symbol: string;
  total_bars: number;
  indicators: StockIndicatorBar[];
}

export interface StockSummaryResponse {
  symbol: string;
  latest_date: string;
  latest_close: number;
  prev_close: number;
  change_pct: number;
  volume: number;
  rsi_14: number;
  sma_20_dev: number;
  sma_50_dev: number;
}

export interface IndexOverview {
  name: string;
  symbol: string;
  value: number;
  change: number;
  change_pct: number;
  volume_str: string;
  value_str: string;
  advancing: number;
  ceiling: number;
  unchanged: number;
  declining: number;
  floor: number;
  sparkline: number[];
}

export interface StockBoardItem {
  symbol: string;
  name: string;
  exchange: string;
  sector: string;
  close: number;
  change: number;
  change_pct: number;
  volume: number;
  ceiling: number;
  floor: number;
  reference: number;
  sparkline: number[];
  buy_ratio: number;
  sell_ratio: number;
  rsi_14: number;
  sma_20_dev: number;
  ai_bias: string;
}

export interface MarketBreadth {
  ceiling: number;
  advancing: number;
  unchanged: number;
  declining: number;
  floor: number;
}

export interface MarketBoardResponse {
  updated_at: string;
  indices: IndexOverview[];
  breadth: MarketBreadth;
  stocks: StockBoardItem[];
  ai_market_insight: string;
  top_gainers: StockBoardItem[];
  top_losers: StockBoardItem[];
  top_search?: StockBoardItem[];
  top_volume?: StockBoardItem[];
}

export interface MarketSyncStatusResponse {
  target_date: string;
  session_type: "session_T" | "session_T_minus_1";
  session_name: string;
  status_label: string;
  is_market_closed: boolean;
  prediction_horizon_desc: string;
  current_time?: string;
  updated_symbols?: string[];
  total_symbols?: number;
}

export interface DayForecast {
  day_offset: number; // 1, 2, 3
  day_name: string; // "T+1", "T+2", "T+3"
  date?: string; // "YYYY-MM-DD"
  predicted_trend: "GIẢM" | "ĐI NGANG" | "TĂNG";
  signal: string; // "BÁN (SELL)" | "NẮM GIỮ (HOLD)" | "MUA (BUY)"
  confidence: number;
  probabilities: {
    GIẢM: number;
    "ĐI NGANG": number;
    TĂNG: number;
    [key: string]: number;
  };
  note?: string;
}

export interface ModelMetricsSummary {
  accuracy?: number;
  macro_f1?: number;
  weighted_f1?: number;
  precision_macro?: number;
  recall_macro?: number;
  [key: string]: unknown;
}

export interface RetrainResponse {
  status: string;
  timestamp: string;
  horizon: string;
  horizon_days: number;
  threshold: number;
  val_buffer_days: number;
  scope?: string;
  symbols_count?: number;
  symbols?: string[];
  latest_market_date: string;
  train_samples: number;
  val_samples: number;
  total_samples: number;
  lightgbm_metrics?: ModelMetricsSummary;
  lstm_metrics?: ModelMetricsSummary;
}

export interface PredictionResponse {
  symbol: string;
  date: string;
  data_as_of_date?: string;
  current_price: number;
  model_type: "lightgbm" | "lstm";
  predicted_label: number; // 0: Giảm, 1: Đi ngang, 2: Tăng
  class_name: "GIẢM" | "ĐI NGANG" | "TĂNG";
  signal: string; // "BÁN (SELL)" | "NẮM GIỮ (HOLD)" | "MUA (BUY)"
  probabilities: {
    GIẢM: number;
    "ĐI NGANG": number;
    TĂNG: number;
    [key: string]: number;
  };
  horizon: string;
  horizon_days?: number;
  is_live_synced?: boolean;
  market_session_label?: string;
  session_info?: MarketSyncStatusResponse;
  trajectory?: DayForecast[];
  summary_guidance?: string;
  training_info?: {
    latest_market_date?: string;
    horizon?: string;
    threshold?: number;
    train_samples?: number;
    val_samples?: number;
    lightgbm_metrics?: ModelMetricsSummary;
    lstm_metrics?: ModelMetricsSummary;
    timestamp?: string;
  };
}

export interface BatchPredictionResponse {
  model_type: string;
  total_symbols: number;
  predictions: PredictionResponse[];
}

export interface BacktestRequest {
  symbol: string;
  model_type: "lightgbm" | "lstm";
  initial_capital: number;
  slippage_rate?: number;
  fee_rate?: number;
  tax_rate?: number;
  lot_size?: number;
  settlement_delay?: number;
  execution_price?: "open" | "close";
  buy_prob_threshold?: number;
  sell_prob_threshold?: number;
  take_profit_pct?: number | null;
  stop_loss_pct?: number | null;
  trailing_stop_pct?: number | null;
  preset_id?: string | null;
}

export interface BacktestMetricsSchema {
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  cagr_pct: number;
  buy_and_hold_return_pct: number;
  excess_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  calmar_ratio: number;
  var_95_pct: number;
  cvar_95_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_trade_return_pct: number;
  avg_holding_days: number;
  total_fees_paid: number;
  total_taxes_paid: number;
  total_costs: number;
  cost_impact_pct: number;
  max_gain_pct?: number;
  max_loss_pct?: number;
  reward_risk_ratio?: string | number;
}

export interface EquityCurvePoint {
  date: string;
  total_equity: number;
  benchmark_equity: number;
  drawdown_pct: number;
  daily_return: number;
}

export interface TradeLogItem {
  trade_id: number;
  order_type: "BUY" | "SELL";
  exec_date: string;
  exec_price: number;
  shares: number;
  fee: number;
  tax: number;
  net_cash_flow: number;
  realized_pnl: number | null;
  realized_return_pct: number | null;
  holding_days: number | null;
  reason: string;
}

export interface BacktestResponse {
  symbol: string;
  strategy_name: string;
  config: Record<string, unknown>;
  metrics: BacktestMetricsSchema;
  equity_curve: EquityCurvePoint[];
  trades: TradeLogItem[];
}

export interface BacktestSummaryItem {
  symbol: string;
  model: string;
  roi_pct: number;
  bh_roi_pct: number;
  excess_pct: number;
  sharpe: number;
  sortino: number;
  mdd_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  trades: number;
  costs: number;
}

export interface BacktestSummaryResponse {
  model_type: string;
  summary: BacktestSummaryItem[];
}

export interface StrategyPresetItem {
  id: string;
  name: string;
  category: string;
  description: string;
  target_symbols: string[];
  default_symbol: string;
  conditions_summary: string;
  win_rate_pct: number;
  cumulative_pnl_pct: number;
  risk_reward_ratio: string;
  copy_count: number;
  take_profit_pct: number;
  stop_loss_pct: number;
  trailing_stop_pct: number;
  model_type: "lightgbm" | "lstm";
  timeframe: string;
}

export interface StrategyPresetsResponse {
  presets: StrategyPresetItem[];
}

export interface RecentSignalItem {
  signal_id: string;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  strategy_name: string;
  price: number;
  target_price: number;
  stop_price: number;
  confidence: number;
  timestamp: string;
  status: string;
}

export interface RecentSignalsResponse {
  signals: RecentSignalItem[];
}

export type BacktestScopeType = "stock" | "index" | "sector" | "portfolio";

export interface BacktestConditionFilter {
  condition_logic?: "AND" | "OR";
  market_condition?: "all" | "uptrend" | "sideways" | "downtrend";

  // 1. Thông tin Cổ phiếu & Khối lượng
  use_stock_price?: boolean;
  min_stock_price?: number;
  max_stock_price?: number;
  use_market_cap?: boolean;
  min_market_cap?: number;
  max_market_cap?: number;
  use_avg_trading_val?: boolean;
  avg_trading_val_period?: number; // 5, 10, 20 phiên
  min_avg_trading_val?: number;
  max_avg_trading_val?: number;
  use_volume_spike?: boolean;
  vol_spike_period?: number; // 5, 10, 20 phiên
  min_vol_spike_pct?: number; // e.g. -100% đến 19900%
  max_vol_spike_pct?: number;

  // 2. Chỉ số kỹ thuật Cổ phiếu
  use_ma?: boolean;
  ma_type?: string;
  ma_left?: string; // "MA 10", "MA 20", "MA 50", "MA 100", "Giá đóng cửa"
  ma_operator?: string; // "Cắt lên" | "Cắt xuống" | "Nằm trên" | "Nằm dưới"
  ma_right?: string; // "MA 10", "MA 20", "MA 50", "MA 100", "Giá đóng cửa"
  use_adx?: boolean;
  min_adx?: number;
  max_adx?: number;
  use_rs?: boolean;
  min_rs?: number;
  max_rs?: number;
  use_rsi?: boolean;
  rsi_threshold?: number; // legacy backward compatibility
  rsi_min?: number;
  rsi_max?: number;
  rsi_sell_threshold?: number;
  use_price_cross?: boolean;
  price_cross_operator?: string; // "Cắt lên" | "Cắt xuống" | "Nằm trên" | "Nằm dưới"
  price_cross_target?: string; // "MA 10", "MA 20", "EMA 20", "BB Trên", "BB Dưới"
  use_price_increase?: boolean;
  price_t0_field?: string; // "Giá đóng cửa T0", "Giá mở cửa T0", "Giá cao nhất T0"
  price_t0_operator?: string; // ">", "<", "=", ">=", "<="
  price_t1_field?: string; // "Giá đóng cửa T-1", "Giá mở cửa T-1", "Giá cao nhất T-1"
  use_ema?: boolean;
  ema_left?: string; // "EMA 10", "EMA 12", "EMA 20", "EMA 26", "EMA 50"
  ema_operator?: string; // "Cắt lên" | "Cắt xuống" | "Nằm trên" | "Nằm dưới"
  ema_right?: string; // "EMA 10", "EMA 20", "EMA 50", "Giá đóng cửa"
  use_macd?: boolean;
  macd_operator?: string; // "Cắt lên" | "Cắt xuống" | "Nằm trên" | "Nằm dưới"
  macd_target?: string; // "Đường tín hiệu" | "Đường 0"
  use_bb?: boolean;

  // 3. Kết quả kinh doanh
  growth_rev_latest?: boolean;
  min_growth_rev_latest?: number;
  max_growth_rev_latest?: number;
  growth_rev_prev?: boolean;
  min_growth_rev_prev?: number;
  max_growth_rev_prev?: number;
  growth_rev_ttm?: boolean;
  min_growth_rev_ttm?: number;
  max_growth_rev_ttm?: number;
  growth_np_latest?: boolean;
  min_growth_np_latest?: number;
  max_growth_np_latest?: number;
  growth_np_prev?: boolean;
  min_growth_np_prev?: number;
  max_growth_np_prev?: number;
  growth_np_ttm?: boolean;
  min_growth_np_ttm?: number;
  max_growth_np_ttm?: number;

  // 4. Định giá
  use_pe?: boolean;
  min_pe?: number | null;
  max_pe?: number | null;
  use_pb?: boolean;
  min_pb?: number | null;
  max_pb?: number | null;
  use_ps?: boolean;
  min_ps?: number | null;
  max_ps?: number | null;
  use_roa?: boolean;
  min_roa?: number | null;
  max_roa?: number | null;
  use_roe?: boolean;
  min_roe?: number | null;
  max_roe?: number | null;
  use_eps?: boolean;
  min_eps?: number | null;
  max_eps?: number | null;
  growth_eps?: boolean;
  min_growth_eps?: number | null;
  max_growth_eps?: number | null;

  // 5. Dòng tiền Cổ phiếu
  foreign_net_buy?: boolean;
  foreign_net_val?: boolean;
  min_foreign_val?: number;
  max_foreign_val?: number;
  foreign_net_vol?: boolean;
  min_foreign_vol?: number;
  max_foreign_vol?: number;
  prop_net_buy?: boolean;
  prop_net_val?: boolean;
  min_prop_val?: number;
  max_prop_val?: number;
  prop_net_vol?: boolean;
  min_prop_vol?: number;
  max_prop_vol?: number;
  foreign_net_sell?: boolean;
  foreign_net_sell_val?: boolean;
  min_foreign_sell_val?: number;
  max_foreign_sell_val?: number;
  foreign_net_sell_vol?: boolean;
  min_foreign_sell_vol?: number;
  max_foreign_sell_vol?: number;
  prop_net_sell_val?: boolean;
  min_prop_sell_val?: number;
  max_prop_sell_val?: number;
  prop_net_sell_vol?: boolean;
  min_prop_sell_vol?: number;
  max_prop_sell_vol?: number;

  // Quản trị vị thế & Bán
  take_profit_pct?: number | null;
  stop_loss_pct?: number | null;
  trailing_stop_pct?: number | null;
}


export interface AdvancedBacktestRequest {
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
  buy_conditions?: BacktestConditionFilter;
  sell_conditions?: BacktestConditionFilter;
  use_advanced_settings?: boolean;
}

export interface SymbolBreakdownItem {
  symbol: string;
  name: string;
  sector: string;
  roi_pct: number;
  bh_roi_pct: number;
  excess_pct: number;
  sharpe: number;
  sortino: number;
  mdd_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  trades: number;
  costs: number;
}

export interface PortfolioBacktestResponse {
  scope_type: BacktestScopeType;
  scope_target: string;
  start_date: string;
  end_date: string;
  symbols_count: number;
  aggregate_metrics: BacktestMetricsSchema;
  portfolio_equity_curve: EquityCurvePoint[];
  symbols_breakdown: SymbolBreakdownItem[];
  individual_results?: Record<string, {
    metrics: BacktestMetricsSchema;
    equity_curve: EquityCurvePoint[];
    trades: TradeLogItem[];
  }>;
}

export interface SectorItem {
  sector: string;
  symbols: string[];
  count: number;
}

export interface SavedStrategyItem {
  id: string;
  name: string;
  status: "active" | "draft"; // "active" = Triển khai (theo dõi tín hiệu realtime), "draft" = Chưa triển khai (bản nháp)
  created_at: string;
  updated_at: string;
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
  last_metrics?: {
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
  };
}

// =============================================================================
// Auth & Personalization Types
// =============================================================================

export type UserRole = "trader" | "admin";
export type RiskProfile = "conservative" | "balanced" | "aggressive";

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: UserRole | string;
  risk_profile: RiskProfile | string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string | null;
  risk_profile?: RiskProfile | string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserWatchlist {
  id: string;
  user_id?: string;
  name: string;
  symbols: string[];
  created_at: string;
  updated_at?: string;
}

export interface UserStrategyPreset {
  id: string;
  user_id?: string;
  name: string;
  description?: string | null;
  parameters: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface BacktestHistoryCreateRequest {
  symbol: string;
  strategy_name: string;
  strategy_type: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  equity_curve: EquityCurvePoint[];
}

export interface UserBacktestHistory {
  id: string;
  user_id?: string;
  symbol: string;
  strategy_name: string;
  strategy_type: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  equity_curve: EquityCurvePoint[];
  executed_at: string;
}
