"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, RefreshCw, Terminal } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { AIPredictionTab } from "@/components/tabs/AIPredictionTab";
import { BacktestSimulatorTab } from "@/components/tabs/BacktestSimulatorTab";
import { MarketOverviewTab } from "@/components/tabs/MarketOverviewTab";
import {
  checkBackendHealth,
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
  const [apiConnected, setApiConnected] = useState<boolean>(true);

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
        const [health, histRes, indRes, sumRes, singlePred, batchPred, btRes] =
          await Promise.allSettled([
            checkBackendHealth(),
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

        setApiConnected(health.status === "fulfilled");

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

  // Kiểm tra sức khỏe Backend thủ công khi bấm nút Thử lại
  const handleCheckHealth = async () => {
    try {
      await checkBackendHealth();
      setApiConnected(true);
    } catch {
      setApiConnected(false);
    }
  };

  // Chạy Backtest tùy biến theo form
  const handleRunBacktest = async (params: BacktestRequest) => {
    setLoadingBacktest(true);
    try {
      const res = await runBacktestSimulation(params);
      setBacktestResult(res);
      setApiConnected(true);
    } catch (err) {
      console.warn("Lỗi chạy kiểm thử Backtest:", err);
    } finally {
      setLoadingBacktest(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      {/* Navbar Điều hướng & Trạng thái */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedSymbol={selectedSymbol}
        setSelectedSymbol={setSelectedSymbol}
        apiConnected={apiConnected}
        onRefreshHealth={handleCheckHealth}
      />

      {/* Cảnh báo kết nối Backend nếu Offline */}
      {!apiConnected && (
        <div className="border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-xs text-amber-300">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
              <span>
                Máy chủ FastAPI Backend (<code className="font-mono">http://localhost:8000</code>) đang ngoại tuyến. Vui lòng chạy lệnh <code className="rounded bg-slate-800 px-1 py-0.5 font-mono text-emerald-400">uv run python app/main.py</code> tại thư mục <code className="font-mono">apps/api</code> để kích hoạt dữ liệu thời gian thực.
              </span>
            </div>
            <button
              onClick={handleCheckHealth}
              className="flex items-center gap-1 rounded bg-amber-500/20 px-2 py-0.5 font-semibold text-amber-200 hover:bg-amber-500/30 transition-all"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Thử lại</span>
            </button>
          </div>
        </div>
      )}

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
  );
}
