#!/usr/bin/python3
import json
import os
import platform
import random
import signal
import string
import subprocess
import sys
import tempfile
import time
from multiprocessing import Process

BASEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

shell = lambda x: subprocess.check_call(x, shell=True)
output = lambda x: subprocess.check_output(x, shell=True).decode()
py_exe = 'py -{}.{}'.format(*sys.version_info[:2])
is_win32 = True if sys.platform == 'win32' else False
dev_null = 'NUL' if is_win32 else '/dev/null'
BREAK_EVENT = signal.CTRL_BREAK_EVENT if is_win32 else signal.SIGTERM


class Timer:
    def __init__(self, timeout=60, rest=3, wait=0, func='tick', debug=False):
        assert isinstance(timeout, int)
        assert func in ['tick', 'spin']
        self.timeout = timeout
        self.rest = rest
        self.wait = wait
        self.func = getattr(self, func)
        self.debug = debug
        self.p = None

    def tick(self, info, error):
        time.sleep(self.wait)
        print(info, end=' ', flush=True)
        for _ in range(int(self.timeout / self.rest)):
            time.sleep(self.rest)
            print('.', end='', flush=True)
        else:
            print(f'\n\n{error}', flush=True)
            os.kill(os.getppid(), BREAK_EVENT)

    def spin(self, info, error):
        time.sleep(self.wait)
        cursor = lambda idx: ('\\|/-')[idx % 4]
        for idx, _ in enumerate(range(self.timeout * 4)):
            time.sleep(0.25)
            print(f'\r{info} {cursor(idx)} ', end='', flush=True)
        else:
            print(f'\n\n{error}', flush=True)
            os.kill(os.getppid(), BREAK_EVENT)

    def puts(self, info, error='Timeout'):
        self.stop(echo=False)
        self.p = Process(target=self.func, args=(info, error))
        self.p.start()

    def loop(self, func, *args, **kw):
        t0 = time.monotonic()
        result = None
        while True:
            try:
                result = func(*args, **kw)
                break
            except Exception as ex:
                if self.debug:
                    print(ex)
            time.sleep(self.rest)
        t1 = time.monotonic()
        echo = (t1 - t0) > self.wait
        self.stop(echo=echo)
        return result

    def stop(self, msg='', end='\n', echo=True):
        self.p and self.p.terminate()
        self.p = None
        if echo:
            print(msg, end=end, flush=True)


def get_path(fname, basedir=BASEDIR, not_exist_mk=True):
    if not os.path.isabs(fname):
        fname = os.path.join(basedir, fname)
    if not_exist_mk:
        parent = os.path.dirname(fname)
        if not os.path.exists(parent):
            os.makedirs(parent)
    return os.path.abspath(fname)


def walk_dir(src, dst):
    src_a, dst_a = [], []
    for root, _, files in os.walk(src):
        for f in files:
            src_a.append(os.path.join(root, f))
            dst_a.append(os.path.join(dst, os.path.relpath(root, src), f))
    return zip(src_a, dst_a)


def log_file(base, created, item):
    log = get_path('{}/log/{}_{}.txt'.format(base, created, item))
    shell('touch {}'.format(log))
    return log


def gen_nonce(d=8):
    pool = string.ascii_letters + string.digits
    chrs = [random.choice(pool) for _ in range(d)]
    return ''.join(chrs)


def play(audio):
    if not is_win32:
        for player in ['aplay', 'mplayer']:
            try:
                shell('{} {} > /dev/null 2>&1'.format(player, audio))
                break
            except Exception as ex:
                print(ex)
    else:
        play_cmd = '{} {}'.format(get_path('blob/win32/player.ps1'), audio)
        shell('PowerShell -ExecutionPolicy Bypass -File {}'.format(play_cmd))


def _exec(fname, args):
    if is_win32:
        cmd = '{} {} {}'.format(py_exe, fname, fmt_args(args))
    else:
        cmd = '{} {}'.format(fname, fmt_args(args))
        shell('chmod +x {}'.format(fname))
    return shell(cmd)


def adb(cmd, ser=''):
    if is_win32:
        adb = get_path('blob/win32/adb/adb.exe')
    else:
        adb = 'adb'
    if ser:
        adb += f' -s {ser}'
    return shell(f'{adb} {cmd}')


def adb_forward(port, ser='', timeout=30, debug=False):
    t = Timer(timeout, wait=1, debug=debug)
    t.puts('Wait for adb', '# Devices not found')
    cmd = f'forward tcp:{port} tcp:{port} > {dev_null} 2>&1'
    t.loop(adb, cmd, ser)


def enter_test(client, board, timeout=30, cache=False):
    t = Timer(timeout, wait=1, debug=client.debug)
    t.puts('Wait for ACK', '# Unable enter test')
    t.loop(client.enter, board, cache)
    print(f"Connected to ('{client.host}', {client.port})\n")


def get_env(fname):
    try:
        env_file = tempfile.mktemp()
        _exec(get_path(fname), env_file)

        with open(env_file, 'r') as f:
            return json.loads(f.read())
    except Exception:
        print(f'Exec {fname} returned non-zero exit status.')
        exit(1)


def fmt_args(args):
    return ' '.join(map(str, args)) if isinstance(args, list) else args


def fmt_ret(ret, auto=True):
    ret = ret if auto else 'PRE-' + ret
    if 'windows-7' in platform.platform().lower():
        fmts = {
            'FAIL': 'x {:<10}',
            'PASS': 'o {:<10}',
            'PRE-PASS': '- {:<10}'
        }
    else:
        fmts = {
            'FAIL': '\033[91m{:<10}\033[0m',
            'PASS': '\033[92m{:<10}\033[0m',
            'PRE-PASS': '\033[96m{:<10}\033[0m'
        }
    if ret not in fmts.keys():
        ret = 'FAIL'
    return fmts[ret].format(ret)


if __name__ == '__main__':
    print(fmt_ret('FALL'))
    print(fmt_ret('PASS'))
    print(fmt_ret('PASS', False))
