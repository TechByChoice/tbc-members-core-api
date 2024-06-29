import gettext
import os
from typing import Dict, Any
from functools import wraps

from django.utils import translation
from django.conf import settings

from logging_utils import get_logger, log_exception, timed_function

logger = get_logger(__name__)

@log_exception(logger)
def setup_localization(locale_dir: str) -> None:
    """
    Set up the localization environment.

    This function initializes the gettext translation system with the specified locale directory.
    It should be called once at the start of your application.

    Args:
        locale_dir (str): The directory containing the locale files.

    Raises:
        FileNotFoundError: If the specified locale directory does not exist.

    Example:
        setup_localization('/path/to/your/locale/directory')
    """
    if not os.path.exists(locale_dir):
        logger.error(f"Locale directory not found: {locale_dir}")
        raise FileNotFoundError(f"Locale directory not found: {locale_dir}")

    try:
        translation.activate(settings.LANGUAGE_CODE)
        logger.info(f"Localization set up with locale directory: {locale_dir}")
    except Exception as e:
        logger.exception(f"Failed to set up localization: {str(e)}")
        raise

@log_exception(logger)
@timed_function(logger)
def translate_text(text: str, language: str) -> str:
    """
    Translate the given text to the specified language.

    Args:
        text (str): The text to translate.
        language (str): The target language code (e.g., 'es' for Spanish).

    Returns:
        str: The translated text.

    Raises:
        ValueError: If the language code is invalid.

    Example:
        translated = translate_text("Hello, world!", "es")
        print(translated)  # "¡Hola, mundo!"
    """
    if not language or len(language) != 2:
        logger.error(f"Invalid language code: {language}")
        raise ValueError(f"Invalid language code: {language}")

    try:
        with translation.override(language):
            return gettext.gettext(text)
    except Exception as e:
        logger.exception(f"Translation failed for text '{text}' to language '{language}': {str(e)}")
        return text  # Fallback to original text

def localize_decorator(function):
    """
    A decorator to automatically handle localization for a function.

    This decorator will set the language for the duration of the function call
    based on the 'language' keyword argument passed to the function.

    Args:
        function: The function to decorate.

    Returns:
        function: The decorated function.

    Example:
        @localize_decorator
        def greet(name, language='en'):
            return _("Hello, {name}!").format(name=name)

        print(greet("Alice", language="es"))  # "¡Hola, Alice!"
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        language = kwargs.get('language', settings.LANGUAGE_CODE)
        with translation.override(language):
            return function(*args, **kwargs)
    return wrapper

@log_exception(logger)
@timed_function(logger)
def localize_data(data: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Recursively localize all string values in a dictionary.

    This function walks through a dictionary and translates all string values
    to the specified language.

    Args:
        data (Dict[str, Any]): The dictionary containing data to localize.
        language (str): The target language code.

    Returns:
        Dict[str, Any]: A new dictionary with all string values localized.

    Example:
        original = {"greeting": "Hello", "items": ["Apple", "Banana"]}
        localized = localize_data(original, "es")
        print(localized)  # {"greeting": "Hola", "items": ["Manzana", "Plátano"]}
    """
    if not isinstance(data, dict):
        logger.error(f"Input data must be a dictionary, got {type(data)}")
        raise TypeError("Input data must be a dictionary")

    localized = {}
    for key, value in data.items():
        if isinstance(value, str):
            localized[key] = translate_text(value, language)
        elif isinstance(value, list):
            localized[key] = [localize_data(item, language) if isinstance(item, dict)
                              else translate_text(item, language) if isinstance(item, str)
                              else item for item in value]
        elif isinstance(value, dict):
            localized[key] = localize_data(value, language)
        else:
            localized[key] = value
    return localized

@log_exception(logger)
def get_supported_languages() -> Dict[str, str]:
    """
    Get a dictionary of supported languages.

    This function returns a dictionary where the keys are language codes
    and the values are the names of the languages in their native form.

    Returns:
        Dict[str, str]: A dictionary of supported languages.

    Example:
        languages = get_supported_languages()
        print(languages)  # {"en": "English", "es": "Español", "fr": "Français"}
    """
    try:
        return dict(settings.LANGUAGES)
    except AttributeError:
        logger.error("LANGUAGES setting is not defined in Django settings")
        return {}

logger.info("Localization utilities loaded successfully")