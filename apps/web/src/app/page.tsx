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
  PredictionResponse,
  StockBar,
  StockIndicatorBar,
  StockSummaryResponse,
} from "@/lib/types";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"market" | "prediction" | "backtest">(
    "market"
  );
  const [selectedSymbol, setSelectedSymbol] = useState<string>("VIC");
  const [modelType, setModelType] = useState<"lightgbm" | "lstm">("lightgbm");
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  // Dữ liệu Thị trường
  const [bars, setBars] = useState<StockBar[]>([]);
  const [indicators, setIndicators] = useState<StockIndicatorBar[]>([]);
  const [summary, setSummary] = useState<StockSummaryResponse | null>(null);
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

  // Thủ tục tải dữ liệu bất đồng bộ với Promise.allSettled
  useEffect(() => {
    let ignore = false;

    async function initData() {
      setLoadingMarket(true);
      setLoadingPrediction(true);
      setLoadingBacktest(true);

      try {
        const [histRes, indRes, sumRes, singlePred, batchPred, btRes] =
          await Promise.allSettled([
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
        selectedSymbol={selectedSymbol}
        setSelectedSymbol={setSelectedSymbol}
      />

      {/* Khung nội dung chính */}
      <div className="flex flex-1 flex-col min-w-0 overflow-x-hidden">
        {/* Thanh Header Trên cùng */}
        <TopHeader
          activeTab={activeTab}
          selectedSymbol={selectedSymbol}
          setSelectedSymbol={setSelectedSymbol}
          isCollapsed={isCollapsed}
          setIsCollapsed={setIsCollapsed}
        />

        {/* Nội dung Màn hình chính theo Active Tab */}
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-5 sm:px-6">
          {activeTab === "market" && (
            <MarketOverviewTab
              symbol={selectedSymbol}
              bars={bars}
              indicators={indicators}
              summary={summary}
              loading={loadingMarket}
            />
          )}

          {activeTab === "prediction" && (
            <AIPredictionTab
              selectedSymbol={selectedSymbol}
              onSelectSymbol={setSelectedSymbol}
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
                Đồ án Tốt nghiệp: <strong>Dự báo Xu hướng & Đánh giá Chiến lược Đầu tư</strong>
              </span>
            </div>
            <div>
              Trường Đại học Mỏ - Địa chất • Khoa Công nghệ Thông tin • Chuyên ngành Tin học Kinh tế
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
