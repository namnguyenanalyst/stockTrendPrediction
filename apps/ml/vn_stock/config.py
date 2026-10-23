from pathlib import Path

# Đường dẫn thư mục chuẩn CCDS v2
PACKAGE_DIR = Path(__file__).resolve().parent
PROJ_ROOT = PACKAGE_DIR.parent
MONOREPO_ROOT = PROJ_ROOT.parent.parent

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
PANEL_DATA_DIR = INTERIM_DATA_DIR / "panel"

MODELS_DIR = PROJ_ROOT / "models"
REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
NOTEBOOKS_DIR = PROJ_ROOT / "notebooks"

# Cấu hình mốc thời gian thu thập và nghiên cứu
# FETCH_START_DATE: Ngày bắt đầu tải dữ liệu lịch sử từ SSI API (cung cấp ~250 phiên năm 2022 làm vùng đệm rolling 200 ngày)
FETCH_START_DATE = "2022-01-01"

# STUDY_START_DATE: Ngày bắt đầu chính thức của cửa sổ nghiên cứu (cắt lại sau feature computation)
# MWG 2022-06-16 SSI chưa điều chỉnh lùi sự kiện chia cổ phiếu 1:1 (hệ số 0,5), làm nhiễu SMA_200_Dev và CV_200 của MWG trong 58 phiên đầu; tính cửa sổ 200 phiên thì phiên sạch đầu tiên là 2023-04-03.
STUDY_START_DATE = "2023-04-03"

# Cấu hình mặc định cho dữ liệu & mô hình (chuẩn PoC v2.1)
DEFAULT_SYMBOL = "VIC"
DEFAULT_SYMBOLS = ["VIC", "HPG", "FPT", "VNM", "MWG"]
DEFAULT_START_DATE = FETCH_START_DATE

def get_default_end_date() -> str:
    """Tự động lấy ngày phiên chốt hợp lệ gần nhất (T sau 15:00, hoặc T-1 trước 15:00)."""
    try:
        from vn_stock.market_session import get_target_market_date

        return get_target_market_date()
    except Exception:
        return "2026-10-22"

DEFAULT_END_DATE = get_default_end_date()
DEFAULT_SEQ_LENGTH = 20

# Danh mục các chỉ số thị trường hỗ trợ
SUPPORTED_INDICES = ["VNINDEX", "VN30", "HNX", "HNX30", "VN100", "UPCOM", "VN30F1M"]
SYMBOL_UNKNOWN_CODE = -1

# Bảng mã hóa cố định định danh cổ phiếu (Symbol -> Code) đảm bảo tính nhất quán tuyệt đối giữa Train và Inference
VN30_SYMBOLS = [
    "ACB",
    "BCM",
    "BID",
    "BVH",
    "CTG",
    "FPT",
    "GAS",
    "GVR",
    "HDB",
    "HPG",
    "MBB",
    "MSN",
    "MWG",
    "PLX",
    "POW",
    "SAB",
    "SHB",
    "SSB",
    "SSI",
    "STB",
    "TCB",
    "TPB",
    "VCB",
    "VHM",
    "VIB",
    "VIC",
    "VJC",
    "VNM",
    "VPB",
    "VRE",
]
SYMBOL_TO_CODE = {sym: idx for idx, sym in enumerate(VN30_SYMBOLS)}

# Siêu tham số PyTorch LSTM (Kế thừa tương thích ngược)
DEFAULT_INPUT_SIZE = 1
DEFAULT_HIDDEN_SIZE = 32
DEFAULT_NUM_LAYERS = 2
DEFAULT_OUTPUT_SIZE = 1
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32

# Cấu hình Phân loại Xu hướng 3 Lớp có ngưỡng (3-class Trend Classification)
DEFAULT_LABEL_THRESHOLD = (
    0.01  # Ngưỡng ±1.0% phân loại Tăng (>=+1%), Đi ngang ((-1%, +1%)), Giảm (<=-1%)
)
DEFAULT_HORIZON_DAYS = 3  # Chu kỳ T+3 bám sát thanh toán T+2 và ngày được phép bán
DEFAULT_TREND_THRESHOLD_3D = 0.02  # Ngưỡng ±2.0% cho chu kỳ 3 ngày
NUM_CLASSES = 3
CLASS_NAMES = {0: "GIẢM", 1: "ĐI NGANG", 2: "TĂNG"}
SIGNAL_RECOMMENDATIONS = {0: "BÁN (SELL)", 1: "NẮM GIỮ (HOLD)", 2: "MUA (BUY)"}
RANDOM_SEED = 42

# Siêu tham số PyTorch Global LSTM Classifier (Đa biến, chuỗi 3D)
DEFAULT_LSTM_INPUT_SIZE = 14  # 13 đặc trưng tương đối + 1 Symbol_Code (ALL_FEATURE_COLS)
DEFAULT_LSTM_HIDDEN_SIZE = 64
DEFAULT_LSTM_NUM_LAYERS = 2
DEFAULT_LSTM_DROPOUT = 0.2
DEFAULT_LSTM_EPOCHS = 40
DEFAULT_LSTM_BATCH_SIZE = 64
DEFAULT_LSTM_LR = 0.001
DEFAULT_LSTM_WEIGHT_DECAY = 1e-4

# Siêu tham số LightGBM Classifier (Dạng bảng đa mã)
DEFAULT_LGB_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.03,
    "max_depth": 5,
    "num_leaves": 20,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": RANDOM_SEED,
    "n_jobs": 1,
    "verbose": -1,
}
DEFAULT_EARLY_STOPPING_ROUNDS = 30

# Giả định chi phí giao dịch thị trường chứng khoán Việt Nam
TRANSACTION_FEE_RATE = 0.0015  # 0.15% phí giao dịch
TAX_RATE = 0.0010  # 0.10% thuế bán chứng khoán
INITIAL_CAPITAL = 100_000_000  # 100 triệu VNĐ
LOT_SIZE = 100  # Lô chẵn 100 cổ phiếu
