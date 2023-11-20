#!/usr/bin/python3
import mimetypes
import os
import re
import socket
import subprocess
import uuid

from http.client import HTTPResponse
from json import dumps, loads
from pathlib import Path
from string import Template
from urllib import request
from urllib.parse import parse_qsl, urlencode

__version__ = '0.1.0'

HTTPResponse.content = property(lambda self: self.read())
HTTPResponse.text = property(lambda self: self.read().decode())
HTTPResponse.json = lambda self: loads(self.text or '""')
HTTPResponse.status_code = property(lambda self: self.code)

DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT

DEFAULT_HEADERS = {
    'User-Agent': 'httpx/%s' % __version__,
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

to_list = lambda x: x.items() if isinstance(x, dict) else x  # noqa: E731
to_bytes = lambda s: s if isinstance(s, bytes) else str(s).encode()  # noqa: E731, E501


def http_get(url, params=None, headers=None, timeout=DEFAULT_TIMEOUT):
    if headers is None:
        headers = dict(DEFAULT_HEADERS)
    else:
        headers = dict(headers)

    if params is not None:
        if isinstance(params, str):
            params = parse_qsl(params)
        elif isinstance(params, set):
            params = list(params)
        url = url + '?' + urlencode(params)

    req = request.Request(url, headers=headers)

    return request.urlopen(req, timeout=timeout)


def open_file(fname):
    if re.match('http[s]?:.*', fname):
        data = http_get(fname).read()
    else:
        with open(fname, 'rb') as f:
            data = f.read()
    return data


def get_ctype_binary(name, value):
    if isinstance(value, bytes):
        fname, binary = name, value
    elif isinstance(value, str):
        fname = os.path.split(value)[-1]
        binary = open_file(value)
    elif hasattr(value, 'read'):
        if hasattr(value, 'name'):
            fname = os.path.split(value.name)[-1]
        else:
            fname = name
        binary = value.read()
    else:
        raise ValueError('Invalid file type: %s.' % type(value))

    ctype = mimetypes.guess_type(fname)[0] or 'application/octet-stream'

    return fname, ctype, binary


def pack_files(data, files, headers):
    if isinstance(data, (str, bytes)):
        raise ValueError('Data must not be a string when files is not None.')

    body = []
    BOUNDARY = str(uuid.uuid4())
    # build body
    for name, value in to_list(data):
        body.append('--' + BOUNDARY)
        body.append('Content-Disposition: form-data; name="%s"' % name)
        body.append('Content-Type: text/plain; charset=US-ASCII')
        body.append('Content-Transfer-Encoding: 8bit')
        body.append('')
        body.append(value)

    for name, value in to_list(files):
        fname, ctype, binary = get_ctype_binary(name, value)
        body.append('--' + BOUNDARY)
        body.append('Content-Disposition: form-data; name="%s"; filename="%s"'
                    % (name, fname))
        body.append('Content-Type: %s' % ctype)
        body.append('Content-Transfer-Encoding: binary')
        body.append('')
        body.append(binary)

    body.append('--' + BOUNDARY + '--')
    body.append('')
    body = map(to_bytes, body)
    body = b'\r\n'.join(body)

    # build headers
    headers.update({
        'Content-Length': str(len(body)),
        'Content-Type': 'multipart/form-data; boundary=' + BOUNDARY
    })

    return body, headers


def http_post(url, data=None, json=None, files=None,
         headers=None, timeout=DEFAULT_TIMEOUT):
    if headers is None:
        headers = dict(DEFAULT_HEADERS)
    else:
        headers = dict(headers)

    if files is not None:
        data, headers = pack_files(data or {}, files, headers)
    else:
        if isinstance(data, (str, bytes)):
            ctype = 'text/plain'
        else:
            data = urlencode(data or '')
            ctype = 'application/x-www-form-urlencoded'
        if json is not None:
            data = dumps(json)
            ctype = 'application/json'

        data = to_bytes(data)
        headers.update({
            'Content-Length': str(len(data or b'')),
            'Content-Type': headers.get('Content-Type') or ctype
        })

    req = request.Request(url, headers=headers)

    return request.urlopen(req, data=data, timeout=timeout)
# httpx end


BASEDIR = os.path.abspath(os.path.dirname(__file__))
HOMEDIR = os.path.expanduser('~/.xpcba')


def shell(cmd):
    return subprocess.check_call(cmd, shell=True)


def output(cmd):
    return subprocess.check_output(cmd, shell=True).decode()


def cat(fname, strip=True):
    strip = lambda s: s.strip() if strip else s
    with open(fname, 'r') as f:
        return strip(f.read())


def get_path(fname, basedir=BASEDIR, not_exist_mk=True, not_exist_touch=True):
    if not os.path.isabs(fname):
        fname = os.path.join(basedir, fname)
    if not_exist_mk:
        parent = os.path.dirname(fname)
        if not os.path.exists(parent):
            os.makedirs(parent)
    if not_exist_touch:
        if not os.path.exists(fname):
            Path(fname).touch()
    return os.path.abspath(fname)


def cache_set(key, val=None, _del=False):
    with open(get_path('cache.json', basedir=HOMEDIR), 'r') as f:
        d = loads(f.read() or b'{}')
        if _del and key in d:
            del d[key]
        else:
            d[key] = val
    with open(get_path('cache.json', basedir=HOMEDIR), 'w') as f:
        f.write(dumps(d))
    return val


def cache_get(key, val=None):
    with open(get_path('cache.json', basedir=HOMEDIR), 'r') as f:
        d = loads(f.read() or b'{}')
    return d.get(key, val)
# utils end
