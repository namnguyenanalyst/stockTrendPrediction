"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  Brain,
  CheckCircle2,
  Clock,
  Cpu,
  HelpCircle,
  History,
  Minus,
  Radio,
  Sparkles,
  Trash2,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { getStockHistory, retrainProductionModel, syncLivePrediction } from "@/lib/api";
import { BatchPredictionResponse, PredictionResponse, StockBar } from "@/lib/types";
import {
  FinancialDetailModal,
  FinancialItemContext,
} from "@/components/market/FinancialDetailModal";
import { FireAntTrajectoryChart } from "@/components/charts/FireAntTrajectoryChart";

export interface PredictionHistoryItem {
  id: string;
  timestamp: string;
  symbol: string;
  model_type: "lightgbm" | "lstm";
  data_date: string;
  current_price: number;
  signal: string;
  prob_up: number;
  prob_hold: number;
  prob_down: number;
  confidence: number;
  horizon: string;
}

const MODEL_SPECIFICATIONS = {
  lightgbm: {
    title: "LightGBM — Chuyên gia Bắt nhịp Ngắn hạn",
    badge: "Phù hợp khi thị trường Đi ngang (Sideway) & Lướt sóng T+3",
    overview:
      "Như một chuyên gia phân tích kỹ thuật soi kính lúp vào phiên hôm nay: đo lường xem nến hôm nay đóng cửa ở đâu, RSI có đang quá mua/quá bán không, dòng tiền ngắn hạn vào hay ra để phản xạ tức thì.",
    purpose:
      "Dự đoán xem trong 1–3 phiên tiếp theo (chu kỳ T+3), cổ phiếu sẽ BẬT TĂNG, CHỈNH GIẢM hay tiếp tục GIẰNG CO theo các mốc hỗ trợ và kháng cự kỹ thuật.",
    whenToUse:
      "LÚC NÊN CHỌN: Thị trường hoặc cổ phiếu đang ĐI NGANG (lình xình không rõ sóng), giá biến động trong biên độ hẹp và bạn muốn lướt sóng nhanh bắt nhịp hồi T+3.",
    signsTitle: "Dấu hiệu trên bảng điện để bạn chọn mô hình này:",
    signs: [
      "Giá cổ phiếu dập dìu trong vùng giá quen thuộc, chưa vượt được đỉnh cũ hay thủng đáy cũ.",
      "Chỉ báo RSI rơi vào vùng Quá bán (< 30 - canh bắt nhịp nảy hồi) hoặc Quá mua (> 70 - canh chốt lời).",
      "Thị trường phân hóa mạnh, dòng tiền đánh nhanh rút gọn, không tạo thành sóng ngành kéo dài.",
    ],
  },
  lstm: {
    title: "LSTM Network — Chuyên gia Bám sóng Quán tính",
    badge: "Phù hợp khi cổ phiếu Vào Sóng Lớn (Trend)",
    overview:
      "Khác với LightGBM chỉ nhìn 1 phiên, mô hình này có 'trí nhớ' chuỗi thời gian: nó xem trọn vẹn cả cuộn phim 20 ngày giao dịch liên tục (~1 tháng) để giải mã xem quán tính của con sóng và lực gom hàng của dòng tiền lớn đang mạnh hay yếu.",
    purpose:
      "Đo lường sức đẩy quán tính của chuỗi ngày qua để dự phóng xem đà tăng/giảm này còn đủ lực kéo tiếp trong 3 phiên tới hay sắp cạn kiệt.",
    whenToUse:
      "LÚC NÊN CHỌN: Cổ phiếu hoặc thị trường đang VÀO SÓNG TĂNG/GIẢM MẠNH (Uptrend/Downtrend), có dòng tiền lớn dẫn dắt và bạn muốn đầu tư bám theo xu hướng lớn (Trend Following).",
    signsTitle: "Dấu hiệu trên bảng điện để bạn chọn mô hình này:",
    signs: [
      "Cổ phiếu có 3–5 phiên tăng liên tục hoặc vừa có phiên nổ khối lượng bứt phá đỉnh cũ (Breakout).",
      "Khối lượng giao dịch (Volume) tăng đột biến gấp 1.5 - 2 lần bình thường (dòng tiền tổ chức tham gia).",
      "Thị trường xuất hiện sóng ngành dẫn dắt rõ rệt (cả họ cổ phiếu cùng tăng mạnh), giá bám sát đà dốc đi lên.",
    ],
  },
};

