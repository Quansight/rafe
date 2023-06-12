# Rafe Plugins

To write a rafe plugin, it must be as a cli application which is read at runtime. Create a __main__.py and a cli.py, which will be picked up and
registered as a plugin. To register, you must enter the function signature which is used as an entrypoint to the application.

