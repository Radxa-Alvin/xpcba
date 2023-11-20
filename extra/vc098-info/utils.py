#!/bin/python3
# pylint: disable=no-name-in-module
import json
import os
import sys

import requests

BASEDIR = os.path.abspath(os.path.dirname(__file__))
pwd = '/tmp/'
key = 'UZu8qNjKmvxaWX2M'
host = 'https://rc115.setq.me'


def get_path(fname, basedir=BASEDIR, not_exist_mk=True):
    if not os.path.isabs(fname):
        fullpath = os.path.join(basedir, fname)
    else:
        fullpath = fname
    if not_exist_mk:
        parent = os.path.dirname(fullpath)
        if not os.path.exists(parent):
            os.makedirs(parent)
    return fullpath


def rm_file(filename):
    os.remove(get_path(filename))


def pretty_xml(element, indent='  ', newline='\n', level=0):
    indent0 = newline + indent * level
    indent1 = newline + indent * (level + 1)

    if len(element):
        if (element.text is None) or element.text.isspace():
            element.text = indent1
        else:
            element.text = indent1 + element.text.strip() + indent1

    temp = list(element)
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):
            subelement.tail = indent1
        else:
            subelement.tail = indent0
        pretty_xml(subelement, indent, newline, level=level + 1)


def download(url, pwd=pwd, fname=None):
    fname = fname or os.path.join(pwd, url.split('/')[-1])
    with open(fname, 'wb') as f:
        dl = 0
        per = 0
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 1))
        for chunk in resp:
            f.write(chunk)
            dl += len(chunk)
            if round((dl / total * 100), 1) > per:
                per += 0.1
                if sys.stdout is not None:
                    sys.stdout.write('\r{:>5.5}%'.format(per))
                    sys.stdout.flush()

    print('\r  download {}'.format(url.split('/')[-1]))


def svg2pdf(path, sn, fmt='pdf'):
    with open(get_path(path)) as f:
        svg = f.read()

    data = {'svg': json.dumps(svg), 'sn': sn, 'key': key, 'fmt': fmt}
    resp = requests.post(host, data)

    fname = get_path('output/{}/{}.{}'.format(fmt, sn, fmt))
    download(resp.json()['url'], fname=fname)


sys.path.insert(0, get_path('../httpd-db'))
from client import db_get, db_inc, db_set
