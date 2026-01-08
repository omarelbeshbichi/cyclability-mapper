import yaml
from pathlib import Path


def read_config(index_name: str,
                config_path: str) -> dict:
    """
    Read a YAML configuration file and return its contents as a dictionary

    Parameters
    ----------
    index_name: str
        Name of the configuration (used for error messages)
    config_path: str
        Path to the YAML configuration file

    Returns
    -------
    dict
        Parsed configuration from the YAML file
    """

    config_path = Path(config_path) 
    # Path check
    if not config_path.exists():
        raise FileNotFoundError(f"Could not find {index_name} config file at {config_path}")

    # Load YAML and return
    with open(config_path, "r") as f:
        return yaml.safe_load(f)