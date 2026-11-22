import type { PredictionResponse } from "./types";

export function predictionLoadErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "status" in error && error.status === 503
      && "detail" in error && typeof error.detail === "string"
      && error.detail.trim().length > 0 && error.detail.length <= 300) return error.detail;
  return "Không thể tải dự báo. Hãy thử lại sau.";
}

export function matchesPrediction(prediction: PredictionResponse | null, symbol: string, model: string): boolean {
  if (!prediction || prediction.symbol !== symbol || typeof prediction.model_type !== "string"
      || prediction.model_type.toLowerCase() !== model.toLowerCase()
      || !prediction.probabilities || !Number.isFinite(prediction.current_price) || prediction.current_price <= 0) return false;
  const classes = ["GIẢM", "ĐI NGANG", "TĂNG"];
  const probabilities = classes.map(key => prediction.probabilities[key]);
  return probabilities.every(value => Number.isFinite(value) && value >= 0 && value <= 1)
    && Math.abs(probabilities.reduce((sum, value) => sum + value, 0) - 1) < 0.01
    && classes[prediction.predicted_label] === prediction.class_name
    && probabilities[prediction.predicted_label] >= Math.max(...probabilities) - 0.0001;
}

export function formatPriceVnd(priceInThousands: number): string {
  return Number.isFinite(priceInThousands) ? `${(priceInThousands * 1000).toLocaleString("vi-VN")} VNĐ` : "—";
}
