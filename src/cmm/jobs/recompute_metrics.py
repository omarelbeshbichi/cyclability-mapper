import click

@click.command()
def main():

    from cmm.services.metrics.compute import recompute_metrics_from_postgis
    from cmm.utils.misc import get_project_root

    root = get_project_root()

    recompute_metrics_from_postgis(
        weights_config_path = root  / "src/cmm/metrics/config/weights.yaml",
        cyclability_config_path =  root  / "src/cmm/metrics/config/cyclability.yaml"
    )
    
if __name__ == "__main__":
    main()