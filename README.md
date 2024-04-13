This repository serves as an example for remote plugins.

Remote plugins are plugins that can be downloaded from the Electrum GUI.
They are listed hash in electrum/plugins.json


The `contrib/make_plugin` script in the electrum repository creates a
zip file that can be distributed via https. Here is how to use it:

First, call `./contrib/make_plugin /path/to/yourplugin`

This will create a plugin file named `yourplugin-version.zip`, where `version` is set in `__init__.py` of the plugin.
It will also update the hash and metadata of your plugin in `electrum/plugins.json`.
This hash update is required by Electrum in order to import the plugin.

In order to test changes to your plugin, you need to both move the zip file to your userspace and update the hash.

It is best to perform both operations together:
`./contrib/make_plugin /path/to/yourplugin && mv /path/to/yourplugin-*.zip ~/.electrum/plugins/`
