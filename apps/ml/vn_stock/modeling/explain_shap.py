"""Module giải thích mô hình Trí tuệ Nhân tạo (Explainable AI - XAI) sử dụng SHAP Values.

Ứng dụng lý thuyết trò chơi hợp tác (Cooperative Game Theory) để lượng hóa mức độ đóng góp
của từng đặc trưng kỹ thuật vào quyết định dự báo xu hướng giá cổ phiếu của mô hình LightGBM.
Xuất biểu đồ phục vụ Báo cáo Đồ án Tốt nghiệp (Chương 4).
"""

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import shap

from vn_stock.config import MODELS_DIR
from vn_stock.data_ingestion import load_panel_dataset
from vn_stock.features import (
    ALL_FEATURE_COLS,
    compute_features_per_symbol,
    transform_model_features,
)
from vn_stock.modeling.predict import load_prediction_snapshot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def prepare_shap_sample(df_features, scaler, sample_size=500):
    """Explain exactly the scaled feature space presented to the trained model."""
    if sample_size < 1 or df_features.empty:
        raise ValueError("SHAP requires a positive sample size and nonempty features.")
    scaled = transform_model_features(df_features, scaler)
    return scaled[ALL_FEATURE_COLS].sample(n=min(sample_size, len(scaled)), random_state=42)


def generate_shap_analysis(
    sample_size: int = 500,
    output_dir: Path = Path("reports/figures"),
    models_dir: Path = MODELS_DIR,
) -> None:
    """Tính toán SHAP values và xuất các biểu đồ trực quan hóa giải thích mô hình."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Nạp mô hình LightGBM đã huấn luyện
    model, scaler, training_info = load_prediction_snapshot("lightgbm", models_dir)

    # 2. Chuẩn bị tập dữ liệu đánh giá
    logger.info("Nạp dữ liệu panel và trích xuất đặc trưng...")
    df = load_panel_dataset()
    df_feat = compute_features_per_symbol(df)
    X_sample = prepare_shap_sample(df_feat, scaler, sample_size)
    logger.info("Đang tính toán SHAP values trên %d mẫu...", len(X_sample))

    # 3. Khởi tạo TreeExplainer
    explainer = shap.TreeExplainer(model, model_output="raw")
    explanation = explainer(X_sample)
    booster = getattr(model, "booster_", model)
    np.testing.assert_allclose(
        explanation.base_values + explanation.values.sum(axis=1),
        booster.predict(X_sample, raw_score=True), rtol=1e-5, atol=1e-6,
    )
    provenance = {"model_output": "raw", "class_index": 2,
                  "sample_size": len(X_sample), "training_info": training_info,
                  "mean_absolute_shap": dict(zip(ALL_FEATURE_COLS,
                      np.abs(explanation.values[:, :, 2]).mean(axis=0).tolist()))}
    (output_dir / "shap_analysis.json").write_text(json.dumps(provenance, indent=2))

    # 4. Xuất Biểu đồ 1: Bar Plot mức độ quan trọng (|SHAP|) đối với xu hướng TĂNG (Class 2)
    logger.info("Tạo Biểu đồ 1: SHAP Feature Importance Bar Plot (Class Tăng)...")
    plt.figure(figsize=(10, 6))
    shap.plots.bar(explanation[:, :, 2], max_display=14, show=False)
    plt.title("Độ Quan Trọng Trung Bình Của Các Chỉ Báo Theo SHAP (Dự Báo Tăng Giá)", fontsize=12, fontweight="bold", pad=20)
    bar_path = output_dir / "shap_feature_importance_bar.png"
    plt.savefig(bar_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Đã lưu: %s", bar_path)

    # 5. Xuất Biểu đồ 2: Beeswarm Plot cho Lớp Tăng (Class 2: TĂNG GIÁ)
    logger.info("Tạo Biểu đồ 2: SHAP Beeswarm Plot (Dự báo xu hướng TĂNG)...")
    plt.figure(figsize=(11, 7))
    shap.plots.beeswarm(explanation[:, :, 2], max_display=14, show=False)
    plt.title("Phân Bố SHAP Theo Raw Score Lớp TĂNG", fontsize=12, fontweight="bold", pad=20)
    plt.xlabel("Giá trị SHAP (đóng góp vào raw score lớp Tăng)", fontsize=11)
    beeswarm_path = output_dir / "shap_beeswarm_up_trend.png"
    plt.savefig(beeswarm_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Đã lưu: %s", beeswarm_path)

    # 6. Xuất Biểu đồ 3: Waterfall Plot giải thích cho 1 phiên dự đoán cụ thể (Local Explanation)
    logger.info("Tạo Biểu đồ 3: SHAP Waterfall Plot (Giải thích 1 phiên cụ thể)...")
    plt.figure(figsize=(10, 6))
    sample_idx = 0
    shap.plots.waterfall(explanation[sample_idx, :, 2], max_display=10, show=False)
    plt.title(f"Minh Họa Giải Thích Quyết Định Dự Báo Tăng Cho Phiên Mẫu #{sample_idx} (Waterfall)", fontsize=11, fontweight="bold", pad=20)
    waterfall_path = output_dir / "shap_waterfall_example.png"
    plt.savefig(waterfall_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Đã lưu: %s", waterfall_path)

    print("\n" + "=" * 70)
    print("✅ HOÀN TẤT PHÂN TÍCH SHAP VALUES & XUẤT 3 BIỂU ĐỒ KHOA HỌC:")
    print(f"1. Biểu đồ tổng quan |SHAP|: {bar_path}")
    print(f"2. Biểu đồ Beeswarm xu hướng Tăng: {beeswarm_path}")
    print(f"3. Biểu đồ Waterfall phiên cụ thể: {waterfall_path}")
    print("=" * 70)


if __name__ == "__main__":
    generate_shap_analysis()
