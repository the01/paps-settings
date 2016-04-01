# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2016, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.0"
__date__ = "2016-04-01"
# Created: 2016-03-27 15:12

import hashlib
from abc import ABCMeta
import threading
import os
import datetime

from paps.crowd import Plugin, PluginException


def get_file_hash(file_path, block_size=1024, hasher=None):
    """
    Generate hash for given file

    :param file_path: Path to file
    :type file_path: str
    :param block_size: Size of block to be read at once (default: 1024)
    :type block_size: int
    :param hasher: Use specific hasher, defaults to md5 (default: None)
    :type hasher: _hashlib.HASH
    :return: Hash of file
    :rtype: str
    """
    if hasher is None:
        hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            buffer = f.read(block_size)
            if len(buffer) <= 0:
                break
            hasher.update(buffer)
    return hasher.hexdigest()


class SettablePlugin(Plugin):
    """
    Abstract interface for plugin which can use the settings plugin
    """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings to be passed for init (default: None)
        :type settings: dict | None
        :rtype: None
        :raises TypeError: Controller missing
        """
        if settings is None:
            settings = {}
        super(SettablePlugin, self).__init__(settings)

        self._resource_path = settings.get('resource_path')
        """ Path to the resource dir
            :type _resource_path: str """
        self._resource_file_types = settings.get(
            'resource_file_types',
            ["html", "js", "css"]
        )
        """ List of acceptable file types (lower case)
            :type _resource_file_types: list[str] """
        self._resource_file_types = [
            s.lower() for s in self._resource_file_types
        ]
        self._resources = {}
        """ Inventory of resources
            :type _resources: dict[str, dict[str, str | datetime.datetime] """
        self._resource_lock = threading.RLock()
        """ Lock to sync access to _resources
            :type _resource_lock: threading.RLock """

    def on_config(self, settings):
        """
        Change the settings for the plugin (implement if supported)

        :param settings: Settings to update current ones
        :type settings: dict
        :rtype: None
        """
        raise NotImplementedError("Please implement")

    def get_data(self):
        """
        Get current data of this plugin for frontend (or empty dict if nothing)
        (settings, etc.)

        :return: Data
        :rtype: dict
        """
        return {}

    def get_info(self):
        """
        Get information about this plugin for frontend
        (e.g. printable name, description, ..)

        :return: Information
        :rtype: dict
        """
        return {
            'name': self.name
        }

    def resource_get_list(self):
        """
        Get list of this plugins resources and a hash to check for file changes

        (It is recommended to keep a in memory representation of this struct
        and not to generate it upon each request)

        :return: List of supported resources and hashes
        :rtype: list[(unicode, unicode)]
        """
        if not self._resources:
            return self.resource_update_list()
        res = []
        with self._resource_lock:
            for key in self._resources:
                res.append((key, self._resources[key]['hash']))
        return res

    def resource_update_list(self, reset=False):
        """
        Update internal struct of resource, hash list and get diff

        (Warning: Resource names have to be unique!!)

        :param reset: Should resources be rebuild from scratch (default: False)
        :type reset: bool
        :return: List of resources and hashes that changed
        :rtype: list[(unicode, unicode)]
        """
        if not self._resource_path:
            raise PluginException("No resource path set")
        if not os.path.isdir(self._resource_path):
            raise PluginException(
                u"Resource path directory '{}' not found".format(
                    self._resource_path
                )
            )
        res = []
        with self._resource_lock:
            if reset:
                self._resources = {}
            old = dict(self._resources)
            for dirname, dirnames, filenames in os.walk(self._resource_path):
                for file_name in filenames:
                    file_ext = os.path.splitext(file_name)[1].lower()[1:]
                    if file_ext not in self._resource_file_types:
                        self.debug(u"Skipping '{}'".format(file_name))
                        continue
                    file_path = os.path.join(dirname, file_name)
                    try:
                        file_hash = get_file_hash(file_path)
                    except:
                        self.exception(
                            u"Failed to hash '{}'".format(file_path)
                        )
                        continue
                    self._resources[file_name] = {
                        'name': file_name,
                        'path': file_path,
                        'hash': file_hash,
                        'checked': datetime.datetime.utcnow()
                    }

            # generate diff
            for key in self._resources:
                resource = self._resources[key]
                if key not in old or old[key]['hash'] != resource['hash']:
                    # new file or hash changed
                    res.append((key, resource['hash']))
        return res

    def resource_get(self, resource_name):
        """
        Return resource info

        :param resource_name: Resource name as returned by resource_get_list()
        :type resource_name: str
        :return: Resource information (empty if not found)
            name: Resource name
            hash: Resource hash
            path: Path to resource
            checked: Last time information was updated
        :rtype: dict[str, str]
        """
        try:
            with self._resource_lock:
                res = self._resources[resource_name]
        except KeyError:
            return {}
        return res
