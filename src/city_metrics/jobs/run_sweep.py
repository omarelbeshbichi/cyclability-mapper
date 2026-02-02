import click
import logging

@click.command()
@click.option("--city", "--city-name", "city_name", type = str, required = True)
@click.option("--group", "target_group", type = str, required = True)
@click.option("--delta", "delta_range", type = float, required = True)
def main(city_name, target_group, delta_range):

    from city_metrics.services.analysis.sensitivity import sensitivity_single_weight_sweep
    from city_metrics.utils.misc import get_project_root
    from city_metrics.data.export.postgres import delete_city_rows
    from city_metrics.utils.config_helpers import read_config
    
    root = get_project_root()

    weights_config_path = root / "src/city_metrics/metrics/config/weights.yaml"
    metrics_config_path = root / "src/city_metrics/metrics/config/cyclability.yaml"

    # Get config info
    #(remove version info from resulting dict)
    weights_config = read_config("weights", "yaml", weights_config_path)
    weights_config.pop("version")

    # Define groups to sweep - either the one provided as input or all if "all" is given
    if target_group.lower() == "all":
        groups_to_sweep = list(weights_config["cyclability"].keys())
    else:
        groups_to_sweep = [target_group]

    # Perform sweep
    for group_name in groups_to_sweep:
        sensitivity_single_weight_sweep(
            city_name = city_name,
            target_group= group_name,
            delta_range = delta_range,
            weights_config_path = weights_config_path,
            metrics_config_path = metrics_config_path
        )
    
    logging.info("DONE")
if __name__ == "__main__":
    main()