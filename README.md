This repository serves as an example for external plugins.

# Adding a plugin to Electrum

In order to add this plugin to Electrum, add the following line to /etc/electrum/plugin_authority:

021027fd5bc3b5e50c9800d48bc8acfbc290d89b857c7ce15572a57048c4c0558e https://raw.githubusercontent.com/spesmilo/electrum-plugin-virtualkeyboard/refs/heads/master/virtualkeyboard.json

The first element is a public key used to sign the plugin, the second one is a URL


# Development and testing

If you are developing an external plugin, you may create a symbolic
link in your electrum/electrum/plugins directory, that links to the
place where you where you forked this repository


# Publishing an external plugin

In order to publish an external plugin, fork this directory and use the `contrib/make_plugin` script in the electrum repository.

 ./contrib/make_plugin <plugin_directory> <privkey> <download_url>


It will create two files:
 - a plugin file named `yourplugin-version.zip`, where `version` is set in `__init__.py` of the plugin.
 - a json file named `yourplugin.json`

Both files need to be uploaded on a webserver.
In this example, we use the github source repository in order to distribute these files.
