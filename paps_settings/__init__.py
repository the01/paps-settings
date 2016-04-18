# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.2.6b0"
__date__ = "2016-04-18"
# Created: 2015-06-27 17:33

import logging

from .plugin import SettingsPlugin
from .settable_plugin import get_file_hash, SettablePlugin

__all_ = ["plugin", "settable_plugin"]
logger = logging.getLogger(__name__)
