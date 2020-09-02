import logging


def setup_logger(
    name: str,
    log_file: str,
    formatter: logging.Formatter,
    level: logging = logging.INFO,
):
    """
    Logger setup.
    Parameter
    __________
    name: str
        Name of a logger.
    log_file: str
        Name of a log file.
    formatter: logging.Formatter
        The format of the log file.
    level: logging.Level
        The logging level.
    """
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
