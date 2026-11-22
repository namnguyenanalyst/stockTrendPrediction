import pytest
from vn_stock.modeling.train import ValidationEarlyStopping


def test_early_stopping_counts_only_consecutive_non_improvement():
    stop = ValidationEarlyStopping(patience=2)
    assert stop.observe(1.0) is False
    assert stop.observe(1.1) is False
    assert stop.observe(.9) is False
    assert stop.observe(.9) is False
    assert stop.observe(1.2) is True
    assert stop.best_loss == .9


def test_early_stopping_rejects_invalid_losses_and_patience():
    with pytest.raises(ValueError):
        ValidationEarlyStopping(patience=0)
    for loss in [float('nan'),float('inf')]:
        with pytest.raises(ValueError):
            ValidationEarlyStopping(patience=2).observe(loss)


def test_training_actually_stops_and_records_actual_epoch_count(tmp_path, monkeypatch):
    import numpy as np
    import pandas as pd
    import torch
    from torch.nn import functional as functional
    from vn_stock.modeling.train import train_production_model
    rng = np.random.default_rng(42)
    close = 50 + rng.normal(size=260)
    panel = pd.DataFrame({'Date':pd.bdate_range('2023-01-02',periods=260), 'Symbol':'VIC',
                          'Open':close, 'High':close+2, 'Low':close-2, 'Close':close,
                          'Volume':1000000., 'VNINDEX_Return_1d':0.005})
    original = functional.cross_entropy
    def fixed_validation_loss(*args, **kwargs):
        if kwargs.get('reduction') == 'sum':
            return torch.tensor(1.,device=args[0].device)
        return original(*args, **kwargs)
    monkeypatch.setattr(functional,'cross_entropy',fixed_validation_loss)
    result = train_production_model(symbols=['VIC'],raw_panel=panel,models_dir=tmp_path,
                                    seq_length=5,val_buffer_days=10,epochs=10,
                                    lstm_patience=2,save_artifacts=False)
    assert result['epochs_requested'] == 10
    assert result['epochs_completed'] == 3
    assert result['best_lstm_epoch'] == 1
    assert result['lstm_early_stopping_patience'] == 2
    assert not list(tmp_path.iterdir())
