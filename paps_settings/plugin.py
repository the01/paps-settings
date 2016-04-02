# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.1"
__date__ = "2016-04-02"
# Created: 2015-06-27 17:33

import logging
from pprint import pformat
import threading
import time
import base64

from twisted.logger import STDLibLogObserver, globalLogBeginner
from twisted.internet import reactor
from twisted.internet.error import ReactorAlreadyRunning
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from flotils.loadable import loadJSON, saveJSON
from paps.crowd import Plugin, PluginException

from .settable_plugin import SettablePlugin


logger = logging.getLogger(__name__)


class PluginClientProtocol(WebSocketClientProtocol):
    """ Websocket linking the plugin to the webserver """

    def onConnect(self, request):
        logger.debug(u"Server connecting: {}".format(request.peer))

    def onOpen(self):
        logger.debug("WebSocket connection open.")
        self._webClient._plugin_protocol = self

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = loadJSON(payload.decode("utf8"))
            try:
                res = self._webClient.handle_msg(payload)
            except:
                logger.exception(u"Failed to handle {}".format(payload))
                return
            if res:
                self.sendMessage(saveJSON(res, pretty=False).encode("utf8"))
        else:
            logger.warning("Unsupported: Received binary payload")

    def onClose(self, wasClean, code, reason):
        logger.debug(u"WebSocket connection closed: {}".format(reason))
        self._webClient._plugin_protocol = None


