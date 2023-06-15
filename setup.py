import sys
from setuptools import setup

import rafe


setup(
    name = "rafe",
    version = rafe.__version__,
    author = "Anirrudh Krishnan, Dillon Roach, Ilan Schnell",
    url = "https://github.com/Quansight/rafe",
    license = "BSD",
    description = "A build and environment analysis tool for Python",
    long_description = open('README.md').read(),
    packages = ['rafe'],
    entry_points = {'console_scripts': [
        'rafe = rafe.main:cli',
    ]},
    install_requires = [
        'typer >= 0.7.0',
        'rich',
        'aiohttp',
        'aiofiles',
        'pyyaml',
        'requests',
        'pydantic'
    ]
    #package_data = {'examples': ['*/*']},
)
