This repository serves as an example for external plugins.
It contains code for a simple plugin that creates a virtual keyboard in the Qt GUI of Electrum.

## Adding an external plugin to Electrum

In order to add this plugin to Electrum, create a `/etc/electrum/trusted_plugins` file with the following line:

`021027fd5bc3b5e50c9800d48bc8acfbc290d89b857c7ce15572a57048c4c0558e:https://raw.githubusercontent.com/spesmilo/electrum-plugin-virtualkeyboard/refs/heads/master/virtualkeyboard.json`

Each line in this file is a public key followed by a URL. The URL
returns plugin metadata signed by the plugin author.  The public key
is used to verify the signature.

Once you have done that, you should see 'Virtual Keyboard' in your list of plugins.

## Development and testing

If you are developing an external plugin, you may fork this directory,
and create a symbolic link in your electrum/electrum/plugins directory
to the place where you where you forked this repository. That way, you
will not need to publish your plugin in order to test it.


## Publishing an external plugin

In order to publish an external plugin, fork this directory and use
the `contrib/make_plugin` script in the electrum repository.

`./contrib/make_plugin <plugin_directory> <privkey> <download_url>`


It will create two files:
 - a plugin file named `yourplugin-version.zip`, where `version` is set in `__init__.py` of the plugin.
 - a json file named `yourplugin.json`

Both files need to be uploaded on a webserver.
In this example, we use the github source repository in order to distribute these files.
