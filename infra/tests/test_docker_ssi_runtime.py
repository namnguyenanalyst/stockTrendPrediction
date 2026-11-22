"""SSI credentials belong in runtime environment, never baked into the image."""
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('relative',['docker-compose.yml','infra/docker-compose.yml'])
def test_api_receives_ssi_runtime_configuration(relative):
    config = yaml.safe_load((ROOT / relative).read_text())
    api = config['services']['vn_stock_api']
    environment = api['environment']
    assert environment.get('SSI_CONSUMER_ID') == '${SSI_CONSUMER_ID:-}'
    assert environment.get('SSI_CONSUMER_SECRET') == '${SSI_CONSUMER_SECRET:-}'
    assert environment.get('SSI_API_URL') == '${SSI_API_URL:-https://fc-data.ssi.com.vn/}'
    build = api['build']
    assert 'SSI_CONSUMER_SECRET' not in build.get('args',{})
