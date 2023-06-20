from rafe.build import build_package
from .config_paths import example_build_filepath

def test_build_bitarray():
    """
    This test will build the bitarray package and then test that the package sucessfully built.
    """
    if example_build_filepath.exists():
        result = build_package(example_build_filepath)
        assert result == 0
