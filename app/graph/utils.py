"""
Shared utilities for the LangGraph workflow.

Includes node timing decorator for measuring and logging execution time
of each graph node (useful for performance analysis).
"""
import functools
import logging
import time

logger = logging.getLogger(__name__)


def log_node_timing(node_name: str):
    """
    Decorator that logs the time consumed by a graph node.

    Logs at start, on success (with elapsed seconds), and on failure
    (with elapsed seconds before the exception propagates).

    Usage:
        @log_node_timing("mapping")
        def mapping_node(state, llm):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            logger.info("[%s] timer started", node_name)
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info("[%s] completed in %.3f s", node_name, elapsed)
                return result
            except Exception:
                elapsed = time.perf_counter() - start
                logger.warning(
                    "[%s] failed after %.3f s",
                    node_name,
                    elapsed,
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
