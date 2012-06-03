###############################################################################
#
# Copyright (c) 2012 Ruslan Spivak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

__author__ = 'Ruslan Spivak <ruslan.spivak@gmail.com>'

import socket
import logging
from logging import handlers

import logsna


class LogUnixSocketHandler(handlers.SocketHandler):
    """Sends pickled log records over a Unix domain socket."""

    def __init__(self, host='/tmp/_cynic.sock'):
        """host - a path to socket"""
        handlers.SocketHandler.__init__(self, host, None)

    def makeSocket(self, timeout=1):
        """Overriden factory method to create Unix Domain Stream socket."""
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if hasattr(s, 'settimeout'):
            s.settimeout(timeout)
        s.connect(self.host)
        return s


def get_stream_logger(name, level=logging.DEBUG):
    """Logger for children that serve client connections.

    It uses LogUnixSocketHandler to communicate with parent's
    logging server.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    socket_handler = LogUnixSocketHandler()
    # don't bother with a formatter, since a socket handler sends the event as
    # an unformatted pickle
    logger.addHandler(socket_handler)
    return logger


def get_console_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create an instance of the sane formatter
    formatter = logsna.Formatter()

    # add our formatter to the console handler
    ch.setFormatter(formatter)

    # add the console handler to the logger
    logger.addHandler(ch)

    return logger
