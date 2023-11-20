#!/usr/bin/python3
import argparse
import json
import os
import sys
import time
from multiprocessing import freeze_support

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.client import Client, __version__, __author__
from core.utils import _exec, adb_forward, enter_test, fmt_ret, get_path, get_env, Timer


class FakeTimer:
    def __init__(self, *args, **kw):
        pass

    def __getattr__(self, name):
        return lambda *a, **k: None


def merge(arr, k, v):
    for x in arr:
        if x['exec'] == k:
            x.update(v)


def conf(args):
    with open(get_path(args.config)) as f:
        for k, v in json.loads(f.read()).items():
            if not args.__dict__.get(k):
                args.__dict__[k] = v
        args.task = args.task or args.board

    with open(get_path(f'conf/{args.board}/{args.task}.json')) as f:
        config = json.loads(f.read())
        args.update = config.get('update', 'undefined')

    if args.env and config.get('source'):
        args.__dict__.update(get_env(config['source']))

    if args.sku:
        with open(get_path(f'conf/{args.board}/{args.sku}.json')) as f:
            for k, v in json.loads(f.read()).items():
                merge(config['items'], k, v)

    if args.debug:
        globals()['Timer'] = FakeTimer

    items, conds = [], []
    for item in config['items']:
        if len(item['name']) > 13:
            raise Exception(f'The name is too long.\n  {item["name"]}')

        if item.get('pass'):
            continue

        d = {
            'name': item['name'],
            'args': {
                'cmd': item['exec'],
                'type': item.get('type', 'buildin'),
                'node': item.get('node', 'bin')
            },
            'cond': item.get('cond'),
            'hint': item.get('hint'),
            'rest': item.get('rest', 0),
            'auto': item.get('auto', True),
            'wait': item.get('wait', False)
        }

        for key in ('args', 'save', 'hook'):
            if item.get(key) is not None:
                d['args'][key] = item[key]

        if item.get('type') == 'external':
            d['args']['file'] = config['scripts'][item['exec']]

        if item.get('cond'):
            conds.append(d)
        else:
            items.append(d)

    return items, conds, config.get('finish')


def print_res(idx, res, item):
    ret = fmt_ret(res['RESULT'], item['auto'])
    err, msg = res['ERR_CODE'], res['MSG']
    print(f'  {idx:>2}. {item["name"]:<15}{ret}{err:<4}{msg}')


def verify(cond, result):
    match = {
        'all:pass': lambda x: not any(x),
        'any:pass': lambda x: not all(x),
        'all:fail': lambda x: all(x),
        'any:fail': lambda x: any(x)
    }

    def some(cond, result):
        key, ret = cond.split(':')
        if key not in result.keys():
            raise Exception('Not a valid condition.')
        return bool(result[key]) == bool(ret == 'fail')

    if cond in match.keys():
        ret = match[cond](result.values())
    else:
        ret = some(cond, result)
    return ret


def main(args):
    print(f'XPCBA v{__version__} client starting up ...')
    # print(f'Powered by {__author__}')

    items, conds, finish = conf(args)
    query, result, cmdlen = {}, {}, 0

    if args.via == 'adb':
        adb_forward(args.port, args.ser, args.timeout, args.debug)

    client = Client(args.host, args.port, args.debug)
    enter_test(client, args.board, args.timeout, args.cache)

    with open(get_path('env.json', client.dtmp), 'w') as f:
        f.write(json.dumps(args.__dict__))

    with open(get_path('items.json', client.dtmp), 'w') as f:
        f.write(json.dumps(items + conds))

    print(f'- board: {args.board}, sku: {args.sku or "default"}')
    print(f'- update: {args.update}')
    print('======== Start Test =========')

    t = Timer(600, wait=1.0, func='spin')
    for item in items:
        name, args = item['name'], item['args']
        cmdlen = max(cmdlen, len(args['cmd']))
        t.puts(item['hint'] or 'wait ack')
        print(f'  {name}')
        client.start(args)
        query[name] = 1
        if item.get('wait') == True:
            while True:
                time.sleep(0.5)
                if client.query(args).get('RESULT'):
                    break
        time.sleep(item['rest'])
        t.stop(f'\r{" " * 80}', '\r')

    print('======== Test Result ========')
    time.sleep(0.5)

    t = Timer(600, wait=0.05, func='spin')
    while True:
        for item in items:
            name, args = item['name'], item['args']
            if query[name]:
                res = client.query(args)
                if res.get('RESULT'):
                    query[name] = 0
                    idx = len(query) - sum(query.values())
                    result[args['cmd']] = int(res['ERR_CODE'])
                    t.stop(f'\r{" " * 80}', '\r')
                    print_res(idx, res, item)
                    time.sleep(0.1)
                else:
                    t.puts(f'query {res["TEST_ITEM"]:<{cmdlen}}')
                    time.sleep(1.05)

        if not any(query.values()):
            break

    with open(get_path('res.json', client.dtmp), 'w') as f:
        f.write(json.dumps(result))

    if conds:
        t = Timer(600, wait=0.05, func='spin')
        print('======== In The End =========')
        for idx, item in enumerate(conds, 1):
            name, args = item['name'], item['args']
            if verify(item['cond'], result):
                t.puts(item['hint'] or f'  Exec {name}')
                client.start(args)
                time.sleep(0.5)
                while True:
                    try:
                        res = client.query(args)
                    except Exception:
                        if 'reset key' in name.lower():  # for power key
                            res = {
                                'MSG': '',
                                'RESULT': 'PASS',
                                'ERR_CODE': '0'
                            }
                    if res.get('RESULT'):
                        t.stop(f'\r{" " * 80}', '\r')
                        print_res(idx, res, item)
                        break
                    time.sleep(1.05)
            else:
                print(f"# Cond '{item['cond']}' not met, skip {name}.")

    if finish:
        _exec(get_path(finish), client.dtmp)

    try:
        client.exit()
    except Exception as ex:
        if client.debug:
            print(ex)


if __name__ == '__main__':
    freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--board')
    parser.add_argument('-v', '--via')
    parser.add_argument('-s', '--sku')
    parser.add_argument('-t', '--task')
    parser.add_argument('-S', '--ser', default='')
    parser.add_argument('-c', '--config', default='ui/config.json')
    parser.add_argument('-C', '--cache', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-e', '--env', action='store_true')
    parser.add_argument('-H', '--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=6688, type=int)
    parser.add_argument('-T', '--timeout', default=30, type=int)
    args = parser.parse_args()

    main(args)

    input('\nPress enter key to exit\n')
    time.sleep(180)
