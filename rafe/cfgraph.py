import requests
import pathlib
import json
import yaml
import os
import re
import logging

from typing import Union, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class CFGraphPaths():
    """
    Given a default home or base path, create and check for these files.
    """

    home: pathlib.Path = pathlib.Path.home()
    cache_age_minutes: int = 120

    def __post_init__(self):

        self.cache: pathlib.Path = self.home.joinpath('.rafe', '.cfcache/')

        self.package_reports: pathlib.Path = self.cache.joinpath('package_reports')
        self.package_jsons: pathlib.Path = self.cache.joinpath('jsons')
        self.match_cache: pathlib.Path = self.cache.joinpath('cache', 'matches')

    
        self.noarch_json: pathlib.Path = self.cache.joinpath(pathlib.Path("noarch_repodata.json"))
        self.linux64_json: pathlib.Path = self.cache.joinpath(pathlib.Path("linux-64_repodata.json"))
        self.win64_json: pathlib.Path = self.cache.joinpath(pathlib.Path("win64_repodata.json"))
        self.grayskull_map: pathlib.Path = self.cache.joinpath(pathlib.Path("grayskull_pypi_mapping.yaml"))
    
@dataclass
class CFGraphURLs():
    """
    By deafult, these are the URLs that the application will check against.
    """
    noarch_repodata: str = "https://conda.anaconda.org/conda-forge/noarch/repodata.json"
    linux64_repodata: str = "https://conda.anaconda.org/conda-forge/linux-64/repodata.json"
    grayskull_map: str = "https://raw.githubusercontent.com/regro/cf-graph-countyfair/master/mappings/pypi/grayskull_pypi_mapping.yaml"

    def __post_init__(self):
        # TODO Update this URL to compile on load
        self.package_root: str = "https://github.com/regro/libcfgraph/raw/master/artifacts/{package_requested}/conda-forge/{package_arch}/"

