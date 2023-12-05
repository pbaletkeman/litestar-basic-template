import logging


def get_logger(mod_name: str) -> logging.Logger:
    """Return logger object."""
    format_obj = '%(asctime)s: %(name)s: %(levelname)s: %(message)s'
    logger_obj = logging.getLogger(mod_name)
    # Writes to stdout
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(format_obj))
    logger_obj.addHandler(ch)
    return logger_obj


logger = get_logger(__package__)
