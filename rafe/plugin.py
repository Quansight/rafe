import os
import sys
import pathlib
import json
import logging

import importlib.util

import typer

"""
This file helps rafe discover, register, and utilize plugins.

To register plugins, there will be two options:
    1) CLI Based Plugins (metaconvert)
    and
    2) PyLint Plugins (TBD)

We will discover both the module and any exposed flie and cli applicatons associated with them and
add them to rafe before runtime.
"""


class RafePlugin:
    """
    A class for storing information on runtime plugins. If there is a cli.py
    exposed, then it adds it to the command line.

    Working as importable is the ideal other way to solve this problem.
    """

    def __init__(
        self, name: str, path: pathlib.Path, entrypoint: str, isCLI: bool = True
    ):
        self.parent_module = self._load_parent_module(name, path)

        if isCLI == True:
            self.cli_module = self._load_cli_module(name, path)
            self.cli_callable = getattr(self.cli_module, entrypoint)

    def _load_parent_module(self, name, path):
        spec = importlib.util.spec_from_file_location(
            name, path.joinpath("__init__.py")
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def _load_cli_module(self, name, path):
        module_cli_import = f"{name}.cli"
        spec = importlib.util.spec_from_file_location(
            module_cli_import, path.joinpath("cli.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class RafePluginManager:
    def __init__(self, app: typer.Typer, path: pathlib.Path, logger: logging.Logger):
        """
        Initializes the configuration class.
        """
        self.logger = logger
        self.configuration_path = path

        self.raw: Dict = self.read_json(path)

        self.plugins: List = self.raw["plugins"]

        if len(self.plugins) == 0:
            self.logger.debug("No plugins found.")
        else:
            self.logger.debug("Loading plugins...")
            self.load_plugins(app)

    def add_plugin(self, name, path, entrypoint):
        entry = {"name": name, "path": str(path), "entrypoint": entrypoint}

        self.plugins.append(entry)
        self.logger.debug(f"Adding plugin {name}")
        self.write_json(self.plugins, self.configuration_path)

    def list_plugins(self):
        p = self.read_json(self.configuration_path)
        return p["plugins"]

    def load_plugins(self, app):
        for idx in range(len(self.plugins)):
            name, path, entrypoint = (
                self.plugins[idx]["name"],
                self.plugins[idx]["path"],
                self.plugins[idx]["entrypoint"],
            )
            path = pathlib.Path(path)
            self.plugins[idx] = RafePlugin(name=name, path=path, entrypoint=entrypoint)
            self.logger.debug(f"Loaded Plugin: {name}")

        for rplugin in self.plugins:
            if hasattr(rplugin, "cli_callable") is True:
                self.logger.debug(f"Registering Plugin: {name} CLI")
                rplugin.cli_callable = app.command(rich_help_panel="Plugins")(
                    rplugin.cli_callable
                )
                self.logger.debug(f"Successfully Registered: {name} CLI")
            else:
                self.logger.debug(f"No CLI found for plugin {name}")

    @staticmethod
    def write_json(o, path: pathlib.Path):
        """
        Writes the configuration file with the currently stored plugins
        """
        d = {}
        d["plugins"] = o
        with open(path, "w") as f:
            f.write(json.dumps(d))
        return

    @staticmethod
    def read_json(path: pathlib.Path):
        """
        Reads a configuration file for the plugins and initializes them.
        """
        with open(path, "r") as f:
            j = json.loads(f.read())
        return j
