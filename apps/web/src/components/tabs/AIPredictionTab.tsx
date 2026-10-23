"use client";

import React, { useState } from "react";
import {
  Activity,
  Brain,
  CheckCircle2,
  ChevronRight,
  Cpu,
  HelpCircle,
  Minus,
  Radio,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { retrainProductionModel, syncLivePrediction } from "@/lib/api";
import { BatchPredictionResponse, PredictionResponse } from "@/lib/types";
import {
  FinancialDetailModal,
  FinancialItemContext,
} from "@/components/market/FinancialDetailModal";

interface AIPredictionTabProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  prediction: PredictionResponse | null;
  batchPrediction: BatchPredictionResponse | null;
  modelType: "lightgbm" | "lstm";
  onChangeModelType: (model: "lightgbm" | "lstm") => void;
  loading: boolean;
}

export const AIPredictionTab: React.FC<AIPredictionTabProps> = ({
  selectedSymbol,
  onSelectSymbol,
  prediction,
  batchPrediction,
  modelType,
  onChangeModelType,
  loading,
}) => {
  const [showInfo, setShowInfo] = useState(false);
  const [localPrediction, setLocalPrediction] = useState<PredictionResponse | null>(null);
  const [isSyncingLive, setIsSyncingLive] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null);
  const [detailModalItem, setDetailModalItem] = useState<FinancialItemContext | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // Hiển thị localPrediction nếu vừa đồng bộ Live, ngược lại hiển thị prediction từ props
  const activePred = localPrediction && localPrediction.symbol === selectedSymbol
    ? localPrediction
    : prediction;

  // Tính toán xác suất
  const probUp = activePred?.probabilities?.["TĂNG"] ?? 0;
  const probHold = activePred?.probabilities?.["ĐI NGANG"] ?? 0;
  const probDown = activePred?.probabilities?.["GIẢM"] ?? 0;

  // Confidence là xác suất cao nhất trong 3 lớp
  const maxProb = Math.max(probUp, probHold, probDown);
  const confidencePct = (maxProb * 100).toFixed(1);

  // Phân màu tín hiệu
  const signal = activePred?.signal || "ĐANG TÍNH TOÁN";
  const isBuy = signal.includes("MUA") || signal.includes("BUY");
  const isSell = signal.includes("BÁN") || signal.includes("SELL");

  // Handler đồng bộ Live từ SSI
  const handleSyncLive = async () => {
    try {
      setIsSyncingLive(true);
      const res = await syncLivePrediction(selectedSymbol, modelType);
      setLocalPrediction(res);
    } catch (err) {
      console.error("Lỗi đồng bộ live:", err);
    } finally {
      setIsSyncingLive(false);
    }
  };

  // Handler huấn luyện lại mô hình thực chiến T+3
  const handleRetrain = async () => {
    try {
      setIsRetraining(true);
      setRetrainMsg(null);
      const res = await retrainProductionModel(3, 0.02, 40);
      const lgbF1 =
        res.lightgbm_metrics?.macro_f1 != null
          ? (res.lightgbm_metrics.macro_f1 * 100).toFixed(1)
          : "0.0";
      const lstmF1 =
        res.lstm_metrics?.macro_f1 != null
          ? (res.lstm_metrics.macro_f1 * 100).toFixed(1)
          : "0.0";
      setRetrainMsg(
        `Huấn luyện thành công! Nến chốt: ${res.latest_market_date} | LGB Macro F1: ${lgbF1}% | LSTM Macro F1: ${lstmF1}%`
      );
      const updated = await syncLivePrediction(selectedSymbol, modelType);
      setLocalPrediction(updated);
    } catch (err: unknown) {
      console.error("Lỗi khi huấn luyện lại:", err);
      const errMsg = err instanceof Error ? err.message : String(err);
      setRetrainMsg(`Lỗi huấn luyện: ${errMsg}`);
    } finally {
      setIsRetraining(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Header & Bộ điều phối Mô hình Học máy & Live Feed */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/20 text-purple-400">
            <Brain className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100 sm:text-xl">
                Trung tâm Tín hiệu AI & Mô hình Định lượng
              </h2>
              <span className="rounded bg-purple-500/10 px-2 py-0.5 text-xs font-semibold text-purple-300 border border-purple-500/30">
                Chu kỳ T+3 Thực chiến
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Khắc phục rủi ro giam vốn T+2 • Dự báo quỹ đạo đa phiên (FireAnt) • Triển khai Live (DNSE)
            </p>
          </div>
        </div>

        {/* Nút hành động Live Sync, Retrain & Chuyển đổi Model */}
        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          {/* Nút Huấn luyện lại mô hình Thực chiến T+3 */}
          <button
            onClick={handleRetrain}
            disabled={isRetraining || loading}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-bold transition-all shadow-sm ${isRetraining
                ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
                : "border-indigo-500/40 bg-indigo-600 text-white hover:bg-indigo-500 shadow-indigo-500/30"
              }`}
            title="Tự động nạp nến mới nhất tới phiên T-1/T và huấn luyện lại LightGBM & LSTM"
          >
            <Sparkles className={`h-3.5 w-3.5 ${isRetraining ? "animate-spin" : ""}`} />
            <span>{isRetraining ? "Đang huấn luyện T+3..." : "Huấn luyện lại T+3"}</span>
          </button>

          {/* Nút Đồng bộ Live SSI */}
          <button
            onClick={handleSyncLive}
            disabled={isSyncingLive || loading}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-bold transition-all shadow-sm ${activePred?.is_live_synced
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                : "border-purple-500/40 bg-purple-600 text-white hover:bg-purple-500 shadow-purple-500/30"
              }`}
            title="Đồng bộ nến mới nhất từ cổng SSI FastConnect và suy luận thời gian thực"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isSyncingLive ? "animate-spin" : ""}`} />
            <span>
              {isSyncingLive
                ? "Đang đồng bộ SSI..."
                : activePred?.is_live_synced
                  ? "Đã đồng bộ Live"
                  : "Triển khai Live (SSI)"}
            </span>
          </button>

          {/* Bộ chọn Mô hình */}
          <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1">
            <button
              onClick={() => {
                setLocalPrediction(null);
                onChangeModelType("lightgbm");
              }}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${modelType === "lightgbm"
                  ? "bg-purple-600 text-white shadow-sm shadow-purple-500/40"
                  : "text-slate-400 hover:text-slate-200"
                }`}
            >
              <Cpu className="h-3.5 w-3.5" />
              <span>LightGBM</span>
            </button>
            <button
              onClick={() => {
                setLocalPrediction(null);
                onChangeModelType("lstm");
              }}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${modelType === "lstm"
                  ? "bg-purple-600 text-white shadow-sm shadow-purple-500/40"
                  : "text-slate-400 hover:text-slate-200"
                }`}
            >
              <Brain className="h-3.5 w-3.5" />
              <span>LSTM Network</span>
            </button>
          </div>
        </div>
      </div>

      {/* Banner thông báo Huấn luyện / Thông tin dữ liệu thực chiến */}
      {retrainMsg && (
        <div className="flex items-center justify-between rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-3 text-xs text-indigo-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>{retrainMsg}</span>
          </div>
          <button
            onClick={() => setRetrainMsg(null)}
            className="text-indigo-400 hover:text-indigo-200 text-xs ml-2"
          >
            Đóng
          </button>
        </div>
      )}

      {/* Thông tin Dữ liệu Huấn luyện & Chân trời Dự phóng */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/70 px-4 py-2 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400" />
          <span>
            Dữ liệu căn cứ: <strong className="text-slate-200">Phiên {activePred?.data_as_of_date || activePred?.date || "gần nhất"}</strong>
          </span>
          {activePred?.market_session_label && (
            <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[11px] font-bold text-emerald-400 border border-emerald-500/20">
              {activePred.market_session_label}
            </span>
          )}
          <span className="text-slate-600">•</span>
          <span>
            Kỳ hạn: <strong className="text-purple-300">3 phiên tiếp theo (T+1 → T+3)</strong>
          </span>
        </div>
        <div className="text-[11px] text-slate-500">
          Học trực tiếp trên 100% dữ liệu lịch sử tích lũy đến T/T-1 • Ràng buộc T+2.5 VSDC
        </div>
      </div>

      {/* 2. Thẻ Khuyến nghị Tín hiệu & Thanh Phân phối Xác suất */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Cột trái: Thẻ Tín hiệu AI Hành động (5 cột) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm lg:col-span-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Khuyến nghị chiến lược ({selectedSymbol})
              </span>
              <div className="flex items-center gap-1.5">
                {activePred?.is_live_synced && (
                  <span className="inline-flex items-center gap-1 rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                    <Radio className="h-2.5 w-2.5 animate-pulse text-emerald-400" />
                    LIVE SSI
                  </span>
                )}
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300">
                  Kỳ hạn: {activePred?.horizon || "T+3"}
                </span>
              </div>
            </div>

            {loading ? (
              <div className="my-8 flex flex-col items-center justify-center gap-2">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
                <span className="text-xs text-slate-400">Mô hình AI đang suy luận...</span>
              </div>
            ) : (
              <div className="my-6">
                <div
                  className={`flex items-center gap-3 rounded-2xl border p-4 ${isBuy
                      ? "border-emerald-500/40 bg-gradient-to-r from-emerald-500/20 to-teal-500/10 text-emerald-300"
                      : isSell
                        ? "border-rose-500/40 bg-gradient-to-r from-rose-500/20 to-pink-500/10 text-rose-300"
                        : "border-amber-500/40 bg-gradient-to-r from-amber-500/20 to-yellow-500/10 text-amber-300"
                    }`}
                >
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${isBuy
                        ? "bg-emerald-500 text-slate-950"
                        : isSell
                          ? "bg-rose-500 text-slate-950"
                          : "bg-amber-400 text-slate-950"
                      }`}
                  >
                    {isBuy ? (
                      <TrendingUp className="h-7 w-7 stroke-[2.5]" />
                    ) : isSell ? (
                      <TrendingDown className="h-7 w-7 stroke-[2.5]" />
                    ) : (
                      <Minus className="h-7 w-7 stroke-[2.5]" />
                    )}
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider opacity-80">
                      Tín hiệu chu kỳ T+3
                    </span>
                    <h3 className="text-xl font-black tracking-tight sm:text-2xl">
                      {activePred?.signal || "NẮM GIỮ (HOLD)"}
                    </h3>
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Xu hướng phân loại:</span>
                    <span className="font-bold text-slate-200">
                      {activePred?.class_name || "ĐI NGANG"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Dữ liệu chốt phiên căn cứ:</span>
                    <span className="font-bold text-slate-200">
                      {activePred?.data_as_of_date || activePred?.date || "---"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Thị giá đóng cửa phiên t:</span>
                    <span className="font-bold text-slate-200">
                      {activePred
                        ? (activePred.current_price * 1000).toLocaleString("vi-VN")
                        : "---"}{" "}
                      VNĐ
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Độ tin cậy mô hình:</span>
                    <span className="font-bold text-purple-400">{confidencePct}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-lg bg-slate-950/80 p-3 text-[11px] text-slate-400 border border-slate-800/60">
            <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>Chu kỳ nắm giữ & Vi cấu trúc T+2</span>
            </div>
            Dự báo bao trọn thời gian lưu ký T+2 và điểm bán khả dụng T+3. Lệnh Mua chỉ phát sinh khi xác suất vượt ngưỡng an toàn sau khi trừ đủ 0.40% thuế phí.
          </div>
        </div>

        {/* Cột phải: Phân phối Xác suất Softmax 3 Lớp (7 cột) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm lg:col-span-7 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Phân phối xác suất 3 lớp (Softmax Probabilities)
                </span>
                <button
                  onClick={() => setShowInfo(!showInfo)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                </button>
              </div>
              <span className="text-[11px] text-slate-500">∑ P = 100%</span>
            </div>

            {showInfo && (
              <div className="mb-4 rounded-lg bg-slate-950 p-3 text-xs text-slate-400 border border-slate-800">
                <p>
                  Mô hình Machine Learning xuất ra 3 giá trị logit, sau đó chuẩn hóa qua hàm Softmax:
                  &sigma;(z)<sub>i</sub> = exp(z<sub>i</sub>) / &sum; exp(z<sub>j</sub>). Điều này giúp phản ánh đúng bản chất ngẫu nhiên của thị trường thay vì đưa ra một con số cứng nhắc.
                </p>
              </div>
            )}

            {/* 3 Thanh tiến trình xác suất */}
            <div className="space-y-4">
              {/* Lớp TĂNG */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium mb-1">
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <TrendingUp className="h-3.5 w-3.5" /> Xu hướng TĂNG (Up)
                  </span>
                  <span className="font-bold text-emerald-400">
                    {(probUp * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 w-full rounded-full bg-slate-950 p-0.5 border border-slate-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-teal-400 transition-all duration-500"
                    style={{ width: `${Math.max(probUp * 100, 3)}%` }}
                  />
                </div>
              </div>

              {/* Lớp ĐI NGANG */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium mb-1">
                  <span className="flex items-center gap-1.5 text-amber-400">
                    <Minus className="h-3.5 w-3.5" /> Xu hướng ĐI NGANG (Neutral)
                  </span>
                  <span className="font-bold text-amber-400">
                    {(probHold * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 w-full rounded-full bg-slate-950 p-0.5 border border-slate-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-600 to-yellow-400 transition-all duration-500"
                    style={{ width: `${Math.max(probHold * 100, 3)}%` }}
                  />
                </div>
              </div>

              {/* Lớp GIẢM */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium mb-1">
                  <span className="flex items-center gap-1.5 text-rose-400">
                    <TrendingDown className="h-3.5 w-3.5" /> Xu hướng GIẢM (Down)
                  </span>
                  <span className="font-bold text-rose-400">
                    {(probDown * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 w-full rounded-full bg-slate-950 p-0.5 border border-slate-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-rose-600 to-pink-500 transition-all duration-500"
                    style={{ width: `${Math.max(probDown * 100, 3)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 border-t border-slate-800/80 pt-3 flex items-center justify-between text-xs text-slate-400">
            <span>Mô hình đang chạy: <strong className="text-slate-200">{modelType.toUpperCase()}</strong></span>
            <span className="text-[11px] text-slate-500">Đã kiểm định Walk-Forward OOS</span>
          </div>
        </div>
      </div>

      {/* 2.5. Quỹ đạo Dự phóng Xu hướng 3 Phiên (Multi-step Trajectory theo chuẩn FireAnt & vi cấu trúc T+2) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
        <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-purple-400" />
            <h3 className="text-sm font-bold text-slate-100 sm:text-base">
              Quỹ đạo Dự phóng Xu hướng 3 Phiên T+1 → T+3 (Trend Trajectory)
            </h3>
            <span className="rounded bg-purple-500/10 px-2 py-0.5 text-[11px] font-semibold text-purple-300 border border-purple-500/20">
              FireAnt Model
            </span>
          </div>
          <span className="text-xs text-slate-400">
            Mô phỏng đường đi xu hướng bám sát chu kỳ nắm giữ tối thiểu của thị trường cơ sở Việt Nam
          </span>
        </div>

        {/* 3 Thẻ Bước trong Quỹ đạo */}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {activePred?.trajectory && activePred.trajectory.length > 0 ? (
            activePred.trajectory.map((step, idx) => {
              const isStepBuy = step.predicted_trend === "TĂNG";
              const isStepSell = step.predicted_trend === "GIẢM";
              const stepConf = (step.confidence * 100).toFixed(1);

              return (
                <div
                  key={step.day_name}
                  className={`relative flex flex-col justify-between rounded-xl border p-4 transition-all ${isStepBuy
                      ? "border-emerald-500/30 bg-emerald-950/20"
                      : isStepSell
                        ? "border-rose-500/30 bg-rose-950/20"
                        : "border-amber-500/30 bg-amber-950/20"
                    }`}
                >
                  <div>
                    {/* Header ngày */}
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="flex h-6 px-1.5 items-center justify-center rounded-md bg-slate-800 text-xs font-bold text-slate-200">
                          {step.day_name}
                        </span>
                        {step.date && (
                          <span className="rounded bg-purple-500/10 px-1.5 py-0.5 font-mono text-[10px] font-bold text-purple-300 border border-purple-500/20">
                            {step.date}
                          </span>
                        )}
                        <span className="text-xs font-semibold text-slate-300">
                          {idx === 0
                            ? "Phiên mở vị thế (Open)"
                            : idx === 1
                              ? "Phiên lưu ký (Khóa T+2)"
                              : "Phiên khả dụng bán (T+3)"}
                        </span>
                      </div>
                      <span className="text-[11px] font-bold text-purple-400">
                        {stepConf}% tin cậy
                      </span>
                    </div>

                    {/* Xu hướng dự báo */}
                    <div className="my-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isStepBuy ? (
                          <TrendingUp className="h-5 w-5 text-emerald-400" />
                        ) : isStepSell ? (
                          <TrendingDown className="h-5 w-5 text-rose-400" />
                        ) : (
                          <Minus className="h-5 w-5 text-amber-400" />
                        )}
                        <span
                          className={`text-sm font-black ${isStepBuy
                              ? "text-emerald-400"
                              : isStepSell
                                ? "text-rose-400"
                                : "text-amber-400"
                            }`}
                        >
                          {step.predicted_trend}
                        </span>
                      </div>
                      <span className="rounded bg-slate-900 px-2 py-0.5 text-[11px] font-semibold text-slate-300 border border-slate-800">
                        {step.signal}
                      </span>
                    </div>

                    {/* Phân bổ xác suất thanh nhỏ */}
                    <div className="space-y-1 text-[11px]">
                      <div className="flex justify-between text-slate-400">
                        <span>Tăng: {(step.probabilities["TĂNG"] * 100).toFixed(0)}%</span>
                        <span>Ngang: {(step.probabilities["ĐI NGANG"] * 100).toFixed(0)}%</span>
                        <span>Giảm: {(step.probabilities["GIẢM"] * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-slate-950 flex overflow-hidden">
                        <div
                          className="bg-emerald-500"
                          style={{ width: `${step.probabilities["TĂNG"] * 100}%` }}
                        />
                        <div
                          className="bg-amber-400"
                          style={{ width: `${step.probabilities["ĐI NGANG"] * 100}%` }}
                        />
                        <div
                          className="bg-rose-500"
                          style={{ width: `${step.probabilities["GIẢM"] * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Ghi chú nghiệp vụ sàn */}
                  <p className="mt-3 border-t border-slate-800/60 pt-2 text-[11px] text-slate-400 italic">
                    {step.note}
                  </p>
                </div>
              );
            })
          ) : (
            <div className="col-span-3 text-center py-6 text-xs text-slate-400">
              Đang tính toán quỹ đạo 3 phiên cho mã {selectedSymbol}...
            </div>
          )}
        </div>

        {/* Khuyến nghị Thực chiến tổng hợp (Executive Strategy Guidance) */}
        {activePred?.summary_guidance && (
          <div className="mt-4 flex items-start gap-3 rounded-lg border border-purple-500/30 bg-purple-950/20 p-3.5 text-xs text-purple-200">
            <Sparkles className="h-4 w-4 shrink-0 text-purple-400 mt-0.5" />
            <div>
              <strong className="font-bold text-purple-300">Nhận định định lượng: </strong>
              <span>{activePred.summary_guidance}</span>
            </div>
          </div>
        )}
      </div>

      {/* 3. Bảng Quét Tín hiệu Danh mục 5 Cổ phiếu Trọng tâm (Batch Screener) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 sm:text-base">
              Bảng quét Radar Tín hiệu Toàn bộ Danh mục 5 Mã Cốt lõi
            </h3>
            <p className="text-[11px] text-slate-400">
              Tổng hợp dự báo tự động cho các mã cổ phiếu nghiên cứu trong ĐATN
            </p>
          </div>
          <span className="rounded bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300">
            5 / 5 Mã HOSE
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-950 text-slate-400">
              <tr>
                <th className="px-3 py-2.5 font-semibold">Mã CP</th>
                <th className="px-3 py-2.5 font-semibold">Thị giá</th>
                <th className="px-3 py-2.5 font-semibold">Tín hiệu Khuyến nghị</th>
                <th className="px-3 py-2.5 font-semibold">Xác suất Tăng</th>
                <th className="px-3 py-2.5 font-semibold">Xác suất Giảm</th>
                <th className="px-3 py-2.5 font-semibold">Độ tin cậy</th>
                <th className="px-3 py-2.5 text-right font-semibold">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {batchPrediction?.predictions.map((pred) => {
                const isItemBuy = pred.signal.includes("MUA") || pred.signal.includes("BUY");
                const isItemSell = pred.signal.includes("BÁN") || pred.signal.includes("SELL");
                const itemProbUp = pred.probabilities?.["TĂNG"] ?? 0;
                const itemProbDown = pred.probabilities?.["GIẢM"] ?? 0;
                const itemConfidence = (
                  Math.max(
                    itemProbUp,
                    pred.probabilities?.["ĐI NGANG"] ?? 0,
                    itemProbDown
                  ) * 100
                ).toFixed(1);

                return (
                  <tr
                    key={pred.symbol}
                    className={`transition-colors hover:bg-slate-800/40 ${selectedSymbol === pred.symbol ? "bg-slate-800/30" : ""
                      }`}
                  >
                    <td className="px-3 py-3 font-bold text-slate-100">
                      <div className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-emerald-400" />
                        <span>{pred.symbol}</span>
                      </div>
                    </td>
                    <td className="px-3 py-3 font-semibold text-slate-200">
                      {(pred.current_price * 1000).toLocaleString("vi-VN")} đ
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold ${isItemBuy
                            ? "bg-emerald-500/10 text-emerald-400"
                            : isItemSell
                              ? "bg-rose-500/10 text-rose-400"
                              : "bg-amber-500/10 text-amber-400"
                          }`}
                      >
                        {isItemBuy ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : isItemSell ? (
                          <TrendingDown className="h-3 w-3" />
                        ) : (
                          <Minus className="h-3 w-3" />
                        )}
                        {pred.signal}
                      </span>
                    </td>
                    <td className="px-3 py-3 font-medium text-emerald-400">
                      {(itemProbUp * 100).toFixed(1)}%
                    </td>
                    <td className="px-3 py-3 font-medium text-rose-400">
                      {(itemProbDown * 100).toFixed(1)}%
                    </td>
                    <td className="px-3 py-3 font-semibold text-purple-400">
                      {itemConfidence}%
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        onClick={() => {
                          onSelectSymbol(pred.symbol);
                          setDetailModalItem({
                            symbol: pred.symbol,
                            currentValue: pred.current_price,
                            isIndex: false,
                          });
                          setIsDetailModalOpen(true);
                        }}
                        className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-slate-200 hover:border-emerald-500 hover:bg-emerald-500 hover:text-slate-950 transition-all"
                        title={`Soi nến và phân tích kỹ thuật ${pred.symbol}`}
                      >
                        <span>Soi nến</span>
                        <ChevronRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal chi tiết kỹ thuật chuẩn hóa */}
      <FinancialDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        item={detailModalItem}
      />
    </div>
  );
};
