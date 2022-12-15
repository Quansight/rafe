import sys
from setuptools import setup

import rafe

assert sys.argv[1] in ('develop', 'sdist')


setup(
    name = "rafe",
    version = rafe.__version__,
    author = "Ilan Schnell",
    url = "https://github.com/Quansight/rafe",
    license = "BSD",
    description = "Reproducible Artifacts for Environments",
    long_description = open('README.md').read(),
    packages = ['rafe', 'examples'],
    entry_points = {'console_scripts': [
        'build = rafe.build:main',
    ]},
    package_data = {'examples': ['*/*']},
)
