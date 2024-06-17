set -e
set -x

# https://docs.software-univention.de/nubus-kubernetes-operation/latest/en/install.html
# https://git.knut.univention.de/univention/customers/dataport/upx/dev-env/
# https://hutten.knut.univention.de/blog/nubus-in-kubernetes-on-notebook/

prepare_system () {
  echo "Preparing system..."
  rm -f /etc/apt/sources.list.d/05univention-system-setup.list
  ucr set repository/online=true
  univention-install -y apt-transport-https ca-certificates curl gpg bash-completion jq

  # stop apache
  ucr set apache2/autostart='no'
  systemctl stop apache2.service
  systemctl disable apache2.service

  # somehow the default config for docker in UCS messes with docker/iptables
  # so that DNS in kind does not work
  # just remove our own config for now
  rm /lib/systemd/system/docker.service.d/20-univention-firewall.conf
  rm /etc/docker/daemon.json
  systemctl daemon-reload
  systemctl restart docker
}

install_tools () {
  echo "Installing tools..."
  install_kind
  install_kubectl
  install_helm
  install_k9s
}

setup_cluster () {
  echo "Creating Kubernetes cluster..."
  kind create cluster --name nubus1 --config=/root/nubus-kind-cluster-config.yaml

  echo "Setting up Ingress..."
  helm upgrade --install ingress-nginx ingress-nginx \
     --repo https://kubernetes.github.io/ingress-nginx \
     --namespace ingress-nginx \
     --create-namespace \
     --version "4.8.0" \
     --set controller.allowSnippetAnnotations=true \
     --set controller.config.hsts=false \
     --set controller.service.enableHttps=false \
     --set controller.hostPort.enabled=true \
     --set controller.service.ports.http=80

  echo "Installing Cert Manager..."
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.0/cert-manager.yaml
}

setup_nubus () {
  local VERSION="0.18.3" NAMESPACE="default"

  echo "Installing Nubus..."

  curl --output custom_values.yaml "https://raw.githubusercontent.com/univention/nubus-stack/v${VERSION}/helm/nubus/example.yaml"

  helm upgrade \
     --install nubus \
     --namespace="$NAMESPACE" \
     oci://artifacts.software-univention.de/nubus/charts/nubus \
     --values custom_values.yaml \
     --timeout 20m \
     --version "$VERSION"

  kubectl -n default get secret nubus-nubus-credentials -o json | jq -r '.data.admin_password' | base64 -d > /root/pass_default.admin
  kubectl -n default get secret nubus-nubus-credentials -o json | jq -r '.data.user_password' | base64 -d > /root/pass_default.user

  ucr set hosts/static/127.0.0.2="id.example.com portal.example.com"
}

run_setup_tests () {
  test_keycloak
  test_udm_rest
}

test_keycloak () {
  curl -ks https://id.example.com/realms/nubus/login-actions/authenticate | grep -q displayCookieBanner
  kubectl logs deployments/nubus-keycloak | tail | grep -q cookie_not_found
}

test_udm_rest () {
  local USERNAME=default.admin PASSWORD FQDN=portal.example.com SLEPT=1 TIMEOUT=300
  PASSWORD="$(</root/pass_default.admin)"

  while [ "$(curl -ks -X GET -H "Accept: application/json"     "https://${USERNAME}:${PASSWORD}@${FQDN}/univention/udm/users/user/?query\[username\]=default.*" | jq .results)" != "2" ]; do
    echo "Waiting for 2 'default.*' users ($SLEPT)...";
    sleep 1;
    if [ $(( SLEPT++ )) -gt $TIMEOUT ]; then
      echo "Failed to find 2 users with name 'default.*' in $TIMEOUT seconds."
      exit 1
    fi
  done
}

install_kind () {
  echo "Installing Kind..."
  curl -Lo /usr/local/bin/kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64
  chmod 755 /usr/local/bin/kind

  kind completion bash > /etc/bash_completion.d/kind
}

install_kubectl () {
  echo "Installing Kubectl..."
  curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor --batch -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
  univention-install -y kubectl

  kubectl completion bash > /etc/bash_completion.d/kubectl
}

install_helm () {
  echo "Installing Helm..."
  curl -fsSL https://baltocdn.com/helm/signing.asc | gpg --dearmor --batch -o /etc/apt/keyrings/helm.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" > /etc/apt/sources.list.d/helm-stable-debian.list
  univention-install -y helm

  helm completion bash > /etc/bash_completion.d/helm
}

install_k9s () {
  echo "Installing k9s"
  curl -sS https://webi.sh/k9s | sh
}
