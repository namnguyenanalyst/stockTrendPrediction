import type { DayForecast, PredictionResponse, StockBar } from './types';
import { matchesPrediction } from './predictionPresentation';
export interface TrajectoryStepPoint {
  date: string;
  dayName: string;
  price: number;
  changePct: number;
  trend: "TĂNG" | "ĐI NGANG" | "GIẢM";
  confidence: number;
  signal: string;
}


export function normalizePredictionDate(value: string | undefined): string | null {
 if (!value || !/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(value)) return null;
 const date=value.slice(0,10);const parsed=new Date(`${date}T00:00:00Z`);
 return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0,10)===date ? date : null;
}
export function trajectoryProblem(prediction: PredictionResponse | null, symbol: string, model: string, lastBar?: StockBar): string | null {
 if (!lastBar) return 'Chưa có nến giá để vẽ kịch bản.';
 if (!matchesPrediction(prediction,symbol,model) || !prediction) return 'Chưa có dự báo hợp lệ để vẽ kịch bản.';
 const base=normalizePredictionDate(prediction.data_as_of_date || prediction.date);
 if (!base || base!==normalizePredictionDate(lastBar.date)) return `Ngày dữ liệu chưa khớp: dự báo ${prediction.data_as_of_date || prediction.date}, nến ${lastBar.date}. Hãy làm mới dữ liệu.`;
 if (!Number.isFinite(lastBar.close) || lastBar.close<=0 || Math.abs(lastBar.close-prediction.current_price)>.011) return 'Giá gốc dự báo chưa khớp với nến. Hãy làm mới dữ liệu.';
 if (prediction.trajectory?.length!==3) return 'Kịch bản chưa đủ ba phiên T+1, T+2, T+3.';
 let previous=base;
 for (const [index,step] of prediction.trajectory.entries()) {
  const date=normalizePredictionDate(step.date);
  if (!date || date<=previous || step.day_offset!==index+1 || !['GIẢM','ĐI NGANG','TĂNG'].includes(step.predicted_trend)
    || !Number.isFinite(step.confidence) || step.confidence<0 || step.confidence>1
    || !step.probabilities || !['GIẢM','ĐI NGANG','TĂNG'].every(k=>Number.isFinite(step.probabilities[k])&&step.probabilities[k]>=0&&step.probabilities[k]<=1)
    || Math.abs(Object.values(step.probabilities).reduce((a,b)=>a+b,0)-1)>.01) return 'Dữ liệu kịch bản không hợp lệ. Hãy thử tải lại.';
  previous=date;
 }
 return null;
}
export function buildTrajectory(prediction: PredictionResponse | null, symbol: string, model: string, lastBar?: StockBar): TrajectoryStepPoint[] {
 if (trajectoryProblem(prediction,symbol,model,lastBar) || !prediction || !lastBar) return [];
    const basePrice = lastBar.close;
    const baseDate = normalizePredictionDate(lastBar.date)!;

    const trajectory = prediction.trajectory!;
    const points: TrajectoryStepPoint[] = [];

    // Điểm gốc: Phiên T (Nến hiện tại)
    points.push({
      date: baseDate,
      dayName: "Phiên T (Hiện tại)",
      price: basePrice,
      changePct: 0,
      trend: "ĐI NGANG",
      confidence: 1.0,
      signal: "CHỐT PHIÊN",
    });

    let currentPrice = basePrice;

    // Duyệt qua 3 bước T+1, T+2, T+3
    for (let i = 0; i < 3; i++) {
      const step: DayForecast | undefined = trajectory[i];
      const dayName = step?.day_name || `T+${i + 1}`;
      const trend = step?.predicted_trend || (prediction?.class_name as "TĂNG" | "ĐI NGANG" | "GIẢM") || "ĐI NGANG";
      const confidence = step?.confidence ?? 0;
      const signal = step?.signal || "NẮM GIỮ (HOLD)";

      // Xác định ngày tương lai hợp lệ (phải lớn hơn ngày trước đó)
      const stepDate = normalizePredictionDate(step!.date)!;

      // Tính toán tỷ lệ biến động giá dự kiến dựa trên xu hướng và xác suất
      let driftPct = 0;
      if (trend === "TĂNG") {
        driftPct = 0.012 + (confidence - 0.33) * 0.02; // Tăng +1.4% đến +2.2%
      } else if (trend === "GIẢM") {
        driftPct = -(0.012 + (confidence - 0.33) * 0.02); // Giảm -1.4% đến -2.2%
      } else {
        const pUp = step?.probabilities?.["TĂNG"] ?? 0.33;
        const pDown = step?.probabilities?.["GIẢM"] ?? 0.33;
        driftPct = (pUp - pDown) * 0.008; // Đi ngang giằng co quanh biên hẹp
      }

      currentPrice = parseFloat((currentPrice * (1 + driftPct)).toFixed(2));
      const totalChangePct = parseFloat(
        (((currentPrice - basePrice) / basePrice) * 100).toFixed(2)
      );

      points.push({
        date: stepDate,
        dayName,
        price: currentPrice,
        changePct: totalChangePct,
        trend,
        confidence,
        signal,
      });
    }

    return points;
}
