# Version: 1.0
# Description: A simple Python package for tracing and logging.
# Author: Yair Mazal
# Author-email: yairmazal@gmail.com
# License: MIT
# Date: 06/06/2024
import logging
from functools import wraps
from typing import Callable, Optional

__ENABLE_TRACE__ = False
__PARENT_LOG_NAME__ = "pytracer"


def is_trace_enabled() -> bool:
    """Returns a boolean indicating whether tracing is enabled.
    :return bool: True if tracing is enabled, False otherwise.
    """
    return __ENABLE_TRACE__


def disable_trace() -> None:
    """Disables tracing."""
    global __ENABLE_TRACE__
    __ENABLE_TRACE__ = False


def enable_trace() -> None:
    """Enables tracing.
    This function should be used only after setup_tracing() has been called, and if tracing has been disabled.  
    """
    global __ENABLE_TRACE__
    __ENABLE_TRACE__ = True


def setup_tracing(log_file: Optional[str] = None, level: int = logging.DEBUG) -> logging.Logger:
    """Sets up tracing.
    
    :param log_file: The log file to write to. If None, the log will be written only to the console. 
    If a string is provided, the log will be written to the file with the given name, as well as to the console.
    :param level: The logging level using the logging module's constants. Default is logging.DEBUG.
    :return logging.Logger: A logger object.
    """
    global __ENABLE_TRACE__
    __ENABLE_TRACE__ = True

    logger = logging.getLogger(__PARENT_LOG_NAME__)
    logger.setLevel(level)
    logger_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(logger_format)
    logger.addHandler(console_handler)

    if log_file is not None:
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logger_format)
        logger.addHandler(file_handler)

    return logger


def add_child_log(child_log_suffix: str, parent_logger_name: Optional[str] = __PARENT_LOG_NAME__
                  ) -> tuple[str, logging.Logger]:
    """Adds a child logger to the parent logger.

    :param child_log_suffix: The suffix to add to the parent logger's name.
    :param parent_logger_name: The name of the parent logger. If None, the default parent logger name will be used.
    :return tuple[str, logging.Logger]: A tuple containing the name of the child logger and the child logger object.
    """
    if not is_trace_enabled():
        raise RuntimeError("Tracing must be enabled before adding a child logger.")
    child_logger_name = f"{parent_logger_name}.{child_log_suffix}"
    child_logger = logging.getLogger(child_logger_name)

    return child_logger_name, child_logger


def trace_decorator(logger_name: str) -> Callable:
    """A decorator that logs function calls and their return values.
    To use this decorator, call it with the name of the logger to use.

    Example:
    @trace_decorator("my_logger")
    def my_function():
        pass

    :param logger_name: The name of the logger to use.
    :return Callable: A decorator function.
    """
    logger = logging.getLogger(logger_name)

    def outer_wrapper(func: Callable) -> Callable:
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            enabled = __ENABLE_TRACE__
            if enabled:
                logger.debug(f"Calling function {func.__name__} with args: {args}, kwargs: {kwargs}")
            result = func(*args, **kwargs)
            if enabled:
                logger.debug(f"Function {func.__name__} returned: {result}")
            return result

        return inner_wrapper

    return outer_wrapper


def trace_msg(msg: str, *args, logger_name: Optional[str] = __PARENT_LOG_NAME__, level: int = logging.DEBUG, **kwargs) -> None:
    """Logs a message to the logger.

    :param msg: The message to log.
    :param args: The positional arguments to pass to the logger, formatted by the message.
    :param logger_name: The name of the logger to use. Default is the parent logger.
    :param level: The logging level using the logging module's constants. Default is logging.DEBUG.
    :param kwargs: The keyword arguments to pass to the logger via the extra parameter. These values can be used in the
    formatter of the logger object.

    Example:
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(client_ip)s')
    logging.basicConfig(format=log_formatter)
    d = {'client_ip': '192.168.0.1'}
    logger = logging.getLogger('tcpserver')
    trace_msg("Connection issue: %s", "Connection reset by peer", logger_name="tcpserver", level=logging.ERROR, **d)

    The code will print:
    2021-07-12 12:00:00 - tcpserver - ERROR - Connection issue: Connection reset by peer - 192.168.0.1
    """
    if __ENABLE_TRACE__:
        logger = logging.getLogger(logger_name)
        stack = level > logging.INFO
        logger.log(level, msg, *args, stack_info=stack, **kwargs)


def trace_exceptions_decorator(logger_name: str) -> Callable:
    """A decorator that logs any exceptions that occur within the decorated function.
    To use this decorator, call it with the name of the logger to use.

    Example:
    @trace_exceptions_decorator("my_logger")
    def my_function():
        pass

    :param logger_name: The name of the logger to use.
    :return Callable: A decorator function.
    """
    logger = logging.getLogger(logger_name)

    def outer_wrapper(func: Callable) -> Callable:
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f'Exception in {func.__name__}: {e}')
                raise e  # re-raise the exception after logging it
        return inner_wrapper

    return outer_wrapper


__all__ = ["is_trace_enabled", "disable_trace", "enable_trace", "setup_tracing", "add_child_log", "trace_decorator",
           "trace_msg", "trace_exceptions_decorator"]
