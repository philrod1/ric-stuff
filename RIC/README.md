# RIC All-in-One Install Script
#### This README file is also the script that does all of the things.  You can run it with this command: -
#### curl -L https://raw.githubusercontent.com/philrod1/ric-stuff/master/RIC/README.md | bash
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


## Refresh apt

    message "Refresh apt"
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y openssh-server nfs-common nginx python3-pip


## Install Ansible

    message "Install Ansible"
    sudo python3 -m pip install ansible


## Clone repo and install

    message "Clone RIC repo"
    git clone https://gerrit.o-ran-sc.org/r/ric-plt/ric-dep
    message "Install kubernetes, helm and docker"
    cd ric-dep/bin
    sudo ./install_k8s_and_helm.sh
    message "Install chartmuseum and ric-common template
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


## Build Modified E2 Termination Pod

    message "Deploying E2 Termination"
    cd ~
    git clone https://github.com/philrod1/ric-plt-e2
    docker run -v /registry-storage:$HOME/registry -d -p 5001:5000 --restart=always --name ric registry:2
    cd ~/ric-plt-e2/RIC-E2-TERMINATION
    docker build -f Dockerfile -t localhost:5001/ric-plt-e2:5.5.0 .
    docker push localhost:5001/ric-plt-e2:5.5.0


## Deploy the Base RIC Components
#### This will create the 'ricinfra' and 'ricplt' namespaces and deploy all the
#### main RIC components from the O-RAN alliance 'e' release

    message "Deploying the RIC"
    cd ~/ric-dep/bin

    sed -i 's/ricip: "[^"]*"/ricip: "$myip"/g' ../RECIPE_EXAMPLE/PLATFORM/example_recipe_oran_e_release_modified_e2.yaml
    sed -i 's/auxip: "[^"]*"/ricip: "$myip"/g' ../RECIPE_EXAMPLE/PLATFORM/example_recipe_oran_e_release_modified_e2.yaml
    . ./deploy-ric-platform ../RECIPE_EXAMPLE/PLATFORM/example_recipe_oran_e_release_modified_e2.yaml
    message "DONE!"



## Addding some more useful aliases for xApp deployment

    message "Useful aliases for xApp deployment"
    echo 'export E2MGR_HTTP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-e2mgr-http -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export KONG_PROXY=`kubectl get svc -n ricplt -l app.kubernetes.io/name=kong -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export APPMGR_HTTP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-appmgr-http -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export ONBOARDER_HTTP=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-xapp-onboarder-http -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    echo 'export E2TERM=`kubectl get svc -n ricplt --field-selector metadata.name=service-ricplt-e2term-sctp-alpha -o jsonpath="{.items[0].spec.clusterIP}"`' >> ~/.bashrc
    source ~/.bashrc


## Install and configure nginx

    message "Installing nginx"
    sudo apt install -y openssh-server nfs-common nginx
    cd /etc/nginx/sites-enabled
    sudo unlink default
    cd
    mkdir xapp_config_files
    sudo chown $USER:www-data xapp_config_files
    cd /etc/nginx/conf.d
    sudo curl -o xapp_configs.local.conf https://raw.githubusercontent.com/philrod1/oaic-ric-installer/master/xapp_configs.local.conf
    sudo sed -i "s/\$USER/$USER/g" xapp_configs.local.conf
    sudo service nginx restart
    

## Onboard the KPIMON xApp

    message "Onbaording the KPIMON xApp"
    export KONG_PROXY=`kubectl get svc -n ricplt -l app.kubernetes.io/name=kong -o jsonpath="{.items[0].spec.clusterIP}"`
    cd ~/oaic/ric-scp-kpimon/
    cp ~/oaic/ric-scp-kpimon/scp-kpimon-config-file.json ~/xapp_config_files/
    tmp="$(jq '.containers[0].image.registry = "oaic.local:5008"' ~/xapp_config_files/scp-kpimon-config-file.json)" && echo -E "${tmp}" > ~/xapp_config_files/scp-kpimon-config-file.json
    docker build . -t oaic.local:5008/scp-kpimon:1.0.1
    curl -L -X POST "http://$KONG_PROXY:32080/onboard/api/v1/onboard/download" --header 'Content-Type: application/json' --data-raw "{\"config-file.json_url\":\"http://$myip:5010/scp-kpimon-config-file.json\"}"
    curl -L -X POST "http://$KONG_PROXY:32080/appmgr/ric/v1/xapps" --header 'Content-Type: application/json' --data-raw '{"xappName": "scp-kpimon"}'
    

#### That's it for now.  Just re-login and wait for the pods to start.

    message "Run 'su - $USER' or re-login to finish up."
    message "After that, you can type 'pods' to check the status of the containers."
    
#### To install the SRS UE, ENb and EPC components, use this guide: https://github.com/philrod1/srsRAN-installer
