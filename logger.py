import logging
import os


def init_logger():
    # Create a custom logger
    log_level_env = os.environ.get('LOGLEVEL', 'INFO')
    log_level = None
    match log_level_env:
        case 'DEBUG':
            log_level = logging.DEBUG
        case 'INFO':
            log_level = logging.INFO
        case 'WARNING':
            log_level = logging.WARNING
        case 'ERROR':
            log_level = logging.ERROR
        case 'CRITICAL':
            log_level = logging.CRITICAL
        case _:
            raise ValueError(
                f'Incorrect env variable: LOGLEVEL={log_level_env}, but should be one of: '
                'DEBUG, INFO, WARNING, ERROR, CRITICAL',
            )

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    f_handler = logging.FileHandler('log.log')
    f_handler.setLevel(logging.ERROR)

    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
