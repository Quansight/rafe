from .config_paths import example_manifest_filepath

from rafe.cfgraph import CFGraph

cfgraph = CFGraph()

def test_load_manifest():
    """
    Load the example provided manifest.
    """
    package_arch, python_version_requested, manifest_packages = cfgraph.read_manifest(example_manifest_filepath)
    assert package_arch == "linux-64"
    assert python_version_requested == "py37"
