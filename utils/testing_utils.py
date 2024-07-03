import random
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

logger = get_logger(__name__)


class ABTest:
    """
    A class to manage A/B tests.

    This class provides utilities for creating, running, and analyzing A/B tests.
    It ensures proper logging of test setup, variant assignment, and results.

    Attributes:
        name (str): The name of the A/B test.
        variants (List[str]): The list of variant names for the test.
        weights (Optional[List[float]]): The weights for each variant. If None, equal weights are used.
        _variant_map (Dict[str, str]): A mapping of user IDs to assigned variants.
    """

    def __init__(self, name: str, variants: List[str], weights: Optional[List[float]] = None):
        """
        Initialize an A/B test.

        Args:
            name (str): The name of the A/B test.
            variants (List[str]): The list of variant names for the test.
            weights (Optional[List[float]], optional): The weights for each variant. Defaults to None.

        Raises:
            ValueError: If the number of weights doesn't match the number of variants.
        """
        self.name = name
        self.variants = variants
        self.weights = weights

        if self.weights and len(self.weights) != len(self.variants):
            raise ValueError("Number of weights must match number of variants")

        self._variant_map: Dict[str, str] = {}

        logger.info(f"Initialized A/B test '{self.name}' with variants: {sanitize_log_data(self.variants)}")

    @log_exception(logger)
    @timed_function(logger)
    def assign_variant(self, user_id: str) -> str:
        """
        Assign a variant to a user.

        This method assigns a variant to a user and logs the assignment.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            str: The assigned variant name.
        """
        if user_id in self._variant_map:
            variant = self._variant_map[user_id]
            logger.info(f"User {user_id} already assigned to variant '{variant}' in test '{self.name}'")
            return variant

        variant = random.choices(self.variants, weights=self.weights, k=1)[0]
        self._variant_map[user_id] = variant
        logger.info(f"Assigned user {user_id} to variant '{variant}' in test '{self.name}'")
        return variant

    @log_exception(logger)
    def get_variant(self, user_id: str) -> Optional[str]:
        """
        Get the assigned variant for a user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            Optional[str]: The assigned variant name, or None if not assigned.
        """
        variant = self._variant_map.get(user_id)
        if variant:
            logger.info(f"Retrieved variant '{variant}' for user {user_id} in test '{self.name}'")
        else:
            logger.info(f"No variant assigned for user {user_id} in test '{self.name}'")
        return variant

    @log_exception(logger)
    @timed_function(logger)
    def record_conversion(self, user_id: str) -> None:
        """
        Record a conversion for a user.

        This method should be called when a user completes the desired action in the test.

        Args:
            user_id (str): The unique identifier for the user.

        Raises:
            ValueError: If the user hasn't been assigned a variant.
        """
        variant = self.get_variant(user_id)
        if not variant:
            raise ValueError(f"User {user_id} hasn't been assigned a variant in test '{self.name}'")

        logger.info(f"Recorded conversion for user {user_id} in variant '{variant}' of test '{self.name}'")
        # Here you would typically update your conversion tracking system
        # For example, increment a counter in a database


def ab_test_decorator(test: ABTest) -> Callable:
    """
    A decorator to apply an A/B test to a function.

    This decorator assigns a variant to the user and passes it to the decorated function.

    Args:
        test (ABTest): The A/B test to apply.

    Returns:
        Callable: A decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_id = kwargs.get('user_id')
            if not user_id:
                logger.warning(f"No user_id provided for A/B test '{test.name}' in {func.__name__}")
                return func(*args, **kwargs)

            variant = test.assign_variant(user_id)
            kwargs['ab_variant'] = variant

            logger.info(f"Applying A/B test '{test.name}' with variant '{variant}' to {func.__name__}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


@log_exception(logger)
@timed_function(logger)
def create_unique_test_id() -> str:
    """
    Create a unique identifier for an A/B test.

    This function generates a UUID and logs its creation.

    Returns:
        str: A unique test identifier.
    """
    test_id = str(uuid.uuid4())
    logger.info(f"Created unique A/B test ID: {test_id}")
    return test_id


@log_exception(logger)
@timed_function(logger)
def calculate_test_results(conversions: Dict[str, int], impressions: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate the results of an A/B test.

    This function computes the conversion rate for each variant.

    Args:
        conversions (Dict[str, int]): A dictionary of variant names to conversion counts.
        impressions (Dict[str, int]): A dictionary of variant names to impression counts.

    Returns:
        Dict[str, float]: A dictionary of variant names to conversion rates.

    Raises:
        ValueError: If a variant in conversions is not in impressions, or vice versa.
    """
    if set(conversions.keys()) != set(impressions.keys()):
        raise ValueError("Mismatch between conversion and impression variants")

    results = {}
    for variant in conversions:
        if impressions[variant] == 0:
            results[variant] = 0
        else:
            results[variant] = conversions[variant] / impressions[variant]

    logger.info(f"Calculated A/B test results: {sanitize_log_data(results)}")
    return results
