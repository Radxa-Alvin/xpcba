#!/usr/bin/python3
import argparse
import os
import socket
import struct
import time
from tempfile import mkdtemp

from protocol import Protocol, proc_args
from utils import _exec, adb_forward, gen_nonce, get_path, play, walk_dir

__version__ = '0.0.6'
__author__ = 'akgnah <setq@radxa.com>'
p = Protocol()


def conn(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, struct.pack('ii', 1, 0))
    sock.connect((host, port))
    sock.settimeout(30)
    return sock


class Client:
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self._conn = False
        self.root = '/tmp/xpcba'
        self.dtmp = mkdtemp()
        debug and print(self.dtmp)

    def send(self, content, mime_typ='text/json'):
        if not self._conn:
            self.sock = conn(self.host, self.port)
        args = proc_args(content, mime_typ)
        return p.send(self.sock, args)

    def recv(self):
        res = p.recv(self.sock)
        if self.debug and res['type'] == 'text/json':
            print(res['content'])
        return res['content'], res['type']

    def enter(self, board, cache=False):
        args = {'type': 'cmd', 'cmd': 'enter', 'board': board}
        args = dict(args, cache=cache) if cache else args
        self.time = time.strftime(r'%Y%m%d-%H%M%S')
        self.send(dict(args, time=self.time))
        content, _ = self.recv()
        if content.get('STATUS') == 'ACK':
            self._conn = True
            if content.get('VER') != __version__:
                print('Warning: server version and client version do not match.\n')
        return content

    def exit(self):
        args = {'type': 'cmd', 'cmd': 'exit'}
        self.send(args)
        content, _ = self.recv()
        if content.get('STATUS') == 'ACK':
            self._conn = False
        return content

    def push(self, item, src, dst, typ='lib'):
        base = {'type': 'cmd', 'test_item': item['cmd']}

        nonce =  gen_nonce()
        args = {
            'cmd': 'push',
            'nonce': nonce,
            'file_path': dst,
            'file_type': typ
        }
        self.send(dict(base, **args))
        content, _ = self.recv()
        if content.get('STATUS') == 'ACK':
            with open(self.path(src), 'rb') as f:
                data = f.read()
            self.send(nonce.encode() + data, 'binary')
            content, _ = self.recv()
            time.sleep(0.05)
        return content

    def pull(self, item, src, dst):
        base = {'type': 'cmd', 'test_item': item['cmd']}

        args = {'cmd': 'pull', 'file_path': src}
        self.send(dict(base, **args))
        content, _ = self.recv()
        with open(self.path(dst), 'wb') as f:
            f.write(content)
        return content

    def start(self, item):
        base = {'type': 'cmd', 'test_item': item['cmd']}

        for key in ('args', 'save'):
            if item.get(key) is not None:
                base[key] = item[key]

        if item.get('hook'):
            self.hook(item, 'load')

        if item.get('type') == 'external':
            node = item.get('node', 'bin')
            dst = f'{self.root}/{node}/{item["cmd"]}'
            self.push(item, item['file'], dst, 'bin')

        self.send(dict(base, cmd='start'))
        content, _ = self.recv()

        if item.get('hook'):
            self.hook(item, 'sent')
        return content

    def query(self, item, hook={}):
        base = {'type': 'cmd', 'test_item': item['cmd']}

        if item.get('args'):
            base['args'] = item['args']

        self.send(dict(base, cmd='query'))
        content, _ = self.recv()

        if content.get('RESULT') and item.get('hook'):
            if not hook.get(item['cmd']):
                self.hook(item, content['RESULT'].lower())
                self.hook(item, 'done')
                hook[item['cmd']] = True
        return content

    def test(self, item):
        if not self._conn:
            raise Exception('Must call enter before testing')

        self.start(item)

        while True:
            res = self.query(item)
            if res.get('RESULT'):
                break
            time.sleep(0.5)
        return res

    def path(self, fname):
        fullpath = get_path(fname, not_exist_mk=False)
        if not os.path.exists(fullpath):
            fullpath = get_path(fname, basedir=self.dtmp)
        return fullpath

    def hook(self, item, step='done'):
        for hook in item['hook'].get(step, '').split(';'):
            if not hook:
                continue
            op, *args = hook.split(':')

            if self.debug:
                print(f'* {op} {" ".join(args)}')

            if op in ('pull', 'push'):
                src, dst = args
                if src.endswith('/') or src.endswith('/*'):
                    for s, d in walk_dir(self.path(src.rstrip('*')), dst):
                        getattr(self, op)(item, s, d)
                    continue
                if dst == '.':
                    dst = os.path.split(src)[-1]
                if dst.endswith(os.path.sep):
                    dst = os.path.join(dst, os.path.split(src)[-1])
                getattr(self, op)(item, src, dst)
            if op == 'play':
                play(self.path(args[0]))
            if op == 'exec':
                fname, *args = args + [self.dtmp]
                _exec(self.path(fname), args)
            time.sleep(0.05)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-S', '--ser', default='')
    parser.add_argument('-v', '--via', default='local')
    parser.add_argument('-b', '--board', default='vc098')
    parser.add_argument('-C', '--cache', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-H', '--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=6688, type=int)
    args = parser.parse_args()

    if args.via == 'adb':
        adb_forward(args.port, args.ser)

    client = Client(args.host, args.port, args.debug)
    client.enter(args.board, args.cache)
    client.exit()
