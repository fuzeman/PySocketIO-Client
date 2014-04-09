from pysocketio.client.url import parse_url
from pysocketio.client.manager import Manager

import logging

log = logging.getLogger(__name__)


managers = {}


def connect(url, opts=None):
    if opts is None:
        opts = {}

    parsed = parse_url(url)
    href = parsed['href']
    id = parsed['id']

    io = None

    if opts.get('forceNew') or opts.get('multiplex') is False:
        log.debug('ignoring socket cache for %s', href)
        io = Manager(href, opts)
    else:
        if not managers.get(id):
            log.debug('new io instance for %s', href)
            managers[id] = Manager(href, opts)

        io = managers[id]

    return io.socket(parsed['path'])
