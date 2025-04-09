This repository serves as an example for external plugins.
It contains code for a simple plugin that creates a virtual keyboard in the Qt GUI of Electrum.

## Publishing a plugin as .zip file

In order to publish an external plugin, fork this directory and use
the `contrib/make_plugin` script in the electrum repository.

`./contrib/make_plugin <plugin_directory>`

It will create a plugin file named `yourplugin-version.zip`, where `version` is set in `manifest.json` of the plugin.

## The manifest.json file

The file contains the following fields:

 - name: The plugin internal name. Electrum will install only one plugin per name.
 - fullname: User visible name, shown in GUI
 - description: User visible description
 - available_for: List of GUIs for which the plugin is available.
 - author: The plugin author
 - license: The licence.
 - version: The version of the plugin. It is added to the zipfile name.
 - min_electrum_version (optional): Minimum supported version of Electrum
 - max_electrum_version (optional): Max supported version of Electrum


## Installing a zipfile plugin

The plugin zipfile needs to be added the `plugins` directory of your electrum directory.

On Linux:

`cp myplugin.zip ~/lelectrum/plugins/myplugin.zip`


The GUI will prompt the user for a plugin authorization password.


## Development and testing

If you are developing an external plugin, you may fork this directory,
and create a symbolic link in your electrum/electrum/plugins directory
to the place where you where you forked this repository. That way, you
will not need to publish your plugin in order to test it.


