#!/bin/bash

Write_file=/tmp/sd_write.txt
Read_file=/tmp/sd_read.txt

lsblk | grep mmcblk1

if [ $? -eq 0 ]; then
    dd if=/dev/zero of=/dev/mmcblk1 bs=1M count=100 oflag=direct &> ${Write_file}
    sleep 0.5
    dd if=/dev/mmcblk1 of=/dev/null bs=1M count=100 iflag=sync &> ${Read_file}
    sleep 0.5
    
    Write=`cat ${Write_file} | grep MB/s | awk 'NR=1{print$10}'`
    Read=`cat ${Read_file} | grep MB/s | awk 'NR=1{print$10}'`

    if [[ `echo "$Write > 40" | bc` -eq 1 ]]&&[[ `echo "$Read > 50" | bc` -eq 1 ]];then	
    	echo "<sd_test,W:${Write}MB/s R:${Read}MB/s>,<PASS>,<0>"
	exit 0
    else
    	echo "<sd_rate,W:${Write}MB/s R:${Read}MB/s>,<FAIL>,<-1>"
	exit -1
    fi
else 
    	echo "<sd_no_dev,<FAIL>,<-1>"
fi
