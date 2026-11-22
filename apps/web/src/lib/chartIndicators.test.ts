import { describe, it, expect } from "vitest";
import {
  searchIndicators,
  parseSelection,
  DEFAULT_INDICATORS,
  CHART_INDICATORS,
} from "./chartIndicators";
describe("detail indicators", () => {
  it("searches names, accents and periods", () => {
    expect(searchIndicators("khoi luong").length).toBe(4);
    expect(searchIndicators("MA 20").map((d) => d.id)).toContain("SMA20");
    expect(searchIndicators("ema 26").map((d) => d.id)).toEqual(["EMA26"]);
    expect(searchIndicators("not-found")).toEqual([]);
  });
  it("restores valid unique selections including empty", () => {
    expect(parseSelection("[]")).toEqual([]);
    expect(parseSelection('["RSI","RSI","bad"]')).toEqual(["RSI"]);
    expect(parseSelection("{bad")).toEqual(DEFAULT_INDICATORS);
  });
  it("only registers supported definitions", () => {
    expect(new Set(CHART_INDICATORS.map((d) => d.id)).size).toBe(
      CHART_INDICATORS.length,
    );
    expect(CHART_INDICATORS.some((d) => d.id === "ATR")).toBe(false);
  });
});
