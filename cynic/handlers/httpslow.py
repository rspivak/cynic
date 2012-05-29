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

import time
from BaseHTTPServer import BaseHTTPRequestHandler

from cynic.handlers.base import BaseHTTPHandler


class SlowHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def do_GET(self):
        body = self.server.TEMPLATE
        if self.server.data:
            body = self.server.data
        self.send_response(200)
        self.send_header('Content-Length', len(body))
        self.send_header('Content-Type', self.server.CONTENT_TYPE)
        self.end_headers()
        # send a byte of data every sleep_interval
        for ch in body:
            self.wfile.write(ch)
            self.wfile.flush()
            time.sleep(self.server.sleep_interval)


class SlowResponse(BaseHTTPHandler):
    """HTTP handler that doesn't send the response body.

    Accepts request, sends response headers,
    and never sends the response body.
    """

    CONTENT_TYPE = 'application/json'

    TEMPLATE = '{"message": "Hello, World!"}'


    def __init__(self,
                 request,
                 client_address,
                 datapath=None,
                 content_type='application/json',
                 sleep_interval=30, # secs
                 httpclass=SlowHTTPHandler
                 ):
        super(SlowResponse, self).__init__(
            request, client_address, datapath, httpclass)
        self.CONTENT_TYPE = content_type
        self.sleep_interval = sleep_interval
