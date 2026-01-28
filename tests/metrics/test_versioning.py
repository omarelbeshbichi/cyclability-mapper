from city_metrics.metrics.config.versioning import get_config_version
from city_metrics.utils.misc import get_project_root


def test_get_config_version():

    root = get_project_root()
    yaml_path = root / "tests/_fixtures/test_yaml.yaml"
    assert get_config_version(yaml_path) == "v1.0.0-8850e607"