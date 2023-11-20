#!/usr/bin/python3
import os
import subprocess
import time
from multiprocessing import Process

retry = 3
timeout = 10


def shell(cmd):
    return subprocess.check_call(cmd, shell=True)


def strip_fn(s, strip=True):
    return s.strip() if strip else s


def output(cmd, strip=True):
    res = subprocess.check_output(cmd, shell=True)
    return strip_fn(res.decode(), strip)


def check_rssi():
    try:
        res = output(f'cat /tmp/btmon | grep RSSI:')
    except subprocess.CalledProcessError:
        res = None
    return res


def get_rssi():
    rssi = [x.strip() for x in check_rssi().split('\n')]
    rssi = [int(x.split(' ')[1]) for x in rssi if x]
    return max(rssi)


def main():
    if not output('ps | grep btmon | grep -v grep | tee'):
        shell('/usr/bin/btmon > /tmp/btmon 2>&1 &')

    for i in range(1, retry + 1):
        if not os.path.exists('/tmp/btmon'):
            time.sleep(1)
            continue

        p = Process(target=lambda: shell('hcitool scan'))
        p.start()
        for _ in range(i * 5 + timeout):
            if check_rssi():
                rssi = get_rssi()
                if rssi > -82:
                    print(f'<bt_test, {rssi}dBm>,<PASS>,<0>')
                    return
            time.sleep(1)

    if check_rssi():
        print(f'<bt_test, {get_rssi()}dBm>,<FAIL>,<-1>')
    else:
        print('<bt_test, scan_fail>,<FAIL>,<-3>')


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        print(ex)
        print('<bt_test, app_error>,<FAIL>,<-2>')
