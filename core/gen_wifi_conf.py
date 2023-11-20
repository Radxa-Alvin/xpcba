#!/usr/bin/python3
import os
import random

user = 'radxa'
board = 'rs107'
conf = f'/home/radxa/xpcba/conf/{board}/{board}.json'
tpl = f'/home/radxa/xpcba/conf/{board}/{board}-tpl.json'
psk_txt = f'/home/{user}/Desktop/wifi_psk.txt'


def gen_ssid_psk():
    digits = [str(i) for i in range(0, 10)]
    nonce = ''.join([random.choice(digits) for _ in range(6)])
    return f'{board}_' + nonce


def write_txt():
    if os.path.exists(psk_txt):
        return

    psk = gen_ssid_psk()
    with open(tpl, 'r') as f:
        data = f.read().replace('xpcba_test', psk)
    with open(conf, 'w') as f:
        f.write(data)
    with open(psk_txt, 'w') as f:
        f.write(psk)


if __name__ == '__main__':
    write_txt()
