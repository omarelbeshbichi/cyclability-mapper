import click
import logging 

@click.command()
@click.option("--city", "--city-name", "city_name", type = str, required = True)
def main(city_name):
    from city_metrics.data.export.postgres import delete_city_rows

    # Clear-up database
    logging.info("CLEAR DATABASE")
    delete_city_rows("network_segments", city_name)
    delete_city_rows("refresh_areas", city_name)
    delete_city_rows("city_metrics", city_name)
    # segment_metrics is deleted automatically (postgres)

    logging.info("DONE")
if __name__ == "__main__":
    main()