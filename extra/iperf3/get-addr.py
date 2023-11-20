#!/usr/bin/python3
import argparse
import time

from utils import cache_get, cache_set, output, shell


def nmcli(args, env={}):
    if not env.get('rescan'):
        print('wifi rescan')
        env['rescan'] = True
        shell('nmcli dev wifi rescan')
    shell(f'nmcli dev wifi connect "{args.ssid}" password "{args.psk}"')


def wpa_cli(args):
    wpa_conf = f'''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=HK

network={{
    ssid="{args.ssid}"
    scan_ssid=1
    psk="{args.psk}"
    key_mgmt=WPA-PSK
}}
'''
    shell(f'echo \'{wpa_conf}\' > /tmp/mfg_wpa.conf')
    shell('wpa_supplicant -D nl80211 -i wlan0 -c /tmp/mfg_wpa.conf &')
    if output('command -v udhcpc | tee'):
        shell('udhcpc -i wlan0')
    else:
        shell('dhclient wlan0')


def get_ip(dev):
    x = output(f"ip addr | egrep -m 1 'inet .+{dev}' | awk '{{print $2}}'").strip()
    if not x and dev == 'wlan0':  # fix pis
        return get_ip('p2p0')
    return x and x[:-3]


def get_bssid(args):
    bssid = cache_get('bssid')
    if not bssid:
        print('get bssid')
        gateway = output("ip route | egrep -m 1 via.*eth0 | awk '{print $3}'").strip()
        bssid = output(f"arp -i eth0 | egrep '{gateway}\\b' | awk '{{print $3}}'").strip().upper()
        cache_set('bssid', bssid)
    args.ssid = bssid


def conn_wifi(args):
    func = {'wpa_cli': wpa_cli}.get(args.mode, nmcli)
    for _ in range(args.retry):
        ip = get_ip('wlan0')
        if '192.168' in ip or '172.16' in ip:
            return
        try:
            return func(args)
        except Exception as ex:
            print(ex)
            time.sleep(3)
    else:
        print('del bssid')
        cache_set('bssid', _del=True)


def main(args):
    ifdev = args.ifdev.split(' ')

    if args.bssid:
        get_bssid(args)

    if 'wlan0' in ifdev:
        conn_wifi(args)

    for _ in range(args.timeout):
        try:
            n = 0
            addr = []
            for dev in ifdev:
                ip = get_ip(dev)
                if '192.168' in ip or '172.16' in ip:
                    n += 1
                    addr.append(ip)
                    cache_set(dev, ip)
                if n == len(ifdev):
                    print(f'<get_addr, {",".join(addr)}>,<PASS>,<0>')
                    return
        except Exception as ex:
            print(ex)
        time.sleep(1)
    else:
        print('<get_addr, timeout>,<FAIL>,<-2>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ifdev')
    parser.add_argument('-m', '--mode', default='wpa_cli')
    parser.add_argument('-b', '--bssid', action='store_true')
    parser.add_argument('-s', '--ssid', default='vms-mi-wifi')
    parser.add_argument('-p', '--psk', default='Hertf0rdsh1re')
    parser.add_argument('-r', '--retry', default=3, type=int)
    parser.add_argument('-t', '--timeout', default=30, type=int)
    args = parser.parse_args()

    try:
        main(args)
    except Exception as ex:
        print(ex)
        print('<get_addr>,<FAIL>,<-1>')
