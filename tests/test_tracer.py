import pytest
import logging
from pytracer import (setup_tracing, enable_trace, disable_trace, is_trace_enabled, add_child_log, trace_decorator, trace_msg,
                      trace_exceptions_decorator)


def test_setup_tracing(mocker):
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_logger = mock_get_logger.return_value

    setup_tracing(log_file='logfile.log', level=logging.INFO)
    mock_get_logger.assert_called_once_with('pytracer')
    assert mock_logger.setLevel.call_count == 1
    assert mock_logger.setLevel.call_args[0][0] == logging.INFO
    assert mock_logger.addHandler.call_count == 2  # Console and File handlers


@pytest.mark.parametrize("initial_state, action, expected_state", [
    (True, disable_trace, False),
    (False, enable_trace, True),
])
def test_trace_toggle(initial_state, action, expected_state):
    if initial_state:
        enable_trace()
    else:
        disable_trace()

    action()

    assert is_trace_enabled() == expected_state


def test_add_child_log(mocker):
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_logger = mock_get_logger.return_value

    enable_trace()  # Make sure tracing is enabled
    add_child_log("child")
    mock_get_logger.assert_called_once_with("pytracer.child")


def test_trace_decorator(mocker):
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_logger = mock_get_logger.return_value

    @trace_decorator("test_logger")
    def test_func():
        return "Hello, World!"

    enable_trace()  # Make sure tracing is enabled
    assert test_func() == "Hello, World!"
    assert mock_get_logger.call_count == 1
    assert mock_get_logger.call_args[0][0] == "test_logger"
    assert mock_logger.debug.call_count == 2  # Function call and return should be logged


def test_trace_msg(tmpdir):
    log_file = tmpdir.join("logfile.log")  # Create a temporary log file
    setup_tracing(log_file=str(log_file), level=logging.DEBUG)  # Setup tracing
    enable_trace()  # Make sure tracing is enabled
    trace_msg("Test message")

    # Read the log file and check if the message is logged
    with open(log_file, 'r') as f:
        log_content = f.read()
        assert "Test message" in log_content


# Additional tests for edge cases
def test_setup_tracing_without_log_file():
    logger = setup_tracing(level=logging.INFO)
    assert logger.level == logging.INFO
    assert isinstance(logger, logging.Logger)
    assert len(logger.handlers) == 1  # Only console handler should be present


def test_add_child_log_without_tracing():
    disable_trace()
    with pytest.raises(RuntimeError):
        add_child_log("child")


def test_trace_decorator_without_tracing(mocker):
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_logger = mock_get_logger.return_value

    @trace_decorator("test_logger")
    def test_func():
        return "Hello, World!"

    disable_trace()  # Make sure tracing is disabled
    assert test_func() == "Hello, World!"
    assert mock_get_logger.call_count == 1  # Logger should be called once by the decorator


def test_trace_msg_without_tracing(mocker):
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_logger = mock_get_logger.return_value

    disable_trace()
    trace_msg("Test message")
    assert mock_get_logger.call_count == 0  # Logger should not be called


def test_trace_exceptions_decorator(mocker):
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_logger = mock_get_logger.return_value

    @trace_exceptions_decorator("test_logger")
    def test_func():
        raise ValueError("Test exception")

    enable_trace()  # Make sure tracing is enabled
    with pytest.raises(ValueError):
        test_func()
    assert mock_get_logger.call_count == 1
    assert mock_get_logger.call_args[0][0] == "test_logger"
    assert mock_logger.error.call_count == 1
    assert "Test exception" in mock_logger.error.call_args[0][0]
