#!/bin/bash
#./stopIperf.sh && ./stopSRS.sh

for s in `screen -ls | sed -En "s/^\s+[^\.]+\.([^\t]+).*/\1/p"`
do
    echo "Stopping $s"
    screen -X -S "$s" stuff "^C"
    sleep 1
done
echo "Done."
