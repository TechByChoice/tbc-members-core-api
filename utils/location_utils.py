import logging
from functools import wraps
import time
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Configure logging
logger = logging.getLogger(__name__)


def log_exception(func):
    """
    A decorator to log exceptions raised in functions.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise

    return wrapper


def timed_function(func):
    """
    A decorator to log the execution time of functions.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} took {end_time - start_time:.2f} seconds to execute.")
        return result

    return wrapper


@log_exception
@timed_function
def geocode_address(address):
    """
    Convert a string address into latitude and longitude coordinates.

    Args:
        address (str): The address to geocode.

    Returns:
        tuple: A tuple containing latitude and longitude as floats.

    Raises:
        ValueError: If the address cannot be geocoded.
    """
    geolocator = Nominatim(user_agent="myGeocoder")
    location = geolocator.geocode(address)

    if location:
        logger.info(f"Successfully geocoded address: {address}")
        return location.latitude, location.longitude
    else:
        logger.warning(f"Failed to geocode address: {address}")
        raise ValueError(f"Unable to geocode address: {address}")


@log_exception
@timed_function
def calculate_distance(origin, destination):
    """
    Calculate the distance between two points on Earth.

    Args:
        origin (tuple): A tuple containing the latitude and longitude of the origin point.
        destination (tuple): A tuple containing the latitude and longitude of the destination point.

    Returns:
        float: The distance between the two points in kilometers.

    Raises:
        ValueError: If either origin or destination is not a valid coordinate tuple.
    """
    if not (isinstance(origin, tuple) and isinstance(destination, tuple) and
            len(origin) == 2 and len(destination) == 2):
        logger.error("Invalid coordinates provided for distance calculation")
        raise ValueError("Both origin and destination must be tuples of (latitude, longitude)")

    distance = geodesic(origin, destination).kilometers
    logger.info(f"Calculated distance between {origin} and {destination}: {distance:.2f} km")
    return distance


@log_exception
@timed_function
def get_timezone(lat, lon):
    """
    Get the timezone for a given latitude and longitude.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        str: The timezone name for the given coordinates.

    Raises:
        requests.RequestException: If there's an error in the API request.
        ValueError: If the API response is invalid or missing timezone information.
    """
    url = f"http://api.geonames.org/timezoneJSON?lat={lat}&lng={lon}&username=YOUR_USERNAME"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'timezoneId' in data:
            timezone = data['timezoneId']
            logger.info(f"Retrieved timezone for coordinates ({lat}, {lon}): {timezone}")
            return timezone
        else:
            logger.warning(f"No timezone information found for coordinates ({lat}, {lon})")
            raise ValueError("No timezone information found in the API response")

    except requests.RequestException as e:
        logger.error(f"Error fetching timezone information: {str(e)}")
        raise


@log_exception
@timed_function
def validate_coordinates(lat, lon):
    """
    Validate if the given latitude and longitude are within valid ranges.

    Args:
        lat (float): Latitude to validate.
        lon (float): Longitude to validate.

    Returns:
        bool: True if coordinates are valid, False otherwise.
    """
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        logger.warning(f"Invalid coordinate types: lat={type(lat)}, lon={type(lon)}")
        return False

    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        logger.warning(f"Coordinates out of valid range: lat={lat}, lon={lon}")
        return False

    logger.info(f"Validated coordinates: lat={lat}, lon={lon}")
    return True
