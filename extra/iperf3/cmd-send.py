#!/usr/bin/python3
import argparse
import os
import random
import time
from multiprocessing import Process

from utils import cache_get, http_post, output, shell

KEY = 'uUQFKhdAacN9c2av'
ROUTE = {}


def route(op, args):
    try:
        if output('command -v route | tee'):
            shell(f'route {op} -host {args.host} metric 99 dev {args.ifdev}')
        else:
            shell(f'ip route {op} {args.host} metric 99 dev {args.ifdev}')
        return True
    except Exception as ex:
        print(ex)


def send(args):
    d = {'key': KEY, 'cmd': 'iperf3', 'args': f'-c {args.bind} -p {args.port} -t 5'}
    if args.mode == 'c':
        d['args'] += ' -R'
    x = http_post(f'http://{args.host}:8082/recv', d)
    return x.read()


def kill(pid, args):
    d = {'key': KEY, 'pid': pid}
    x = http_post(f'http://{args.host}:8082/kill', d)
    return x.read()


def get_speed(args, logfile):
    flag = 'sender' if args.mode == 'c' else 'receiver'
    for _ in range((5 + 1) * 2):  # 5s + 1s
        if output(f'cat {logfile} | grep {flag} | tee'):
            break
        time.sleep(0.5)

    speed = output(f"cat {logfile} | grep sec | awk 'NR<51 {{print $7}}'")
    print(speed)
    speed = sorted([float(x) for x in speed.strip().split('\n')])[-30:]
    unit = output(f"cat {logfile} | grep {flag} | awk '{{print $8}}'")

    return sum(speed) / len(speed), unit.strip()


def test_speed(args, logfile):
    if os.path.exists(logfile):
        os.remove(logfile)

    args.port = random.choice(range(10000, 12000))
    cmd = f'iperf3 -s -f m -i 0.1 -p {args.port} > {logfile}'
    p = Process(target=lambda: shell(cmd))
    p.daemon = True
    p.start()
    time.sleep(0.2)
    pid = send(args)

    try:
        speed, unit = get_speed(args, logfile)
    except Exception as ex:
        speed, unit = 0, 'Mbits/sec'
        print(ex)

    kill(pid, args)
    p.terminate()

    return speed, unit


def main(args):
    if not args.host:
        raise Exception('The iperf3 host not found')

    ROUTE['add'] = route('add', args)

    cmd_msg = f'iperf3_{args.ifdev}_{args.mode}'
    logfile = f'/tmp/x_{cmd_msg}_log'

    for _ in range(args.retry):
        speed, unit = test_speed(args, logfile)
        if unit == 'Mbits/sec' and speed > args.limit:
            print(f'<{cmd_msg}, {speed:.0f}{unit}>,<PASS>,<0>')
            break
        else:
            print('retry')
    else:
        if speed == 0:
            print(f'<{cmd_msg}, timeout>,<FAIL>,<-3>')
        else:
            print(f'<{cmd_msg}, {speed:.0f}{unit}>,<FAIL>,<-1>')

    if ROUTE.get('add'):
        route('del', args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ifdev')
    parser.add_argument('-l', '--limit', type=int)
    parser.add_argument('-m', '--mode', choices=['c', 's'])
    parser.add_argument('-r', '--retry', default=3, type=int)
    parser.add_argument('-t', '--timeout', default=20, type=int)
    args = parser.parse_args()

    if not args.limit:
        if args.ifdev == 'wlan0':
            args.limit = 150
        else:
            args.limit = 900
    args.bind = cache_get(args.ifdev)
    args.host = cache_get('host')

    #  -R, --reverse             run in reverse mode (server sends, client receives)
    try:
        main(args)
    except Exception as ex:
        print(ex)
        print(f'<iperf3_{args.ifdev}_{args.mode}>,<FAIL>,<-2>')
