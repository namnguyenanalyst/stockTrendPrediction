"""Immutable artifact generations committed by a single atomic manifest replacement."""

import hashlib
import json
from pathlib import Path
import shutil
from uuid import uuid4

from vn_stock.config import SYMBOL_TO_CODE
from vn_stock.features import ALL_FEATURE_COLS, FEATURE_COLS


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_names(names, horizon):
    required = {f"production_scaler_t{horizon}.pkl", f"production_lstm_t{horizon}.pth",
                f"production_training_info_t{horizon}.json"}
    model_names = {f"production_lgb_t{horizon}.txt", f"production_lgb_t{horizon}.pkl"}
    if not required.issubset(names) or not model_names.intersection(names):
        raise ValueError("Incomplete model/scaler/metadata bundle.")


def publish_bundle(models_dir: Path, horizon: int, writers: dict, metadata: dict) -> Path:
    """Only expose a generation once every model, scaler and metadata file is written."""
    models_dir = Path(models_dir)
    generation = models_dir / "runs" / uuid4().hex
    generation.mkdir(parents=True)
    manifest_path = models_dir / f"production_bundle_t{horizon}.json"
    temporary = manifest_path.with_name(f".{manifest_path.name}.{uuid4().hex}.tmp")
    try:
        for name, write in writers.items():
            if Path(name).name != name:
                raise ValueError("Artifact name must be a filename.")
            write(generation / name)
        info_name = f"production_training_info_t{horizon}.json"
        (generation / info_name).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        files = {p.name: {"path": str(p.relative_to(models_dir)), "sha256": _digest(p)}
                 for p in generation.iterdir()}
        _validate_names(files, horizon)
        manifest = {"schema_version": 1, "horizon_days": horizon,
                    "feature_cols": FEATURE_COLS, "all_feature_cols": ALL_FEATURE_COLS,
                    "symbol_to_code": SYMBOL_TO_CODE, "files": files}
        temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        temporary.replace(manifest_path)
    except Exception:
        shutil.rmtree(generation, ignore_errors=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return manifest_path


def resolve_bundle(models_dir: Path, horizon: int) -> dict[str, Path]:
    """Resolve one snapshot; never fall back to loose files if its manifest is broken."""
    models_dir = Path(models_dir).resolve()
    manifest = json.loads((models_dir / f"production_bundle_t{horizon}.json").read_text())
    if (manifest.get("schema_version") != 1 or manifest.get("horizon_days") != horizon
            or manifest.get("feature_cols") != FEATURE_COLS
            or manifest.get("all_feature_cols") != ALL_FEATURE_COLS
            or manifest.get("symbol_to_code") != SYMBOL_TO_CODE):
        raise ValueError("Artifact bundle schema/horizon mismatch.")
    _validate_names(manifest["files"], horizon)
    paths = {}
    for name, record in manifest["files"].items():
        path = (models_dir / record["path"]).resolve()
        if not path.is_relative_to(models_dir / "runs") or path.name != name:
            raise ValueError("Invalid artifact path in manifest.")
        if _digest(path) != record["sha256"]:
            raise ValueError(f"Artifact hash mismatch: {name}")
        paths[name] = path
    if len({path.parent for path in paths.values()}) != 1:
        raise ValueError("Artifact paths belong to different generations.")
    return paths
