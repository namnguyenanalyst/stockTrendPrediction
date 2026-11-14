"""Offline temporal holdout: fit/select before cutoff, score only later matured labels."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from vn_stock.config import MODELS_DIR
from vn_stock.features import (
    ALL_FEATURE_COLS,
    compute_features_per_symbol,
    create_multivariate_sequences,
    transform_model_features,
)
from vn_stock.modeling.predict import load_prediction_snapshot
from vn_stock.modeling.train import evaluate_predictions, train_production_model
from vn_stock.splitting_data import apply_study_window, create_multi_day_labels, get_warmup_tail


@dataclass(frozen=True)
class EvaluationConfig:
    cutoff_date: str
    end_date: str
    horizon: int = 3
    threshold: float = 0.02
    val_buffer_days: int = 40
    seq_length: int = 20
    epochs: int = 40

    def __post_init__(self):
        if min(self.horizon, self.val_buffer_days, self.seq_length, self.epochs) < 1:
            raise ValueError("Evaluation sizes must be positive.")
        if self.threshold < 0:
            raise ValueError("Threshold must be nonnegative.")


def prepare_temporal_holdout(panel: pd.DataFrame, config: EvaluationConfig):
    cutoff, end = pd.Timestamp(config.cutoff_date), pd.Timestamp(config.end_date)
    if cutoff >= end or config.horizon < 1:
        raise ValueError("Holdout end must follow cutoff; horizon must be positive.")
    panel = panel.copy()
    panel["Date"] = pd.to_datetime(panel["Date"])
    panel = panel[panel.Date <= end].sort_values(["Date", "Symbol"]).reset_index(drop=True)
    if panel.duplicated(["Date", "Symbol"]).any():
        raise ValueError("Duplicate Date/Symbol observations.")
    features = compute_features_per_symbol(panel, drop_na=True)
    labeled = create_multi_day_labels(apply_study_window(features), config.horizon, config.threshold)
    test = labeled[labeled.Date > cutoff].copy()
    if test.empty:
        raise ValueError("No matured labels strictly after the model cutoff.")
    return panel[panel.Date <= cutoff].copy(), features, test


def _predict_symbol(model, scaler, features, test, config, model_type):
    scaled = transform_model_features(test, scaler)
    if model_type == "lightgbm":
        return model.predict_proba(scaled[ALL_FEATURE_COLS]) if hasattr(model, "predict_proba") else model.predict(scaled[ALL_FEATURE_COLS])
    import torch
    warm = features[(features.Symbol == test.Symbol.iloc[0]) & (features.Date < test.Date.min())]
    warm = transform_model_features(get_warmup_tail(warm, config.seq_length), scaler)
    sequences, _ = create_multivariate_sequences(scaled, warm, ALL_FEATURE_COLS, config.seq_length)
    if len(sequences) != len(test):
        raise ValueError("Insufficient pre-test history for LSTM; do not pad future data.")
    with torch.no_grad():
        inputs = torch.from_numpy(sequences).to(next(model.parameters()).device)
        return model.predict_proba(inputs).cpu().numpy()


def run_temporal_evaluation(panel, output_dir: Path, config: EvaluationConfig) -> dict:
    """Train both models in an isolated directory; never promote an evaluation run."""
    output_dir = Path(output_dir).resolve()
    production = MODELS_DIR.resolve()
    if output_dir == production or output_dir.is_relative_to(production):
        raise ValueError("Evaluation outputs must be outside production models.")
    train_panel, features, test = prepare_temporal_holdout(panel, config)
    output_dir.mkdir(parents=True, exist_ok=False)
    artifact_dir = output_dir / "artifacts"
    summary = train_production_model(
        symbols=sorted(train_panel.Symbol.unique()), horizon=config.horizon,
        threshold=config.threshold, val_buffer_days=config.val_buffer_days,
        epochs=config.epochs, seq_length=config.seq_length,
        models_dir=artifact_dir, raw_panel=train_panel,
    )
    majority = int(np.argmax(summary["train_class_counts"]))
    records, metrics = [], {}
    for kind in ("lightgbm", "lstm"):
        model, scaler, info = load_prediction_snapshot(kind, artifact_dir, config.horizon)
        if pd.Timestamp(info["latest_market_date"]) >= test.Date.min():
            raise ValueError("Artifact vintage overlaps the held-out test period.")
        truth, predicted = [], []
        for symbol, group in test.groupby("Symbol", sort=True):
            group = group.sort_values("Date")
            probs = _predict_symbol(model, scaler, features, group, config, kind)
            labels = np.argmax(probs, axis=1)
            truth.extend(group.Label.tolist())
            predicted.extend(labels.tolist())
            records.extend({"model": kind, "symbol": symbol, "date": str(row.Date.date()),
                            "label": int(row.Label), "prediction": int(label),
                            "probabilities": probability.tolist()}
                           for row, label, probability in zip(group.itertuples(), labels, probs))
        metrics[kind] = evaluate_predictions(np.array(truth), np.array(predicted))
    metrics["train_majority_baseline"] = evaluate_predictions(
        test.Label.to_numpy(), np.full(len(test), majority),
    )
    report = {"evaluation_role": "temporal_holdout", "config": asdict(config),
              "data_sha256": hashlib.sha256(pd.util.hash_pandas_object(
                  panel.sort_values(["Date", "Symbol"]), index=False).values.tobytes()).hexdigest(),
              "test_start_date": str(test.Date.min().date()),
              "test_end_date": str(test.Date.max().date()), "test_samples": len(test),
              "training_info": summary, "metrics": metrics,
              "limitations": ["Current constituent universe; not survivorship-adjusted.",
                              "Classification holdout; not a claim of tradable profitability."]}
    (output_dir / "predictions.json").write_text(json.dumps(records, indent=2))
    (output_dir / "evaluation.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    from vn_stock.data_ingestion import load_panel_dataset
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=40)
    args = parser.parse_args()
    result = run_temporal_evaluation(load_panel_dataset(), args.output,
                                    EvaluationConfig(args.cutoff, args.end, epochs=args.epochs))
    print(json.dumps(result["metrics"], indent=2))
