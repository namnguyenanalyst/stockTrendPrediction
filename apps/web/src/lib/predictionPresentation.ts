import type { PredictionResponse } from "./types";

export function matchesPrediction(prediction: PredictionResponse | null, symbol: string, model: string): boolean {
  if (!prediction || prediction.symbol !== symbol || prediction.model_type.toLowerCase() !== model.toLowerCase()) return false;
  const probabilities = ["TĂNG", "ĐI NGANG", "GIẢM"].map(key => prediction.probabilities[key]);
  return probabilities.every(value => Number.isFinite(value) && value >= 0 && value <= 1)
    && Math.abs(probabilities.reduce((sum, value) => sum + value, 0) - 1) < 0.01;
}

export function formatPriceVnd(priceInThousands: number): string {
  return Number.isFinite(priceInThousands) ? `${(priceInThousands * 1000).toLocaleString("vi-VN")} VNĐ` : "—";
}
