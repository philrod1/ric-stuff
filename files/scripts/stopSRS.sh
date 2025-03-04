#!/bin/bash

declare -a arr=("ue_0" "ue_1" "ue_2" "enb" "epc")

for i in "${arr[@]}"
do
    echo "Stopping $i"
    screen -X -S "$i" stuff "^C"
    sleep 5
done
echo "Done."
