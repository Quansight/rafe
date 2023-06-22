import asyncio
import pathlib
import typing
import requests

import aiohttp
import aiofiles

from urllib.request import urlopen
from rich import print
from rich.progress import Progress
from rafe.cfgraph import CFGraph

log_color = (
    lambda color, hl_string, string: f"[bold {color}]"
    + hl_string
    + "[/bold"
    + f" {color}] | "
    + str(string)
)


def load_repodata(
    cfgraph: CFGraph, task_id, progress: Progress, arch: str
) -> typing.Union[str, bool]:
    """
    A wrapper function to load repodata objects into a collection of JSON formatted strings.
    """

    # win64_json_object = cfgraph.load_repodata_jsons(arch="win64")

    if arch == "noarch":
        noarch_json_object = cfgraph.load_repodata(arch="noarch")
        progress.update(task_id, advance=1)
        return noarch_json_object

    if arch == "linux-64":
        linux64_json_object = cfgraph.load_repodata(arch="linux-64")
        progress.update(task_id, advance=1)
        return linux64_json_object

    if arch == "win64":
        cfgraph.logger.error(
            "Windows 64-Bit is unsupported. Please raise an issue with the developers if you would like to see this."
        )

    if arch == "win32":
        cfgraph.logger.error(
            "Windows 64-Bit is unsupported. Please raise an issue with the developers if you would like to see this."
        )

    return False


def update_all_repodata(cfgraph: CFGraph, task_id, progress: Progress):
    """
    A wrapper function which calls the update_repodata_arch function in cfgraph.py
    Refactor this later, pressed on time lol.
    """
    # grayskull
    if not cfgraph.check_update_repodata(cfgraph.config.grayskull_map):
        cfgraph.logger.info(
            log_color("green", "CACHED", cfgraph.config.grayskull_map),
            extra={"markup": True},
        )
        progress.update(task_id, advance=2)
    else:
        fetch_repodata_file(
            cfgraph.urls.grayskull_map, cfgraph.config.grayskull_map, progress
        )
        progress.update(task_id, advance=2)

    # linux-64
    if not cfgraph.check_update_repodata(cfgraph.config.linux64_json):
        cfgraph.logger.info(
            log_color("green", "CACHED", cfgraph.config.linux64_json),
            extra={"markup": True},
        )
        progress.update(task_id, advance=2)
    else:
        fetch_repodata_file(
            cfgraph.urls.linux64_repodata, cfgraph.config.linux64_json, progress
        )
        progress.update(task_id, advance=2)

    # noarch
    if not cfgraph.check_update_repodata(cfgraph.config.noarch_json):
        cfgraph.logger.info(
            log_color("green", "CACHED", cfgraph.config.noarch_json),
            extra={"markup": True},
        )
        progress.update(task_id, advance=2)
    else:
        fetch_repodata_file(
            cfgraph.urls.noarch_repodata, cfgraph.config.noarch_json, progress
        )
        progress.update(task_id, advance=2)


def fetch_all_package_jsons(to_fetch: typing.List[typing.Tuple], progress: Progress):
    sem = asyncio.BoundedSemaphore(10)
    # session = aiohttp.ClientSession(trust_env=True)

    async def fetch_file(url: str, destination: pathlib.Path):
        async with sem, aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(url) as response:
                print(f"Get {url}")
                """
                total_size = int(response.headers.get("Content-Length", 0))
                if total_size == 0:
                    site = urlopen(url)
                    meta = site.info()
                    total_size = int(meta["Content-Length"])
                """
                assert response.status == 200
                data = await response.read()
            # print(type(data), type(response))

        async with aiofiles.open(destination, "wb") as out:
            print(f"Writing | {destination.name}")
            await out.write(data)

    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(fetch_file(i[0], i[1])) for i in to_fetch]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    return


