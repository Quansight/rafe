import pathlib

HERE = pathlib.Path(__file__).parent.resolve()
EXAMPLES = HERE.parent.resolve().joinpath("examples")
example_manifest_filepath: pathlib.Path = list(EXAMPLES.joinpath("manifests").glob('*.json'))[0]
example_build_filepath: pathlib.Path = EXAMPLES.joinpath("bitarray")
