import logging
from functools import wraps
from typing import Dict, List, Any, Callable
from datetime import datetime

# Import the custom logging utilities
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

# Create a logger for this module
logger = get_logger(__name__)


@log_exception(logger)
@timed_function(logger)
def aggregate_data(data: List[Dict[str, Any]], aggregation_key: str, aggregation_func: Callable) -> Dict[str, Any]:
    """
    Aggregate data based on a specified key and aggregation function.

    This function takes a list of dictionaries, groups them by a specified key,
    and applies an aggregation function to each group.

    Args:
        data (List[Dict[str, Any]]): A list of dictionaries containing the data to aggregate.
        aggregation_key (str): The key in each dictionary to group by.
        aggregation_func (Callable): A function to apply to each group for aggregation.

    Returns:
        Dict[str, Any]: A dictionary with keys being the unique values of the aggregation_key,
                        and values being the result of the aggregation function for each group.

    Example:
        >>> data = [{'category': 'A', 'value': 1}, {'category': 'B', 'value': 2}, {'category': 'A', 'value': 3}]
        >>> aggregate_data(data, 'category', sum)
        {'A': 4, 'B': 2}

    Raises:
        KeyError: If the aggregation_key is not present in all dictionaries in the data.
        TypeError: If the data is not a list of dictionaries or if the aggregation_func is not callable.
    """
    logger.info(f"Starting data aggregation on key: {aggregation_key}")

    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        logger.error("Invalid data format: expected list of dictionaries")
        raise TypeError("Data must be a list of dictionaries")

    if not callable(aggregation_func):
        logger.error("Invalid aggregation function: not callable")
        raise TypeError("Aggregation function must be callable")

    try:
        result = {}
        for item in data:
            key = item[aggregation_key]
            if key not in result:
                result[key] = []
            result[key].append(item)

        for key in result:
            result[key] = aggregation_func(result[key])

        logger.info(f"Data aggregation completed successfully for key: {aggregation_key}")
        return result
    except KeyError as e:
        logger.error(f"KeyError during aggregation: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during data aggregation: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def generate_time_series_report(data: List[Dict[str, Any]], time_key: str, value_key: str,
                                start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
    """
    Generate a time series report from the given data.

    This function creates a time series report by organizing data points over time.
    It can optionally filter the data to a specific time range.

    Args:
        data (List[Dict[str, Any]]): A list of dictionaries containing the time series data.
        time_key (str): The key in each dictionary that represents the timestamp.
        value_key (str): The key in each dictionary that represents the value to be reported.
        start_time (datetime, optional): The start of the time range to include in the report.
        end_time (datetime, optional): The end of the time range to include in the report.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing a 'time' and 'value' key,
                              sorted by time in ascending order.

    Example:
        >>> data = [{'timestamp': datetime(2023, 1, 1), 'value': 10},
        ...         {'timestamp': datetime(2023, 1, 2), 'value': 20}]
        >>> generate_time_series_report(data, 'timestamp', 'value')
        [{'time': datetime(2023, 1, 1), 'value': 10}, {'time': datetime(2023, 1, 2), 'value': 20}]

    Raises:
        KeyError: If the time_key or value_key is not present in all dictionaries in the data.
        ValueError: If the time_key values cannot be parsed as datetime objects.
    """
    logger.info(f"Generating time series report for key: {value_key}")

    try:
        report = []
        for item in data:
            time = item[time_key]
            if not isinstance(time, datetime):
                time = datetime.fromisoformat(time)

            if (start_time is None or time >= start_time) and (end_time is None or time <= end_time):
                report.append({'time': time, 'value': item[value_key]})

        report.sort(key=lambda x: x['time'])

        logger.info(f"Time series report generated successfully for key: {value_key}")
        return report
    except KeyError as e:
        logger.error(f"KeyError during report generation: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"ValueError during time parsing: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during report generation: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def calculate_growth_rate(current_value: float, previous_value: float) -> float:
    """
    Calculate the growth rate between two values.

    This function computes the percentage change from the previous value to the current value.

    Args:
        current_value (float): The current value.
        previous_value (float): The previous value to compare against.

    Returns:
        float: The growth rate as a percentage. A positive value indicates growth,
               while a negative value indicates decline.

    Example:
        >>> calculate_growth_rate(110, 100)
        10.0  # Represents a 10% growth

    Raises:
        ValueError: If the previous_value is zero, as division by zero is undefined.
        TypeError: If the inputs are not numeric.
    """
    logger.info("Calculating growth rate")

    try:
        if not (isinstance(current_value, (int, float)) and isinstance(previous_value, (int, float))):
            raise TypeError("Both inputs must be numeric")

        if previous_value == 0:
            raise ValueError("Previous value cannot be zero when calculating growth rate")

        growth_rate = ((current_value - previous_value) / previous_value) * 100
        logger.info(f"Growth rate calculated: {growth_rate}%")
        return growth_rate
    except TypeError as e:
        logger.error(f"TypeError during growth rate calculation: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"ValueError during growth rate calculation: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during growth rate calculation: {str(e)}")
        raise