#!/usr/bin/python3
# pylint: disable=maybe-no-member
from multiprocessing import Process

from bottle import request, route, run
from utils import shell

KEY = 'uUQFKhdAacN9c2av'
CMDS = ['iperf3', 'ls']
POOL = {}


def log_file(x1, x2):
    return f'/tmp/x_{x1}_{x2.replace(" ", "_")}'


@route('/ping')
def index():
    return 'pong'


@route('/recv', 'POST')
def recv():
    if KEY != request.params.get('key'):
        return 'hello, bottle'

    cmd = request.params.get('cmd')
    if cmd not in CMDS:
        return 'hello, bottle'

    args = request.params.get('args', '')
    log = log_file(cmd, args)
    shell(f'echo "" > {log}')
    cmd = f'{cmd} {args} > {log}'
    p = Process(target=lambda: shell(cmd))
    p.start()
    POOL[p.pid] = p

    return str(p.pid)


@route('/kill', 'POST')
def kill():
    if KEY != request.params.get('key'):
        return 'hello, bottle'

    pid = int(request.params.get('pid'))
    if pid not in POOL.keys():
        return 'hello, bottle'

    p = POOL[pid]
    if p.is_alive():
        p.terminate()
        p.join()
    del POOL[pid]

    return 'ack'


@route('/free', 'POST')
def free():
    if KEY != request.params.get('key'):
        return 'hello, bottle'

    return 'free' if not POOL else 'wait'


if __name__ == '__main__':
    run(host='0.0.0.0', port=8082)
