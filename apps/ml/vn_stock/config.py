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

# Cấu hình mặc định cho dữ liệu & mô hình (chuẩn PoC v2.1)
DEFAULT_SYMBOL = "VIC"
DEFAULT_SYMBOLS = ["VIC", "HPG", "FPT", "VNM", "MWG"]
DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "2026-09-11"
DEFAULT_SEQ_LENGTH = 20

# Bảng mã hóa cố định định danh cổ phiếu (Symbol -> Code) đảm bảo tính nhất quán tuyệt đối giữa Train và Inference
VN30_SYMBOLS = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"
]
SYMBOL_TO_CODE = {sym: idx for idx, sym in enumerate(VN30_SYMBOLS)}

# Siêu tham số PyTorch LSTM
DEFAULT_INPUT_SIZE = 1
DEFAULT_HIDDEN_SIZE = 32
DEFAULT_NUM_LAYERS = 2
DEFAULT_OUTPUT_SIZE = 1
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32

# Giả định chi phí giao dịch thị trường chứng khoán Việt Nam
TRANSACTION_FEE_RATE = 0.0015  # 0.15% phí giao dịch
TAX_RATE = 0.0010              # 0.10% thuế bán chứng khoán
INITIAL_CAPITAL = 100_000_000  # 100 triệu VNĐ
LOT_SIZE = 100                 # Lô chẵn 100 cổ phiếu
