import os
import logging
import pathlib

from datetime import datetime, timedelta
from rich.logging import RichHandler

# ------ FORMATTERS ------
shell_format = '%(message)s'
shell_formatter = logging.Formatter(shell_format)

# ------ HANDLERS ------
shell_handler = RichHandler(show_path=False)
shell_handler.setFormatter(shell_formatter)

# ------ LOGGERS ------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(shell_handler)

def setFileHandle(logger, filepath: pathlib.Path):
    if len([i for i in filepath.glob('*.log')])>0:
        last_modified_time = datetime.fromtimestamp(os.path.getmtime([i for i in filepath.glob('*.log')][-1])) 
        diff = datetime.now() - last_modified_time
    else:
        diff = timedelta(seconds=99999)
    if 30 >= (diff.total_seconds() / 60):
        fh = logging.FileHandler(list(filepath.glob('*.log'))[-1])
        logger.addHandler(fh)
        logger.debug(f'Using logfile: {list(filepath.glob("*.log"))[-1]}')
    else:
        filepath = filepath.joinpath(f"rafe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logger.info(f'Creating logfile: {filepath}')
        fh = logging.FileHandler(filepath)
        logger.addHandler(fh)
        return

