-- SQL schema definition executed at container start
CREATE TABLE IF NOT EXISTS test_geoms (
    id SERIAL PRIMARY KEY,
    street_name TEXT,
    geom GEOMETRY(LineString, 4326)
);