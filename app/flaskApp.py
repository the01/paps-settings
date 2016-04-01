# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.2"
__date__ = "2016-04-01"
# Created: 2015-06-25 03:41

import logging
import uuid

from flask import Flask, Blueprint, render_template
from flask.ext.restful import Api
from flask.ext.bower import Bower

from flotils.loadable import DateTimeEncoder

from restAPI import PluginListAPI, PluginAPI, PluginResourceAPI, api_path
from db import db_plugin_instance


logger = logging.getLogger(__name__)
page = Blueprint('page', __name__)


def create_app(debug=False):
    """
    Create the flask app

    :param debug: Use debug mode
    :type debug: bool
    :return: Created app
    :rtype: flask.Flask
    """
    app = Flask(__name__)
    app.secret_key = str(uuid.uuid4())
    app.json_encoder = DateTimeEncoder
    app.register_blueprint(page)
    Bower(app)
    api = Api(app)
    api.add_resource(
        PluginListAPI,
        api_path + "plugins/",
        endpoint="APIPlugins"
    )
    api.add_resource(
        PluginAPI,
        api_path + "plugins/<plugin_key>",
        endpoint="APIPlugin"
    )
    api.add_resource(
        PluginResourceAPI,
        api_path + "plugins/<plugin_key>/resources/",
        endpoint="APIPluginResource"
    )

    if debug:
        # Setup app for real debuging mode
        app.debug = True
        # Force update of static files (even in dev mode, browsers still cache)
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        @app.after_request
        def add_header(response):
            response.headers['Cache-Control'] = "public, max-age=0"
            return response
    return app


@page.route("/")
@page.route("/index")
def index():
    """
    Serve index page
    """
    return render_template("widget_seats.html", api_path=api_path)


@page.route("/plugin")
@page.route("/plugin/")
@page.route("/plugin/<plugin_key>")
def plugin(plugin_key=None):
    """
    Serve plugin page

    :param plugin_key: Which plugin page to server; if None -> landing page
            (default: None)
    :type plugin_key: None | unicode
    """
    p = None
    if plugin_key:
        try:
            p = db_plugin_instance.plugin_get(plugin_key)
        except KeyError:
            logger.error(u"Plugin '{}' not found".format(plugin_key))

    return render_template("plugin.html", title="Plugins", plugin=p)


if __name__ == "__main__":
    import logging.config
    from flotils.logable import default_logging_config

    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.DEBUG)

    app = create_app(debug=True)
    app.run(host="0.0.0.0", debug=True)