def fetch_repodata_file(url: str, destination: pathlib.Path, progress: Progress):
    """
    Fetches the repodata files with special streaming with the URL. Saves it to the
    filepath defined by destination.
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("Content-Length", 0))
    if total_size == 0:
        site = urlopen(url)
        meta = site.info()
        total_size = int(meta["Content-Length"])

    task_id = progress.add_task(
        f"[cyan] Get {destination.name} ({total_size/(1024*1024):.2f}Mb):" + " [/cyan]",
        total=total_size,
    )

    with open(destination, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
            progress.update(task_id, advance=len(chunk))


def match_nearest_version(how: str = "package") -> None:
    """
    Matches the nearest version found for a missed package depending on the specified parameter.

    @param how -> str either set to "package" or "pyVer"
    """

    pass


def missed_and_matched_from_manifest(
    cfgraph,
    package_arch,
    python_version_requested,
    manifest_packages,
    drop_versions,
    json_object,
):
    """
    A gigantic loop to be moved outside of here, and to the cli.
    """

    if python_version_requested != None:
        python_version_matches = [
            i for i in json_object["packages"] if python_version_requested in i
        ]

    else:
        python_version_matches = json_object["packages"]

    package_report = {"matched_packages": [], "missed_packages": []}

    converted_grayskull_map = cfgraph.convert_grayskull_map()

    for i in manifest_packages:
        if ("pyVer" in i.keys()) and (i["pyVer"] == "2.7"):
            cfgraph.logger.info(
                "[bold yellow] Skipping [/bold yellow]"
                + f"{i['name']}=={i['version']}, pyVer = {i['pyVer']}",
                extra={"markup": True},
            )
            continue

        i["name"] = cfgraph.convert_pypi_conda_name(i["name"], converted_grayskull_map)
        i["name"] = i["name"].lower()  # conda packages are all lower
        i["version"] = i["version"].split("+")[0]

        if i["version"] == "0.0.0" or len(i["version"].split(".")) > 3 or drop_versions:
            i["version"] = ""

        matched_package = cfgraph.match_versioned_packages(
            i["name"], i["version"], python_version_matches
        )

        if len(matched_package) > 0:
            breakpoint()
            cfgraph.fetch_package_json(i["name"], matched_package[0], package_arch)
            package_report["matched_packages"].append(
                {"name": i["name"], "version": i["version"]}
            )
            cfgraph.logger.info(
                "[bold green] Match Found [/bold green]"
                + f"{i['name']}=={i['version']}",
                extra={"markup": True},
            )

        elif "eggName" in i:
            i["eggName"] = cfgraph.convert_pypi_conda_name(
                i["eggName"], converted_grayskull_map
            )
            i["eggName"] = i["eggName"].lower()

            matched_package = cfgraph.match_versioned_packages(
                i["eggName"], i["version"], python_version_matches
            )

            if len(matched_package) > 0:
                cfgraph.fetch_package_json(
                    i["eggName"], matched_package[0], package_arch
                )
                package_report["matched_packages"].append(
                    {"name": i["name"], "version": i["version"]}
                )
                cfgraph.logger.info(
                    "[bold green] Match Found [/bold green]"
                    + f"{i['name']}/{i['eggName']}=={i['version']}",
                    extra={"markup": True},
                )

            else:
                package_report["missed_packages"].append(
                    {"name": i["name"], "version": i["version"]}
                )
                cfgraph.logger.info(
                    "[bold red] No Matches [/bold red]"
                    + f"{i['name']}/{i['eggName']}=={i['version']}",
                    extra={"markup": True},
                )
        else:
            package_report["missed_packages"].append(
                {"name": i["name"], "version": i["version"]}
            )
            cfgraph.logger.info(
                "[bold red] No Matches [/bold red]" + f"{i['name']}=={i['version']}",
                extra={"markup": True},
            )

    output = cfgraph.config.package_reports.joinpath(
        pathlib.Path(f"cfgraph-package-report-{datetime.now()}.json")
    )

    with open(output, "w") as write_file:
        json.dump(package_report, write_file)
        cfgraph.logger.info(
            f"[bold pink] WROTE SUMMARY FILE: " + "[/bold pink]" + str(output),
            extra={"markup": True},
        )
