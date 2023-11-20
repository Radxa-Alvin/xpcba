#!/usr/bin/python3
import argparse
import random
import time
from multiprocessing import Process

from utils import cache_get, http_post, output, shell

KEY = 'uUQFKhdAacN9c2av'
ROUTE = {}


def route(op, args):
    try:
        shell(f'route {op} -host {args.host} metric 100 dev {args.ifdev}')
        return True
    except Exception as ex:
        print(ex)


def send(args):
    d = {'key': KEY, 'cmd': 'iperf3', 'args': f'-s -p {args.port}'}
    x = http_post(f'http://{args.host}:8082/recv', d)
    return x.read()


def kill(pid, args):
    d = {'key': KEY, 'pid': pid}
    x = http_post(f'http://{args.host}:8082/kill', d)
    return x.read()


def get_speed(args, log_file):
    for _ in range(args.timeout // args.retry * 2):
        if output(f'cat {log_file}').strip():
            break
        time.sleep(0.5)

    speed = output(f"cat {log_file} | grep sec | awk 'NR<6 {{print $7}}'")
    speed = sorted([float(x) for x in speed.strip().split('\n')])[-3:]
    unit = output(f"cat {log_file} | grep receiver | awk '{{print $8}}'")

    return sum(speed) / len(speed), unit.strip()


def main(args):
    if not args.host:
        raise Exception('The iperf3 host not found')

    ROUTE['add'] = route('add', args)

    log_file = f'/tmp/x_iperf3_{args.ifdev}_c_log'
    shell(f'echo "" > {log_file}')

    pid = send(args)
    time.sleep(0.25)

    cmd = f'iperf3 -f m -B {args.bind} -c {args.host} -p {args.port} -t 5 > {log_file}'
    p = Process(target=lambda: shell(cmd))
    p.start()

    for _ in range(args.retry):
        try:
            speed, unit = get_speed(args, log_file)
            break
        except Exception as ex:
            print(ex)
            print('retry')
    else:
        speed, unit = 0, 'Mbits/sec'
        print(f'<iperf3_{args.ifdev}_c, timeout>,<FAIL>,<-3>')

    x = kill(pid, args)
    print(x.decode())

    if ROUTE.get('add'):
        route('del', args)

    if unit == 'Mbits/sec' and speed > args.limit:
        print(f'<iperf3_{args.ifdev}_c, {speed:.0f}Mb/s>,<PASS>,<0>')
    elif speed > 0:
        print(f'<iperf3_{args.ifdev}_c, {speed:.0f}{unit}>,<FAIL>,<-1>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ifdev')
    parser.add_argument('-l', '--limit', type=int)
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
    args.port = random.choice(list(range(9001, 50001, 2)))

    try:
        main(args)
    except Exception as ex:
        print(ex)
        print(f'<iperf3_{args.ifdev}_c>,<FAIL>,<-2>')
