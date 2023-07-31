# rafe: Reproducible Artifacts for Environments

rafe is a tool for inspecting python environments and building packages (irrespective of language) in a reproducible manner.

-----------------------------------------------------------
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Quansight/rafe/build-package.yml?label=Build&logo=github&style=for-the-badge)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Quansight/rafe/test-rafe.yml?label=Tests&logo=github&style=for-the-badge)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Quansight/rafe/publish-to-pypi.yml?label=Publish&logo=github&style=for-the-badge)<br>
![GitHub release (latest by date)](https://img.shields.io/github/v/release/Quansight/rafe?logo=github&style=for-the-badge)
![PyPI](https://img.shields.io/pypi/v/rafe?logo=pypi&style=for-the-badge)

## Building

To press a fresh rafe wheel from source, simply run:

```bash
python setup.py bdist_wheel
```

And the wheel should be available in the `dist/` folder.

## Installing

To install rafe, simply pip install the wheel 

```bash
pip install <wheel>
```

## Usage

Before starting to use rafe, it needs to generate a configuration. Do this by running:

```bash
rafe config --init
```

Now, you can use rafe however you'd like. Note that you can call it in two ways:

* `python -m rafe`
* `rafe`

Both are valid.

### Workflow for Griffe API checks

Assuming you have already run `rafe config --init` you will have the folder `.rafe/work/` - place your git repo folder there, such that numpy would be at `.rafe/work/numpy/`

With this in place you should next run

```bash
python rafe check-api-breaks --package numpy --old v1.12.1 --new v1.17.5`
```
In older griffe versions, if you are given a git branch error, you'll need to clean up the griffe created branches before rerunning. E.g. `git branch -D griffe_v1.12.1` from the appropriate folder
It has been verified that this is no longer an issue with griffe v0.30.1 (last to support py3.7)

Once you have run the above you should be able to run the verify pass (for objects removed) using the command below:
```bash
python rafe verify-breaks --package numpy --path ./numpy_objects_removed.json`
```
This will attempt to eval a `hasattr()` for each of the missing items, and where it fails it may attempt to import the missing attribute and try again. The resulting `numpy_actual_misses.json` should be much closer to the truth.
