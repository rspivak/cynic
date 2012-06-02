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

from BaseHTTPServer import BaseHTTPRequestHandler


class BaseHandler(object):
    """Base handler class for stream sockets."""

    def __init__(self, connection, client_address):
        """
        Args:
            connection - connected socket returned by server's accept
            client_address - tuple containing client_host and client_port
        """
        self.connection = connection
        self.client_address = client_address

    def handle(self):
        pass


class BaseHTTPHandler(BaseHTTPRequestHandler):
    """Base handler class for HTTP protocol."""

    protocol_version = 'HTTP/1.0'

    CONTENT_TYPE = 'text/plain'
    TEMPLATE = ''

    def __init__(self, connection, client_address, datapath=None):
        """
        Args:
            connection - connected socket returned by server's accept
            client_address - tuple containing client_host and client_port
            datapath - file path to a data file that will be sent as
                       as a response body to the client
        """
        self.connection = self.request = connection
        self.client_address = client_address
        self.server = self
        self.setup()

        self.data = open(datapath).read() if datapath is not None else ''

    def do_GET(self):
        """HTTP GET request handler"""
        body = self.TEMPLATE
        if self.data:
            body = self.data
        self.send_response(200)
        self.send_header('Content-Length', len(body))
        self.send_header('Content-Type', self.CONTENT_TYPE)
        self.end_headers()
        self.wfile.write(body)
