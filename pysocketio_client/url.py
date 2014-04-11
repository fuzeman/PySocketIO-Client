from urlparse import urlparse
import re


def get_components(url):
    parsed = urlparse(url)

    return {
        'protocol': parsed.scheme,
        'host': parsed.hostname,
        'port': parsed.port,
        'path': parsed.path or '/'
    }


def parse_url(url):
    obj = get_components(url)

    if re.search(r'(http|ws)', obj['protocol']) and obj['port'] == 80:
        obj['port'] = None

    if re.search(r'(http|ws)s', obj['protocol']) and obj['port'] == 443:
        obj['port'] = None

    obj['id'] = obj['protocol'] + obj['host'] + ((':%s' % obj['port']) if obj['port'] else '')

    obj['href'] = '%s://%s%s' % (
        obj['protocol'],
        obj['host'],
        (':%s' % obj['port']) if obj['port'] else ''
    )

    return obj
