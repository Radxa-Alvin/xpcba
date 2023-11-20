#!/usr/bin/python3
import os
import sys
import time
from datetime import datetime

import segno

from utils import db_inc, db_set, get_path, pretty_xml, rm_file, svg2pdf

try:
    import lxml.etree as el
except ImportError:
    import xml.etree.ElementTree as el

batch = {'cb': '01', 'wm': '01', 'sm': '01'}
pn = {'cb': '735-00202', 'wm': '735-00217', 'sm': '735-00211'}
rev = {'cb': 'Rev.1', 'wm': 'Rev.1', 'sm': 'Rev.1'}
info_file = f'{sys.argv[-1]}/mac_info.txt'
PRT_CMD = rf'PowerShell -ExecutionPolicy Bypass -File {get_path("print.ps1")} {{}}'

err_path = '<path d="M8 8 L26 26 M26 8 L8 26" style="stroke:black;stroke-width:2" />'


def get_year():
    return str(datetime.now().year)[2:]


def get_week(date=None):
    date_at = datetime.date(date or datetime.now())
    return f'{date_at.isocalendar()[1]:02}'


def get_uuid(key):
    return f'{int(db_inc(key, db="vc098-uuid")):04}'


def get_mac(tpy, cache={}):
    if not cache.get(tpy):
        with open(get_path(info_file)) as f:
            for line in f.readlines():
                val, key = line.split('#')
                val, key = ''.join(val.strip().split(':')), key.strip()
                cache[key] = val.upper() if len(val) == 12 else None
    return cache.get(tpy)


def get_sn(key):
    return key.upper() + get_year() + get_week() + batch[key] + get_uuid(key)


def get_data(key, sn):
    func = {
        'cb': lambda sn: f'SN:{sn}',
        'sm': lambda sn: f'SN:{sn};LAN:{get_mac("eth")}',
        'wm': lambda sn: f'SN:{sn};WFM:{get_mac("wlan")};BTM:{get_mac("bt")}'
    }
    return func[key](sn)


def back_uuid(key, cache={}):
    keys = ('cb', 'sm', 'wm')
    for x in keys[: keys.index(key) + 1]:
        if not cache.get(x):
            db_inc(x, -1, db='vc098-uuid')
            cache[x] = True


def find_elem(root, gid):
    for x in root.iter('{http://www.w3.org/2000/svg}g'):
        if x.attrib.get('id') == gid:
            return x


def update_qr(root, data, line=None):
    qr = segno.make(data, micro=False)
    qr.save(get_path('output/tmp-qr.svg'), scale=1)

    if line is None:
        qrline = None
        tmp = el.parse(get_path('output/tmp-qr.svg'))
        for x in tmp.getroot():
            if x.attrib.get('class') == 'qrline':
                qrline = x
                break
    else:
        qrline = el.fromstring(line)

    elem = find_elem(root, 'qr')

    if elem is not None and qrline is not None:
        for x in elem.getchildren():
            if x.attrib.get('class') == 'qrline':
                for k, v in qrline.attrib.items():
                    x.set(k, v)

    rm_file('output/tmp-qr.svg')


def update_sn(root, sn):
    elem = find_elem(root, 'sn')
    for x in elem:
        if x.attrib.get('id') == 'sn-text':
            x.text = sn


def gen_label(key):
    sn = get_sn(key)
    data = get_data(key, sn)

    db_set(sn, data, 'vc098-info')

    tree = el.parse(get_path(f'format/{key}-qr.svg'))
    root = tree.getroot()

    if 'None' in data:
        update_qr(root, data, err_path)
        update_sn(root, 'NOT FOUND MAC')
        back_uuid('wm')
    else:
        update_qr(root, data)
        update_sn(root, f'SN: {sn}')

    pretty_xml(root)
    tree.write(get_path(f'output/{key}-qr.svg'))

    try:
        svg2pdf(f'output/{key}-qr.svg', sn, 'pdf')
        rm_file(f'output/{key}-qr.svg')
    except Exception as ex:
        back_uuid(key)
        print(ex)
        exit(1)

    return get_path(f'output/pdf/{sn}.pdf')


def print_pdf():
    files = [gen_label(x) for x in ('cb', 'sm', 'wm')]
    for fname in files:
        os.system(PRT_CMD.format(fname))
        time.sleep(2)


if __name__ == '__main__':
    print_pdf()
