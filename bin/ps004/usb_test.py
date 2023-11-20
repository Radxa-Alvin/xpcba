#!/usr/bin/python3
import os
import re
import sys
import subprocess

THRESHOLD = {
    2.0: (10, 20),
    3.0: (30, 60),
    3.2: (250, 300)
}

FDISK_CMD = '''
/sbin/fdisk -w always -W always /dev/{} > /dev/null << EOF
g
n
1
2048

w
EOF
'''

DD_READ = "dd if=/mnt/{}/1 of=/dev/null bs=32M count={} iflag=direct 2>&1 | awk '{{print $10}}'"
DD_WRITE = "dd if=/dev/zero of=/mnt/{}/1 bs=32M count={} oflag=direct 2>&1 | awk '{{print $10}}'"


def shell(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()


def get_speed(sdx):
    info = shell(f'udevadm info -a /dev/{sdx} | grep speed')
    speed = min([int(x) for x in re.findall('"(\d+)"', info)])
    return {12: 1.1, 480: 2.0, 5000: 3.0, 10000: 3.2}.get(speed)


def get_disks():
    return shell("lsblk -o NAME,TRAN | grep usb | awk '{print $1}'").split('\n')


def format_and_mount(sdx):
    umount_disk(sdx)
    shell(FDISK_CMD.format(sdx))
    shell(f'mkfs.ext4 /dev/{sdx}1')
    shell(f'mount -t ext4 /dev/{sdx}1 /mnt/{sdx}')


def umount_disk(sdx):
    all_point = shell(f"mount | grep {sdx} | awk '{{print $3}}'")
    for point in all_point.split('\n'):
        if not point:
            continue
        try:
            print(f'umount {point}')
            shell(f'umount {point}')
        except Exception as ex:
            print(ex)


def mount_disk(sdx):
    if not os.path.exists(f'/mnt/{sdx}'):
        os.mkdir(f'/mnt/{sdx}')

    try:
        shell(f'mount -t ext4 /dev/{sdx}1 /mnt/{sdx}')
    except Exception as ex:
        print(ex)
        format_and_mount(sdx)


def test_speed(disks):
    _ws, _rs = '', ''

    for sdx, speed in disks:
        mount_disk(sdx)
        count = 4 if speed > 2.0 else 2
        shell('echo 3 > /proc/sys/vm/drop_caches')
        ws = float(shell(DD_WRITE.format(sdx, count)))
        shell('echo 3 > /proc/sys/vm/drop_caches')
        rs = float(shell(DD_READ.format(sdx, count)))
        umount_disk(sdx)
        print(sdx, speed, ws, rs)
        if not all(a > b for a, b in zip((ws, rs), THRESHOLD[speed])):
            print(f'<usb_test, USB{speed} R:{rs:.1f}MB/s W:{ws:.1f}MB/s>,<FAIL>,<{-1}>')
            return
        _ws += f'{ws:.1f} '
        _rs += f'{rs:.1f} '
    _ws, _rs = _ws.strip(), _rs.strip()

    print(f'<usb_test R:{_rs} W:{_ws}>,<PASS>,<0>')


def main(args):
    disks = [(sdx, get_speed(sdx)) for sdx in get_disks()]
    print(disks)

    speeds = sorted([speed for _, speed in disks])
    expect = sorted([float(x) for x in args.split(',')])

    print(speeds)
    print(expect)

    if speeds != expect:
        for idx in range(len(speeds)):
            if speeds[idx] != expect[idx]:
                lack = expect[idx]
                break
        else:
            if idx < len(expect) - 1:
                lack = expect[idx + 1]
            else:
                lack = ''
        print(f'<usb_test, lack {lack} USB>,<FAIL>,<-4>')
        return

    test_speed(disks)


if __name__ == '__main__':
    try:
        print(shell('lsblk -t'))
        print(shell('lsusb -t'))
        main(sys.argv[-1])
    except Exception as ex:
        print(ex)
        print(f'<usb_test, app_error>,<FAIL>,<-2>')
