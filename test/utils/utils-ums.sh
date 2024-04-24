set -e
set -x

# https://docs.software-univention.de/nubus-operation/latest/en/install.html
# https://git.knut.univention.de/univention/customers/dataport/upx/dev-env/

install_tools () {
	rm -f /etc/apt/sources.list.d/05univention-system-setup.list
	ucr set repository/online=true
	univention-install -y sudo build-essential procps curl file git

	# stop apache
	ucr set apache2/autostart='no'
	service apache2 stop

	# somehow the default config for docker in UCS messes with docker/iptables
	# so that DNS in kind does not work
	# just remove our own config for now
	rm /lib/systemd/system/docker.service.d/20-univention-firewall.conf
	rm /etc/docker/daemon.json
	systemctl daemon-reload
	systemctl restart docker

	# install homebrew and kind
	echo "%sudo ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers
	adduser --disabled-password --gecos "" nubus
	adduser nubus sudo
	# shellcheck disable=SC2016
	su nubus -c 'NONINTERACTIVE=1 /bin/bash -x -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
	su - nubus << EOF
NONINTERACTIVE=1
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
brew install kubectl
brew install helm
brew install kind
brew install tilt
brew install derailed/k9s/k9s
EOF
	# shellcheck disable=SC2016
	(echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> /home/nubus/.bashrc
	# shellcheck disable=SC2016
	(echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> /root/.bashrc
}

setup_cluster () {
	git clone https://git.knut.univention.de/univention/customers/dataport/upx/dev-env/
	cd dev-env/
	./bootstrap-kind-cluster.sh
}

setup_ums_stack () {
	local ums_umc_gatway
	git clone https://git.knut.univention.de/univention/customers/dataport/upx/ums-stack
	cd ums-stack/
	cp helm/ums/demo_values.yaml helm/ums/custom_values.yaml
	helm dependency build helm/ums
	# TODO remove || true, currently setup fails for some pods
	helm upgrade --install ums --namespace=default helm/ums --values helm/ums/custom_values.yaml --timeout 1800s || true

	# TODO why
	ums_stack_gatway="$(kubectl get pods| grep ^ums-stack-gateway-|awk '{print $1}')"
	kubectl port-forward --address 0.0.0.0 "pods/$ums_stack_gatway" 80:8080 &
}

# kubectl --namespace default events
# helm uninstall  ums
# kind delete cluster --name souvap-dev-env

# get default user
# kubectl get cm ums-stack-data-swp-data -o jsonpath='{.data.dev-test-users\.yaml}' -n default
