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

import os
import sys
import errno
import socket
import select
import signal
import optparse
import StringIO
import ConfigParser

from cynic.utils import get_console_logger

READ_ONLY = select.POLLIN
POLL_TIMEOUT = 1000 # 1 sec
BACKLOG = 5

DEFAULT_CONFIG = """\
[handler:httphtml]
# send simple 'hello world!' HTML page over HTTP as a response
class = cynic.handlers.httphtml.HTTPHtmlResponse
#args = ('/tmp/test.html', )
host = 0.0.0.0
port = 2000

[handler:httpjson]
# send simple 'hello world!' JSON over HTTP as a response
class = cynic.handlers.httpjson.HTTPJsonResponse
#args = ('/tmp/test.json', )
host = 0.0.0.0
port = 2001

[handler:httpnone]
# send headers, but not the response body
class = cynic.handlers.httpnone.HTTPNoBodyResponse
host = 0.0.0.0
port = 2002

[handler:httpslow]
# send one byte of response every 30 seconds
class = cynic.handlers.httpslow.HTTPSlowResponse
#args = ('/tmp/test.json', 'application/json', 1)
host = 0.0.0.0
port = 2003

[handler:reset]
# accepts connection and sends RST packet right away
class = cynic.handlers.reset.RSTResponse
host = 0.0.0.0
port = 2004
"""

# taken from logging.config
def _resolve(name):
    """Resolve a dotted name to a global object."""
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found


def _reap_children(signum, frame):
    """Collect zombie children."""
    while True:
        try:
            # wait for all children, do not block
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0: # no more zombies
                break
        except:
            # Usually this would be OSError exception
            # with 'errno' attribute set to errno.ECHILD
            # which means there are no more children
            break


def _load_config(fname):
    """Return an instance of ConfigParser."""
    config = ConfigParser.ConfigParser()
    if hasattr(fname, 'readline'):
        config.readfp(fname)
    else:
        config.read(fname)

    return config


class HandlerConfig(object):
    def __init__(self, klass, args, host, port):
        self.klass = klass
        self.args = args
        self.host = host
        self.port = port
        # for Unix domain stream protocol address contains path
        self.address = (host, port) if port is not None else host

def _get_handler_configs(config):
    configs = []
    for section in config.sections():
        if not section.startswith('handler:'):
            continue

        clsname = config.get(section, 'class')
        klass = _resolve(clsname)
        host = config.get(section, 'host')
        port = config.getint(section, 'port')
        args = ()
        if config.has_option(section, 'args'):
            args = eval(config.get(section, 'args'), {})
        hconfig = HandlerConfig(klass, args, host, port)
        configs.append(hconfig)

    # special config for the server's log handler
    klass = _resolve('cynic.handlers.log.LogRecordHandler')
    host = '/tmp/_cynic.sock'
    port = None # signifies AF_UNIX protocol
    args = ()
    hconfig = HandlerConfig(klass, args, host, port)
    configs.append(hconfig)

    return configs


logger = get_console_logger('server')


class IOLoop(object):
    """Main IO loop.

    Spawns children to handle requests.
    """
    def __init__(self, handler_configs):
        self.handler_configs = handler_configs
        self.fd_to_hconfig = {}
        self.poller = None
        self._setup()

    def _setup(self):
        signal.signal(signal.SIGCHLD, _reap_children)

        self.poller = poller = select.poll()

        for hconfig in self.handler_configs:
            if hconfig.port is None:
                # Unix domain socket
                server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            else:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.setblocking(0)

            logger.info(
                'Starting %-20r on port %s',
                hconfig.klass.__name__, hconfig.port or hconfig.host
                )

            self.fd_to_hconfig[server.fileno()] = server, hconfig
            if hconfig.port is None:
                # Unix domain socket
                try:
                    os.unlink(hconfig.host)
                except:
                    pass
                server.bind(hconfig.host)
            else:
                server.bind((hconfig.host, hconfig.port))
            server.listen(BACKLOG)

            poller.register(server, READ_ONLY)


    def run(self):
        while True:
            try:
                events = self.poller.poll(POLL_TIMEOUT)
            except select.error as e:
                code, msg = e.args
                if code == errno.EINTR:
                    continue
                else:
                    raise

            for fd, flag in events:
                # retrieve the actual socket and handler class
                # from its file descriptor
                sock, hconfig = self.fd_to_hconfig[fd]

                # we're interested only in READ events
                if not flag & READ_ONLY:
                    continue

                # socket is ready to accept a connection
                try:
                    request, client_address = sock.accept()
                except IOError as e:
                    code, msg = e.args
                    if code == errno.EINTR:
                        continue
                    else:
                        raise

                # spawn a child that will handle the request (connection)
                pid = os.fork()
                if pid == 0: # child
                    for sock, _ in self.fd_to_hconfig.values():
                        sock.close()
                    klass = hconfig.klass
                    handler = klass(request, client_address, *hconfig.args)
                    handler.handle()
                    os._exit(0)
                else:
                    request.close()


def main():
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', dest='config_path',
                      help='Path to configuration file')

    options, args = parser.parse_args()

    path = options.config_path
    if path is None:
        path = StringIO.StringIO(DEFAULT_CONFIG)

    config = _load_config(path)
    handlers = _get_handler_configs(config)
    ioloop = IOLoop(handlers)
    ioloop.run()
