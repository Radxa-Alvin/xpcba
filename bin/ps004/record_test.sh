#!/bin/bash

amixer -c mt8395evk cset name='PGA1 Volume' 3
aplay -D jack_speaker /home/root/xpcba/bin/ps004/start-record.wav
sleep 0.5

arecord -D jack_mic -r 48000 -f S32_LE /tmp/test.wav
sleep 0.5

aplay -D jack_speaker /tmp/test.wav

if [ $? -eq 0 ]; then
	   echo "<sound_recoud_test>,<PASS>,<0>"
	      exit 0
      else
	         echo "<sound_recoud_test>,<FAIL>,<-1>"
		    exit 1
fi


