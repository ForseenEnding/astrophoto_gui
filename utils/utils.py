from typing import Any, Callable
import logging
logger = logging.getLogger(__name__)
 
def default_on_exception(default_value: Any, func: Callable):
    try:
        return func()
    except Exception as e:
        logger.error(f"Error calling {func.__name__}: {e}")
        return default_value