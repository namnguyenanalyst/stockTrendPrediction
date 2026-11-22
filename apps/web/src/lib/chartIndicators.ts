export interface ChartIndicatorBar {
  date: string;
  values: Record<string, number | null>;
}
export interface ChartIndicatorsResponse {
  symbol: string;
  total_bars: number;
  indicators: ChartIndicatorBar[];
}
export interface IndicatorDefinition {
  id: string;
  name: string;
  description: string;
  color: string;
  pane: "price" | "volume" | "rsi" | "macd" | "adx";
  columns: string[];
  keywords: string;
}
const colors = [
  "#fbbf24",
  "#fb923c",
  "#34d399",
  "#c084fc",
  "#38bdf8",
  "#f472b6",
  "#a3e635",
  "#22d3ee",
];
export const CHART_INDICATORS: IndicatorDefinition[] = [
  ...[5, 10, 20, 50, 100, 200].map((p, i) => ({
    id: `SMA${p}`,
    name: `SMA (${p})`,
    description: `Trung bình động ${p} phiên`,
    color: colors[i],
    pane: "price" as const,
    columns: [`SMA${p}`],
    keywords: `MA ${p} SMA ${p} trung binh dong`,
  })),
  ...[5, 10, 12, 20, 26, 50, 100, 200].map((p, i) => ({
    id: `EMA${p}`,
    name: `EMA (${p})`,
    description: `Trung bình động hàm mũ ${p} phiên`,
    color: colors[i],
    pane: "price" as const,
    columns: [`EMA${p}`],
    keywords: `EMA ${p} ham mu`,
  })),
  {
    id: "BB",
    name: "Bollinger Bands (20, 2)",
    description: "Đường giữa và hai biên",
    color: "#22d3ee",
    pane: "price",
    columns: ["BB_Upper", "SMA20", "BB_Lower"],
    keywords: "BB bollinger dai bien",
  },
  {
    id: "Volume",
    name: "Volume",
    description: "Khối lượng giao dịch",
    color: "#94a3b8",
    pane: "volume",
    columns: [],
    keywords: "khoi luong",
  },
  ...[5, 10, 20].map((p, i) => ({
    id: `Vol_SMA${p}`,
    name: `MA khối lượng (${p})`,
    description: `Khối lượng trung bình ${p} phiên`,
    color: colors[i],
    pane: "volume" as const,
    columns: [`Vol_SMA${p}`],
    keywords: `volume MA ${p} khoi luong`,
  })),
  {
    id: "RSI",
    name: "RSI (14)",
    description: "Sức mạnh tương đối",
    color: "#a5b4fc",
    pane: "rsi",
    columns: ["RSI"],
    keywords: "suc manh tuong doi",
  },
  {
    id: "MACD",
    name: "MACD (12, 26, 9)",
    description: "MACD và đường tín hiệu",
    color: "#38bdf8",
    pane: "macd",
    columns: ["MACD", "MACD_Signal"],
    keywords: "tin hieu",
  },
  {
    id: "ADX",
    name: "ADX (14)",
    description: "Sức mạnh xu hướng",
    color: "#fbbf24",
    pane: "adx",
    columns: ["ADX"],
    keywords: "suc manh xu huong",
  },
];
export const DEFAULT_INDICATORS = ["SMA20", "SMA50", "Volume", "RSI"];
export const INDICATOR_STORAGE_KEY = "stockpulse.detail-indicators.v1";
export function normalizeSearch(s: string) {
  return s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .replace(/[()]/g, "");
}
export function searchIndicators(query: string) {
  const tokens = normalizeSearch(query).split(/\s+/).filter(Boolean);
  return CHART_INDICATORS.filter((d) =>
    tokens.every((t) =>
      normalizeSearch(
        `${d.id} ${d.name} ${d.description} ${d.keywords}`,
      ).includes(t),
    ),
  );
}
export function parseSelection(raw: string | null): string[] {
  try {
    const v = JSON.parse(raw ?? "null");
    if (!Array.isArray(v)) return [...DEFAULT_INDICATORS];
    return [
      ...new Set(
        v.filter(
          (id): id is string =>
            typeof id === "string" && CHART_INDICATORS.some((d) => d.id === id),
        ),
      ),
    ];
  } catch {
    return [...DEFAULT_INDICATORS];
  }
}
