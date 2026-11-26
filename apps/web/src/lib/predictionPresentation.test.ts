import { describe, it, expect } from "vitest";
import {
  formatIsoDateTimeVi,
  formatPercentVi,
  formatPriceVnd,
  matchesPrediction,
} from "./predictionPresentation";
import type { PredictionResponse } from "./types";

const prediction = { symbol: "VIC", date: "2026-11-13", current_price: 50, predicted_label: 2, class_name: "TĂNG", signal: "MUA", horizon: "T+3", horizon_days: 3, is_live_synced: false, market_session_label: "Đóng cửa", trajectory: [], summary_guidance: "", model_type: "lightgbm", probabilities: { "TĂNG": .5, "ĐI NGANG": .3, "GIẢM": .2 } } as PredictionResponse;
describe("Prediction presentation boundaries", () => {
  it("accepts the matching symbol and model", () => expect(matchesPrediction(prediction, "VIC", "lightgbm")).toBe(true));
  it("rejects another symbol", () => expect(matchesPrediction(prediction, "HPG", "lightgbm")).toBe(false));
  it("rejects an old model response", () => expect(matchesPrediction(prediction, "VIC", "lstm")).toBe(false));
  it("does not invent a prediction", () => expect(matchesPrediction(null, "VIC", "lstm")).toBe(false));
  it("rejects invalid probability distributions", () => {
    for (const value of [NaN, Infinity, -1, 2, .1]) {
      expect(matchesPrediction({ ...prediction, probabilities: { ...prediction.probabilities, "TĂNG": value } }, "VIC", "lightgbm")).toBe(false);
    }
  });
  it("converts thousands of dong to dong", () => expect(formatPriceVnd(50)).toBe("50.000 VNĐ"));
  it("formats percentages in vi-VN decimal comma style", () => {
    expect(formatPercentVi(1.54, 2)).toBe("1,54%");
    expect(formatPercentVi(50, 1)).toBe("50,0%");
  });
  it("formats timestamps consistently using YYYY-MM-DD in Asia/Ho_Chi_Minh", () => {
    expect(formatIsoDateTimeVi("2026-11-22T01:00:00Z")).toBe("08:00 2026-11-22");
    expect(formatIsoDateTimeVi("2026-11-22T01:05:09Z", true)).toBe("08:05:09 2026-11-22");
  });
});
