
# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------

import logging
import os
import platform
import tempfile

from dpa.env.vars import DpaVars
from dpa.user import current_username

# ----------------------------------------------------------------------------
# Private functions:
# ----------------------------------------------------------------------------
def _create_log_file(path):
    with open(path, "w+") as f:
        f.write("")
    os.chmod(path, 0660)

# ----------------------------------------------------------------------------
def _log_level_from_name(level_name):
    return getattr(logging, level_name.upper())

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class Logger(object):

    # ------------------------------------------------------------------------
    # Public class attributes:
    # ------------------------------------------------------------------------

    # the available levels for logging
    levels = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    # log to the shared log directory, or a tempdirectory if undefined
    log_dir = DpaVars.share_logs(default=tempfile.gettempdir()).get()
    
    # the default logging level
    log_level = "WARNING"

    # ------------------------------------------------------------------------
    # Private class attributes:
    # ------------------------------------------------------------------------

    # ---- setup consistent stdout handling for all dpa code

    # formatting for all logging to stdout
    _stdout_formatter = logging.Formatter(
        fmt="%(name)s %(levelname)s: %(message)s"
    )

    # handler for all stdout. Anything logged at a level matching or above
    # should go to stdout
    _stdout_handler = logging.StreamHandler()
    _stdout_handler.setFormatter(_stdout_formatter)
    _stdout_handler.setLevel(_log_level_from_name(log_level))

    # format all log messages 
    _logfile_formatter = logging.Formatter(
        fmt="[%(asctime)s] {un}@{ma} %(name)s %(levelname)s: %(message)s".\
            format(ma=platform.node(), un=current_username()),
        datefmt="%Y/%m/%d-%H:%M:%S",
    )

    # attach the handler to the root logger. 
    _root_logger = logging.getLogger()
    _root_logger.addHandler(_stdout_handler)

    # keep track of processed logger names
    _logger_cache = dict()

    # ------------------------------------------------------------------------
    # Class methods:
    # ------------------------------------------------------------------------
    @classmethod
    def get(cls, name=None):

        if not name:
            name = "dpa"

        # make sure everything is namespaced with dpa.
        if not name.startswith("dpa"):
            name = ".".join(["dpa", name])

        if not name in cls._logger_cache.keys():

            # create the custom logger wrapper
            # log to a file based on the logger's name
            log_file = name + ".log"
            log_path = os.path.join(cls.log_dir, log_file)

            # ensure path exists with proper permissions first
            if not os.path.exists(log_path):
                _create_log_file(log_path)

            # create a handler to output to a log file, set the level to INFO
            logfile_handler = logging.FileHandler(filename=log_path)
            logfile_handler.setLevel(_log_level_from_name('INFO'))
            logfile_handler.setFormatter(cls._logfile_formatter)

            # get the named logger, set have it process all messages, and 
            # have it send output to the file handler. note the level is
            # set on the handler.
            logger = logging.getLogger(name)
            logger.setLevel(_log_level_from_name('DEBUG'))
            logger.addHandler(logfile_handler)

            cls._logger_cache[name] = logger

        return cls._logger_cache[name]

    # ------------------------------------------------------------------------
    @classmethod
    def set_level(cls, level):
        """Set the level for the root logger's stdout."""
        cls.log_level = level
        cls._stdout_handler.setLevel(_log_level_from_name(level))

