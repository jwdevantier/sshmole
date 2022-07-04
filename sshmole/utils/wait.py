from typing import Callable
import threading


def wait_for(fn: Callable, timeout: int):
    """Wait until function finishes execution or timeout occurs.

    Returns:
        True iff. thread finished execution within allotted timeout
    """
    th = threading.Thread(target=fn)
    th.daemon = True
    th.start()
    th.join(timeout=timeout)
    return not th.is_alive()
