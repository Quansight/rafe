# rafe: Reproducible Artifacts for Environments

rafe is a tool for inspecting python environments and building packages (irrespective of language) in a reproducible manner. 

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
