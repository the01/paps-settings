paps-settings
#############

.. image:: https://img.shields.io/pypi/v/paps-settings.svg
    :target: https://pypi.python.org/pypi/paps-settings

.. image:: https://img.shields.io/pypi/l/paps-settings.svg
    :target: https://pypi.python.org/pypi/paps-settings

.. image:: https://img.shields.io/pypi/dm/paps-settings.svg
    :target: https://pypi.python.org/pypi/paps-settings

Plugin for the `paps framework <https://pypi.python.org/pypi/paps/>`_ adding a simple
way to control plugins from a web browser by inherting from ``SettablePlugin`` and
providing html/js files.

This package has two parts: the webserver and the plugin. For the time being to
run the webserver you have to get the `git repository <https://github.com/the01/paps-settings>`_
and call the ``create_server`` method in ``app/server.py`` or execute ``app/server.py``
directly. This will create a flask app running on a twisted server.

The second part is a normal paps plugin which can be installed from PyPI. By executing
the settings plugin together with one or more ``SettablePlugin`` s inside a ``CrowdController``
it will first connect to the webserver via a websocket, autodetect all available
plugins and register them with the server backend. This involves beside providing
basic information on the plugin, uploading the provided resource-files. By separating
the webserver serving the actual http traffic (files, etc.) and the plugins (potentially
to another machine), the load on maschine handling the core paps functionality gets
reduced.

For example plugins have a look at the following plugins:

- `DummyPlugin - demo plugin from the paps example directory extended for usage with paps-settings and demonstrating two configurable values <https://github.com/the01/paps-settings/tree/master/example/plugin-dummy>`_
- `SoundMix - a plugin to create audience based sound mixing <https://github.com/the01/paps-soundmix>`_
- `Realtime - a plugin to display audience seating status live <https://github.com/the01/paps-realtime>`_
