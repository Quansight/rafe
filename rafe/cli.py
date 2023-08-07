import typing
import pathlib
import json
import typer

from datetime import datetime

from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.prompt import Prompt

from rafe import __version__
from rafe.griffe_util import check_breaks, verify_removals
from rafe.cfgraph import CFGraph
from rafe.build import build_package
from rafe.config import create_app_dirs
from rafe.logger import logger, setFileHandle

from rafe.plugin import RafePluginManager

from rafe.cli_api import load_repodata, update_all_repodata, fetch_all_package_jsons

app = typer.Typer(rich_markup_mode="rich", add_completion=False)

if pathlib.Path.home().joinpath(".rafe", "plugins_conf.json").exists():
    rpm = RafePluginManager(
        app, pathlib.Path.home().joinpath(".rafe", "plugins_conf.json"), logger
    )


def callback_get_version(value: bool):
    """
    prints the current verson of rafe used
    """
    if value:
        print(f":rocket: Rafe Version: [bold green]{__version__}[/bold green]")
        raise typer.Exit()


def callback_config_init(init: bool):
    """
    initializes the folders that are required for rafe to run
    """
    if init:
        create_app_dirs()
        raise typer.Exit()


search_options = {
    "python_version": typer.Option("py37", "--pyV", help="specify a python version"),
    "package_name": typer.Option(
        ..., "--package", help="search for existance of conda-forge package name"
    ),
    "package_arch": typer.Option(
        "linux-64", "--arch", help="specify an architecture type"
    ),
    "package_version": typer.Option(None, "--version", help="specify package version"),
    "fetch": typer.Option(None, "--fetch", help="specify package version"),
}


@app.command(rich_help_panel="Inspect")
def search(
    python_version: str = search_options["python_version"],
    package_name: str = search_options["package_name"],
    package_version: str = search_options["package_version"],
    package_arch: str = search_options["package_arch"],
    fetch: typing.Optional[bool] = search_options["fetch"],
):
    """
    Given the arguments, this searches for packages across conda-forge, matches them with any given input, and returns them.
    """

    def match_packages(
        cfgraph: CFGraph, repodata_object: str, progress: Progress
    ) -> typing.List:
        """
        Matches Packages, and returns the set of matched possibilities.
        """
        matched_packages = cfgraph.match_packages(
            package_name, package_version, python_version, package_arch, repodata_object
        )
        progress.update(task_id, advance=1)
        return matched_packages

    cfgraph = CFGraph(logger=logger)

    total_steps = 8
    # Add conditional step to fetch
    if fetch is True:
        total_steps += 1

    with Progress() as progress:
        task_id = progress.add_task(
            "[cyan] Total Search progress: [/cyan]", total=total_steps
        )

        # Update Repodata; Total progress advances 6
        update_all_repodata(cfgraph, task_id, progress)

        # Load Repodata; Total progress advance 1
        json_object = load_repodata(cfgraph, task_id, progress, package_arch)

        # Search conda-forge for all possible package matches; Total progress advance 1
        matched_packages = match_packages(cfgraph, json_object, progress)

        # TODO: Implement package filtering here
        logger.info(matched_packages)

        if fetch is True:
            cfgraph.fetch_package_json(package_name, matched_packages[0], package_arch)
            progress.update(task_id, advance=1)

    return


depends_options = {
    "package": typer.Option(..., "--package", help="target package to check"),
    "debug": typer.Option(None, "--debug", help="print matched build tags"),
    "run": typer.Option(None, "--run", help="run check for runtime depends"),
    "build": typer.Option(None, "--build", help="run check for buildtime depends"),
}


@app.command(rich_help_panel="Inspect")
def depends(
    package: str = depends_options["package"],
    debug: typing.Optional[bool] = depends_options["debug"],
    run_flag: typing.Optional[bool] = depends_options["run"],
    build_flag: typing.Optional[bool] = depends_options["build"],
):
    """
    Verify runtime dependencies for a supplied package
    """
    if not (run_flag or build_flag):
        logger.info(
            "Please supply either --run or --build to specify which dependencies to check"
        )
        return
    cfgraph = CFGraph(logger=logger)
    lin64_json_object = cfgraph.load_repodata(arch="linux-64")
    noarch_json_object = cfgraph.load_repodata(arch="noarch")
    if run_flag:
        cfgraph.check_package_build(
            package, lin64_json_object, noarch_json_object, "run", debug
        )
    elif build_flag:
        cfgraph.check_package_build(
            package, lin64_json_object, noarch_json_object, "build", debug
        )
    else:
        logger.info(
            "Please supply either --run or --build to specify which dependencies to check"
        )
    return


manifest_fetch_options = {
    "manifest": typer.Option(..., "--manifest", help="path to manifest json file"),
    "arch": typer.Option("linux-64", "--arch", help="specific architecture to target"),
    "drop_versions": typer.Option(
        None, "--drop-versions", help="drop package version requirements in match"
    ),
    "from_cache": typer.Option(
        None, "--from-cache", help="load the last used matches from missed and matched"
    ),
}


