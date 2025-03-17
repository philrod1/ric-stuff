# srsRAN Project
#### This README file is also the script that does all of the things.  You can run it with this command: -
#### curl -L https://raw.githubusercontent.com/philrod1/ric-stuff/main/srsRAN/README.md | bash
#### Alternatively, you can click on the 🖉 symbol in Github and copy the raw markdown.
#### You could also run each section by using the copy option

## Run this script after a clean install of the RIC
#### My RIC installer can be found here: https://github.com/philrod1/ric-stuff/tree/main/RIC
### Tested using ubuntu-20.04.1-legacy-server-amd64.iso image
#### Hypervisor details: KVM, qemu-system-x86_64, Q35, BIOS
#### Guest system: 4 cores, 16G RAM, 150G storage, default networking (NAT)
#### Host system: Ubuntu 23.10, Kernel 6.5.0, Intel i7-1370P, 64G RAM


## Setup Useful Aliases

    export myip=`hostname  -I | cut -f1 -d' '`
    export E2NODE_PORT=5006
    export E2TERM_IP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-e2term-sctp-alpha -o jsonpath='{.items[0].spec.clusterIP}'`


## Do apt Stuff

    message () { echo -e "\e[1;93m$1\e[0m"; }
    message "Refresh apt"
    sudo add-apt-repository ppa:ettusresearch/uhd
    sudo apt update
    sudo apt upgrade -y     
    sudo apt install -y libuhd-dev libuhd4.1.0 uhd-host libzmq3-dev
    sudo apt install -y python3-pip npm iperf3 pax openssh-server build-essential cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev libtool autoconf ccache
    mkdir $HOME/srs_logs
    pip3 install websockets
    sudo pip3 install --upgrade Jinja2


## Install asn1c Compiler

    cd ~
    sudo apt install libtool autoconf
    git clone https://gitlab.eurecom.fr/oai/asn1c.git
    cd asn1c
    git checkout velichkov_s1ap_plus_option_group
    autoreconf -iv
    ./configure
    make -j`nproc`
    sudo make install
    sudo ldconfig


## Build and install srsRAN E2 agent

    message "Cloning the srsRAN-e2 project"
    cd ~
    git clone https://github.com/philrod1/srsRAN-e2.git
    cd ~/srsRAN-e2
    mkdir build
    export SRS=`realpath .`
    cd build
    message "... cmake"
    cmake ../ -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DRIC_GENERATED_E2AP_BINDING_DIR=${SRS}/e2_bindings/E2AP-v01.01 \
    -DRIC_GENERATED_E2SM_KPM_BINDING_DIR=${SRS}/e2_bindings/E2SM-KPM \
    -DRIC_GENERATED_E2SM_GNB_NRT_BINDING_DIR=${SRS}/e2_bindings/E2SM-GNB-NRT
    message "... make"
    make -j`nproc`
    message "... install"
    sudo make install
    message "... load"
    sudo ldconfig
    message "Install configs"
    sudo mkdir -p /root/.config/srsran
    cd /usr/local/share/srsran
    sudo pax -rw -pe -s/.example// . /root/.config/srsran/


## Getting Scripts

    cd ~
    su - $USER
    source .bashrc
    echo "E2TERM: $E2TERM"
    echo "myip  : $myip"
    mkdir scripts
    mkdir iperf
    cd scripts
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/killAllThings.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/iperf.yml
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/srs.yml
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/startClient.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/startServer.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/startENB.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/startUE.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/stopIperf.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/stopSRS.sh
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/radio.py
    wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/scripts/clean_evicted_pods.sh
    sed -i "s|\$HOME|$HOME|g" srs.yml
    sed -i "s|\$HOME|$HOME|g" iperf.yml
    sed -i "s|\$HOME|$HOME|g" startServer.sh
    sed -i "s|\"\$E2TERM\"|$E2TERM|g" startENB.sh
    sed -i "s|\"\$myip\"|$myip|g" startENB.sh
    chmod +x *.sh   


## Getting configs

    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/enb.conf -O /root/.config/srsran/enb.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/epc.conf -O /root/.config/srsran/epc.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/mbms.conf -O /root/.config/srsran/mbms.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/rb.conf -O /root/.config/srsran/rb.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/rr.conf -O /root/.config/srsran/rr.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/sib.conf -O /root/.config/srsran/sib.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/ue.conf -O /root/.config/srsran/ue.conf
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/slice_db.csv -O /root/.config/srsran/slice_db.csv
    sudo wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/config/user_db.csv -O /root/.config/srsran/user_db.csv    


## What now?
### If not already running: -
#### Start the RICMON web app (in a screen) from inside ~/ricmon with `npm start`.  Open `http://localhost:3003` or `http://<ip-address>:3003`
#### Start the xApp Store from inside `~/appstore` with `npm start`.  Open `http://localhost:3000` or `http://<ip-address>:3000`

### Run the radio scripts.
#### From inside `~/scripts`
#### Start srsRAN components with ``sudo ansible-playbook srs.yml``
#### Start the radio (in a screen or sepatate terminal) with ``python3 radio.py``
#### Open the SIM in RICMON.  Nothing should be happening yet, but the sim talks to GNURadio.
#### Check in the srs logs in RICMON.  The UEs should be assigned IP addresses.  If not, try again.
#### Start the iperf servers and clients with ``sudo ansible-playbook iperf.yml``
#### Check the SIM in RICMON.  You should see traffic indicated in the guages.

## Go again?
### This stuff seems flaky and prone to failure.  The start-up routine needs to be done correctly to have any hope.
### Restarting srsRAN is often required.  So often, in fact, that I made a script to help.
#### First, stop the radio script with Ctrl-C
#### Then, run the kill script from the scripts directory ``./killAllThings.sh``