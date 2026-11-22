"""Fail before accepting work when the training service cannot publish artifacts."""
import os
from pathlib import Path
import tempfile


def verify_training_storage(root: Path = Path('/app/apps/ml')) -> None:
    if not os.environ.get('INTERNAL_WORKER_SECRET'):
        raise RuntimeError('Training service requires INTERNAL_WORKER_SECRET.')
    for relative in ('models', 'data/raw', 'data/interim', 'data/processed'):
        directory = root / relative
        directory.mkdir(parents=True, exist_ok=True)
        # Check actual bind-mount permissions as the configured unprivileged UID.
        with tempfile.TemporaryFile(dir=directory) as probe:
            probe.write(b'write-check')
            probe.flush()


if __name__ == '__main__':
    verify_training_storage()
    os.execvp('uvicorn', ['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'])