@app.command(rich_help_panel="Inspect")
def manifest_fetch(
    manifest: pathlib.Path = manifest_fetch_options["manifest"],
    arch: str = manifest_fetch_options["arch"],
    from_cache: typing.Optional[bool] = manifest_fetch_options["from_cache"],
    drop_versions: typing.Optional[bool] = manifest_fetch_options["drop_versions"],
):
    """
    Takes formatted JSON manifest and caches matched libcfgraph artifacts
    """
    cfgraph = CFGraph(logger=logger)
    total_steps = 9

    with Progress() as progress:
        task_id = progress.add_task(
            "[cyan] Total Package Match Progress: [/cyan]", total=total_steps
        )

        if manifest.exists():
            (
                package_arch,
                python_version_requested,
                manifest_packages,
            ) = cfgraph.read_manifest(manifest)
            progress.update(task_id, advance=1)

            update_all_repodata(cfgraph, task_id, progress)

            json_object = load_repodata(cfgraph, task_id, progress, arch)

            if arch != "linux-64":
                package_arch = arch
            if package_arch == "noarch":
                python_version_requested = None

            if from_cache is True:
                to_fetch = cfgraph.read_missed_and_matched_from_cache()
            else:
                to_fetch = cfgraph.missed_and_matched_from_manifest(
                    package_arch,
                    python_version_requested,
                    manifest_packages,
                    drop_versions,
                    json_object,
                )

            progress.update(task_id, advance=1)

            logger.info(f"Fetching package jsons for matched {len(to_fetch)}")

            fetch_all_package_jsons(to_fetch, progress)

        else:
            logger.error(
                "The provided manifest file does not exist or could not be found."
            )
            raise typer.Exit()


depends_on_options = {
    "package_name": typer.Option(
        ...,
        "--package",
        help="check all cached json files for inclusion of given package in build dependency",
    ),
    "arch": typer.Option(
        "linux-64", "--arch", help="specified architecture to generate dependencies for"
    ),
    "output": typer.Option(
        ..., "-o", help="Path of where to place the resulting query's output file"
    ),
}


@app.command(rich_help_panel="Inspect")
def depends_on(package_name: str = depends_on_options["package_name"]):
    """
    Searches cached jsons for build-time dependency on given package
    """
    cfgraph = CFGraph(logger=logger)
    matches = cfgraph.check_all_package_jsons("linux-64", package_name)
    print(matches)
    return


convert_missed_options = {
    "path": typer.Option(..., "--path", help="path to json produced by rafe"),
    "arch": typer.Option(
        "linux-64", "--arch", help="specified architecture to set in new manifest"
    ),
    "pyVer": typer.Option(
        None, "--pyVer", help="specified python version to set in new manifest"
    ),
    "output": typer.Option(
        ".", "--output", help="directory location to write output file"
    ),
}


@app.command(rich_help_panel="Inspect")
def convert_missed(
    json_path: pathlib.Path = convert_missed_options["path"],
    arch: str = convert_missed_options["arch"],
    pyVer: str = convert_missed_options["pyVer"],
):
    """
    Creates a new manifest based on the missed_packages from a previous manifest match json
    """
    if arch == "noarch":
        pyVer = ""

    if (pyVer != None) and (pyVer != ""):
        pyVer = "".join(pyVer.split("."))
        if pyVer[:2] != "py":
            pyver = "py" + pyVer
    if len(pyVer) > 4:
        logger.error("PyVer format should be 'py37' or '3.7' or '37'")
        raise typer.Exit()

    if json_path.exists():
        with open(json_path, "r") as f:
            manifest_json = json.load(f)
    else:
        raise FileNotFound()

    converted = {
        "python_version_requested": pyVer,
        "package_arch": arch,
        "packages": [],
    }
    converted["packages"] = manifest_json["missed_packages"]
    if json_path.parent.is_dir():
        file_name = (
            f"converted_missed_{arch}_{pyVer}_{datetime.now().strftime('%H%M%S')}.json"
        )
        output = json_path.parent.joinpath(file_name)
        try:
            with open(output, "w") as write_file:
                json.dump(converted, write_file)
            logger.info(f"Converted json written to: {str(output)}")
        except:
            logger.error("Error writing to file")
            raise typer.Exit()
    else:
        logger.error(
            "Parent path of input file not a directory, aborting without specified output dir."
        )
        raise typer.Exit()
    return


build_options = {
    "recipe_dir": typer.Option(
        ..., "--recipe-dir", help="path to build recipies for packages"
    ),
    "package": typer.Option(..., "--package", help="name of package to build"),
}


@app.command(rich_help_panel="Build")
def build(
    recipe_dir: pathlib.Path = build_options["recipe_dir"],
    package: pathlib.Path = build_options["package"],
):
    """
    Builds a python wheel given a directory and recipe
    """
    package_path = pathlib.Path.joinpath(recipe_dir, package)

    if package_path.exists():
        result = build_package(package_path)
        if result == 0:
            raise typer.Exit()
    else:
        raise FileNotFoundError(
            f'Cannot find "{package_path}" ({package_path.absolute()})'
        )


