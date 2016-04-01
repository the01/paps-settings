# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.0"
__date__ = "2016-04-01"
# Created: 2015-07-27 15:18

import logging
import threading
from collections import OrderedDict
from abc import ABCMeta, abstractmethod

from flotils.logable import Logable


logger = logging.getLogger(__name__)
db_test = {}


class PluginDatabase(Logable):
    """ Abstract database for plugin data """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings for init
        :type settings: dict
        :rtype: None
        """
        if settings is None:
            settings = {}
        super(PluginDatabase, self).__init__(settings)
        if 'data_init' in settings:
            # init this instance
            for plugin_key in settings['data_init']:
                self.plugin_set(plugin_key, settings['data_init'][plugin_key])

    @abstractmethod
    def plugin_keys(self):
        """
        Return key list of installed plugins

        :return: Installed plugin keys
        :rtype: list[str]
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def plugin_get(self, plugin_key):
        """
        Retrieve information on plugin

        :param plugin_key: Key of plugin
        :type plugin_key: str
        :return: Plugin information
        :rtype: dict[str: object]
        :raises KeyError: Plugin key not found
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def plugin_set(self, plugin_key, plugin_data):
        """
        Set plugin data (overwrite old)

        :param plugin_key: Key of plugin
        :type plugin_key: str
        :param plugin_data: New data of plugin
        :type plugin_data: dict
        :rtype: None
        """
        raise NotImplementedError("Please implement")


class DictPluginDatabase(PluginDatabase):
    """ Dict based implementation """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        self.db_lock = threading.RLock()
        """ Lock for database
            :type _db_lock: threading.RLock """
        self._db = {
            'plugins': OrderedDict({})
        }
        """ Database data
            :type _db: dict[str: dict[str: object]] """
        super(DictPluginDatabase, self).__init__(settings)

    def plugin_keys(self):
        with self.db_lock:
            return self._db['plugins'].keys()

    def plugin_get(self, plugin_key):
        res = {
            'key': plugin_key,
            'name': plugin_key
        }
        with self.db_lock:
            res.update(self._db['plugins'][plugin_key])
        return res

    def plugin_set(self, plugin_key, plugin_data):
        with self.db_lock:
            self._db['plugins'][plugin_key] = plugin_data


class CallbackDatabase(Logable):
    """ Abstract database for callbacks """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings for init
        :type settings: dict
        :rtype: None
        """
        if settings is None:
            settings = {}
        super(CallbackDatabase, self).__init__(settings)

    @abstractmethod
    def callback_add(self, callback_event, callback):
        """
        Add callback

        :param callback_event: Event on which to trigger callback
        :type callback_event: str
        :param callback: To be called on event
            first param is plugin name
            second param is data
        :type callback: (str, dict) -> None
        :rtype: None
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def callback_get(self, callback_event):
        """
        Get callbacks for event

        :param callback_event: Event on which to trigger callback
            (Not validated)
        :type callback_event: str
        :return: Callbacks
        :rtype: list[(str, dict) -> None]
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def callback_remove(self, callback_event, callback):
        """
        Remove callback

        :param callback_event: Event on which to trigger callback
        :type callback_event: str
        :param callback: To be called on event
            first param is plugin name
            second param is data
        :type callback: (str, dict) -> None
        :rtype: None
        """
        raise NotImplementedError("Please implement")


class DictCallbackDatabase(CallbackDatabase):
    """ Dict based implementation """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(DictCallbackDatabase, self).__init__(settings)
        self.db_lock = threading.RLock()
        """ Lock for database
            :type _db_lock: threading.RLock """
        self._db = {
            'callbacks': OrderedDict({})
        }
        """ Database data
            :type _db: dict[str: dict[str: list[(str, dict) -> None]]] """

    def callback_remove(self, callback_event, callback):
        with self.db_lock:
            try:
                self._db['callbacks'][callback_event].remove(callback)
            except (KeyError, ValueError,):
                self.error(
                    u"Failed to remove callback {} for {}".format(
                        callback, callback_event
                    )
                )

    def callback_add(self, callback_event, callback):
        with self.db_lock:
            self._db['callbacks'].setdefault(
                callback_event, []
            ).append(callback)

    def callback_get(self, callback_event):
        with self.db_lock:
            return list(self._db['callbacks'].get(callback_event, []))


db_plugin_instance = DictPluginDatabase({
    'data_init': db_test
})
db_callback_instance = DictCallbackDatabase({})
