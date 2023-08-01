from setuptools import setup

import rafe


setup(
    name="rafe",
    version=rafe.__version__,
    author="Anirrudh Krishnan, Dillon Roach, Ilan Schnell",
    url="https://github.com/Quansight/rafe",
    license="BSD",
    description="A build and environment analysis tool for Python",
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    packages=["rafe"],
    entry_points={
        "console_scripts": [
            "rafe = rafe.main:cli",
        ]
    },
    install_requires=[
        "typer >= 0.7.0",
        "griffe == 0.30.1",
        "rich",
        "GitPython",
        "aiohttp",
        "aiofiles",
        "pyyaml",
        "requests",
        "pydantic",
    ]
)
