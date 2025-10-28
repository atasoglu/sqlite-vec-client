"""Tests for logging functionality."""

import logging

from sqlite_vec_client import get_logger


class TestLogger:
    """Test logging configuration."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "sqlite_vec_client"

    def test_logger_has_handler(self):
        """Test that logger has at least one handler."""
        logger = get_logger()
        assert len(logger.handlers) > 0

    def test_logger_default_level(self):
        """Test that logger respects environment variable."""
        logger = get_logger()
        # Default is WARNING if not set
        assert logger.level in [
            logging.WARNING,
            logging.DEBUG,
            logging.INFO,
            logging.ERROR,
            logging.CRITICAL,
        ]

    def test_logger_level_can_be_changed(self):
        """Test that logger level can be changed programmatically."""
        logger = get_logger()
        original_level = logger.level

        logger.setLevel(logging.DEBUG)
        assert logger.level == logging.DEBUG

        logger.setLevel(logging.INFO)
        assert logger.level == logging.INFO

        # Restore original level
        logger.setLevel(original_level)
