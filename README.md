This repository serves as an example for external plugins.
It contains code for a simple plugin that creates a virtual keyboard in the Qt GUI of Electrum.

## Adding an external plugin to Electrum

In order to add this plugin to Electrum, add the zip file to your `/opt/electrum_plugins` directory.
That directory and the file it contains must be owned by root, and they must not be user writeable.

## Development and testing

If you are developing an external plugin, you may fork this directory,
and create a symbolic link in your electrum/electrum/plugins directory
to the place where you where you forked this repository. That way, you
will not need to publish your plugin in order to test it.


## Publishing an external plugin

In order to publish an external plugin, fork this directory and use
the `contrib/make_plugin` script in the electrum repository.

`./contrib/make_plugin <plugin_directory>`

It will create a plugin file named `yourplugin-version.zip`, where `version` is set in `__init__.py` of the plugin.
