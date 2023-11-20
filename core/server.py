#!/usr/bin/python3
import argparse
import os
import re
import socket
import time
from multiprocessing import Process
from pathlib import Path

from protocol import Protocol, proc_args
from utils import fmt_args, get_path, log_file, output, shell

__version__ = '0.0.6'
__author__ = 'akgnah <1024@setq.me>'
p = Protocol()


class Server:
    def __init__(self, host, port, base, timeout=120):
        self.host = host
        self.port = port
        self.base = get_path(base)
        self.timeout = timeout
        self.root = '/tmp/xpcba'
        self.env = {}
        self.pool = {}
        self.nonce = {}
        self.cache = {}

    def enter(self, content):
        self.time, board = content['TIME'], content['BOARD']
        self.cache = self.cache if content.get('CACHE') else {}
        for root, _, files in os.walk(self.base):
            if root in (self.base, os.path.join(self.base, board)):
                for item in files:
                    self.env[item] = os.path.join(root, item)
                    self.env[Path(item).stem] = self.env[item]
                    shell('chmod +x {}'.format(self.env[item]))
        time_file = get_path('enter_time', self.root)
        shell('echo {} > {}'.format(self.time, time_file))
        return {'CMD': 'ENTER', 'STATUS': 'ACK', 'VER': __version__}

    def exit(self, _):
        self.env = {}
        return {'CMD': 'EXIT', 'STATUS': 'ACK'}

    def start(self, content):
        item = content['TEST_ITEM']
        args = fmt_args(content.get('ARGS', ''))
        log = log_file(self.root, self.time, item)
        cmd = '{} {} > {}'.format(self.env.get(item), args, log)
        if content.get('SAVE') == 'FALSE':
            self.cache[item] = None
        if (self.cache.get(item) or {}).get('RESULT') != 'PASS':
            p = Process(target=lambda: shell(cmd))
            p.start()
            self.cache[item] = None
            self.pool[item] = {'t0': time.monotonic(), 'pid': p.pid}
        return {'CMD': 'START', 'TEST_ITEM': item, 'STATUS': 'ACK'}

    def query(self, content):
        item = content['TEST_ITEM']
        ack = {'CMD': 'QUERY', 'TEST_ITEM': item, 'STATUS': 'ACK'}
        key = ('MSG', 'RESULT', 'ERR_CODE')
        log = log_file(self.root, self.time, item)
        res = output('cat {}'.format(log))
        if self.cache.get(item):
            return self.cache[item]
        if '>,<' in res:
            m = re.search('<([^>]*)>,<([^>]*)>,<([^>]*)>', res)
            val = m.groups() if m else (item, 'FAIL', '-255')
            self.cache[item] = dict(zip(key, val))
        if time.monotonic() - self.pool[item]['t0'] > self.timeout:
            self.cache[item] = dict(zip(key, (item, 'FAIL', '-254')))
        return self.cache.get(item) or ack

    def write(self, content):
        hdr = content[:8].decode()
        if self.nonce.get(hdr):
            item = self.nonce[hdr]['TEST_ITEM']
            fname = self.nonce[hdr]['FILE_PATH']
            with open(self.path(fname), 'wb') as f:
                f.write(content[8:])
            if self.nonce[hdr]['FILE_TYPE'] == 'BIN':
                shell('chmod +x {}'.format(fname))
                self.env[item] = fname
            del self.nonce[hdr]
            return {'CMD': 'PUSH', 'FILE_PATH': fname, 'STATUS': 'ACK'}
        return {'CMD': 'PUSH', 'FILE_PATH': 'Not Found', 'STATUS': 'ACK'}

    def push(self, content):
        self.nonce[content['NONCE']] = content
        return {'CMD': 'PUSH', 'TEST_ITEM': content['TEST_ITEM'], 'STATUS': 'ACK'}

    def pull(self, content):
        fname = self.path(content['FILE_PATH'])
        with open(fname, 'rb') as f:
            data = f.read()
        return data

    def path(self, fname):
        fullpath = get_path(fname, not_exist_mk=False)
        if not os.path.exists(fullpath):
            fullpath = get_path(fname, basedir=self.root)
        return fullpath

    def recv(self, conn):
        res = p.recv(conn) or {'content': {}, 'type': 'text/json'}
        return res['content'], res['type']

    def send(self, conn, content, mime_typ='text/json'):
        args = proc_args(content, mime_typ)
        return p.send(conn, args)

    def select(self, content, mime_typ):
        if mime_typ == 'binary':
            return self.write(content), 'text/json'

        cmds = {
            'ENTER': (self.enter, 'text/json'),
            'START': (self.start, 'text/json'),
            'QUERY': (self.query, 'text/json'),
            'PUSH': (self.push, 'text/json'),
            'PULL': (self.pull, 'binary'),
            'EXIT': (self.exit, 'text/json'),
            '!404': (lambda *x: {}, 'text/json')
        }

        func, mime_typ = cmds.get(content.get('CMD')) or cmds['!404']
        return func(content), mime_typ

    def watch(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen()

        while True:
            conn, addr = sock.accept()
            print('Connected by', addr)
            while True:
                data, mime = self.recv(conn)
                if not data:
                    break
                content, mime_typ = self.select(data, mime)
                self.send(conn, content, mime_typ)
            conn.close()

    def run(self):
        print(f'XPCBA v{__version__} server starting up ...')
        print(f'Powered by {__author__}')
        print(f"Listening on ('{self.host}', {self.port})")
        print('Hit Ctrl-C to quit.\n')

        try:
            self.watch()
        except KeyboardInterrupt:
            print('\nBye.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base', default='bin')
    parser.add_argument('-H', '--host', default='0.0.0.0')
    parser.add_argument('-p', '--port', default=6688, type=int)
    parser.add_argument('-t', '--timeout', default=120, type=int)
    args = parser.parse_args()

    server = Server(args.host, args.port, args.base, args.timeout)
    server.run()
