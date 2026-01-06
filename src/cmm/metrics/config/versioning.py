import hashlib
import yaml

def get_config_version(yaml_path: str) -> str:
    """
    Generate a version string for a YAML configuration file.

    The version combines the 'version' field in the YAML (default '0.0.0') 
    with a short SHA-256 hash of the canonical YAML content.

    Parameters
    ----------
    yaml_path: str
        Path to the YAML configuration file

    Returns
    -------
    str
        Version string in the format "v<version>-<hash>", where <hash> is 
        the first 8 characters of the SHA-256 hash of the YAML content
    """
    
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    v_prefix = config.get('version', '0.0.0') # default: 0.0.0

    # Determine hash of yaml from 
    canonical_yaml = yaml.dump(config, sort_keys=True).encode("utf-8")
    full_hash = hashlib.sha256(canonical_yaml).hexdigest()

    # Final metric version as string
    final_version = f"v{v_prefix}-{full_hash[:8]}"

    return final_version