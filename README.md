This repository serves as an example for external plugins.
It contains code for a simple plugin that creates a virtual keyboard in the Qt GUI of Electrum.

## Publishing a plugin as .zip file

In order to publish an external plugin, fork this directory and use
the `contrib/make_plugin` script in the electrum repository.

`./contrib/make_plugin <plugin_directory>`

It will create a plugin file named `yourplugin-version.zip`, where `version` is set in `manifest.json` of the plugin.

This file needs to be added to you the plugins directory of your electrum installation.


## External directory plugin

If you are running an Electrum binary (Appimage, MacOS), you will not
have access to your plugins directory. In that case, you may create a
`/opt/electrum_plugins` directory on your system. That directory and
the file it contains must be owned by root, and they must not be user
writeable.

Example:
```
  sudo mkdir -p /opt/electrum_plugins
  sudo cp *.zip /opt/electrum_plugins
  sudo chown root:root /opt/electrum_plugins/*
```

## Development and testing

If you are developing an external plugin, you may fork this directory,
and create a symbolic link in your electrum/electrum/plugins directory
to the place where you where you forked this repository. That way, you
will not need to publish your plugin in order to test it.


