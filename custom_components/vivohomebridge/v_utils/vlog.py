"""
 Copyright 2024 vivo Mobile Communication Co., Ltd.
 Licensed under the Apache License, Version 2.0 (the "License");

    http://www.apache.org/licenses/LICENSE-2.0
"""
import logging
from ..const import (DOMAIN)
DEBUG = 0
INFO = 1
WARN = 2
ERROR = 3
_LOGGER = logging.getLogger(DOMAIN)


class VLog:
    level = DEBUG
    is_enabled = True
    _logger_initialized = False

    @classmethod
    def set_level(cls, level):
        """Set the logging level."""
        cls.level = level

    @classmethod
    def enable_log(cls):
        """Enable logging output."""
        cls.is_enabled = True

    @classmethod
    def disable_log(cls):
        """Disable logging output."""
        cls.is_enabled = False

    @classmethod
    def _log(cls, level, content):
        """Internal method to log a message with a given level."""
        if not cls.is_enabled:
            return

        if level < cls.level:
            return

        log_func = {
            DEBUG: _LOGGER.debug,
            INFO: _LOGGER.info,
            WARN: _LOGGER.warning,
            ERROR: _LOGGER.error,
        }.get(level)
        log_func(content)

    @classmethod
    def debug(cls, tag, content):
        cls._log(DEBUG, f"[{tag}]" + content)

    @classmethod
    def info(cls, tag, content):
        cls._log(INFO, f"[{tag}]" + content)

    @classmethod
    def warning(cls, tag, content):
        cls._log(WARN, f"[{tag}]" + content)

    @classmethod
    def error(cls, tag, content):
        cls._log(ERROR, f"[{tag}]" + content)
