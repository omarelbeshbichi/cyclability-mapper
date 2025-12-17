import yaml
from .misc import get_project_root

def read_config(index_name: str) -> dict:
    """
    Text

    Parameters
    ----------
    index_name: str
        Name of index to be processed
            - 'cyclability'
            - 'etc'
    
    Returns
    -------
    config_dict: dict
        Dictionary containing configuration parameters

    """

    # Retrieve paths
    root_path = get_project_root()
    config_path = root_path  / 'src' / 'cmm' / 'scoring' / 'config' / f"{index_name}.yaml"

    # Path check
    if not config_path.exists():
        raise FileNotFoundError(f'Could not find {index_name} config file at {config_path}')

    # Load YAML and return
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)