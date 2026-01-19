import click

@click.command()
@click.option("--south", type = float, required = True)
@click.option("--west", type = float, required = True)
@click.option("--north", type = float, required = True)
@click.option("--east", type = float, required = True)
def main(south, west, north, east):
    from cmm.services.pipeline import build_network_from_api
    from cmm.utils.misc import get_project_root
    from cmm.data.ingest.overpass_queries import roads_in_bbox


    root = get_project_root()

    query = roads_in_bbox(
        south, west,
        north, east
    )

    build_network_from_api(
        query = query,
        weights_config_path = root / "src/cmm/metrics/config/weights.yaml",
        cyclability_config_path = root / "src/cmm/metrics/config/cyclability.yaml"
    )

if __name__ == "__main__":
    main()
