"use client";

import React, { useEffect, useState } from "react";
import { Terminal } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { TopHeader } from "@/components/TopHeader";
import { AIPredictionTab } from "@/components/tabs/AIPredictionTab";
import { BacktestSimulatorTab } from "@/components/tabs/BacktestSimulatorTab";
import { MarketOverviewTab } from "@/components/tabs/MarketOverviewTab";
import {
  getBatchPrediction,
  getMarketBoard,
  getPredictionSignal,
  getStockHistory,
  getStockIndicators,
  getStockSummary,
  runBacktestSimulation,
} from "@/lib/api";
import {
  BacktestRequest,
  BacktestResponse,
  BatchPredictionResponse,
  MarketBoardResponse,
  PredictionResponse,
  StockBar,
  StockIndicatorBar,
  StockSummaryResponse,
} from "@/lib/types";

interface DashboardAppProps {
  initialTab?: "market" | "prediction" | "backtest";
}

export function DashboardApp({ initialTab = "market" }: DashboardAppProps) {
  const [activeTab, setActiveTabState] = useState<"market" | "prediction" | "backtest">(
    initialTab
  );
  const [selectedSymbol, setSelectedSymbol] = useState<string>("VIC");
  const [modelType, setModelType] = useState<"lightgbm" | "lstm">("lightgbm");
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  // Dữ liệu Thị trường
  const [bars, setBars] = useState<StockBar[]>([]);
  const [indicators, setIndicators] = useState<StockIndicatorBar[]>([]);
  const [summary, setSummary] = useState<StockSummaryResponse | null>(null);
  const [marketBoard, setMarketBoard] = useState<MarketBoardResponse | null>(null);
  const [loadingMarket, setLoadingMarket] = useState<boolean>(true);

  // Dữ liệu Dự báo AI
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [batchPrediction, setBatchPrediction] =
    useState<BatchPredictionResponse | null>(null);
  const [loadingPrediction, setLoadingPrediction] = useState<boolean>(false);

  // Dữ liệu Kiểm thử Backtest
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(
    null
  );
  const [loadingBacktest, setLoadingBacktest] = useState<boolean>(false);

  // Đồng bộ hóa URL browser khi chuyển tab
  const setActiveTab = (tab: "market" | "prediction" | "backtest") => {
    setActiveTabState(tab);
    if (typeof window !== "undefined") {
      const targetUrl = tab === "backtest" ? "/backtest" : "/dashboard";
      if (window.location.pathname !== targetUrl) {
        window.history.pushState(null, "", targetUrl);
      }
    }
  };

  useEffect(() => {
    const onPopState = () => {
      if (typeof window !== "undefined") {
        if (window.location.pathname === "/backtest") {
          setActiveTabState("backtest");
        } else if (window.location.pathname === "/dashboard") {
          setActiveTabState("market");
        }
      }
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  // Thủ tục tải dữ liệu bất đồng bộ với Promise.allSettled
  useEffect(() => {
    let ignore = false;

    async function initData() {
      setLoadingMarket(true);
      setLoadingPrediction(true);
      setLoadingBacktest(true);

      try {
        const [boardRes, histRes, indRes, sumRes, singlePred, batchPred, btRes] =
          await Promise.allSettled([
            getMarketBoard(),
            getStockHistory(selectedSymbol),
            getStockIndicators(selectedSymbol),
            getStockSummary(selectedSymbol),
            getPredictionSignal(selectedSymbol, modelType),
            getBatchPrediction(modelType),
            runBacktestSimulation({
              symbol: selectedSymbol,
              model_type: modelType,
              initial_capital: 100_000_000,
            }),
          ]);

        if (ignore) return;

        if (boardRes.status === "fulfilled") {
          setMarketBoard(boardRes.value);
        }
        if (histRes.status === "fulfilled") {
          setBars(histRes.value.bars);
        }
        if (indRes.status === "fulfilled") {
          setIndicators(indRes.value.indicators);
        }
        if (sumRes.status === "fulfilled") {
          setSummary(sumRes.value);
        }
        if (singlePred.status === "fulfilled") {
          setPrediction(singlePred.value);
        }
        if (batchPred.status === "fulfilled") {
          setBatchPrediction(batchPred.value);
        }
        if (btRes.status === "fulfilled") {
          setBacktestResult(btRes.value);
        }
      } catch (err) {
        console.warn("Lỗi đồng bộ Dashboard:", err);
      } finally {
        if (!ignore) {
          setLoadingMarket(false);
          setLoadingPrediction(false);
          setLoadingBacktest(false);
        }
      }
    }

    initData();

    return () => {
      ignore = true;
    };
  }, [selectedSymbol, modelType]);

  // Tự động cập nhật bảng giá và các chỉ số thị trường định kỳ mỗi 10 giây
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const board = await getMarketBoard();
        setMarketBoard(board);
      } catch (err) {
        console.debug("Lỗi cập nhật bảng giá tự động:", err);
      }
    }, 10_000);

    return () => clearInterval(timer);
  }, []);

  // Chạy Backtest tùy biến theo form
  const handleRunBacktest = async (params: BacktestRequest) => {
    setLoadingBacktest(true);
    try {
      const res = await runBacktestSimulation(params);
      setBacktestResult(res);
    } catch (err) {
      console.warn("Lỗi chạy kiểm thử Backtest:", err);
    } finally {
      setLoadingBacktest(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Thanh điều hướng Dọc (Vertical Collapsible Sidebar) */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
      />

      {/* Khung nội dung chính */}
      <div className="flex flex-1 flex-col min-w-0 overflow-x-hidden">
        {/* Thanh Header Trên cùng */}
        <TopHeader
          activeTab={activeTab}
          selectedSymbol={selectedSymbol}
          setSelectedSymbol={setSelectedSymbol}
        />

        {/* Nội dung Màn hình chính theo Active Tab */}
        <main className="mx-auto w-full max-w-7xl flex-1 px-3 py-4 sm:px-6">
          {activeTab === "market" && (
            <MarketOverviewTab
              symbol={selectedSymbol}
              onSelectSymbol={setSelectedSymbol}
              bars={bars}
              indicators={indicators}
              summary={summary}
              marketBoard={marketBoard}
              loading={loadingMarket}
              onGoToPrediction={() => setActiveTab("prediction")}
            />
          )}

          {activeTab === "prediction" && (
            <AIPredictionTab
              selectedSymbol={selectedSymbol}
              onSelectSymbol={setSelectedSymbol}
              bars={bars}
              prediction={prediction}
              batchPrediction={batchPrediction}
              modelType={modelType}
              onChangeModelType={setModelType}
              loading={loadingPrediction}
            />
          )}

          {activeTab === "backtest" && (
            <BacktestSimulatorTab
              selectedSymbol={selectedSymbol}
              onSelectSymbol={setSelectedSymbol}
              backtestResult={backtestResult}
              onRunBacktest={handleRunBacktest}
              loading={loadingBacktest}
            />
          )}
        </main>

        {/* Chân trang ĐATN chuẩn mực */}
        <footer className="border-t border-slate-800/80 bg-slate-950 py-4 text-xs text-slate-500">
          <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-4 sm:flex-row sm:px-6">
            <div className="flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5 text-emerald-500" />
              <span>
                Đồ án Tốt nghiệp: <strong>Dự báo Xu hướng &amp; Đánh giá Chiến lược Đầu tư</strong>
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
