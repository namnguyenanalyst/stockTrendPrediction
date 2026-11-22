"""The shared package must pin the sklearn serialization runtime for both apps."""
from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def test_shared_sklearn_runtime_matches_existing_serving_artifacts():
    root=Path(__file__).resolve().parents[2]
    project=tomllib.loads((root/'apps/ml/pyproject.toml').read_text())
    requirements=project['project']['dependencies']
    assert 'scikit-learn==1.7.2' in requirements
    api=tomllib.loads((root/'apps/api/pyproject.toml').read_text())
    assert 'vn-stock' in api['project']['dependencies']
    assert api['tool']['uv']['sources']['vn-stock']['path']=='../ml'