class SettingsPlugin(Plugin):
    """ Class handling plugin to webserver transmission """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(SettingsPlugin, self).__init__(settings)
        self._host = settings.get('host', "localhost")
        self._port = settings.get('port', 5000)
        self._ws_path = settings.get('ws_path', "")
        self._is_debug = settings.get('use_debug', False)
        self._factory = None
        self.plugins = {}
        self.plugin_lock = threading.Lock()
        self.people = {}
        self.people_lock = threading.Lock()
        self._plugin_protocol = None
        """ Handle to plugin client protocol
            :type _plugin_protocol: PluginClientProtocol """

    def on_person_new(self, people):
        with self.people_lock:
            for person in people:
                self.people[person.id] = person

    def on_person_leave(self, people):
        with self.people_lock:
            for person in people:
                del self.people[person.id]

    def on_person_update(self, people):
        with self.people_lock:
            for person in people:
                self.people[person.id] = person

    def _plugin_get(self, plugin_name):
        """
        Find plugins in controller

        :param plugin_name: Name of the plugin to find
        :type plugin_name: str | None
        :return: Plugin or None and error message
        :rtype: (settable_plugin.SettablePlugin | None, str)
        """
        if not plugin_name:
            return None, u"Plugin name not set"
        for plugin in self.controller.plugins:
            if not isinstance(plugin, SettablePlugin):
                continue
            if plugin.name == plugin_name:
                return plugin, ""
        return None, u"Settable plugin '{}' not found".format(plugin_name)

    def handle_msg(self, payload):
        """
        Handle message for network plugin protocol

        :param payload: Received message
        :type payload: dict
        :return: Response to send (if set)
        :rtype: None | dict
        """
        self.debug(u"\n{}".format(pformat(payload)))
        msg = payload['msg']
        res = {
            'msg': msg,
            'error': ""
        }
        if msg == "plugin_list":
            res['plugin_names'] = []
            # Generate list of plugins available for frontend
            for plugin in self.controller.plugins:
                # Limit to plugins that work with this
                if isinstance(plugin, SettablePlugin):
                    res['plugin_names'].append(plugin.name)
            return res
        elif msg == "plugin_get":
            res['plugin'] = {}
            plugin_name = payload.get('plugin_name')
            plugin, err = self._plugin_get(plugin_name)
            if not plugin:
                res['error'] = err
                return res
            res['plugin_name'] = plugin_name
            res['plugin'] = plugin.get_info()
            return res
        elif msg == "plugin_resource_list":
            res['resource_names'] = []
            plugin_name = payload.get('plugin_name')
            plugin, err = self._plugin_get(plugin_name)
            if not plugin:
                res['error'] = err
                return res
            res['plugin_name'] = plugin_name
            try:
                res['resource_names'] = plugin.resource_get_list()
            except PluginException as e:
                if str(e) == "No resource path set":
                    self.debug(
                        u"Plugin '{}' has no resources".format(plugin.name)
                    )
                else:
                    self.exception(
                        u"Failed to get resource list for plugin '{}'".format(
                            plugin.name
                        )
                    )
            return res
        elif msg == "plugin_resource_get":
            res['resource'] = {}
            plugin_name = payload.get('plugin_name')
            resource_name = payload.get('resource_name')
            if not resource_name:
                res['error'] = "Resource name not set"
                return res
            plugin, err = self._plugin_get(plugin_name)
            if not plugin:
                res['error'] = err
                return res
            res['plugin_name'] = plugin_name
            res['resource_name'] = resource_name
            res['resource'] = dict(plugin.resource_get(resource_name))
            if "path" in res['resource']:
                del res['resource']['path']
            return res
        elif msg == "plugin_resource_load":
            res['resource_data'] = ""
            plugin_name = payload.get('plugin_name')
            resource_name = payload.get('resource_name')
            if not resource_name:
                res['error'] = "Resource name not set"
                return res
            plugin, err = self._plugin_get(plugin_name)
            if not plugin:
                res['error'] = err
                return res
            res['plugin_name'] = plugin_name
            res['resource_name'] = resource_name
            resource_dict = plugin.resource_get(resource_name)
            if not resource_dict:
                res['error'] = u"Resource '{}' not found".format(resource_name)
                return res
            self.debug(u"Resource {}".format(resource_dict))
            try:
                with open(resource_dict['path'], 'rb') as f:
                    res['resource_data'] = base64.b64encode(f.read())
            except:
                self.exception(
                    u"Failed to load '{}'".format(resource_dict['path'])
                )
                res['error'] = u"Failed to load"
            return res
        elif msg == "plugin_data_get":
            plugin_name = payload.get('plugin_name')
            plugin, err = self._plugin_get(plugin_name)
            if not plugin:
                res['error'] = err
                return res
            res['plugin_name'] = plugin_name
            res['data'] = plugin.get_data()
            return res
        elif msg == "plugin_data_set":
            plugin_name = payload.get('plugin_name')
            plugin, err = self._plugin_get(plugin_name)
            if not plugin:
                res['error'] = err
                return res
            res['plugin_name'] = plugin_name
            data = payload.get('data')
            if not data:
                res['error'] = u"No data provided"
                return res
            try:
                plugin.on_config(data)
            except NotImplementedError:
                res['error'] = u"Plugin does not support setting data"
                return res
            except:
                self.exception(
                    u"Failed to set data for {}".format(plugin_name)
                )
                res['error'] = "Failed to set data"
                return res
            return {}
        else:
            self.error(u"Unknown cmd '{}'\n{}".format(msg, payload))
        return {}

    def _reactor_start(self):
        try:
            if not reactor.running:
                observer = STDLibLogObserver(name="twisted")
                globalLogBeginner.beginLoggingTo([observer])
                reactor.run(False)
            else:
                self.info("Reactor already running")
        except ReactorAlreadyRunning:
            self.info("Reactor already running")
        except:
            self.exception("Failed to start reactor")

    def start(self, blocking=False):
        self.debug("()")
        if self._is_running:
            self.debug("Already running")
            return
        # old logging mode
        # observer = log.PythonLoggingObserver(loggerName='twisted')
        # observer.start()

        self._factory = WebSocketClientFactory(
            u"ws://{}:{}{}".format(self._host, self._port, self._ws_path)
        )

        self._factory.protocol = PluginClientProtocol
        self._factory.protocol._webClient = self
        # self._factory.protocol.onOpen = self._on_ws_open

        reactor.connectTCP(self._host, self._port, self._factory)
        # False or dict alone should be enough
        a_thread = threading.Thread(
            target=self._reactor_start
        )
        a_thread.daemon = True
        a_thread.start()
        super(SettingsPlugin, self).start(blocking)

    def stop(self):
        self.debug("()")
        if not self._is_running:
            return
        if self._plugin_protocol:
            reactor.callFromThread(self._plugin_protocol.sendClose)
            time.sleep(1.0)
        reactor.callFromThread(reactor.stop)
        self._factory = None
        super(SettingsPlugin, self).stop()
        self.info("Done")
