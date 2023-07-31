import pydantic
import pathlib
import json

from rafe.logger import logger
from os.path import dirname, join

class RafeConfig(pydantic.BaseModel):
    pass

def create_rafe_rootdir(rootdir: pathlib.Path) -> None:
    """
    """
    if not rootdir.exists():
        rootdir.mkdir(parents=True, exist_ok=True)
        logger.info('[bold green] CREATE DIRECTORY: [/bold green]'  + str(rootdir), extra={"markup": True}) 
    else:
        logger.warn('[bold yellow] DIRECOTRY EXISTS: [/bold yellow]'  + str(rootdir), extra={"markup": True}) 
    return 

def create_cfcache_subfolder(rootdir: pathlib.Path) -> None:
    """
    Given a root directory, setup the folder structure for cfgraph
    """
    folders = ['.cfcache/', '.cfcache/jsons/', '.cfcache/package_reports', '.cfcache/jsons/linux-64', '.cfcache/jsons/noarch']
    for sf in folders:
        folder = rootdir.joinpath(sf)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info('[bold green] CREATE DIRECTORY: [/bold green]'  + str(folder), extra={"markup": True}) 
        else:
            logger.warn('[bold yellow] DIRECOTRY EXISTS: [/bold yellow]'  + str(folder), extra={"markup": True}) 
    return 


def create_work_subfolder(rootdir: pathlib.Path) -> None:
    """
    Given a root directory, create general work folder
    """
    folders = ['work']
    for sf in folders:
        folder = rootdir.joinpath(sf)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info('[bold green] CREATE DIRECTORY: [/bold green]'  + str(folder), extra={"markup": True}) 
        else:
            logger.warn('[bold yellow] DIRECOTRY EXISTS: [/bold yellow]'  + str(folder), extra={"markup": True}) 
    return 


def create_plugin_config(rootdir: pathlib.Path) -> None:
    """
    Given the root directory, create a plugin json.
    """
    plugin_configuration_json: pathlib.Path = rootdir.joinpath('plugins_conf.json')

    if not plugin_configuration_json.exists():
        logger.info('[bold green] CREATE PLUGIN CONFIGURATION [/bold green]'  + str(plugin_configuration_json), extra={"markup": True}) 
        
        empty_plugins = {"plugins" : []}
        with open(plugin_configuration_json, 'w') as f:
            f.write(json.dumps(empty_plugins))

    else:
        logger.warn('[bold yellow] FILE EXISTS: [/bold yellow]'  + str(plugin_configuration_json), extra={"markup": True}) 

    return

def create_app_dirs(rootdir = pathlib.Path.home().joinpath('.rafe/')) -> int:
    """
    Given a root directory, create it inside the homedir and then create
    subfolders for neccesary functions.
    """
    create_rafe_rootdir(rootdir)
    create_cfcache_subfolder(rootdir)
    create_plugin_config(rootdir)
    create_work_subfolder(rootdir)
    return 0    


class RafeConfig(pydantic.BaseModel):
    pass


def create_rafe_rootdir(rootdir: pathlib.Path) -> None:
    """ """
    if not rootdir.exists():
        rootdir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "[bold green] CREATE DIRECTORY: [/bold green]" + str(rootdir),
            extra={"markup": True},
        )
    else:
        logger.warn(
            "[bold yellow] DIRECOTRY EXISTS: [/bold yellow]" + str(rootdir),
            extra={"markup": True},
        )
    return


def create_cfcache_subfolder(rootdir: pathlib.Path) -> None:
    """
    Given a root directory, setup the folder structure for cfgraph
    """
    folders = [
        ".cfcache/",
        ".cfcache/jsons/",
        ".cfcache/package_reports",
        ".cfcache/jsons/linux-64",
        ".cfcache/jsons/noarch",
    ]
    for sf in folders:
        folder = rootdir.joinpath(sf)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(
                "[bold green] CREATE DIRECTORY: [/bold green]" + str(folder),
                extra={"markup": True},
            )
        else:
            logger.warn(
                "[bold yellow] DIRECOTRY EXISTS: [/bold yellow]" + str(folder),
                extra={"markup": True},
            )
    return


def create_plugin_config(rootdir: pathlib.Path) -> None:
    """
    Given the root directory, create a plugin json.
    """
    plugin_configuration_json: pathlib.Path = rootdir.joinpath("plugins_conf.json")

    if not plugin_configuration_json.exists():
        logger.info(
            "[bold green] CREATE PLUGIN CONFIGURATION [/bold green]"
            + str(plugin_configuration_json),
            extra={"markup": True},
        )

        empty_plugins = {"plugins": []}
        with open(plugin_configuration_json, "w") as f:
            f.write(json.dumps(empty_plugins))

    else:
        logger.warn(
            "[bold yellow] FILE EXISTS: [/bold yellow]"
            + str(plugin_configuration_json),
            extra={"markup": True},
        )

    return


def create_app_dirs(rootdir=pathlib.Path.home().joinpath(".rafe/")) -> int:
    """
    Given a root directory, create it inside the homedir and then create
    subfolders for neccesary functions.
    """
    create_rafe_rootdir(rootdir)
    create_cfcache_subfolder(rootdir)
    create_plugin_config(rootdir)
    create_work_subfolder(rootdir)
    return 0


root_dir = dirname(dirname(__file__))
src_cache = join(root_dir, "src_cache")
work_dir = join(root_dir, "work")
