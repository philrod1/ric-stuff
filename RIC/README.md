# RIC All-in-One Install Script
#### This README file is also the script that does all of the things.  You can run it with this command: -
#### curl -L https://raw.githubusercontent.com/philrod1/ric-stuff/main/RIC/README.md | bash
#### Alternatively, you can click on the 🖉 symbol in Github and copy the raw markdown.
#### You could also run each section by using the copy option

#### Based on these instructions: https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-ric-dep/en/latest/installation-guides.html

## Start with a fresh install of Ubuntu 20.04
### Tested using ubuntu-20.04.1-legacy-server-amd64.iso image
#### Hypervisor details: KVM, qemu-system-x86_64, Q35, BIOS
#### Guest system: 4 cores, 16G RAM, 150G storage, default networking (NAT)
#### Host system: Ubuntu 23.10, Kernel 6.5.0, Intel i7-1370P, 64G RAM


## Setup Useful Aliases

    message () { echo -e "\e[1;93m$1\e[0m"; }
    message "Modifying .bashrc"
    export myip=`hostname  -I | cut -f1 -d' '`
    echo 'alias pods="kubectl get pods -A"' >> ~/.bashrc
    echo 'alias srv="kubectl get services -A"' >> ~/.bashrc
    echo 'alias flushpods="kubectl delete pods -A --field-selector=\"status.phase==Failed\""' >> ~/.bashrc
    echo "export myip=`hostname  -I | cut -f1 -d' '`" >> ~/.bashrc
    echo 'export KUBECONFIG="${HOME}/.kube/config"' >> ~/.bashrc
    echo 'export HELM_HOME="${HOME}/.helm"' >> ~/.bashrc
    echo 'export CHART_REPO_URL=http://0.0.0.0:8090' >> ~/.bashrc


## Refresh apt

    message "Refresh apt"
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y openssh-server nfs-common nginx python3-pip npm


## Install Ansible

    message "Install Ansible"
    sudo python3 -m pip install ansible


## Clone repo and install

    message "Clone RIC repo"
    git clone https://gerrit.o-ran-sc.org/r/ric-plt/ric-dep
    message "Install kubernetes, helm and docker"
    cd ric-dep/bin
    sudo ./install_k8s_and_helm.sh
    message "Install chartmuseum and ric-common template"
    sudo ./install_common_templates_to_helm.sh


## Configure 'docker' and 'kubectl' For Non-root User 

    message "Enabling docker and kubectl as standard user"
    sudo usermod -aG docker $USER && newgrp docker
    message () { echo -e "\e[1;93m$1\e[0m"; }
    export myip=`hostname  -I | cut -f1 -d' '`
    mkdir -p ~/.kube
    sudo cp -i /etc/kubernetes/admin.conf ~/.kube/config
    sudo chown -R $USER:$USER ~/.kube
    chmod 600 ~/.kube/config


## Configure Helm

    message "Setup Helm"
    cd ~
    mkdir -p ~/.helm
    helm repo add stable https://charts.helm.sh/stable
    helm repo update
    helm install nfs-release-1 stable/nfs-server-provisioner --namespace ricinfra --create-namespace
    kubectl patch storageclass nfs -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'


## Configure ChartMuseum

    message "Configure ChartMuseum"
    mkdir charts
    docker kill chartmuseum
    docker run --rm -u 0 -it -d --name chartmuseum -p 8090:8080 -e DEBUG=1 -e STORAGE=local -e STORAGE_LOCAL_ROOTDIR=/charts -v $(pwd)/charts:/charts chartmuseum/chartmuseum:latest


## Build Modified E2 Termination (not currently used)

    #message "Deploying E2 Termination"
    #cd ~
    #git clone https://github.com/philrod1/ric-plt-e2
    docker run -v /registry-storage:$HOME/registry -d -p 5001:5000 --restart=always --name ric registry:2
    #cd ~/ric-plt-e2/RIC-E2-TERMINATION
    #docker build -f Dockerfile -t localhost:5001/ric-plt-e2:5.5.0 .
    #docker push localhost:5001/ric-plt-e2:5.5.0
    #cd ~/ric-dep/RECIPE_EXAMPLE
    #wget https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/ric_recipe_oran_k_release_modified_e2.yaml
    #ln -sf ric_recipe_oran_k_release_modified_e2.yaml example_recipe_latest_stable.yaml



