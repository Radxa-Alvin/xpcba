#!/bin/bash
bt_mac=$(hcitool dev | grep hci0 | awk '{print $2}')
eth_mac=$(ip addr show eth0 | grep ether | awk '{print $2}')
wlan_mac=$(ip addr show wlan0 | grep ether | awk '{print $2}')

echo "$eth_mac  # eth" > /tmp/mac_info.txt
echo "$bt_mac  # bt" >> /tmp/mac_info.txt
echo "$wlan_mac  # wlan" >> /tmp/mac_info.txt

if [ $? != "0" ]; then
    echo "<get_info>,<FAIL>,<-1>"
    exit 1
fi

echo "<get_info>,<PASS>,<0>"
