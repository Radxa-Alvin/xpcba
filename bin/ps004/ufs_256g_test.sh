#!/bin/bash

size=`cat /sys/bus/scsi/devices/0\:0\:0\:2/block/sdc/size`
let size=${size}/2/1024/1024

echo "I: get ufs size: ${size}GB"

if [ $size -gt 240 ]&&[ $size -lt 260 ]; then
         echo "<ufs_test,${size}GB>,<PASS>,<0>"
else echo "<ufs_test, ${size}GB>,<FAIL>,<-1>"
fi
