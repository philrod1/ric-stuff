#!/bin/bash
#./stopIperf.sh && ./stopSRS.sh

for s in `sudo screen -ls | sed -En "s/^\s+[^\.]+\.([^\t]+).*/\1/p"`
do
    echo "Stopping $s"
    sudo screen -X -S "$s" stuff "^C"
    sleep 1
done
sudo killall -9 srsenb
echo "Done."
