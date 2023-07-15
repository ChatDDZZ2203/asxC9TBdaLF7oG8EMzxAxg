import time
import random
import traceback
from typing import Union

def exc_to_str(
        exc: Exception, title: str = "EXCEPTION:\n\n",
        limit: Union[int, None] = 2, separator: str = "", chain: bool = False
) -> str:
    return title + separator.join(
        traceback.format_exception(
            type(exc), exc, exc.__traceback__,
            limit=limit, chain=chain
        ))

def random_sleep(min_secs: float, max_secs: float):
    """Takes min and max values in seconds"""
    time.sleep(random.uniform(min_secs, max_secs))


