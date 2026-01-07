import requests
import logging 

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'


logger = logging.getLogger(__name__)


def run_overpass_query(query: str,
                       timeout: int = 200) -> dict:
    
    logger.info('Running Overpass query (%d chars)', len(query))

    response = requests.post(
        OVERPASS_URL,
        data={'data': query},
        timeout=timeout
    )
    
    # Handle HTTP errors
    response.raise_for_status()

    # Fetched GeoJSON
    data = response.json()

    # Handle overpass errors
    if 'elements' not in data:
        raise RuntimeError(f'Overpass error: {data}')
    
    return response.json()