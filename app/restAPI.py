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
# Created: 2015-06-25 05:25

import logging
import os
import base64
import time

from flask import current_app, url_for, jsonify
from flask.ext.restful import Resource, reqparse, Api

from db import db_plugin_instance, db_callback_instance


logger = logging.getLogger(__name__)
api_path = "/api/v1.0/"
resource_path = "resources/"
resource_dir_path = os.path.join("app/static", resource_path)
TIMEOUT_UPDATE = 1.0


def save_resource(plugin_name, resource_name, resource_data):
    """
    Save a resource in local cache

    :param plugin_name: Name of plugin this resource belongs to
    :type plugin_name: str
    :param resource_name: Name of resource
    :type resource_name: str
    :param resource_data: Resource content - base64 encoded
    :type resource_data: str
    :rtype: None
    """
    path = os.path.join(resource_dir_path, plugin_name)
    if not os.path.exists(path):
        os.makedirs(path)
    path = os.path.join(path, resource_name)
    logger.debug("Saving {}".format(path))
    with open(path, 'wb') as f:
        f.write(base64.b64decode(resource_data))


class PluginListAPI(Resource):
    """ View for plugin list """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(PluginListAPI, self).__init__()

    def get(self):
        with db_plugin_instance.db_lock:
            return jsonify({
                'plugins': [
                    {
                        'key': plugin_key,
                        'name': db_plugin_instance.plugin_get(
                            plugin_key
                        ).get('name', plugin_key),
                        'uri': url_for("APIPlugin", plugin_key=plugin_key)
                    }
                    for plugin_key in db_plugin_instance.plugin_keys()
                ],
                'error': ""
            })


class PluginAPI(Resource):
    """ View for plugin information """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('data', type=dict, location='json')
        self.api = Api(current_app)
        super(PluginAPI, self).__init__()

    def get(self, plugin_key):
        plugin = db_plugin_instance.plugin_get(plugin_key)
        if not plugin:
            return {
                "error": u"Plugin '{}' not found".format(plugin_key)
            }
        upd = plugin.get('data_updated')
        # Update plugin data
        with db_callback_instance.db_lock:
            for func in db_callback_instance.callback_get('plugin_data_get'):
                try:
                    func(plugin_key, None)
                except:
                    logger.exception(u"Failed to trigger ws callback")
        # Wait for data updated or timeout
        start = time.time()
        while time.time() - start < TIMEOUT_UPDATE \
                and upd == plugin.get('data_updated'):
            plugin = db_plugin_instance.plugin_get(plugin_key)
        plugin['uri'] = url_for("APIPlugin", plugin_key=plugin_key)
        if "resources" in plugin:
            plugin['resources'] = {
                key: url_for(
                    "APIPluginResource",
                    plugin_key=plugin_key,
                    resource_name=key
                )
                for key in plugin['resources']
            }
        return jsonify({
            'plugin': plugin,
            'error': ""
        })

    def post(self, plugin_key):
        args = self.reqparse.parse_args()
        logger.debug(u"Got post: {}".format(args))
        plugin = db_plugin_instance.plugin_get(plugin_key)
        if not plugin:
            return {
                "error": u"Plugin '{}' not found".format(plugin_key)
            }
        # Only set data attribute
        plugin.setdefault('data', {}).update(args.get('data', {}))
        db_plugin_instance.plugin_set(plugin_key, plugin)
        with db_callback_instance.db_lock:
            for func in db_callback_instance.callback_get('plugin_data_set'):
                try:
                    func(plugin_key, plugin['data'])
                except:
                    logger.exception("Failed to trigger ws callback")
        return {
            "error": ""
        }


class PluginResourceAPI(Resource):
    """ View for accessing plugin resources """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('resource_name', type=str)
        super(PluginResourceAPI, self).__init__()

    def get(self, plugin_key):
        args = self.reqparse.parse_args()
        resource_name = args.get('resource_name')
        plugin = db_plugin_instance.plugin_get(plugin_key)
        res = {
            'resource': {},
            'error': ""
        }
        if not resource_name:
            return {
                "error": u"Resource required"
            }
        if not plugin:
            return {
                "error": u"Plugin '{}' not found".format(plugin_key)
            }
        resources = plugin.get('resources')
        if not resources:
            # No resources for this plugin registered
            return res
        if resource_name not in resources:
            res['error'] = u"Resource '{}' not found".format(resource_name)
            return res
        res['resource'] = resources[resource_name]
        res['resource']['uri'] = url_for(
            "static",
            filename=u"{}{}/{}".format(
                resource_path,
                plugin_key,
                resource_name
            )
        )
        return jsonify(res)