class CFGraph():
    """
    This class manages the local repodata for _where_ packages come from. It can be initalized with any filepath,
    and will look for the filepaths that it needs in order to work.
    """
    def __init__(self, 
                arch: str = "linux-64", 
                configuration: CFGraphPaths = CFGraphPaths(), 
                urls: CFGraphURLs = CFGraphURLs(),
                logger: logging.Logger = None, 
        ):

        self.config = configuration 
        self.urls = urls

        # Initialize the logging mechanism
        if isinstance(logger, logging.Logger):
                self.logger = logger
        else:
            logger = logging.getLogger(__name__)    
            self.logger = logger

    ###### REPODATA MANAGEMENT ######

    def get_file_age(self, filepath: pathlib.Path)-> timedelta:
        """
        Get the age of a file and when it was last modified. Returns a datetime.timedelta
        """
        if filepath.exists():
            last_modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            current_time = datetime.now()

            file_age = current_time - last_modified_time
        else:
            file_age = timedelta(seconds=9999999)

        return file_age
    
    def convert_pypi_conda_name(self, package_name: str, gs_map: Dict) -> str:
        """
        This function converts a pypi package name to a conda name using an initialized grayskull map if it's in there. Else,
        it just returns the input.
        """

        if package_name in gs_map.keys():
            conda_name = gs_map[package_name]
            self.logger.info("[bold purple] Converted Package Name: [/bold purple]" +  "[bold blue]Py[/bold blue][bold yellow]Pi[/bold yellow] | " + f'{package_name} ->' \
                    + '[bold Green] Conda[/bold green] |' + f' {conda_name}', extra = {"markup": True})
            return conda_name
        return package_name
    
    def fetch_repodata_file(self, url: str, destination: pathlib.Path):
        """
        DEPRECATED

        Fetches the repodata files with special streaming with the URL. Saves it to the
        filepath defined by destination. 
        response = requests.get(url, stream=True)
        response.raise_for_status()
    
        total_size = response.headers.get("Content-Length", 0)
        if total_size == 0:
            site = urlopen(url)
            meta = site.info()
            total_size = int(meta["Content-Length"])

        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        """

    def check_update_repodata(self, filepath: pathlib.Path) -> bool:
        """
        Given a filepath (to a JSON or YAML formatted repodata file) and a URL, check and see
        whether an update is needed. 

        If return is True, you'll want to call self.update_repodata()
        """
        age = self.get_file_age(filepath).total_seconds() / 60 

        if age >= self.config.cache_age_minutes:
            return True
        else:
            return False
    
    def update_repodata(self, arch : str) -> None:
        """
        Runs the "update repodata" method on all filepaths and URLS as described in the
        input objects. 
        """
        grayskull_url = self.urls.grayskull_map

        if arch == "linux-64":
            path = self.config.linux64_json
            url = self.urls.linux64_repodata

        elif arch == "noarch":
            path = self.config.noarch_json
            url = self.urls.noarch_repodata

        #elif arch == "win64"
        #   path = self.config.win64_json
        #   url = self.urls.linux64_repodata
        #   noarch_path = self.config.noarch_json
        #   noarch_url = self.urls.noarch_repodata
        return


    def load_repodata(self, arch: str = "noarch") -> Union[Dict, None]:
        """
        Given an architecture, return a json object. Defaults to noarch.
        Possible arch arguments: "noarch", "linux-64", "win64"
        """
        if arch == "linux-64":
            path = self.config.linux64_json
        elif arch == "noarch":
            path = self.config.noarch_json
        elif arch == "win64":
            path = self.config.win64_json

        if path.exists():
            with open(path, 'r') as read_file:
                json_object = json.load(read_file)

        missing_timestamp = [i for i in json_object['packages'] if 'timestamp' not in json_object['packages'][i].keys()]
        for i in missing_timestamp:
            json_object['packages'][i]['timestamp'] = 0

        self.logger.info(f'Load Repodata | from {path} | Success')
        return json_object

        
    ##### PACKAGE VERSION MATCHING ######

    @staticmethod
    def get_package_name(s: str) -> str:
        """
        Gets the human-readable name of the package from the uploaded package tarball name.
        """
        pattern = r'^(.*?)(?=-\d+\.\d+\.\d+)'
        match = re.match(pattern, s)
        return match.group(0) if match else ''

    @staticmethod
    def get_package_version(filename: str) -> Union[str, None]:
        """
        Gets the package version given a filename string.
        """
        pattern = r'(?<=-)\d+\.\d+\.\d+'
        match = re.search(pattern, filename)
        return match.group(0) if match else None

    @staticmethod
    def get_package_build(filename: str) -> Union[str, None]:
        """
        Gets the package build identifier from filename string.
        """
        pattern = r'(?<=\d-).*(?=.tar.bz2)'
        match = re.search(pattern, filename)
        return match.group(0) if match else ''

    def fetch_package_json(self, requested_package, matched_package, arch = "linux-64"):
        """
        Fetches the metadata for a given single package.
        """
        
        root_url = f"https://github.com/regro/libcfgraph/raw/master/artifacts/{requested_package}/conda-forge/{arch}/"

        if len(matched_package) > 0:
            url = root_url+matched_package.replace(".tar.bz2",".json")
        else:
            url = ""    
    
        self.logger.info(f'Fetching from {url}')
        pkg_metadata_json_filepath = self.config.package_jsons.joinpath(arch).joinpath(url.split("/")[-1])

        if not pkg_metadata_json_filepath.exists():
            with open(pkg_metadata_json_filepath,'wb') as write_file:
                self.logger.info("[bold blue] Downloading,.. [/bold blue]"+ f"{url.split('/')[-1]}", extra={"markup": True}) 
                r = requests.get(url)
                if len(r.content)>0:
                    write_file.write(r.content)


    def format_package_json(self, requested_package, matched_package, arch = "linux-64"):
        """
        Fetches the metadata for a given package.
        """
        
        root_url = f"https://github.com/regro/libcfgraph/raw/master/artifacts/{requested_package}/conda-forge/{arch}/"

        if len(matched_package) > 0:
            url = root_url+matched_package.replace(".tar.bz2",".json")
        else:
            url = ""    

        pkg_metadata_json_filepath = self.config.package_jsons.joinpath(arch).joinpath(url.split("/")[-1])
        return (url, pkg_metadata_json_filepath)

            
    def read_missed_and_matched_from_cache(self):
        """
        Reads a cached manifest file and then uses that if a search was just done. 
        """
        fp = list(self.config.package_reports.glob('cfgraph-to-fetch-*.json'))[-1]
        with open(fp, 'r') as read_file:
            json_object = json.load(read_file)
        
        return json_object

    def read_manifest(self, manifest_file_path):
        """
        Reads a JSON formatted manifest. You can do this using the metaconvert functon.
        """
        with open(manifest_file_path, 'r') as read_file:
            json_object = json.load(read_file)
        
        package_arch = json_object["package_arch"]
        python_version_requested = json_object["python_version_requested"]
        manifest_packages = json_object["packages"]
        
        return package_arch, python_version_requested, manifest_packages


    def match_packages(self, package_requested, version_requested, python_version_requested, package_arch, json_object):

        self.logger.info(f'Matching | {package_requested} | {version_requested} ')
        
        all_matches = [i for i in json_object["packages"] if self.get_package_name(i) == package_requested]
        
        if version_requested != None:
            version_matches = [i for i in all_matches if self.get_package_version(i) == version_requested]

        else:
            version_matches = all_matches
    
        if python_version_requested != "":
            version_matches = [i for i in version_matches if python_version_requested in i]
            
        return version_matches

    def choose_build(self, version_requested, matched_packages, json_object):
        if len(matched_packages) == 1:
            return matched_packages[0]
        if (version_requested == "") or (version_requested is None):
            repo_matched_subset = {i:json_object[i] for i in matched_packages}
            return [i[0] for i in sorted(repo_matched_subset.items(), key=lambda x:x[1]['timestamp'])][-1]
        else:
            versions = [json_object[i]['version'] for i in matched_packages]
            if version_requested in versions:
                version_exact = version_requested
            else:
                versions2 = versions.copy()
                versions2.append(version_requested)
                versions2.sort(key=StrictVersion)
                version_index = versions2.index(version_requested)
                if version_index == len(versions2) - 1:
                    version_index = version_index - 1
                else:
                    version_index = version_index + 1
                version_exact = versions2[version_index]
            repo_matched_subset = {i:json_object[i] for i in matched_packages}
            versioned_subset = {i:repo_matched_subset[i] for i in repo_matched_subset if repo_matched_subset[i]['version'] == version_exact}
            if len(versioned_subset) == 1:
                return versioned_subset[0]
            else:
                return [i[0] for i in sorted(versioned_subset.items(), key=lambda x:x[1]['timestamp'])][-1]
        return []

    def match_versioned_packages(self, package_requested, version_requested, json_object):
        
        if version_requested == "":
            version_requested = None
    
        if version_requested != None:
            version_matches = [i for i in json_object if json_object[i]["name"] == package_requested and json_object[i]["version"] == version_requested]
        else:
            version_matches = [i for i in json_object if json_object[i]["name"] == package_requested]
            
        return version_matches

    def check_build_host_depends(self, package_requested: str, json_object: str):
        if 'build' in json_object['rendered_recipe']['requirements'].keys():
            build_match = [i for i in json_object['rendered_recipe']['requirements']['build'] if package_requested in i]
        else:
            build_match = []
        if 'host' in json_object['rendered_recipe']['requirements'].keys():
            host_match = [i for i in json_object['rendered_recipe']['requirements']['host'] if package_requested in i]
        else:
            host_match = []

        return build_match, host_match

    def check_package_build(self, package_requested, lin64_json_object, noarch_json_object, mode, debug):
        package_requested = package_requested.lower()
        all_jsons = list(self.config.package_jsons.joinpath("linux-64").glob("*.json"))
        picked_json = [i for i in all_jsons if package_requested == self.get_package_name(str(i.name))]
        if len(picked_json)==0:
            all_jsons = list(self.config.package_jsons.joinpath("noarch").glob("*.json"))
            picked_json = [i for i in all_jsons if package_requested == self.get_package_name(str(i.name))]

        if len(picked_json)>0:
            picked_json = picked_json[0]
        else:
            self.logger.info(f"Unable to find local json for requested '{package_requested}'")
            return
        with open(picked_json, 'r') as f:
            package_json = json.load(f)

        if mode == 'run':
            if 'run' in package_json['rendered_recipe']['requirements'].keys():
                depends = [i.split(" ")[0] for i in package_json['rendered_recipe']['requirements']['run']]
            self.logger.info(f"Run-time dependencies for {package_requested}:")
        elif mode == 'build':
            if 'build' in package_json['rendered_recipe']['requirements'].keys():
                depends_build = [i.split(" ")[0] for i in package_json['rendered_recipe']['requirements']['build']]
            else:
                depends_build = []
            if 'host' in package_json['rendered_recipe']['requirements'].keys():
                depends_host = [i.split(" ")[0] for i in package_json['rendered_recipe']['requirements']['host']]
            else:
                depends_host = []
            depends = depends_host + depends_build
            self.logger.info(f"Build-time dependencies for {package_requested}:")
        else:
            #TODO unhandled, but open to extension
            ...
        name_matches = [i for i in lin64_json_object["packages"] if self.get_package_name(i) in depends]

        for j in depends:
            basic_matches = [i for i in name_matches if j in i]
            is_python = [self.get_package_build(i) for i in basic_matches if "py" in self.get_package_build(i).split("cpython")[0].split("pypy")[0]]
            if debug: self.logger.info(f"{j}: {is_python}")
            if len(basic_matches)==0:
                name_matches_noarch = [i for i in noarch_json_object["packages"] if self.get_package_name(i) in depends]
                if len(name_matches_noarch)>0:
                    self.logger.info(f"[bold green] {j} : noarch [/bold green]", extra={"markup": True})
                else: 
                    self.logger.info(f"[bold yellow] {j} : not found in linux-64 or noarch[/bold yellow]", extra={"markup": True})

            elif len(is_python)>0:
                self.logger.info(f"[bold green] {j} [/bold green]", extra={"markup": True})
            else:
                self.logger.info(f"[bold blue] {j} : non-python [/bold blue]", extra={"markup": True})

    def check_all_package_jsons(self, arch: str, package_requested: str):
        all_jsons = list(self.config.package_jsons.joinpath(arch).glob("*.json"))
        matches = []
        
        for i in all_jsons:
            with open(i, 'r') as read_file:
                json_object = json.load(read_file)
            build_match, host_match = self.check_build_host_depends(package_requested, json_object)
            if len(build_match) > 0 or len(host_match) > 0:
                matches.append(f"{i.name}: {set(build_match + host_match)}")
        return matches

    def convert_grayskull_map(self) -> Dict:
        """
        Converts a given grayskull map from pypi -> conda.
        """
        gs_mapping = {}

        if self.config.grayskull_map.exists():
            with open(self.config.grayskull_map, 'r') as file:
                gs_map = yaml.safe_load(file)

            for i in gs_map:
                if gs_map[i]['conda_name'] != gs_map[i]['pypi_name']:
                    #self.logger.info(f"GRAYSKULL SWAP | ADD MORE DETAILED LOGS HERE")
                    gs_mapping[gs_map[i]['pypi_name']] = gs_map[i]['conda_name']
        else:
            self.logger.warn("LOAD ERROR | gs_mapping yaml did not load properly")

        return gs_mapping

    def missed_and_matched_from_manifest(self, package_arch, python_version_requested, manifest_packages, drop_versions, json_object):
        """
        A gigantic loop to be moved outside of here, and to the cli.
        """

        if python_version_requested != None:
            python_version_matches = {i:json_object["packages"][i] for i in json_object["packages"] if python_version_requested in i}
        else:
            python_version_matches = json_object["packages"]
        
        package_report = {
                'matched_packages' : [],
                'missed_packages' : []
        }

        to_fetch: List[Tuple] = []

        converted_grayskull_map = self.convert_grayskull_map()

        for i in manifest_packages:

            if ('pyVer' in i.keys()) and (i['pyVer'] == '2.7'):
                self.logger.info("[bold yellow] Skipping [/bold yellow]" + f"{i['name']}=={i['version']}, pyVer = {i['pyVer']}", extra={"markup": True})
                continue

            i["name"] = self.convert_pypi_conda_name(i["name"], converted_grayskull_map)
            i["name"] = i["name"].lower() #conda packages are all lower
            i["version"] = i["version"].split("+")[0]

            if i["version"] == "0.0.0" or len(i["version"].split("."))>3 or drop_versions:
                i["version"] = ""

            matched_package = self.match_versioned_packages(i["name"], i["version"], python_version_matches)

            if len(matched_package) > 0:
                matched_package = self.choose_build(i["version"], matched_package, python_version_matches)
                self.logger.info("[bold green] Match Found [/bold green]" + f"{i['name']}=={python_version_matches[matched_package]['version']}", extra={"markup": True})
                payload = self.format_package_json(i["name"], matched_package, package_arch)
                to_fetch.append(payload)

                package_report["matched_packages"].append({"name" : i['name'],"version" : i['version'] })

            elif 'eggName' in i:

                i["eggName"] = self.convert_pypi_conda_name(i["eggName"], converted_grayskull_map)
                i["eggName"] = i["eggName"].lower()

                matched_package = self.match_versioned_packages(i["eggName"], i["version"], python_version_matches)

                if len(matched_package) > 0:
                    matched_package = self.choose_build(i["version"], matched_package, python_version_matches)
                    self.logger.info("[bold green] Match Found [/bold green]" + f"{i['name']}/{i['eggName']}=={python_version_matches[matched_package]['version']}", extra={"markup": True})
                    payload = self.format_package_json(i["eggName"], matched_package, package_arch)
                    to_fetch.append(payload)

                    package_report["matched_packages"].append({"name" : i['eggName'],"version" : i['version'] })

                else:
                    package_report["missed_packages"].append({"name" : i['eggName'],"version" : i['version'] })
                    self.logger.info("[bold red] No Matches [/bold red]" + f"{i['name']}/{i['eggName']}=={i['version']}", extra={"markup": True})
            else:
                package_report["missed_packages"].append({"name" : i['name'],"version" : i['version'] })
                self.logger.info("[bold red] No Matches [/bold red]"  + f"{i['name']}=={i['version']}", extra={"markup": True})
        
        #remove duplicates by converting list of dicts to set of dicts after serialization, then back to list. 
        package_report["missed_packages"] = [json.loads(i) for i in set(json.dumps(i, sort_keys=True) for i in package_report["missed_packages"])]
        package_report["matched_packages"] = [json.loads(i) for i in set(json.dumps(i, sort_keys=True) for i in package_report["matched_packages"])]

        self.logger.info("[bold green] Total Matched: [/bold green]" + f"{len(package_report['matched_packages'])}", extra={"markup": True})
        self.logger.info("[bold red] Total Missed: [/bold red]" + f"{len(package_report['missed_packages'])}", extra={"markup": True})
        unique_missed = len(set([i["name"] for i in package_report["missed_packages"]]))
        self.logger.info("[bold red] Unique Missed: [/bold red]" + f"{unique_missed}", extra={"markup": True})

        output = self.config.package_reports.joinpath(pathlib.Path(f'cfgraph-package-report-{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'))
        to_fetch_output = self.config.package_reports.joinpath(pathlib.Path(f'cfgraph-to-fetch-{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'))

        with open(output, "w") as write_file:
           json.dump(package_report, write_file)
           self.logger.info(f'[bold pink] WROTE SUMMARY FILE: ' + '[/bold pink]' + str(output), extra={"markup": True})

        #with open(to_fetch_output, "w") as write_file:
        #   json.dump(d, write_file)
        #   self.logger.info(f'[bold pink] WROTE MATCH CACHE: ' + '[/bold pink]' + str(to_fetch_output), extra={"markup": True})

        ##need a test to verify downloads succeed - config_folder_var.joinpath("jsons").joinpath(package_arch).joinpath(matched_package.replace(".tar.bz2",".json"))
        
        return set(to_fetch)