interface AIPredictionTabProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  bars?: StockBar[];
  prediction: PredictionResponse | null;
  batchPrediction?: BatchPredictionResponse | null;
  modelType: "lightgbm" | "lstm";
  onChangeModelType: (model: "lightgbm" | "lstm") => void;
  loading: boolean;
}

export const AIPredictionTab: React.FC<AIPredictionTabProps> = ({
  selectedSymbol,
  onSelectSymbol,
  bars,
  prediction,
  modelType,
  onChangeModelType,
  loading,
}) => {
  const [showInfo, setShowInfo] = useState(false);
  const [localPrediction, setLocalPrediction] = useState<PredictionResponse | null>(null);
  const [fallbackBars, setFallbackBars] = useState<StockBar[]>([]);
  const chartBars = bars && bars.length > 0 ? bars : fallbackBars;
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null);

  // Tải nến dự phòng nếu không nhận được bars từ props
  useEffect(() => {
    if (!bars || bars.length === 0) {
      let ignore = false;
      getStockHistory(selectedSymbol)
        .then((res) => {
          if (!ignore && res && res.bars) setFallbackBars(res.bars);
        })
        .catch((err) => console.warn("Lỗi tải nến biểu đồ:", err));
      return () => {
        ignore = true;
      };
    }
  }, [bars, selectedSymbol]);
  const [detailModalItem, setDetailModalItem] = useState<FinancialItemContext | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [history, setHistory] = useState<PredictionHistoryItem[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = localStorage.getItem("vn_stock_prediction_history");
      return stored ? JSON.parse(stored) : [];
    } catch (err) {
      console.warn("Không thể tải lịch sử dự báo từ localStorage:", err);
      return [];
    }
  });

  // Trạng thái hover 3 giây hiển thị đặc tả mô hình
  const [hoveredModel, setHoveredModel] = useState<"lightgbm" | "lstm" | null>(null);
  const [activeTooltipModel, setActiveTooltipModel] = useState<"lightgbm" | "lstm" | null>(null);
  const hoverTimerRef = useRef<NodeJS.Timeout | null>(null);

  const startHoverTimer = (m: "lightgbm" | "lstm") => {
    setHoveredModel(m);
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = setTimeout(() => {
      setActiveTooltipModel(m);
      setHoveredModel(null);
    }, 3000);
  };

  const cancelHoverTimer = () => {
    setHoveredModel(null);
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
  };

  // Lắng nghe phím Escape để đóng modal đặc tả mô hình
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && activeTooltipModel) {
        setActiveTooltipModel(null);
        setHoveredModel(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeTooltipModel]);

  // Hiển thị localPrediction nếu vừa đồng bộ Live, ngược lại hiển thị prediction từ props
  const activePred = localPrediction && localPrediction.symbol === selectedSymbol
    ? localPrediction
    : prediction;

  // Tự động ghi vết dự báo vào lịch sử khi người dùng chọn cổ phiếu hoặc đổi mô hình
  useEffect(() => {
    if (!activePred || loading) return;

    const timer = setTimeout(() => {
      setHistory((prev) => {
        const last = prev[0];
        const dataDate = activePred.data_as_of_date || activePred.date;
        // Tránh ghi lặp nếu vừa ghi cùng mã, cùng mô hình và cùng phiên căn cứ
        if (
          last &&
          last.symbol === activePred.symbol &&
          last.model_type === activePred.model_type &&
          last.data_date === dataDate
        ) {
          return prev;
        }

        const pUp = activePred.probabilities?.["TĂNG"] ?? 0;
        const pHold = activePred.probabilities?.["ĐI NGANG"] ?? 0;
        const pDown = activePred.probabilities?.["GIẢM"] ?? 0;
        const conf = Math.max(pUp, pHold, pDown);

        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")} ${String(now.getDate()).padStart(2, "0")}/${String(now.getMonth() + 1).padStart(2, "0")}/${now.getFullYear()}`;

        const newItem: PredictionHistoryItem = {
          id: `${Date.now()}_${activePred.symbol}`,
          timestamp: timeStr,
          symbol: activePred.symbol,
          model_type: (activePred.model_type as "lightgbm" | "lstm") || modelType,
          data_date: dataDate,
          current_price: activePred.current_price,
          signal: activePred.signal,
          prob_up: pUp,
          prob_hold: pHold,
          prob_down: pDown,
          confidence: conf,
          horizon: activePred.horizon || "T+3",
        };

        const updated = [newItem, ...prev].slice(0, 50); // Giới hạn 50 bản ghi gần nhất
        try {
          localStorage.setItem("vn_stock_prediction_history", JSON.stringify(updated));
        } catch (err) {
          console.warn("Không thể lưu lịch sử vào localStorage:", err);
        }
        return updated;
      });
    }, 0);

    return () => clearTimeout(timer);
  }, [
    activePred,
    loading,
    modelType,
  ]);

  const handleClearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem("vn_stock_prediction_history");
    } catch (err) {
      console.warn("Không thể xóa lịch sử từ localStorage:", err);
    }
  };

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


  // Handler huấn luyện lại mô hình thực chiến T+3 trên toàn bộ rổ VN30
  const handleRetrain = async () => {
    try {
      setIsRetraining(true);
      setRetrainMsg(null);
      const res = await retrainProductionModel(3, 0.02, 40, "VN30");
      const lgbF1 =
        res.lightgbm_metrics?.macro_f1 != null
          ? (res.lightgbm_metrics.macro_f1 * 100).toFixed(1)
          : "0.0";
      const lstmF1 =
        res.lstm_metrics?.macro_f1 != null
          ? (res.lstm_metrics.macro_f1 * 100).toFixed(1)
          : "0.0";
      setRetrainMsg(
        `Huấn luyện thành công toàn bộ rổ VN30! Nến chốt: ${res.latest_market_date} | Mẫu train: ${res.train_samples?.toLocaleString() || 0} | LGB Macro F1: ${lgbF1}% | LSTM Macro F1: ${lstmF1}%`
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
      <div className="flex flex-col gap-3 rounded-lg border border-slate-800 bg-slate-900 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10 text-blue-400">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100 sm:text-lg">
                Trung tâm Tín hiệu AI & Mô hình Định lượng
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Dự báo xác suất xu hướng giá theo chu kỳ T+3 cho nhà đầu tư cá nhân
            </p>
          </div>
        </div>

        {/* Nút hành động Live Sync, Retrain & Chuyển đổi Model */}
        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          {/* Nút Huấn luyện lại mô hình Thực chiến T+3 trên toàn bộ rổ VN30 */}
          <button
            onClick={handleRetrain}
            disabled={isRetraining || loading}
            className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors ${isRetraining
              ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
              : "border-blue-600 bg-blue-600 text-white hover:bg-blue-500"
              }`}
            title="Tự động nạp nến mới nhất và huấn luyện lại LightGBM & LSTM trên toàn bộ 30 mã rổ VN30"
          >
            <Sparkles className={`h-3.5 w-3.5 ${isRetraining ? "animate-spin" : ""}`} />
            <span>{isRetraining ? "Đang huấn luyện VN30..." : "Huấn luyện lại T+3"}</span>
          </button>


          {/* Bộ chọn Mô hình kèm Cơ chế Hover 3 Giây Thả Đặc Tả */}
          <div className="relative flex items-center gap-1 rounded-md border border-slate-800 bg-slate-950 p-1">
            <button
              onClick={() => {
                setLocalPrediction(null);
                onChangeModelType("lightgbm");
              }}
              onMouseEnter={() => startHoverTimer("lightgbm")}
              onMouseLeave={cancelHoverTimer}
              className={`relative flex items-center gap-1.5 overflow-hidden rounded px-2.5 py-1 text-xs font-semibold transition-colors ${modelType === "lightgbm"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-slate-200"
                }`}
              title="Giữ chuột 3 giây để xem cửa sổ đặc tả mô hình LightGBM"
            >
              <Cpu className="h-3.5 w-3.5" />
              <span>LightGBM</span>
              {/* Thanh đếm giờ 3 giây trực quan */}
              {hoveredModel === "lightgbm" && activeTooltipModel !== "lightgbm" && (
                <span
                  className="absolute bottom-0 left-0 h-0.5 bg-blue-400"
                  style={{
                    animation: "fillProgress 3s linear forwards",
                  }}
                />
              )}
            </button>
            <button
              onClick={() => {
                setLocalPrediction(null);
                onChangeModelType("lstm");
              }}
              onMouseEnter={() => startHoverTimer("lstm")}
              onMouseLeave={cancelHoverTimer}
              className={`relative flex items-center gap-1.5 overflow-hidden rounded px-2.5 py-1 text-xs font-semibold transition-colors ${modelType === "lstm"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-slate-200"
                }`}
              title="Giữ chuột 3 giây để xem cửa sổ đặc tả mô hình PyTorch LSTM"
            >
              <Brain className="h-3.5 w-3.5" />
              <span>LSTM Network</span>
              {/* Thanh đếm giờ 3 giây trực quan */}
              {hoveredModel === "lstm" && activeTooltipModel !== "lstm" && (
                <span
                  className="absolute bottom-0 left-0 h-0.5 bg-sky-400"
                  style={{
                    animation: "fillProgress 3s linear forwards",
                  }}
                />
              )}
            </button>

            <style>{`
              @keyframes fillProgress {
                from { width: 0%; opacity: 0.7; }
                to { width: 100%; opacity: 1; }
              }
            `}</style>
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
            Kỳ hạn: <strong className="text-blue-300 font-mono">3 phiên tiếp theo (T+3)</strong>
          </span>
        </div>
      </div>

      {/* 2. Thẻ Khuyến nghị Tín hiệu & Thanh Phân phối Xác suất */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Cột trái: Thẻ Tín hiệu AI Hành động (5 cột) */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 lg:col-span-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Khuyến nghị ({selectedSymbol})
              </span>
              <div className="flex items-center gap-1.5">
                {activePred?.is_live_synced && (
                  <span className="inline-flex items-center gap-1 rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                    <Radio className="h-2.5 w-2.5 animate-pulse text-emerald-400" />
                    LIVE SSI
                  </span>
                )}
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300 font-mono">
                  {activePred?.horizon || "T+3"}
                </span>
              </div>
            </div>

            {loading ? (
              <div className="my-8 flex flex-col items-center justify-center gap-2">
                <div className="h-7 w-7 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                <span className="text-xs text-slate-400">Mô hình AI đang suy luận...</span>
              </div>
            ) : (
              <div className="my-4">
                <div
                  className={`flex items-center gap-3 rounded-lg border p-3.5 ${isBuy
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                    : isSell
                      ? "border-rose-500/30 bg-rose-500/10 text-rose-300"
                      : "border-amber-500/30 bg-amber-500/10 text-amber-300"
                    }`}
                >
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md ${isBuy
                      ? "bg-emerald-500 text-slate-950"
                      : isSell
                        ? "bg-rose-500 text-white"
                        : "bg-amber-400 text-slate-950"
                      }`}
                  >
                    {isBuy ? (
                      <TrendingUp className="h-6 w-6 stroke-[2.5]" />
                    ) : isSell ? (
                      <TrendingDown className="h-6 w-6 stroke-[2.5]" />
                    ) : (
                      <Minus className="h-6 w-6 stroke-[2.5]" />
                    )}
                  </div>
                  <div>
                    <span className="text-[11px] font-medium uppercase tracking-wider opacity-80">
                      Tín hiệu chu kỳ T+3
                    </span>
                    <h3 className="text-lg font-bold tracking-tight sm:text-xl">
                      {activePred?.signal || "NẮM GIỮ (HOLD)"}
                    </h3>
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Xu hướng phân loại:</span>
                    <span className="font-semibold text-slate-200">
                      {activePred?.class_name || "ĐI NGANG"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Dữ liệu chốt phiên căn cứ:</span>
                    <span className="font-mono text-slate-200">
                      {activePred?.data_as_of_date || activePred?.date || "---"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Thị giá đóng cửa phiên t:</span>
                    <span className="font-mono font-semibold text-slate-200">
                      {activePred
                        ? (activePred.current_price * 1000).toLocaleString("vi-VN")
                        : "---"}{" "}
                      VNĐ
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-400">Độ tin cậy mô hình:</span>
                    <span className="font-mono font-semibold text-blue-400">{confidencePct}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Cột phải: Phân phối Xác suất Softmax 3 Lớp (7 cột) */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 lg:col-span-7 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Phân phối xác suất 3 lớp
                </span>
                <button
                  onClick={() => setShowInfo(!showInfo)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {showInfo && (
              <div className="mb-4 rounded-md bg-slate-950 p-3 text-xs text-slate-300 border border-slate-800 leading-relaxed">
                <p>
                  Mô hình AI dự báo xác suất 3 kịch bản trong chu kỳ T+3: <strong>TĂNG</strong> (kỳ vọng lãi &gt; 1.5%), <strong>GIẢM</strong> (nguy cơ lỗ &gt; 1.5%) hoặc <strong>ĐI NGANG</strong>. Tổng xác suất bằng 100%. Kịch bản có xác suất cao nhất sẽ đưa ra khuyến nghị Mua, Bán hoặc Nắm giữ an toàn cho nhà đầu tư cá nhân.
                </p>
              </div>
            )}

            {/* 3 Thanh tiến trình xác suất */}
            <div className="space-y-3.5">
              {/* Lớp TĂNG */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium mb-1">
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <TrendingUp className="h-3.5 w-3.5" /> Xu hướng TĂNG (Up)
                  </span>
                  <span className="font-mono font-bold text-emerald-400">
                    {(probUp * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${Math.max(probUp * 100, 2)}%` }}
                  />
                </div>
              </div>

              {/* Lớp ĐI NGANG */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium mb-1">
                  <span className="flex items-center gap-1.5 text-amber-400">
                    <Minus className="h-3.5 w-3.5" /> Xu hướng ĐI NGANG (Neutral)
                  </span>
                  <span className="font-mono font-bold text-amber-400">
                    {(probHold * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-amber-500 transition-all duration-300"
                    style={{ width: `${Math.max(probHold * 100, 2)}%` }}
                  />
                </div>
              </div>

              {/* Lớp GIẢM */}
              <div>
                <div className="flex items-center justify-between text-xs font-medium mb-1">
                  <span className="flex items-center gap-1.5 text-rose-400">
                    <TrendingDown className="h-3.5 w-3.5" /> Xu hướng GIẢM (Down)
                  </span>
                  <span className="font-mono font-bold text-rose-400">
                    {(probDown * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-rose-500 transition-all duration-300"
                    style={{ width: `${Math.max(probDown * 100, 2)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 border-t border-slate-800/80 pt-3 flex items-center justify-between text-xs text-slate-400">
            <span>Mô hình đang chạy: <strong className="text-slate-200">{modelType.toUpperCase()}</strong></span>
            <span className="text-[11px] text-slate-500">Đã kiểm định OOS Thực chiến</span>
          </div>
        </div>
      </div>

      {/* 2.5. Biểu đồ Nến Kỹ thuật & Quỹ đạo Dự phóng Xu hướng T+1 -> T+3 chuẩn FireAnt */}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <div className="mb-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-100 sm:text-base">
              Biểu đồ Nến & Quỹ đạo Dự phóng Xu hướng (T+1 → T+3)
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            Mô phỏng chu kỳ thanh toán T+2.5 và đường cong kỳ vọng giá AI ({modelType.toUpperCase()})
          </span>
        </div>

        {/* Biểu đồ Nến Kỹ thuật & Quỹ đạo Dự phóng Xu hướng T+1 -> T+3 chuẩn FireAnt */}
        <FireAntTrajectoryChart
          symbol={selectedSymbol}
          bars={chartBars}
          prediction={activePred}
          modelType={modelType}
          height={460}
        />
      </div>

      {/* 3. Bảng Nhật ký Lịch sử Dự báo & Tín hiệu Mô hình */}
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-slate-100 sm:text-base">
                Nhật ký Lịch sử Dự báo & Phân tích Mô hình
              </h3>
            </div>
            <p className="text-[11px] text-slate-400">
              Tự động lưu vết các lần chọn cổ phiếu, thời điểm phân tích và khuyến nghị của mô hình AI •{" "}
              <span className="text-emerald-400 font-medium">Nhấn vào dòng bất kỳ để mở biểu đồ nến</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300">
              {history.length} bản ghi
              {history.length > 10 && (
                <span className="ml-1 text-[10px] font-normal text-blue-400">
                  • Cuộn xem thêm
                </span>
              )}
            </span>
            {history.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="flex items-center gap-1 rounded border border-rose-500/30 bg-rose-500/10 px-2.5 py-1 text-[11px] font-semibold text-rose-300 hover:bg-rose-500/20 hover:text-rose-200 transition-all"
                title="Xóa toàn bộ lịch sử dự báo đã lưu"
              >
                <Trash2 className="h-3 w-3" />
                <span>Xóa lịch sử</span>
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto overflow-y-auto max-h-[515px] rounded-lg border border-slate-800/80 [scrollbar-width:thin] [scrollbar-color:#334155_#090d16]">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/95 backdrop-blur-md text-slate-400 shadow-sm">
              <tr>
                <th className="px-3 py-2.5 font-semibold">Thời điểm</th>
                <th className="px-3 py-2.5 font-semibold">Mã CP</th>
                <th className="px-3 py-2.5 font-semibold">Mô hình</th>
                <th className="px-3 py-2.5 font-semibold">Nến căn cứ</th>
                <th className="px-3 py-2.5 font-semibold">Thị giá</th>
                <th className="px-3 py-2.5 font-semibold">Tín hiệu Khuyến nghị</th>
                <th className="px-3 py-2.5 font-semibold">Xác suất Tăng</th>
                <th className="px-3 py-2.5 font-semibold">Xác suất Giảm</th>
                <th className="px-3 py-2.5 font-semibold">Độ tin cậy</th>
                <th className="px-3 py-2.5 text-right font-semibold">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {history.length > 0 ? (
                history.map((item) => {
                  const isItemBuy = item.signal.includes("MUA") || item.signal.includes("BUY");
                  const isItemSell = item.signal.includes("BÁN") || item.signal.includes("SELL");

                    return (
                      <tr
                        key={item.id}
                        onClick={() => {
                          onSelectSymbol(item.symbol);
                          setDetailModalItem({
                            symbol: item.symbol,
                            currentValue: item.current_price,
                            isIndex: item.symbol.includes("VNINDEX") || item.symbol.includes("VN30"),
                          });
                          setIsDetailModalOpen(true);
                        }}
                        title={`Nhấn để mở biểu đồ nến chi tiết của ${item.symbol}`}
                        className={`group cursor-pointer transition-colors ${selectedSymbol === item.symbol
                          ? "bg-emerald-500/10 hover:bg-emerald-500/15"
                          : "hover:bg-slate-800/60"
                          }`}
                      >
                        <td className="px-3 py-3 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <Clock className="h-3 w-3 text-slate-500" />
                            <span>{item.timestamp}</span>
                          </div>
                        </td>
                        <td className="px-3 py-3 font-bold text-slate-100 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-emerald-400" />
                            <span className="font-mono group-hover:text-emerald-400 transition-colors">
                              {item.symbol}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] font-bold border ${item.model_type === "lightgbm"
                              ? "border-blue-500/30 bg-blue-500/10 text-blue-300"
                              : "border-sky-500/30 bg-sky-500/10 text-sky-300"
                              }`}
                          >
                            {item.model_type === "lightgbm" ? (
                              <Cpu className="h-2.5 w-2.5" />
                            ) : (
                              <Brain className="h-2.5 w-2.5" />
                            )}
                            {item.model_type.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-3 py-3 font-mono text-slate-300 whitespace-nowrap">
                          {item.data_date}
                        </td>
                        <td className="px-3 py-3 font-mono font-semibold text-slate-200 whitespace-nowrap">
                          {(item.current_price * 1000).toLocaleString("vi-VN")} đ
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-bold ${isItemBuy
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
                            {item.signal}
                          </span>
                        </td>
                        <td className="px-3 py-3 font-mono text-emerald-400 whitespace-nowrap">
                          {(item.prob_up * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-3 font-mono text-rose-400 whitespace-nowrap">
                          {(item.prob_down * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-3 font-mono font-semibold text-blue-400 whitespace-nowrap">
                          {(item.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="px-3 py-3 text-right whitespace-nowrap">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectSymbol(item.symbol);
                              onChangeModelType(item.model_type);
                            }}
                            className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-semibold text-slate-200 hover:border-blue-500 hover:bg-blue-600 hover:text-white transition-colors"
                            title={`Nạp lại dự báo mã ${item.symbol} (${item.model_type.toUpperCase()})`}
                          >
                            <span>Xem lại</span>
                          </button>
                        </td>
                      </tr>
                    );
                })
              ) : (
                <tr>
                  <td colSpan={10} className="px-3 py-8 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-1.5">
                      <Clock className="h-5 w-5 text-slate-600" />
                      <p className="text-xs font-medium text-slate-400">
                        Chưa có lịch sử phân tích
                      </p>
                      <p className="text-[11px] text-slate-500">
                        Mỗi khi bạn chọn một mã cổ phiếu hoặc thay đổi mô hình, kết quả dự báo sẽ tự động được ghi lại tại đây.
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cửa sổ Modal Đặc tả Mô hình Định lượng (Nền tối & mờ, hiển thị chính diện trước mặt người dùng) */}
      {activeTooltipModel && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200"
          onClick={() => {
            setActiveTooltipModel(null);
            setHoveredModel(null);
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-xl max-h-[90vh] flex flex-col rounded-lg border border-slate-700 bg-slate-900 shadow-xl overflow-hidden"
          >
            {/* Header Modal */}
            <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg ${activeTooltipModel === "lightgbm"
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                    : "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                    }`}
                >
                  {activeTooltipModel === "lightgbm" ? (
                    <Cpu className="h-5 w-5" />
                  ) : (
                    <Brain className="h-5 w-5" />
                  )}
                </div>
                <div>
                  <h3 className="font-bold text-slate-100 text-base leading-tight">
                    {MODEL_SPECIFICATIONS[activeTooltipModel].title}
                  </h3>
                  <span className="inline-block mt-1 rounded px-2.5 py-0.5 text-[11px] font-semibold border border-slate-700 bg-slate-800 text-slate-300">
                    {MODEL_SPECIFICATIONS[activeTooltipModel].badge}
                  </span>
                </div>
              </div>
              <button
                onClick={() => {
                  setActiveTooltipModel(null);
                  setHoveredModel(null);
                }}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
                title="Đóng cửa sổ (hoặc bấm Esc / bấm vùng ngoài)"
              >
                <span className="text-xl font-bold leading-none">&times;</span>
              </button>
            </div>

            {/* Body Modal (Cuộn mượt mà nếu màn hình nhỏ) */}
            <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)] text-xs text-slate-200">
              {/* 1. Mô hình này là mô hình gì? */}
              <div className="rounded-md border border-slate-800 bg-slate-950/60 p-3.5">
                <div className="flex items-center gap-2 font-bold text-slate-100 mb-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded bg-blue-500/20 text-xs text-blue-300 font-mono font-bold">
                    1
                  </span>
                  <span className="text-sm">Mô hình này là gì? (Cách hiểu đơn giản)</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-300 pl-7">
                  {MODEL_SPECIFICATIONS[activeTooltipModel].overview}
                </p>
              </div>

              {/* 2. Tác dụng ngắn gọn */}
              <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-3.5">
                <div className="flex items-center gap-2 font-bold text-slate-100 mb-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-xs text-indigo-300 font-mono font-bold">
                    2
                  </span>
                  <span className="text-sm">Tác dụng ngắn gọn của mô hình:</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-300 pl-7">
                  {MODEL_SPECIFICATIONS[activeTooltipModel].purpose}
                </p>
              </div>

              {/* 3. Khi nào nên chọn mô hình này? */}
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-3.5">
                <div className="flex items-center gap-2 font-bold text-emerald-400 mb-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/30 text-xs text-emerald-300 font-mono font-bold">
                    3
                  </span>
                  <span className="text-sm">Lúc nào bạn nên chọn mô hình này?</span>
                </div>
                <p className="text-xs leading-relaxed text-emerald-200 pl-7 font-medium">
                  {MODEL_SPECIFICATIONS[activeTooltipModel].whenToUse}
                </p>
              </div>

              {/* 4. Dấu hiệu thực tế nhận biết trên bảng điện */}
              <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-3.5">
                <div className="flex items-center gap-2 font-bold text-amber-300 mb-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-xs text-amber-400 font-mono font-bold">
                    4
                  </span>
                  <span className="text-sm">{MODEL_SPECIFICATIONS[activeTooltipModel].signsTitle}</span>
                </div>
                <div className="space-y-2 pl-7">
                  {MODEL_SPECIFICATIONS[activeTooltipModel].signs.map((sign, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 text-xs text-slate-300 bg-slate-900/90 border border-slate-800 rounded-lg p-2.5"
                    >
                      <span className="text-amber-400 font-bold shrink-0 mt-0.5">✔</span>
                      <span className="leading-relaxed">{sign}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Tip Footer Box */}
              <div className="rounded-md border border-blue-500/20 bg-slate-950 p-3 text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5">
                <span className="font-semibold text-blue-200">💡 Quy tắc ghi nhớ nhanh:</span>
                <span className="font-medium text-slate-300">
                  Thị trường Sideway / Lướt ngắn ➔ <strong className="text-blue-300">LightGBM</strong> | Vào Sóng mạnh / Trend ➔ <strong className="text-sky-300">LSTM</strong>
                </span>
              </div>
            </div>

            {/* Footer Modal với các nút hành động */}
            <div className="border-t border-slate-800 bg-slate-950/80 px-6 py-3.5 flex flex-wrap items-center justify-between gap-3">
              <span className="text-[11px] text-slate-500 italic">
                Bấm phím Esc hoặc bấm ra ngoài màn hình để đóng
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setActiveTooltipModel(null);
                    setHoveredModel(null);
                  }}
                  className="rounded-md border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                >
                  Đã hiểu & Đóng
                </button>
                {modelType !== activeTooltipModel ? (
                  <button
                    onClick={() => {
                      setLocalPrediction(null);
                      onChangeModelType(activeTooltipModel);
                      setActiveTooltipModel(null);
                      setHoveredModel(null);
                    }}
                    className="flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 transition-colors"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Chuyển sang dùng mô hình này</span>
                  </button>
                ) : (
                  <span className="flex items-center gap-1.5 text-xs text-blue-400 font-semibold px-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Đang áp dụng mô hình này
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal chi tiết kỹ thuật chuẩn hóa */}
      <FinancialDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        item={detailModalItem}
      />
    </div>
  );
};
