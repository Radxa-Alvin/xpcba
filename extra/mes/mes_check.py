#!/usr/bin/python3
import argparse
import os
import json
import time

from mc import fput_object
from scanning import get_scan
from tkinfo import show_msg
from utils import shell, output, http_get, cat


api_url = 'http://192.168.8.12/api.ashx'
base_args = {
    'check': {
        'action': 'CheckRoute',
        'step': '04-PCBA-FCT',
    },
    'complete': {
        'action': 'complete',
        'step': '04-PCBA-FCT',
        'station': 'PCBA-L9-FCT',
        'user': 'DCP',
        'code': '',
    },
}


def set_time():
    try:
        date = output('curl http://x2.setq.me/date 2>/dev/null')
        shell('timedatectl set-timezone Asia/Shanghai')
        shell('timedatectl set-time "{}"'.format(date))
    except Exception as ex:
        print(ex)


def get_sn(dtmp):
    try:
        return cat(f'{dtmp}/scan.txt')
    except Exception:
        text = get_scan('eth0')
        if text == 'empty':
            show_msg('Cannot get sn')
            raise Exception('Empty SN')
        print(text)
        with open(f'{dtmp}/scan.txt', 'w') as f:
            f.write(text)
        return text


def get_code(dtmp):
    try:
        res = ''
        mescode = {}
        result = json.loads(cat(f'{dtmp}/res.json'))
        items = json.loads(cat(f'{dtmp}/items.json'))
        for idx, item in enumerate(items, 1):
            mescode[item['args']['cmd']] = f'OKDO{idx:03d}'
        for k in mescode.keys():
            if result.get(k, 0) != 0:
                res = mescode[k]
                break
        return res
    except Exception as ex:
        print(ex)
        return ''


def upload_log(dtmp):
    t0 = cat(f'{dtmp}/enter_time')
    dst = f'okdo-3c/{get_sn(dtmp)}'
    base = f'/tmp/xpcba/log/{t0}'

    shell(f'mkdir -p {base}')
    shell(f'dmesg > {base}/dmesg.txt')
    shell(f'cp {base}_* {base}/')
    shell('touch /tmp/x_iperf3*')
    shell(f'cp /tmp/x_iperf3* {base}/')
    shell(f'cp /tmp/xpcba/server.txt {base}/')
    shell('sleep 0.1 && sync')
    shell(f'tar -czvf {base}.tgz {base} > /dev/null 2>&1')

    fput_object(f'{dst}/{t0}.tgz', f'{base}.tgz')


def check(args):
    mode, query = args.mode, {}
    for k, v in base_args[mode].items():
        query[k] = v or args.__dict__[k]
    query['sn'] = get_sn(args.dtmp)

    if mode == 'complete':
        query['code'] = get_code(args.dtmp)

    if args.debug:
        print(query)

    if mode == 'complete':
        time.sleep(0.2)
        upload_log(args.dtmp)

    resp = http_get(api_url, query, timeout=10)
    text = resp.read().decode()

    if text:
        show_msg(text)
        os.kill(os.getppid(), 9)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', default='print')
    parser.add_argument('-c', '--code', default='')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-f', '--fix', action='store_true')
    parser.add_argument('dtmp', default='/tmp/_', nargs='?')
    args = parser.parse_args()

    if args.fix:
        base_args['check']['step'] = '03-PCBA-QC'
        base_args['complete']['step'] = '03-PCBA-QC'
        base_args['complete']['station'] = 'PCBA-L9-AOI'

    if args.mode == 'print':
        set_time()
        print('<mes_check>,<PASS>,<0>')
    else:
        check(args)
