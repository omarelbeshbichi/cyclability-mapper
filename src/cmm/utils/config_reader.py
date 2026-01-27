import yaml
import json
from pathlib import Path
from typing import Any
from ruamel.yaml import YAML

def read_config(index_name: str,
                file_type: str,
                config_path: str) -> dict:
    """
    Read a YAML configuration file and return its contents as a dictionary

    Parameters
    ----------
    index_name: str
        Name of the configuration (used for error messages)
    file_type: str
        File extension (e.g., "json")
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

    # Load config and return

    if file_type == "yaml":
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    elif file_type == "json":
        with open(config_path, "r") as f:
            return json.load(f)
    else:
        return {}
    

def add_config_data(feature_name: str,
                    feature_value: str,
                    feature_score: float,
                    metrics_config_path: str) -> None:
    """
    Add feature line (feature_name: feature_score) in config YAML file.

    Categorical feature is assumed.
    """

    # Using here ruamel.yaml package to preserve YAML layout
    yaml = YAML()
    yaml.preserve_quotes = True

    # Read YAML file and save content in dict
    with open(metrics_config_path, "r", encoding="utf-8") as f:
        config = yaml.load(f)

    # Check if feature_name is legal
    if feature_name not in config:
        raise KeyError(f"Index '{feature_name}' not found in config")
    
    # Define YAML part related to feature_name in dedicated cfg
    # It's not a copy! It's a reference -> you can later save directly config back to YAML
    feature_cfg = config[feature_name]

    # Check if type is categorical
    if feature_cfg.get("type") != "categorical":
        raise ValueError(f"Index '{feature_cfg}' is not categorical")
    
    # Add new line to mapping 
    feature_cfg["mapping"][feature_value] = float(feature_score)

    # Save
    with open(metrics_config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)