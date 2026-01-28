import requests
import logging 
import time


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

logger = logging.getLogger(__name__)

def run_overpass_query(query: str, timeout: int = 200, retries: int = 3, delay: float = 2.0) -> dict:
    """
    Execute Overpass API query and return response as dictionary
    Retries N times on failure with a delay to avoid overloading the API

    Parameters
    ----------
    query : str
        Overpass QL query
    timeout : int
        Timeout in seconds
    retries : int
        Number of retries
    delay : float
        Seconds to wait between retries

    Returns
    -------
    dict
        Parsed JSON response from the Overpass API
    """
    logger.info("Running Overpass query (%d chars)", len(query))

    # Attempt fetch N times
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            if "elements" not in data:
                raise RuntimeError(f"Overpass error: {data}")

            logger.info("Overpass query successfully completed.")

            return data

        except (requests.RequestException, RuntimeError) as e:
            logger.warning("Attempt %d/%d failed: %s", attempt, retries, e)
            
            # 
            if attempt < retries:
                logger.info("Retrying in %.1f seconds...", delay)
                # Delay client before next attempt (API interface)
                time.sleep(delay)
            else:
                logger.error("All attempts failed.")
                raise