![Alt text](media/demo_image.png)

# City Metrics Mapper 
(City metrics mapper - maybe new name later on) is a Python-based system for computing segment-level and city-level cyclability metrics from OpenStreetMap (OSM) road data. The system ingests raw OSM data, normalizes and segments the road network, computes a simplified cyclability metric, and stores results in a spatial relational database (PostGIS) for analysis, API access, and map-based access using kepler.gl.

The project is structured as a complete pipeline: from geospatial data ingestion to quality metrics computation and visualization. While the current focus is cyclability, the architecture may be applied to other quality indices.

## System Structure

The system is organized into the following logical steps:
- **Input**: OpenStreetMap road network data retrieved from Overpass API.
- **Processing** Normalization of OSM tags, segmentation and derivation of city-scale network, computation of segment-level metrics, and aggregation into city-level metrics. Missing data is explicitly tracked as qualitative uncertainty.
- **Storage** PostgreSQL with PostGIS is used as the authoritative storage system for geometries, features, and computed metrics.
- **Orchestration** Application services and database are coordinated using Docker Compose.
- **Output**
  - Segment-level cyclability metrics
  - City-level aggregated metrics with uncertainty indicators
  - FastAPI-based data access and Kepler-based frontend for results exploration

## Resources

- **Documentation (link later)**: Detailed descriptions of data model, process pipeline, metrics definition, database schema, jobs, and API structure.
- **Example notebooks (link later)**:  Jupyter notebooks with practical examples.

## Quick start

To run the project it is recommended to use Docker. The instructions below assume a macOS environment using Colima, but the same Docker Compose setup may be adjusted for use with other systems.

Install the required tools:
```bash
brew install colima
brew install docker
brew install docker-compose
```

Start Colima with enough dedicated resources for PostGIS and data processing, for example:
```bash
colima start --cpu 4 --memory 8
```
CPU and memory values can be adjusted depending on available hardware and application.

To run the repository and start services:
```bash
docker compose up -d
```

Once the containers are running, data ingestion and network building can be started by using the CLI jobs provided.

For example, to build the road network and compute associated cyclability metrics for Oslo, Norway:
```bash
docker compose exec app python -m cmm.jobs.build_network --c oslo --cc no
```
Where:
- `--c` is the city name
- `--cc` is the country code (ISO-2)

The job will:
- Define the administrative city boundary
- Fetch OSM road data available within the boundary
- Normalize and segment the network
- Compute cyclability metrics
- Store results in PostGIS

Multiple cities can be stored in the database.

After the pipeline is successfully run, results can be explored in two different ways:
- **Map**: An interactive map rendering all available data for a city:
  ```bash
  http://localhost:8000/maps/oslo
  ```
- **API**: Segment-level data retrieved via OSM IDs:
  ```bash
  http://localhost:8000/api/segments/oslo/4708813
  ```

Additional endpoints and CLI jobs are described in the project documentation.

## Project Structure
- `docker/`: Database schema initialization (init.sql).
- `docs/`: Technical documentation.
- `frontend/`: Frontend-related code (for now it includes Kepler.gl visualization).
- `src/cmm/`: Source code: ingestion, normalization, metrics computation, database services, API, and CLI jobs.

## Status
The project is currently under development.