def callback_plugin_add(path):
    if isinstance(path, pathlib.Path) and path.exists():
        absolute_path = path.resolve()
        name = path.name
        entrypoint = Prompt.ask(
            "Please Define an entrypoint; This is the function that will be used like rafe <function>"
        )
        rpm.add_plugin(name, absolute_path, entrypoint)
    else:
        # TODO Investigate why this gets called back.
        ...


def callback_plugin_list():
    p = rpm.list_plugins()
    table = Table(title="Rafe Plugins")

    table.add_column("Name", style="green")
    table.add_column("Entrypoint", style="cyan")
    table.add_column("Path", style="purple")

    for r in p:
        table.add_row(r["name"], r["entrypoint"], r["path"])

    console = Console()
    console.print(table)
    return


check_api_breaks_options = {
    "package": typer.Option(
        ..., "--package", help="Name of package folder name to check"
    ),
    "old_tag": typer.Option(..., "--old", help="First package version in comparison"),
    "new_tag": typer.Option(..., "--new", help="Second package version in comparison"),
    "path": typer.Option(
        None,
        "--path",
        help="Path to package source. Default behavior expects folder in .rafe/work/{package}",
    ),
    "break_type": typer.Option(
        None,
        "--type",
        help="Type of api breakage to check. Default behavior dumps all breaks.",
    ),
    "output": typer.Option(
        None, "--out", help="Path for output json. Default behavior dumps to pwd."
    ),
}


@app.command(rich_help_panel="API Breaks")
def check_api_breaks(
    package: str = check_api_breaks_options["package"],
    old_tag: str = check_api_breaks_options["old_tag"],
    new_tag: str = check_api_breaks_options["new_tag"],
    path: pathlib.Path = check_api_breaks_options["path"],
    break_type: str = check_api_breaks_options["break_type"],
    output_path: pathlib.Path = check_api_breaks_options["output"],
):
    """
    Compares two instances of the same package to check for API breaking changes between versions.
    Default behavior is to expect you have a source copy of the package in .rafe/work/{package} with .git info
    """
    if path is None:
        path = pathlib.Path.home().joinpath(".rafe", "work", package)

    # could consider setting up an auto-acquire here
    if not path.exists():
        raise FileNotFoundError(
            f'Missing "{path}" (did you clone the "{package}" repo?)'
        )
    if output_path is None:
        output_path = pathlib.Path.cwd()

    temp = check_breaks(
        package, old_tag, new_tag, path, break_type, output_path, logger
    )

    return


verify_breaks_options = {
    "package": typer.Option(
        ...,
        "--package",
        help="Import name of package to check. May be different than package name.",
    ),
    "path": typer.Option(..., "--path", help="Path to breakage json source."),
}


@app.command(rich_help_panel="API Breaks")
def verify_breaks(
    package: str = check_api_breaks_options["package"],
    path: pathlib.Path = check_api_breaks_options["path"],
):
    """
    Assumes 'new' package version has been installed in some way and added to the pythonpath
    The easiest route would likely be to unzip a wheel into a working folder and add that folder
    to $PYTHONPATH. e.g. on linux: export PYTHONPATH=<local path>:$PYTHONPATH
    """
    if pathlib.Path(path).exists():
        verify_removals(package, path, logger)
    else:
        logger.error(f"Did not find {path}.")

    return


plugin_configuration_options = {
    "add": typer.Option(
        None, "--add", help="Add a plugin given a folder", callback=callback_plugin_add
    ),
    "list": typer.Option(
        None,
        "--list",
        help="Print the current plugin configuration",
        callback=callback_plugin_list,
    ),
    "generate-cli-template": "",
    "clean-cache": typer.Option(
        None, "--clean-cache", help="Cleans the plugin cache", callback=None
    ),
    "show-cache": typer.Option(
        None, "--show-cache", help="Look at the currently cached objects", callback=None
    ),
}


@app.command(rich_help_panel="Utilities")
def plugin(
    add: typing.Optional[pathlib.Path] = plugin_configuration_options["add"],
    lst: typing.Optional[bool] = plugin_configuration_options["list"],
    clean_cache: typing.Optional[bool] = plugin_configuration_options["clean-cache"],
    show_cache: typing.Optional[bool] = plugin_configuration_options["show-cache"],
):
    """
    Manages rafe plugins and configuration.
    """
    return


configuration_options = {
    "init": typer.Option(
        None,
        "--init",
        help="initializes a configuration with sane defaults",
        callback=callback_config_init,
        is_eager=True,
    ),
}


@app.command(rich_help_panel="Utilities")
def config(init: typing.Optional[bool] = configuration_options["init"]):
    """
    Manages the rafe configuration. Run `--init` to get started!
    """
    return


main_options = {
    "version": typer.Option(
        None,
        "--version",
        help="prints the current version",
        callback=callback_get_version,
        is_eager=True,
    ),
}


@app.callback()
def main(version: typing.Optional[bool] = main_options["version"]):
    """
    Rafe is a build tool for python
    """
    return


def run():
    if pathlib.Path.home().joinpath(".rafe").exists():
        setFileHandle(
            logger, pathlib.Path.home().joinpath(".rafe", ".cfcache", "package_reports")
        )
    app(prog_name="rafe")
