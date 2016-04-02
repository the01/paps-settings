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
# Created: 2015-06-25 02:09
""" Webserver serving the plugin website """

import logging
logging.basicConfig(level=logging.DEBUG)

from twisted.logger import STDLibLogObserver, globalLogBeginner
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource\
    #, HTTPChannelHixie76Aware

from flaskApp import create_app
from pluginProtocol import PluginServerProtocol


logger = logging.getLogger(__name__)


def create_server(
        host="localhost", port=5000, debug=False,
        observer_name="twisted", flask_app=None
):
    """
    Create and setup twisted server
    (only need to do a reactor.run() after)

    :param host: Host address to bind to (default: localhost)
    :type host: str
    :param port: Port to bind to (default: 5000)
    :type port: int
    :param debug: Should use debug mode (default: False)
    :type debug: bool
    :param observer_name: Name of twisted observer to log to stdlib
        (default: twisted)
        if None -> do not create observer
    :type observer_name: None | str
    :param flask_app: Flask object to be served (default: None)
        if None -> use imported app
    :type flask_app: flask.Flask
    :rtype: None
    """
    if observer_name is not None:
        observer = STDLibLogObserver(name=observer_name)
        globalLogBeginner.beginLoggingTo([observer])
    if flask_app is None:
        flask_app = create_app(debug=debug)

    # Create a Twisted Web resource for our WebSocket server
    ws_factory = WebSocketServerFactory(
        u"ws://{}:{}".format(host, port)
    )

    ws_factory.protocol = PluginServerProtocol
    # Needed if Hixie76 is to be supported
    # ws_factory.setProtocolOptions(allowHixie76=True)
    ws_resource = WebSocketResource(ws_factory)

    # Create a Twisted Web WSGI resource for our Flask server
    wsgi_resource = WSGIResource(reactor, reactor.getThreadPool(), flask_app)

    # Create a root resource serving everything via WSGI/Flask, but
    # The path "/ws" served by our webocket
    root_resource = WSGIRootResource(wsgi_resource, {'ws': ws_resource})

    # Create a Twisted Web Site and run everything
    site = Site(root_resource)
    # Needed if Hixie76 is to be supported
    # site.protocol = HTTPChannelHixie76Aware

    reactor.listenTCP(port, site)


if __name__ == "__main__":
    import logging

    import logging.config
    from flotils.logable import default_logging_config
    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("twisted").setLevel(logging.INFO)

    create_server("localhost", 5000, True, "twisted")
    reactor.run()
