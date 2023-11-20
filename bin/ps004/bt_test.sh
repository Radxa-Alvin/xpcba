#!/bin/bash

echo "I: Start testing Bluetooth"

rfkill unblock all
TIMEOUT=60
RESULT_FILE=/tmp/bt_result.txt

wait_file() {
    local file="$1"
    local wait_loops="$2"

    until test $((wait_loops--)) -eq 0 -o -s "$file"
    do
        sleep 0.25
        echo `ls $file`
    done
}

rm -rf ${RESULT_FILE}

for i in `seq ${TIMEOUT}`;do
    echo "I: Waiting for Bluetooth adapter... `expr ${TIMEOUT} - ${i}`"
    sleep 1

    hciconfig hci0 up
    ret=$?
    if [ "${ret}" = "0" ]; then
        echo "I: Bluetooth adapter is found"
        sleep 2
        BT_ADDR=`hcitool dev | grep hci0 | awk '{print $2}'`
        if [ "$BT_ADDR" ]; then
            echo "I: BT Address is ${BT_ADDR}"
            echo "I: Scanning remote BT device..."
            hcitool scan | awk 'NR>=2{print $1}' &>${RESULT_FILE}
            wait_file "${RESULT_FILE}" 40
            if [ -s "${RESULT_FILE}" ]; then
                echo "I: List remote BT device:"
                cat "${RESULT_FILE}"
                echo "<bt_test, ADDRESS ${BT_ADDR}>,<PASS>,<0>"
                exit 0
            else
                echo "I: There is no remote BT device"
                echo "<bt_test>,<FAIL>,<-3>"
                exit 3
            fi
        else
            echo "I: BT Address is NULL"
            echo "<bt_test>,<FAIL>,<-2>"
            exit 2
        fi
    fi
done

echo "<bt_test>,<FAIL>,<-1>"
exit 1
