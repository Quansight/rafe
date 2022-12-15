# rafe: Reproducible Artifacts for Environments

A tool for building any type of package (e.g. wheel) in a reproducible
fashion.  The tool is a thin wrapper around a script which gets executed
in the source directory of a package.  The script, as well as metadata (such
has source URL, name, version, patches, etc.) are part of a recipe.

Trying it out::

    $ python setup.py develop

Building a package (must have a recipe in `recipes/`::

    $ build bitarray
