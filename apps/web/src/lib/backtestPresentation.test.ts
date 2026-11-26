import { expect, it } from "vitest";
import {
  formatBacktestMetric,
  formatRewardRiskRatio,
  formatSignedPercent,
} from "./backtestPresentation";

it("distinguishes a measured zero from an undefined metric", () => {
  expect(formatBacktestMetric(0)).toBe("0.00");
  expect(formatBacktestMetric(0, 1, "%")).toBe("0.0%");
  for (const missing of [null, undefined, NaN, Infinity]) {
    expect(formatBacktestMetric(missing, 1, "%")).toBe("—");
  }
});

it("formats reward-risk ratio and signed percentages consistently", () => {
  expect(formatRewardRiskRatio(2.5)).toBe("2.50 : 1");
  expect(formatRewardRiskRatio("1.8")).toBe("1.80 : 1");
  expect(formatRewardRiskRatio(0)).toBe("0.00 : 1");
  for (const missing of [null, undefined, "", NaN, Infinity]) {
    expect(formatRewardRiskRatio(missing)).toBe("—");
  }

  expect(formatSignedPercent(12.345)).toBe("+12.35%");
  expect(formatSignedPercent(-5.4)).toBe("-5.40%");
  expect(formatSignedPercent(0)).toBe("0.00%");
  for (const missing of [null, undefined, NaN, Infinity]) {
    expect(formatSignedPercent(missing)).toBe("—");
  }
});
