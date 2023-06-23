import pathlib
from rafe.cli import app
from rafe.logger import logger, setFileHandle


def cli():
    if pathlib.Path.home().joinpath(".rafe").exists():
        setFileHandle(
            logger, pathlib.Path.home().joinpath(".rafe", ".cfcache", "package_reports")
        )
    app(prog_name="rafe")
