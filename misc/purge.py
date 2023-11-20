#!/usr/bin/python3
import io
import time
from tempfile import mkdtemp

from core.client import Client
from core.utils import adb, adb_forward, enter_test, get_path, shell

host = '127.0.0.1'
port = 6688
debug = False
board = 'cs317'
dtmp = mkdtemp()
xpcba = '/rockchip_test/xpcba'


def gen_del_sh():
    del_xpcba = f'''#!/bin/bash
mv {xpcba}/bin/mock_emmc_test.sh /tmp
rm -rf {xpcba}/*
rm -rf {xpcba}-master.zip
mkdir -p {xpcba}/bin
mv /tmp/mock_emmc_test.sh {xpcba}/bin
sync
echo "<del_xpcba>,<PASS>,<0>"'''

    with io.open(f'{dtmp}/del_xpcba.sh', 'w', newline='\n') as f:
        f.write(del_xpcba)


def push_xpcba():
    time.sleep(1)
    for x in ['utils.py', 'server.py', 'protocol.py']:
        adb(f'push {get_path("core/" + x)} {xpcba}/')
    adb('shell sync')
    adb('shell reboot')


def start_test():
    adb_forward(port)
    client = Client(host, port, debug)
    enter_test(client, board, timeout=30)

    item0 = {
        'cmd': 'del_xpcba',
        'type': 'external',
        'file': f'{dtmp}/del_xpcba.sh'
    }

    print('====== Delete PCBA ======')
    print(client.test(item0))


if __name__ == '__main__':
    gen_del_sh()
    start_test()
    push_xpcba()
