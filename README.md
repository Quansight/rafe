# rafe: Reproducible Artifacts for Environments

rafe is a tool for inspecting python environments and building packages (irrespective of language) in a reproducible manner.

-----------------------------------------------------------
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Quansight/rafe/build-package.yml?label=Build&logo=github&style=for-the-badge)
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
