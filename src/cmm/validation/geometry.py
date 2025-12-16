"""
Module for validating geometries in PostGIS database.
"""
from typing import List, Tuple

def find_invalid_geometries(cur, table_name: str) -> Tuple[bool, List]:
    """
    Find invalid geometries in PostGIS database and returns associated ids and reasons
    and boolean for invalid geometry detection.

    Parameters
    ----------
    cur
        psycopg2 cursor object
    table_name: str
        Table name in PostGIS database

    Returns
    -------
    is_invalid: bool
        Returns true if invalid geometries have been detected
    invalid_id_reason: list
        List storing for each invalid geometry its id and invalid description
    """

    # Query to collect data from database
    query = f"""
    SELECT id, ST_IsValidReason(geom) AS invalid_reason
    FROM {table_name}
    WHERE NOT ST_IsValid(geom);
    """
    cur.execute(query)
    invalid_id_reason = cur.fetchall()

    # Invalid geometries detection boolean
    is_invalid = False if len(invalid_id_reason) == 0 else True
      
    return is_invalid, invalid_id_reason

def clean_linestrings(cur, table_name: str) -> int:
    """
    Delete degenerate LineStrings from a PostGIS table.

    Parameters
    ----------
    cur : psycopg2 cursor
        Active cursor
    table_name : str
        PostGIS table containing LineString geometries

    Returns
    -------
    n_deleted : int
        Number of deleted degenerate LineStrings
    """
    query_delete_degenerate = f"""
    DELETE FROM {table_name}
    WHERE ST_NPoints(geom) < 2
        OR ST_Length(geom) = 0
    RETURNING id;
    """
    cur.execute(query_delete_degenerate)
    n_deleted = len(cur.fetchall())

    return n_deleted



