# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.0"
__date__ = "2016-04-01"
# Created: 2015-06-27 15:04

from pprint import pformat
import datetime

from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet import reactor

from flotils.loadable import loadJSON, saveJSON
from flotils.logable import ModuleLogable

from restAPI import save_resource
from db import db_plugin_instance, db_callback_instance


class Logger(ModuleLogable):
    pass


logger = Logger()
clients = []


class PluginServerProtocol(WebSocketServerProtocol):

    def _sendJSON(self, data):
        logger.debug(u"Sending\n{}".format(pformat(data)))
        try:
            self.sendMessage(saveJSON(data, pretty=False).encode("utf"))
        except:
            logger.exception(u"Could not send\n{}".format(data))

    def onConnect(self, request):
        logger.debug(u"Client connecting: {}".format(request.peer))

    def onOpen(self):
        logger.debug("WebSocket connection open")
        clients.append(self)
        db_callback_instance.callback_add(
            "plugin_data_set", self.onSettingsChange
        )
        db_callback_instance.callback_add(
            "plugin_data_get", self.onRefreshPluginData
        )
        self._sendJSON({
            'msg': "plugin_list"
        })

    def onClose(self, wasClean, code, reason):
        logger.debug(u"WebSocket connection closed: {}".format(reason))
        db_callback_instance.callback_remove(
            "plugin_data_set", self.onSettingsChange
        )
        db_callback_instance.callback_remove(
            "plugin_data_get", self.onRefreshPluginData
        )
        clients.remove(self)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            try:
                payload = loadJSON(payload.decode("utf8"))
            except:
                logger.exception(u"Could not load json\n{}".format(payload))
            try:
                self._handle_msg(payload)
            except:
                logger.exception(u"Failed to handle {}".format(payload))
                return
        else:
            logger.warning("Unsupported: Received binary payload")

    def onSettingsChange(self, plugin_name, data):
        """
        The plugin has been changed by the frontend

        :param plugin_name: Name of plugin that changed
        :type plugin_name: str
        :param data: Complete data (changed and unchanged)
        :type data: dict
        :rtype: None
        """
        logger.info(u"onSettingsChange: {}".format(data))
        if not plugin_name:
            logger.error("Missing plugin name")
            return
        if not data:
            logger.error("Missing data")
            return
        logger.info(u"Sending data {}".format(data))
        reactor.callFromThread(self._sendJSON, {
            'msg': "plugin_data_set",
            'plugin_name': plugin_name,
            'data': data
        })
        # trigger db update
        reactor.callFromThread(self._sendJSON, {
            'msg': "plugin_data_get",
            'plugin_name': plugin_name
        })

    def onRefreshPluginData(self, plugin_name, data):
        """
        Frontend requests a data refresh

        :param plugin_name: Name of plugin that changed
        :type plugin_name: str
        :param data: Additional data
        :type data: None
        :rtype: None
        """
        logger.info(u"onRefreshPluginData: {}".format(plugin_name))
        if not plugin_name:
            logger.error("Missing plugin name")
            return
        reactor.callFromThread(self._sendJSON, {
            'msg': "plugin_data_get",
            'plugin_name': plugin_name
        })

    def _handle_msg(self, payload):
        logger.debug(u"Got: {}".format(payload))
        msg = payload['msg']

        if payload.get('error'):
            logger.error(u"Cmd '{}' failed: {}\n({})".format(
                msg, payload['error'], payload
            ))
            return
        if msg == "plugin_list":
            for plugin_name in payload['plugin_names']:
                self._sendJSON({
                    'msg': "plugin_get",
                    'plugin_name': plugin_name
                })
        elif msg == "plugin_get":
            plugin_name = payload.get('plugin_name')
            plugin = payload.get('plugin')
            if not plugin_name or not plugin:
                logger.error(u"Cmd '{}' missing params: \n{}".format(
                    msg, payload
                ))
                return
            db_plugin_instance.plugin_set(plugin_name, plugin)
            self._sendJSON({
                'msg': "plugin_resource_list",
                'plugin_name': plugin_name
            })
            self._sendJSON({
                'msg': "plugin_data_get",
                'plugin_name': plugin_name
            })
        elif msg == "plugin_resource_list":
            plugin_name = payload.get('plugin_name')
            if not plugin_name:
                logger.error(u"Cmd '{}' missing params: \n{}".format(
                    msg, payload
                ))
                return
            for resource, hash in payload['resource_names']:
                self._sendJSON({
                    'msg': "plugin_resource_get",
                    'plugin_name': plugin_name,
                    'resource_name': resource
                })
        elif msg == "plugin_resource_get":
            plugin_name = payload.get('plugin_name')
            resource_name = payload.get('resource_name')
            resource = payload.get('resource')
            if not plugin_name or not resource_name or not resource:
                logger.error(u"Cmd '{}' missing params: \n{}".format(
                    msg, payload
                ))
                return
            res = db_plugin_instance.plugin_get(plugin_name)
            res.setdefault('resources', {})[resource_name] = resource
            db_plugin_instance.plugin_set(plugin_name, res)
            self._sendJSON({
                'msg': "plugin_resource_load",
                'plugin_name': plugin_name,
                'resource_name': resource_name
            })
        elif msg == "plugin_resource_load":
            plugin_name = payload.get('plugin_name')
            resource_name = payload.get('resource_name')
            resource_data = payload.get('resource_data')
            if not plugin_name or not resource_name or not resource_data:
                logger.error(u"Cmd '{}' missing params: \n{}".format(
                    msg, payload
                ))
                return
            try:
                save_resource(plugin_name, resource_name, resource_data)
            except:
                logger.exception(u"Failed to save '{}'".format(resource_name))
        elif msg == "plugin_data_get":
            plugin_name = payload.get('plugin_name')
            data = payload.get('data')
            if not plugin_name or data is None:
                logger.error(u"Cmd '{}' missing params: \n{}".format(
                    msg, payload
                ))
                return
            res = db_plugin_instance.plugin_get(plugin_name)
            res['data_updated'] = datetime.datetime.utcnow()
            res['data'] = dict(data)
            db_plugin_instance.plugin_set(plugin_name, res)
        else:
            logger.error(u"Unkown cmd '{}'\n{}".format(msg, payload))
