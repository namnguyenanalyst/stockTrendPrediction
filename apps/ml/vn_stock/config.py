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

MODELS_DIR = PROJ_ROOT / "models"
REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
NOTEBOOKS_DIR = PROJ_ROOT / "notebooks"

# Cấu hình mặc định cho dữ liệu & mô hình
DEFAULT_SYMBOL = "VIC"
DEFAULT_START_DATE = "2020-01-01"
DEFAULT_SEQ_LENGTH = 30

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
