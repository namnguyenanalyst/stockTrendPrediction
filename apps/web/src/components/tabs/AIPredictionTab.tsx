"use client";

import React, { useState } from "react";
import {
  Brain,
  CheckCircle2,
  ChevronRight,
  Cpu,
  HelpCircle,
  Minus,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { BatchPredictionResponse, PredictionResponse } from "@/lib/types";

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

  // Tính toán xác suất
  const probUp = prediction?.probabilities?.["TĂNG"] ?? 0;
  const probHold = prediction?.probabilities?.["ĐI NGANG"] ?? 0;
  const probDown = prediction?.probabilities?.["GIẢM"] ?? 0;

  // Confidence là xác suất cao nhất trong 3 lớp
  const maxProb = Math.max(probUp, probHold, probDown);
  const confidencePct = (maxProb * 100).toFixed(1);

  // Phân màu tín hiệu
  const signal = prediction?.signal || "ĐANG TÍNH TOÁN";
  const isBuy = signal.includes("MUA") || signal.includes("BUY");
  const isSell = signal.includes("BÁN") || signal.includes("SELL");

  return (
    <div className="space-y-4">
      {/* 1. Header & Bộ chọn Mô hình Học máy */}
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
                XAI Powered
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Dự báo đa lớp không rò rỉ dữ liệu (No Lookahead Bias) • Chu kỳ Walk-forward
            </p>
          </div>
        </div>

        {/* Nút chuyển đổi Mô hình AI */}
        <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1 self-start sm:self-auto">
          <button
            onClick={() => onChangeModelType("lightgbm")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
              modelType === "lightgbm"
                ? "bg-purple-600 text-white shadow-sm shadow-purple-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>Ensemble LightGBM</span>
          </button>
          <button
            onClick={() => onChangeModelType("lstm")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
              modelType === "lstm"
                ? "bg-purple-600 text-white shadow-sm shadow-purple-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>PyTorch LSTM</span>
          </button>
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
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300">
                Kỳ hạn: {prediction?.horizon || "T+1 → T+5"}
              </span>
            </div>

            {loading ? (
              <div className="my-8 flex flex-col items-center justify-center gap-2">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
                <span className="text-xs text-slate-400">Mô hình AI đang suy luận...</span>
              </div>
            ) : (
              <div className="my-6">
                <div
                  className={`flex items-center gap-3 rounded-2xl border p-4 ${
                    isBuy
                      ? "border-emerald-500/40 bg-gradient-to-r from-emerald-500/20 to-teal-500/10 text-emerald-300"
                      : isSell
                      ? "border-rose-500/40 bg-gradient-to-r from-rose-500/20 to-pink-500/10 text-rose-300"
                      : "border-amber-500/40 bg-gradient-to-r from-amber-500/20 to-yellow-500/10 text-amber-300"
                  }`}
                >
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${
                      isBuy
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
                      Tín hiệu dự báo
                    </span>
                    <h3 className="text-xl font-black tracking-tight sm:text-2xl">
                      {prediction?.signal || "NẮM GIỮ (HOLD)"}
                    </h3>
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Xu hướng phân loại:</span>
                    <span className="font-bold text-slate-200">
                      {prediction?.class_name || "ĐI NGANG"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Thị giá căn cứ phiên t:</span>
                    <span className="font-bold text-slate-200">
                      {prediction
                        ? (prediction.current_price * 1000).toLocaleString("vi-VN")
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
              <span>Cơ chế quản trị rủi ro</span>
            </div>
            Lệnh chỉ được kích hoạt khi xác suất lớp mục tiêu vượt ngưỡng dung sai (Threshold &gt; 40%). Tuân thủ thời gian chờ khớp lệnh Open T+1.
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
                    className={`transition-colors hover:bg-slate-800/40 ${
                      selectedSymbol === pred.symbol ? "bg-slate-800/30" : ""
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
                        className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold ${
                          isItemBuy
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
                        onClick={() => onSelectSymbol(pred.symbol)}
                        className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-slate-200 hover:border-emerald-500 hover:bg-emerald-500 hover:text-slate-950 transition-all"
                      >
                        <span>Chi tiết</span>
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
    </div>
  );
};
