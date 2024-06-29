import os
import json
import sys
from typing import Any, Dict, Optional
from functools import lru_cache
import logging

from logging_helper import get_logger, log_exception, sanitize_log_data

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


@lru_cache(maxsize=None)
def get_environment() -> str:
    """
    Retrieve the current environment name.

    This function is cached to avoid repeated environment variable lookups.

    Returns:
        str: The name of the current environment (e.g., 'development', 'production').

    Raises:
        ConfigurationError: If the ENVIRONMENT variable is not set.
    """
    env = os.getenv('ENVIRONMENT')
    if not env:
        logger.error("ENVIRONMENT variable is not set")
        raise ConfigurationError("ENVIRONMENT variable must be set")
    logger.info(f"Current environment: {env}")
    return env


@log_exception(logger)
def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        Dict[str, Any]: Loaded configuration as a dictionary.

    Raises:
        ConfigurationError: If the file cannot be read or parsed.
    """
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
        raise ConfigurationError(f"Failed to load configuration: {str(e)}")


@log_exception(logger)
def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value from environment variables.

    This function prioritizes environment variables over default values for security.

    Args:
        key (str): The configuration key to retrieve.
        default (Any, optional): Default value if the key is not found.

    Returns:
        Any: The configuration value.

    Raises:
        ConfigurationError: If a required configuration value is missing.
    """
    value = os.getenv(key, default)
    if value is None:
        logger.error(f"Missing required configuration: {key}")
        raise ConfigurationError(f"Missing required configuration: {key}")

    sanitized_value = sanitize_log_data({key: value})[key]
    logger.info(f"Retrieved configuration value for {key}: {sanitized_value}")
    return value


@log_exception(logger)
def set_feature_flag(flag_name: str, value: bool) -> None:
    """
    Set a feature flag.

    Args:
        flag_name (str): The name of the feature flag.
        value (bool): The value to set for the feature flag.

    Raises:
        ConfigurationError: If there's an error setting the feature flag.
    """
    try:
        # This is a placeholder. In a real application, you might use a database or a
        # feature flag service to store this information.
        os.environ[f"FEATURE_{flag_name.upper()}"] = str(value)
        logger.info(f"Feature flag '{flag_name}' set to {value}")
    except Exception as e:
        logger.error(f"Failed to set feature flag '{flag_name}': {str(e)}")
        raise ConfigurationError(f"Failed to set feature flag: {str(e)}")


@log_exception(logger)
def get_feature_flag(flag_name: str, default: bool = False) -> bool:
    """
    Get the value of a feature flag.

    Args:
        flag_name (str): The name of the feature flag.
        default (bool, optional): Default value if the flag is not set.

    Returns:
        bool: The value of the feature flag.
    """
    value = os.getenv(f"FEATURE_{flag_name.upper()}", str(default)).lower()
    is_enabled = value in ('true', '1', 'yes')
    logger.info(f"Feature flag '{flag_name}' is {'enabled' if is_enabled else 'disabled'}")
    return is_enabled


@log_exception(logger)
def update_config(config_updates: Dict[str, Any]) -> None:
    """
    Update multiple configuration values at once.

    This function should be used carefully, especially in a production environment.

    Args:
        config_updates (Dict[str, Any]): A dictionary of configuration updates.

    Raises:
        ConfigurationError: If there's an error updating the configuration.
    """
    try:
        for key, value in config_updates.items():
            os.environ[key] = str(value)

        sanitized_updates = sanitize_log_data(config_updates)
        logger.info(f"Configuration updated: {sanitized_updates}")
    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}")
        raise ConfigurationError(f"Failed to update configuration: {str(e)}")


def init_config(config_path: Optional[str] = None) -> None:
    """
    Initialize the application configuration.

    This function should be called at application startup.

    Args:
        config_path (str, optional): Path to a configuration file.

    Raises:
        ConfigurationError: If there's an error initializing the configuration.
    """
    try:
        env = get_environment()
        logger.info(f"Initializing configuration for {env} environment")

        if config_path:
            config = load_config(config_path)
            for key, value in config.items():
                if key not in os.environ:
                    os.environ[key] = str(value)

        # Validate required configurations
        required_configs = ['DATABASE_URL', 'SECRET_KEY', 'DEBUG']
        for config in required_configs:
            get_config_value(config)

        logger.info("Configuration initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {str(e)}")
        raise ConfigurationError(f"Failed to initialize configuration: {str(e)}")


if __name__ == "__main__":
    # Example usage
    try:
        init_config('config.json')
        debug_mode = get_config_value('DEBUG', 'False').lower() == 'true'
        print(f"Debug mode: {debug_mode}")

        set_feature_flag('NEW_FEATURE', True)
        if get_feature_flag('NEW_FEATURE'):
            print("New feature is enabled!")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
