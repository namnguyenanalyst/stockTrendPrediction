/** Undefined ratios remain visibly unavailable; a measured zero still renders as zero. */
export function formatBacktestMetric(value: number | null | undefined, digits = 2, suffix = ""): string {
  return value != null && Number.isFinite(value) ? `${value.toFixed(digits)}${suffix}` : "—";
}

/** Format Reward/Risk ratio as `X.XX : 1`, or `—` when undefined. */
export function formatRewardRiskRatio(value: number | string | null | undefined): string {
  const num =
    typeof value === "number"
      ? value
      : typeof value === "string" && value.trim() !== ""
        ? Number(value)
        : NaN;
  return Number.isFinite(num) ? `${num.toFixed(2)} : 1` : "—";
}

/** Format signed percentage (`+X.XX%`, `-X.XX%`, `0.00%`), or `—` when undefined. */
export function formatSignedPercent(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return "—";
  if (value === 0) return `${(0).toFixed(digits)}%`;
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(digits)}%`;
}
