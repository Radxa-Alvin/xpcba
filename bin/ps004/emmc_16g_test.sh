#!/bin/bash

#SDA_PATH=/tmp/sda1
USBHOST_SD_WS_FILE=/tmp/mmcblk0_ws.txt
USBHOST_SD_RS_FILE=/tmp/mmcblk0_rs.txt
#mkdir $SDA_PATH
DEV1_PATH=/dev/mmcblk0
#echo "mounting sda1"
#mount $DEV_PATH $SDA_PATH
#if [ $? == 0 ]; then
#echo "mounted sda1"
#fi
EMMC_SIZE1=8 #GB
EMMC_SIZE2=16 #GB
EMMC_SIZE3=32 #GB
if [ ! -e "/dev/mmcblk0" ]; then

   echo "<emmc_test>,<FAIL>,<-1>"
   exit 1
fi

dd if=/dev/zero of=$DEV1_PATH bs=4M count=10 oflag=direct &>${USBHOST_SD_WS_FILE}
if [ $? == 0 ]; then
   echo "write is ok"
else
   echo "write is err"
fi

ret_sd_ws=`cat ${USBHOST_SD_WS_FILE} | grep "copied" | awk '{print $10}'`
if [ $? == 0 ]; then
    echo "ret_sd_ws is ok"
else
    echo "ret_sd_ws  is err"
fi

ret_sd_ws_gb=`cat ${USBHOST_SD_WS_FILE} | grep "copied" | awk '{print $11}'`
if [ $? == 0 ]; then
    echo "ret_sd_ws_gb is ok"
else
    echo "ret_sd_ws_gb  is err"
fi

dd if=$DEV1_PATH  of=/dev/null bs=4M count=10 &>${USBHOST_SD_RS_FILE}
if [ $? == 0 ]; then
   echo "read is ok"
else
   echo "resd is err"
fi

ret_sd_rs=`cat ${USBHOST_SD_RS_FILE} | grep "copied" | awk '{print $10}'`
if [ $? == 0 ]; then
    echo "ret_sd_rs is ok"
else
    echo "ret_sd_rs  is err"
fi

ret_sd_rs_gb=`cat ${USBHOST_SD_RS_FILE} | grep "copied" | awk '{print $11}'`
if [ $? == 0 ]; then
   echo "ret_sd_rs_gb is ok"
else
    echo "ret_sd_rs_gb  is err"
fi

sleep 1


get_emmc_size() {
    local size=$1
    local emmc_size=1
    local emmc_size_double=2
    local emmc_total=0
    
    size=`cat /sys/bus/mmc/devices/mmc0:0001/block/mmcblk0/size`
    let size=${size}/2/1024/1024
    
    if [ ${size} -gt 0 ] && [ ${size} -le 1 ]; then
        return 1
    fi
    
    for i in {1..10}
    do
        let emmc_size_double=${emmc_size}*2
        if [ "$size" -gt "${emmc_size}" ] && [ "$size" -le "$emmc_size_double" ]; then
            let emmc_size=${emmc_size}*2
            emmc_total=${emmc_size}
            return ${emmc_total}
        fi
        let emmc_size=${emmc_size}*2
    done
    
    return -1
}

get_emmc_size
emmc_size_real=$?
echo "I: get eMMC size: ${emmc_size_real}GB"

#rm $SDA_PATH/zero.img
#umount ${SDA_PATH}
echo "size:${emmc_size_real} & W:${ret_sd_ws} R:${ret_sd_rs}"

ret_sd_ws_1=`awk  -v  num1="$ret_sd_ws" -v num2=30 'BEGIN{print(num1>num2)?"0":"1"}'`
ret_sd_rs_1=`awk  -v  num3="$ret_sd_rs" -v num4=80 'BEGIN{print(num3>num4)?"0":"1"}'`
if [ "$ret_sd_ws_gb" == "GB/s" ]; then
   ret_sda_ws_1=0
fi

if [ "$ret_sd_rs_gb" == "GB/s" ]; then
   ret_sda_rs_1=0
fi

#if [ "$emmc_size_real" = "${EMMC_SIZE1}" ]; then
if [ "$emmc_size_real" = "${EMMC_SIZE2}" ]; then
# if [ "$emmc_size_real" = "${EMMC_SIZE3}" ]; then
   if [ "$ret_sd_ws_1" -eq 0 ]; then
      if [ "$ret_sd_rs_1" -eq 0 ]; then
         echo "<emmc_test,${emmc_size_real}GB,ws:$ret_sd_ws,rs:$ret_sd_rs>,<PASS>,<0>"
         echo "emmc pass"
         exit 0
      else 
       echo "<emmc_test,${emmc_size_real}GB,ws:$ret_sd_ws,rs:$ret_sd_rs>,<FAIL>,<-2>"
       exit 2 
      fi
   else 
       echo "<emmc_test,size:${emmc_size_real}GB,ws:$ret_sd_ws,rs:$ret_sd_rs>,<FAIL>,<-3>"
       exit 3
   fi
else echo "<emmc_test, ${emmc_size_real}GB>,<FAIL>,<-1>"
fi












