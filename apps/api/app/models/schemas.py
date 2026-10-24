"""Pydantic V2 Schemas chuẩn hóa dữ liệu Request và Response cho VN Stock API.

Bao gồm:
1. Monitoring: HealthResponse
2. Dữ liệu cổ phiếu: StockBar, StockHistoryResponse, StockIndicatorBar, StockIndicatorsResponse, StockSummaryResponse
3. Dự báo AI: PredictionResponse, BatchPredictionResponse
4. Kiểm thử chiến lược: BacktestRequest, BacktestMetricsSchema, EquityCurvePoint, TradeLogItem, BacktestResponse, BacktestSummaryResponse
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# 1. MONITORING SCHEMAS
# ============================================================================
class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Trạng thái hệ thống")
    service: str = Field(default="vn-stock-api", description="Tên service")
    version: str = Field(default="0.1.0", description="Phiên bản API")
    environment: str = Field(default="development", description="Môi trường vận hành")


# ============================================================================
# 2. STOCKS & INDICATORS SCHEMAS
# ============================================================================
class StockSymbolInfo(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu (ví dụ: VIC, HPG)")
    name: str = Field(..., description="Tên công ty niêm yết")
    exchange: str = Field(default="HOSE", description="Sàn giao dịch (HOSE, HNX)")
    is_core: bool = Field(
        default=False, description="Có thuộc 5 mã trọng tâm nghiên cứu hay không"
    )
    sector: str = Field(default="Đa ngành", description="Nhóm ngành nghề")
    is_vn30: bool = Field(default=False, description="Có thuộc rổ chỉ số VN30 hay không")


class StockBar(BaseModel):
    date: str = Field(..., description="Ngày giao dịch (YYYY-MM-DD)")
    open: float = Field(..., description="Giá mở cửa")
    high: float = Field(..., description="Giá cao nhất")
    low: float = Field(..., description="Giá thấp nhất")
    close: float = Field(..., description="Giá đóng cửa")
    volume: int = Field(..., description="Khối lượng giao dịch")


class StockHistoryResponse(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu")
    total_bars: int = Field(..., description="Tổng số phiên giao dịch")
    bars: list[StockBar] = Field(..., description="Danh sách các nến giá OHLCV")


class StockIndicatorBar(BaseModel):
    date: str = Field(..., description="Ngày giao dịch (YYYY-MM-DD)")
    close: float = Field(..., description="Giá đóng cửa")
    open_close_ratio: float = Field(..., description="Tỷ lệ (Open - Close) / Close")
    hl_ratio: float = Field(..., description="Biên độ (High - Low) / Close")
    sma_20_dev: float = Field(..., description="Độ lệch so với SMA 20 phiên")
    sma_50_dev: float = Field(..., description="Độ lệch so với SMA 50 phiên")
    sma_200_dev: float = Field(..., description="Độ lệch so với SMA 200 phiên")
    cv_50: float = Field(..., description="Hệ số biến thiên rủi ro 50 phiên (SD / SMA)")
    cv_200: float = Field(..., description="Hệ số biến thiên rủi ro 200 phiên")
    rsi_14: float = Field(..., description="Chỉ số sức mạnh tương đối RSI 14")
    return_1d: float = Field(..., description="Lợi suất 1 phiên quá khứ")
    vol_ratio: float = Field(..., description="Tỷ lệ thanh khoản Volume / SMA_Vol_20")
    vnindex_return_1d: float = Field(..., description="Lợi suất chỉ số toàn thị trường VN-Index")


class StockIndicatorsResponse(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu")
    total_bars: int = Field(..., description="Tổng số phiên giao dịch")
    indicators: list[StockIndicatorBar] = Field(..., description="Danh sách các chỉ báo kỹ thuật")


class StockSummaryResponse(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu")
    latest_date: str = Field(..., description="Ngày giao dịch gần nhất")
    latest_close: float = Field(..., description="Giá đóng cửa gần nhất (nghìn VNĐ)")
    prev_close: float = Field(..., description="Giá đóng cửa phiên trước đó")
    change_pct: float = Field(..., description="Tỷ lệ thay đổi giá 1 phiên (%)")
    volume: int = Field(..., description="Khối lượng giao dịch phiên gần nhất")
    rsi_14: float = Field(..., description="RSI 14 phiên")
    sma_20_dev: float = Field(..., description="Độ lệch so với SMA 20 (%)")
    sma_50_dev: float = Field(..., description="Độ lệch so với SMA 50 (%)")


class IndexOverview(BaseModel):
    name: str = Field(..., description="Tên chỉ số")
    symbol: str = Field(..., description="Mã chỉ số (VNINDEX, VN30...)")
    value: float = Field(..., description="Điểm số hiện tại")
    change: float = Field(..., description="Điểm tăng/giảm")
    change_pct: float = Field(..., description="Tỷ lệ tăng/giảm (%)")
    volume_str: str = Field(..., description="Khối lượng giao dịch định dạng chuỗi")
    value_str: str = Field(..., description="Giá trị giao dịch định dạng chuỗi")
    advancing: int = Field(default=0, description="Số mã tăng")
    ceiling: int = Field(default=0, description="Số mã trần")
    unchanged: int = Field(default=0, description="Số mã tham chiếu")
    declining: int = Field(default=0, description="Số mã giảm")
    floor: int = Field(default=0, description="Số mã sàn")
    sparkline: list[float] = Field(default_factory=list, description="Chuỗi giá trị thu nhỏ vẽ biểu đồ")


class StockBoardItem(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu")
    name: str = Field(..., description="Tên công ty niêm yết")
    exchange: str = Field(default="HOSE", description="Sàn giao dịch")
    sector: str = Field(default="Đa ngành", description="Nhóm ngành kinh tế")
    close: float = Field(..., description="Giá khớp gần nhất (nghìn VNĐ)")
    change: float = Field(..., description="Thay đổi giá so với tham chiếu")
    change_pct: float = Field(..., description="Tỷ lệ thay đổi giá (%)")
    volume: int = Field(..., description="Khối lượng giao dịch khớp lệnh")
    ceiling: float = Field(..., description="Giá trần")
    floor: float = Field(..., description="Giá sàn")
    reference: float = Field(..., description="Giá tham chiếu")
    sparkline: list[float] = Field(default_factory=list, description="Chuỗi nến 10 phiên gần nhất")
    buy_ratio: int = Field(default=50, description="Tỷ lệ áp lực Mua chủ động (%)")
    sell_ratio: int = Field(default=50, description="Tỷ lệ áp lực Bán chủ động (%)")
    rsi_14: float = Field(default=50.0, description="Chỉ số RSI 14")
    sma_20_dev: float = Field(default=0.0, description="Độ lệch SMA 20 (%)")
    ai_bias: str = Field(default="ĐI NGANG", description="Xu hướng AI dự phóng ('TĂNG', 'GIẢM'...)")


class MarketBreadth(BaseModel):
    ceiling: int = Field(default=0, description="Số mã giá trần")
    advancing: int = Field(default=0, description="Số mã tăng giá")
    unchanged: int = Field(default=0, description="Số mã tham chiếu")
    declining: int = Field(default=0, description="Số mã giảm giá")
    floor: int = Field(default=0, description="Số mã giá sàn")


class MarketBoardResponse(BaseModel):
    updated_at: str = Field(..., description="Thời điểm cập nhật")
    indices: list[IndexOverview] = Field(..., description="Các chỉ số thị trường")
    breadth: MarketBreadth = Field(..., description="Độ rộng thị trường")
    stocks: list[StockBoardItem] = Field(..., description="Danh sách cổ phiếu trên bảng giá")
    ai_market_insight: str = Field(..., description="Nhận định thị trường từ Trợ lý AI")
    top_gainers: list[StockBoardItem] = Field(default_factory=list, description="Top cổ phiếu tăng mạnh nhất")
    top_losers: list[StockBoardItem] = Field(default_factory=list, description="Top cổ phiếu giảm mạnh nhất")
    top_search: list[StockBoardItem] = Field(
        default_factory=list,
        description="Top 10 cổ phiếu được quan tâm / tìm kiếm nhiều nhất dựa trên dữ liệu thanh khoản & biến động",
    )
    top_volume: list[StockBoardItem] = Field(
        default_factory=list,
        description="Top 10 cổ phiếu có khối lượng giao dịch (KLGD) lớn nhất phiên",
    )


# ============================================================================
# 3. AI PREDICTION SCHEMAS
# ============================================================================
class DayForecast(BaseModel):
    day_offset: int = Field(..., description="Chỉ số ngày (1: T+1, 2: T+2, 3: T+3)")
    day_name: str = Field(..., description="Tên phiên ('T+1', 'T+2', 'T+3')")
    date: str = Field(default="", description="Ngày giao dịch dương lịch tương ứng")
    predicted_trend: str = Field(..., description="Xu hướng dự phóng ('GIẢM', 'ĐI NGANG', 'TĂNG')")
    signal: str = Field(
        ..., description="Tín hiệu hành động ('BÁN (SELL)', 'NẮM GIỮ (HOLD)', 'MUA (BUY)')"
    )
    confidence: float = Field(..., description="Độ tin cậy xác suất lớn nhất")
    probabilities: dict[str, float] = Field(..., description="Phân bổ xác suất 3 lớp của phiên")
    note: str = Field(default="", description="Ghi chú nghiệp vụ vi cấu trúc giao dịch")


class PredictionResponse(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu dự báo")
    date: str = Field(..., description="Ngày của phiên giao dịch căn cứ")
    data_as_of_date: str = Field(default="", description="Ngày chốt dữ liệu căn cứ")
    current_price: float = Field(..., description="Thị giá đóng cửa phiên căn cứ (nghìn VNĐ)")
    model_type: str = Field(..., description="Mô hình sử dụng ('lightgbm' hoặc 'lstm')")
    predicted_label: int = Field(..., description="Nhãn dự báo (0: Giảm, 1: Đi ngang, 2: Tăng)")
    class_name: str = Field(..., description="Tên xu hướng ('GIẢM', 'ĐI NGANG', 'TĂNG')")
    signal: str = Field(
        ..., description="Khuyến nghị đầu tư ('BÁN (SELL)', 'NẮM GIỮ (HOLD)', 'MUA (BUY)')"
    )
    probabilities: dict[str, float] = Field(
        ..., description="Phân bổ xác suất 3 lớp {'GIẢM': p0, 'ĐI NGANG': p1, 'TĂNG': p2}"
    )
    horizon: str = Field(default="T+3", description="Kỳ hạn dự báo")
    horizon_days: int = Field(default=3, description="Số ngày nắm giữ mục tiêu (3 phiên)")
    is_live_synced: bool = Field(default=False, description="Trạng thái đồng bộ nến mới nhất từ SSI")
    market_session_label: str = Field(default="", description="Nhãn phiên giao dịch căn cứ")
    session_info: dict | None = Field(default=None, description="Chi tiết trạng thái phiên giao dịch")
    trajectory: list[DayForecast] = Field(
        default_factory=list, description="Quỹ đạo dự phóng 3 phiên T+1, T+2, T+3"
    )
    summary_guidance: str = Field(default="", description="Khuyến nghị hành động thực chiến")
    training_info: dict | None = Field(
        default=None, description="Thông tin metadata của mô hình thực chiến đã huấn luyện"
    )


class LiveSyncRequest(BaseModel):
    symbol: str = Field(default="VIC", description="Mã cổ phiếu cần đồng bộ và dự báo")
    model_type: str = Field(default="lightgbm", description="Loại mô hình ('lightgbm' hoặc 'lstm')")


class BatchPredictionResponse(BaseModel):
    model_type: str = Field(..., description="Loại mô hình sử dụng")
    total_symbols: int = Field(..., description="Tổng số mã đã phân tích")
    predictions: list[PredictionResponse] = Field(..., description="Danh sách kết quả dự báo")


# ============================================================================
# 4. BACKTESTING SCHEMAS
# ============================================================================
class BacktestRequest(BaseModel):
    symbol: str = Field(default="VIC", description="Mã cổ phiếu cần kiểm thử")
    model_type: str = Field(
        default="lightgbm", description="Loại mô hình AI ('lightgbm' hoặc 'lstm')"
    )
    initial_capital: float = Field(default=100_000_000.0, description="Vốn đầu tư ban đầu (VNĐ)")
    slippage_rate: float = Field(default=0.0005, description="Tỷ lệ trượt giá khớp lệnh (0.05%)")
    fee_rate: float = Field(default=0.0015, description="Phí môi giới mỗi chiều (0.15%)")
    tax_rate: float = Field(default=0.0010, description="Thuế chuyển nhượng khi bán (0.10%)")
    lot_size: int = Field(default=100, description="Quy cách lô chẵn (100 cổ phiếu)")
    settlement_delay: int = Field(default=2, description="Chu kỳ thanh toán (T+2)")
    execution_price: str = Field(default="open", description="Giá khớp lệnh ('open' hoặc 'close')")
    buy_prob_threshold: float = Field(
        default=0.40, description="Ngưỡng xác suất kích hoạt lệnh Mua"
    )
    sell_prob_threshold: float = Field(
        default=0.40, description="Ngưỡng xác suất kích hoạt lệnh Bán"
    )
    take_profit_pct: float | None = Field(
        default=None, description="Tỷ lệ chốt lời Take Profit (ví dụ: 0.10 cho 10%)"
    )
    stop_loss_pct: float | None = Field(
        default=None, description="Tỷ lệ cắt lỗ Stop Loss (ví dụ: 0.07 cho 7%)"
    )
    trailing_stop_pct: float | None = Field(
        default=None, description="Tỷ lệ Trailing Stop bảo toàn lãi từ đỉnh (ví dụ: 0.05 cho 5%)"
    )
    preset_id: str | None = Field(
        default=None, description="Mã định danh chiến thuật mẫu nếu áp dụng từ preset"
    )


class BacktestMetricsSchema(BaseModel):
    initial_capital: float = Field(..., description="Vốn ban đầu (VNĐ)")
    final_equity: float = Field(..., description="Tài sản ròng kết thúc (VNĐ)")
    total_return_pct: float = Field(..., description="Tỷ suất sinh lời tổng thể (ROI %)")
    cagr_pct: float = Field(..., description="Tỷ suất sinh lời kép năm hóa (CAGR %)")
    buy_and_hold_return_pct: float = Field(..., description="Lợi nhuận chiến lược Buy & Hold (%)")
    excess_return_pct: float = Field(..., description="Lợi nhuận vượt trội Alpha (%)")
    annualized_volatility_pct: float = Field(..., description="Độ biến động năm hóa (%)")
    sharpe_ratio: float = Field(..., description="Tỷ số Sharpe năm hóa (Rf=4%)")
    sortino_ratio: float = Field(..., description="Tỷ số Sortino năm hóa")
    max_drawdown_pct: float = Field(..., description="Mức sụt giảm vốn lớn nhất từ đỉnh (MDD %)")
    calmar_ratio: float = Field(..., description="Tỷ số Calmar (CAGR / MDD)")
    var_95_pct: float = Field(..., description="Giá trị chịu rủi ro VaR 95% 1 ngày (%)")
    cvar_95_pct: float = Field(..., description="Kỳ vọng tổn thất vượt mức CVaR 95% (%)")
    win_rate_pct: float = Field(..., description="Tỷ lệ lệnh có lãi Win Rate (%)")
    profit_factor: float = Field(..., description="Hệ số lợi nhuận Profit Factor")
    total_trades: int = Field(..., description="Tổng số vòng giao dịch đã đóng")
    winning_trades: int = Field(..., description="Số vòng giao dịch có lãi")
    losing_trades: int = Field(..., description="Số vòng giao dịch hòa/lỗ")
    avg_trade_return_pct: float = Field(..., description="Lợi nhuận bình quân mỗi lệnh (%)")
    avg_holding_days: float = Field(..., description="Thời gian nắm giữ bình quân (phiên)")
    total_fees_paid: float = Field(..., description="Tổng phí môi giới đã trả (VNĐ)")
    total_taxes_paid: float = Field(..., description="Tổng thuế chuyển nhượng đã nộp (VNĐ)")
    total_costs: float = Field(..., description="Tổng chi phí thuế phí (VNĐ)")
    cost_impact_pct: float = Field(..., description="Tác động chi phí trên vốn ban đầu (%)")


class EquityCurvePoint(BaseModel):
    date: str = Field(..., description="Ngày giao dịch (YYYY-MM-DD)")
    total_equity: float = Field(..., description="Giá trị tài sản ròng chiến lược AI (VNĐ)")
    benchmark_equity: float = Field(..., description="Giá trị tài sản chiến lược Buy & Hold (VNĐ)")
    drawdown_pct: float = Field(..., description="Mức sụt giảm từ đỉnh tại ngày t (%)")
    daily_return: float = Field(..., description="Lợi suất vốn ngày t (%)")


class TradeLogItem(BaseModel):
    trade_id: int = Field(..., description="Mã định danh lệnh")
    order_type: str = Field(..., description="Loại lệnh ('BUY' hoặc 'SELL')")
    exec_date: str = Field(..., description="Ngày thực thi lệnh trên sàn")
    exec_price: float = Field(..., description="Giá khớp lệnh thực tế (nghìn VNĐ)")
    shares: int = Field(..., description="Số lượng cổ phiếu (lô 100)")
    fee: float = Field(..., description="Phí môi giới (VNĐ)")
    tax: float = Field(..., description="Thuế chuyển nhượng (VNĐ)")
    net_cash_flow: float = Field(..., description="Dòng tiền ròng thực nhận/chi (VNĐ)")
    realized_pnl: float | None = Field(default=None, description="Lợi nhuận thực hiện (VNĐ)")
    realized_return_pct: float | None = Field(
        default=None, description="Tỷ suất sinh lời thực hiện (%)"
    )
    holding_days: float | None = Field(default=None, description="Số ngày nắm giữ")
    reason: str = Field(
        ..., description="Lý do sinh lệnh ('SIGNAL_BUY', 'SIGNAL_SELL', 'FINAL_LIQUIDATION')"
    )


class BacktestResponse(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu kiểm thử")
    strategy_name: str = Field(..., description="Tên chiến lược")
    config: dict[str, Any] = Field(..., description="Cấu hình tham số kiểm thử")
    metrics: BacktestMetricsSchema = Field(..., description="Bộ chỉ số hiệu quả định lượng")
    equity_curve: list[EquityCurvePoint] = Field(
        ..., description="Đường cong tăng trưởng vốn theo từng ngày"
    )
    trades: list[TradeLogItem] = Field(..., description="Nhật ký chi tiết các lệnh giao dịch")


class BacktestSummaryItem(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu")
    model: str = Field(..., description="Mô hình AI")
    roi_pct: float = Field(..., description="ROI (%)")
    bh_roi_pct: float = Field(..., description="Buy & Hold ROI (%)")
    excess_pct: float = Field(..., description="Alpha (%)")
    sharpe: float = Field(..., description="Tỷ số Sharpe")
    sortino: float = Field(..., description="Tỷ số Sortino")
    mdd_pct: float = Field(..., description="Max Drawdown (%)")
    win_rate_pct: float = Field(..., description="Tỷ lệ thắng (%)")
    profit_factor: float = Field(..., description="Profit Factor")
    trades: int = Field(..., description="Tổng số lệnh đóng")
    costs: float = Field(..., description="Tổng chi phí (VNĐ)")


class BacktestSummaryResponse(BaseModel):
    model_type: str = Field(..., description="Loại mô hình AI")
    summary: list[BacktestSummaryItem] = Field(..., description="Bảng tổng hợp đối chứng các mã")


class StrategyPresetItem(BaseModel):
    id: str = Field(..., description="Mã định danh chiến thuật mẫu")
    name: str = Field(..., description="Tên chiến thuật mẫu")
    category: str = Field(..., description="Trường phái đầu tư")
    description: str = Field(..., description="Mô tả chiến thuật")
    target_symbols: list[str] = Field(..., description="Danh sách cổ phiếu khuyến nghị")
    default_symbol: str = Field(..., description="Mã cổ phiếu mặc định")
    conditions_summary: str = Field(..., description="Tóm tắt bộ điều kiện")
    win_rate_pct: float = Field(..., description="Tỷ lệ thắng mẫu (%)")
    cumulative_pnl_pct: float = Field(..., description="Lãi/lỗ lũy kế mẫu (%)")
    risk_reward_ratio: str = Field(..., description="Tỷ lệ Rủi ro / Lợi nhuận")
    copy_count: int = Field(..., description="Số lượt sao chép")
    take_profit_pct: float = Field(..., description="Mức chốt lời mặc định")
    stop_loss_pct: float = Field(..., description="Mức cắt lỗ mặc định")
    trailing_stop_pct: float = Field(..., description="Mức trailing stop mặc định")
    model_type: str = Field(..., description="Mô hình AI mặc định")
    timeframe: str = Field(default="1 ngày (Daily)", description="Khung thời gian nến")


class StrategyPresetsResponse(BaseModel):
    presets: list[StrategyPresetItem] = Field(..., description="Danh sách 8 chiến thuật mẫu chuẩn DNSE")


class RecentSignalItem(BaseModel):
    signal_id: str = Field(..., description="Mã tín hiệu")
    symbol: str = Field(..., description="Mã cổ phiếu")
    action: str = Field(..., description="Hành động ('BUY', 'SELL', 'HOLD')")
    strategy_name: str = Field(..., description="Tên chiến thuật phát sinh")
    price: float = Field(..., description="Mức giá khuyến nghị (VNĐ)")
    target_price: float = Field(..., description="Giá mục tiêu (VNĐ)")
    stop_price: float = Field(..., description="Giá cắt lỗ (VNĐ)")
    confidence: float = Field(..., description="Độ tin cậy của AI (%)")
    timestamp: str = Field(..., description="Thời điểm phát sinh")
    status: str = Field(..., description="Trạng thái tín hiệu ('MỚI', 'CHỐT LÃI', 'ĐÃ KHỚP T+1')")


class RecentSignalsResponse(BaseModel):
    signals: list[RecentSignalItem] = Field(..., description="Danh sách tín hiệu thời gian thực")


# ============================================================================
# 5. ADVANCED MULTI-SYMBOL & PORTFOLIO BACKTESTING SCHEMAS (DNSE BENCHMARK)
# ============================================================================
class BacktestScopeType(str, Enum):
    STOCK = "stock"          # Cổ phiếu đơn lẻ
    INDEX = "index"          # Rổ chỉ số (VN30, VN100, VNINDEX)
    SECTOR = "sector"        # Ngành nghề
    PORTFOLIO = "portfolio"  # Danh mục tùy chọn nhiều mã


class BacktestConditionFilter(BaseModel):
    market_condition: str | None = Field(default="all", description="Điều kiện VN-Index ('all', 'uptrend', 'sideways', 'downtrend')")
    use_ma: bool = Field(default=False, description="Điều kiện MA (Close > SMA20)")
    ma_type: str = Field(default="SMA20", description="Loại đường MA")
    use_ema: bool = Field(default=False, description="Điều kiện EMA (EMA12 > EMA26)")
    use_macd: bool = Field(default=False, description="Điều kiện MACD (MACD > Signal)")
    use_rsi: bool = Field(default=False, description="Điều kiện RSI")
    rsi_threshold: float = Field(default=45.0, description="Ngưỡng RSI mua (<=)")
    rsi_sell_threshold: float = Field(default=70.0, description="Ngưỡng RSI bán (>=)")
    use_bb: bool = Field(default=False, description="Điều kiện chạm dải dưới Bollinger Bands")
    use_volume_spike: bool = Field(default=False, description="Khối lượng đột biến > 1.2x SMA20 Volume")
    use_price_increase: bool = Field(default=False, description="Giá T0 > T-1")
    max_pe: float | None = Field(default=None, description="P/E tối đa")
    max_pb: float | None = Field(default=None, description="P/B tối đa")
    min_roe: float | None = Field(default=None, description="ROE tối thiểu (%)")
    foreign_net_buy: bool = Field(default=False, description="Khối ngoại mua ròng")
    foreign_net_sell: bool = Field(default=False, description="Khối ngoại bán ròng")
    prop_net_buy: bool = Field(default=False, description="Tự doanh mua ròng")
    take_profit_pct: float | None = Field(default=None, description="Chốt lời (%)")
    stop_loss_pct: float | None = Field(default=None, description="Cắt lỗ (%)")
    trailing_stop_pct: float | None = Field(default=None, description="Trailing Stop (%)")


class AdvancedBacktestRequest(BaseModel):
    scope_type: BacktestScopeType = Field(default=BacktestScopeType.STOCK, description="Phạm vi kiểm thử")
    symbol: str = Field(default="VIC", description="Mã cổ phiếu đơn lẻ nếu scope_type == 'stock'")
    index_name: str | None = Field(default="VN30", description="Tên rổ chỉ số nếu scope_type == 'index'")
    sector_name: str | None = Field(default=None, description="Tên nhóm ngành nếu scope_type == 'sector'")
    portfolio_symbols: list[str] | None = Field(default=None, description="Danh sách mã cổ phiếu nếu scope_type == 'portfolio'")
    start_date: str = Field(..., description="Ngày bắt đầu (YYYY-MM-DD)")
    end_date: str = Field(..., description="Ngày kết thúc (YYYY-MM-DD, cách start_date không quá 365 ngày)")
    initial_capital: float = Field(default=100_000_000.0, description="Vốn khởi điểm danh mục (VNĐ)")
    model_type: str = Field(default="lightgbm", description="Mô hình AI ('lightgbm' hoặc 'lstm')")
    slippage_rate: float = Field(default=0.0005, description="Tỷ lệ trượt giá (0.05%)")
    buy_conditions: BacktestConditionFilter = Field(default_factory=BacktestConditionFilter, description="Bộ điều kiện Mua")
    sell_conditions: BacktestConditionFilter = Field(default_factory=BacktestConditionFilter, description="Bộ điều kiện Bán")


class SymbolBreakdownItem(BaseModel):
    symbol: str = Field(..., description="Mã cổ phiếu")
    name: str = Field(..., description="Tên công ty")
    sector: str = Field(..., description="Nhóm ngành")
    roi_pct: float = Field(..., description="Tỷ suất sinh lời ROI (%)")
    bh_roi_pct: float = Field(..., description="Buy & Hold ROI (%)")
    excess_pct: float = Field(..., description="Alpha vượt trội (%)")
    sharpe: float = Field(..., description="Tỷ số Sharpe")
    sortino: float = Field(..., description="Tỷ số Sortino")
    mdd_pct: float = Field(..., description="Mức sụt giảm tối đa MDD (%)")
    win_rate_pct: float = Field(..., description="Tỷ lệ thắng (%)")
    profit_factor: float = Field(..., description="Profit Factor")
    trades: int = Field(..., description="Tổng số lệnh")
    costs: float = Field(..., description="Tổng chi phí giao dịch (VNĐ)")


class PortfolioBacktestResponse(BaseModel):
    scope_type: str = Field(..., description="Phạm vi đã kiểm thử ('stock', 'index', 'sector', 'portfolio')")
    scope_target: str = Field(..., description="Mục tiêu kiểm thử (tên mã, tên rổ, tên ngành)")
    start_date: str = Field(..., description="Ngày bắt đầu")
    end_date: str = Field(..., description="Ngày kết thúc")
    symbols_count: int = Field(..., description="Số lượng mã trong danh mục kiểm thử")
    aggregate_metrics: BacktestMetricsSchema = Field(..., description="Chỉ số hiệu quả tổng hợp toàn danh mục")
    portfolio_equity_curve: list[EquityCurvePoint] = Field(..., description="Đường cong tài sản danh mục")
    symbols_breakdown: list[SymbolBreakdownItem] = Field(..., description="Bảng phân tích chi tiết từng mã thành phần")
    individual_results: dict[str, Any] = Field(default_factory=dict, description="Kết quả chi tiết từng mã (trades, equity) phục vụ đào sâu (drill-down)")