## Deploy the Base RIC Components
#### This will create the 'ricinfra' and 'ricplt' namespaces and deploy all the
#### main RIC components from the O-RAN alliance 'e' release

    message "Deploying the RIC"
    cd ~/ric-dep/bin
    sed -i "s/ricip: \"[^\"]*\"/ricip: \"$myip\"/g" ../RECIPE_EXAMPLE/example_recipe_latest_stable.yaml
    sed -i "s/auxip: \"[^\"]*\"/auxip: \"$myip\"/g" ../RECIPE_EXAMPLE/example_recipe_latest_stable.yaml
    sudo ./install -f ../RECIPE_EXAMPLE/example_recipe_latest_stable.yaml
    message "DONE!"



## Addding some more useful aliases for xApp deployment

    message "Useful aliases for xApp deployment"
    echo 'export E2MGR_HTTP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-e2mgr-http -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export KONG_PROXY=`kubectl get svc -n ricplt --field-selector metadata.name=r4-infrastructure-kong-proxy -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export APPMGR_HTTP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-appmgr-http -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo '# export ONBOARDER_HTTP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-xapp-onboarder-http -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export E2TERM=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-e2term-sctp-alpha -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    source ~/.bashrc


## Install and configure nginx

    message "Installing nginx"
    sudo apt install -y openssh-server nfs-common nginx
    cd /etc/nginx/sites-enabled
    sudo unlink default
    cd ~
    mkdir xapp_config_files
    sudo chown $USER:www-data xapp_config_files
    cd /etc/nginx/conf.d
    sudo curl -o xapp_configs.local.conf https://raw.githubusercontent.com/philrod1/ric-stuff/refs/heads/main/files/xapp_configs.local.conf
    sudo sed -i "s/\$USER/$USER/g" xapp_configs.local.conf
      

## Install dms_cli for xApp management

    message "Installing dms_cli"
    cd ~
    pip install --upgrade Flask flask-restx
    docker kill chartmuseum
    docker run --rm -u 0 -it -d --name chartmuseum -p 8090:8080 -e DEBUG=1 -e STORAGE=local -e STORAGE_LOCAL_ROOTDIR=/charts -v $(pwd)/charts:/charts chartmuseum/chartmuseum:latest
    export CHART_REPO_URL=http://0.0.0.0:8090
    git clone "https://gerrit.o-ran-sc.org/r/ric-plt/appmgr"
    cd appmgr/xapp_orchestrater/dev/xapp_onboarder
    pip3 uninstall xapp_onboarder
    sudo pip3 install ./


## Install *RICMON*
    message "Installing RICMON"
    cd ~
    git clone --branch srsRAN --single-branch https://github.com/philrod1/ricmon.git
    cd ricmon
    sed -i "s/\(ws:\/\/\)[0-9.]\+\(:8765\)/\1$myip\2/" public/javascripts/sketch.js
    npm install
    ansible localhost -m shell -a "screen -dmS ricmon npm start"


## Install *xApp Store*
    message "Installing xApp Store"
    cd ~
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
    cd ~
    source ~/.bashrc
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
    nvm install 16
    nvm use 16
    wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    sudo systemctl start mongod
    sudo systemctl enable mongod
    git clone https://github.com/philrod1/appstore.git
    cd appstore
    npm install
    ansible localhost -m shell -a "screen -dmS xappstore npm start"


#### That's it for now.  Just re-login and wait for the pods to start.

    message "Run 'su - $USER' or re-login to finish up."
    message "After that, you can type 'pods' to check the status of the containers."
    message "If you want to start RICMON, 'cd ~/ricmon' then 'npm start'"
    message "If you want to start the xApp Store, 'cd ~/appstore' then 'npm start'"
    message "Open a browser and go to http://<ip-address>:3003/pods"
    message "For the xApp Store, go to http://<ip-address>:3000"
    message "You will need to manually restart RICMON and the xApp Store if you reboot your machine"
    

#### Go to `https://github.com/philrod1/ric-stuff/tree/main/srsRAN` for the next part
