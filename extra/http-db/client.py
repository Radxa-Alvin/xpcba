#!/usr/bin/python3
import json
import os
import socket
from math import nan
from http.client import HTTPResponse
from urllib import request
from urllib.parse import urlencode

KEY = 'uUQFKhdAacN9c2av'
DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT

HTTPResponse.text = property(lambda self: self.read().decode())
HTTPResponse.json = lambda self: json.loads(self.text or '""')

if os.environ.get('xpcba') == 'debug':
    base_url = 'http://127.0.0.1:8094/{}'
else:
    base_url = 'https://r2.setq.me/{}'


def http_get(url, query={}, timeout=DEFAULT_TIMEOUT):
    url = url + '?' + urlencode(query)
    req = request.Request(url)
    return request.urlopen(req, timeout=timeout)


def http_post(url, data=None, timeout=DEFAULT_TIMEOUT):
    req = request.Request(url)
    data = urlencode(data).encode()
    return request.urlopen(req, data=data, timeout=timeout)


def curl(endpoint, args, method):
    func = http_get if method == 'get' else http_post
    return func(base_url.format(endpoint), args).json()


def db_set(name, value, db='default', method='get'):
    args = dict(name=name, value=value, db=db, key=KEY)
    data = curl('set', args, method)
    return bool(data['msg'] == 'ok')


def db_del(name, db='default', method='get'):
    args = dict(name=name, db=db, key=KEY)
    data = curl('del', args, method)
    return bool(data['msg'] == 'ok')


def db_inc(name, value=1, db='default', method='get'):
    args = dict(name=name, value=value, db=db, key=KEY)
    data = curl('inc', args, method)
    return int(data['value']) if data['msg'] == 'ok' else nan


def db_get(name, value='', db='default', method='get'):
    args = dict(name=name, value=value, db=db, key=KEY)
    data = curl('get', args, method)
    return data['value'] if data['msg'] == 'ok' else value


if __name__ == '__main__':
    print(db_set('hello', 'flask'))
    print(db_get('hello'))
    print(db_del('hello'))
    print(db_get('hello'))
    print(db_set('var', 32))
    print(db_inc('var', 10))
