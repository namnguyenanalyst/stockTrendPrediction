"use client";
import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createChart,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import { X } from "lucide-react";
import {
  CHART_INDICATORS,
  type ChartIndicatorBar,
} from "@/lib/chartIndicators";
import type { StockBar } from "@/lib/types";

export function DetailIndicatorChart({
  bars,
  indicators,
  selected,
  onRemove,
}: {
  bars: StockBar[];
  indicators: ChartIndicatorBar[];
  selected: string[];
  onRemove: (id: string) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const candle = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const extra = useRef<ISeriesApi<"Line" | "Histogram">[]>([]);
  const panes = ["volume", "rsi", "macd", "adx"].filter((p) =>
    CHART_INDICATORS.some((d) => selected.includes(d.id) && d.pane === p),
  );
  useEffect(() => {
    if (!root.current) return;
    const c = createChart(root.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#020617" },
        textColor: "#94a3b8",
        panes: {
          separatorColor: "#334155",
          separatorHoverColor: "#475569",
          enableResize: true,
        },
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      rightPriceScale: { borderColor: "#334155", minimumWidth: 75 },
      timeScale: { borderColor: "#334155" },
    });
    chart.current = c;
    candle.current = c.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#f43f5e",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#f43f5e",
    });
    return () => {
      extra.current = [];
      candle.current = null;
      chart.current = null;
      c.remove();
    };
  }, []);
  useEffect(() => {
    if (!candle.current || !chart.current) return;
    candle.current.setData(
      bars.map((b) => ({
        time: b.date as Time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      })),
    );
    chart.current.timeScale().fitContent();
  }, [bars]);
  useEffect(() => {
    const c = chart.current;
    if (!c) return;
    const range = c.timeScale().getVisibleRange();
    for (const s of [...extra.current].reverse()) c.removeSeries(s);
    extra.current = [];
    const definitions = CHART_INDICATORS.filter((d) => selected.includes(d.id));
    const paneNames = ["volume", "rsi", "macd", "adx"].filter((p) =>
      definitions.some((d) => d.pane === p),
    );
    const byDate = new Map(indicators.map((row) => [row.date, row]));
    for (const d of definitions) {
      const pane = d.pane === "price" ? 0 : paneNames.indexOf(d.pane) + 1;
      if (d.id === "Volume") {
        const s = c.addSeries(
          HistogramSeries,
          { priceFormat: { type: "volume" }, title: "Volume" },
          pane,
        );
        s.setData(
          bars.map((b) => ({
            time: b.date as Time,
            value: b.volume,
            color: b.close >= b.open ? "#10b98180" : "#f43f5e80",
          })),
        );
        extra.current.push(s);
      }
      for (const [i, column] of d.columns.entries()) {
        const s = c.addSeries(
          LineSeries,
          {
            color: i === 1 && d.id === "MACD" ? "#fb923c" : d.color,
            lineWidth: 2,
            title: d.columns.length > 1 ? column : d.name,
            priceFormat:
              d.pane === "volume"
                ? { type: "volume" }
                : { type: "price", precision: 2, minMove: 0.01 },
          },
          pane,
        );
        s.setData(
          bars.map((b) => {
            const row = byDate.get(b.date);
            const v = row?.values[column];
            return typeof v === "number" && Number.isFinite(v)
              ? { time: b.date as Time, value: v }
              : { time: b.date as Time };
          }),
        );
        if (d.id === "RSI")
          for (const n of [30, 70])
            s.createPriceLine({
              price: n,
              color: "#64748b",
              lineWidth: 1,
              lineStyle: 2,
              axisLabelVisible: true,
              title: String(n),
            });
        extra.current.push(s);
      }
    }
    c.panes().forEach((p, i) => p.setHeight(i === 0 ? 340 : 130));
    if (range) c.timeScale().setVisibleRange(range);
  }, [bars, indicators, selected]);
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-2">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-300">
        <span>Nến OHLCV</span>
        {CHART_INDICATORS.filter((d) => selected.includes(d.id)).map((d) => (
          <button
            key={d.id}
            aria-label={`Gỡ ${d.name}`}
            onClick={() => onRemove(d.id)}
            className="flex min-h-9 items-center gap-1 px-1"
            style={{ color: d.color }}
          >
            {d.name}
            <X size={12} />
          </button>
        ))}
      </div>
      <div
        ref={root}
        style={{ height: 340 + panes.length * 130 }}
        className="w-full"
      />
    </div>
  );
}
