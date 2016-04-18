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
__date__ = "2016-04-18"
# Created: 2015-06-28 16:34

import os
import threading

from paps_settings import SettablePlugin


class DummyPlugin(SettablePlugin):
    """
    Simple dummy plugin with settings
    """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(DummyPlugin, self).__init__(settings)
        # Resource file is in this module
        self._prePath = os.path.abspath(os.path.dirname(__file__))
        self._resource_path = self.joinPathPrefix("resources")

        # Two example variable can be set via web frontend
        self._var1 = "hi"
        self._var2 = "5"
        self._var_lock = threading.Lock()

    def start(self, blocking=False):
        self.debug("()")
        super(DummyPlugin, self).start(blocking)

    def stop(self):
        self.debug("()")
        super(DummyPlugin, self).stop()

    def on_config(self, settings):
        self.debug("()")
        with self._var_lock:
            self._var1 = settings['var1']
            self._var2 = settings['var2']
            self.info(u"Now set to {} and {}".format(self._var1, self._var2))

    def get_data(self):
        self.debug("()")
        with self._var_lock:
            return {
                'var1': self._var1,
                'var2': self._var2
            }

    def on_person_new(self, people):
        self.debug(people)

    def on_person_update(self, people):
        self.debug(people)

    def on_person_leave(self, people):
        self.debug(people)

    def get_info(self):
        self.debug("()")
        return {
            'name': "Dummy plugin",
            'description': "A simple plugin-dummy plugin"
        }
