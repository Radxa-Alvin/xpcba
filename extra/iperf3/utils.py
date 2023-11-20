#!/usr/bin/python3
import json
import os
import socket
import subprocess
from pathlib import Path
from urllib import request
from urllib.parse import urlencode

BASEDIR = os.path.abspath(os.path.dirname(__file__))
HOMEDIR = os.path.expanduser('~/.xpcba')
DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT

shell = lambda x: subprocess.check_call(x, shell=True)
output = lambda x: subprocess.check_output(x, shell=True).decode()
to_json = lambda x: lambda x=x: json.loads(x.read().decode() or '""')


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
        d = json.loads(f.read() or b'{}')
        if _del and key in d:
            del d[key]
        else:
            d[key] = val
    with open(get_path('cache.json', basedir=HOMEDIR), 'w') as f:
        f.write(json.dumps(d))
    return val


def cache_get(key, val=None):
    with open(get_path('cache.json', basedir=HOMEDIR), 'r') as f:
        d = json.loads(f.read() or b'{}')
    return d.get(key, val)


def http_get(url, query={}, timeout=DEFAULT_TIMEOUT):
    url = url + '?' + urlencode(query)
    req = request.Request(url)
    resp = request.urlopen(req, timeout=timeout)
    resp.json = to_json(resp)
    return resp


def http_post(url, data=None, timeout=DEFAULT_TIMEOUT):
    req = request.Request(url)
    data = urlencode(data).encode()
    resp = request.urlopen(req, data=data, timeout=timeout)
    resp.json = to_json(resp)
    return resp


if __name__ == '__main__':
    cache_set('eth0', '192.168.42.1')
    print(cache_get('eth0'))
