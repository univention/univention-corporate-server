#!/bin/bash
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# This script is really hard to maintain due to how it works with YAML files.
# Pined versions, etc.

# install OX 8 (kubernetes)
# see https://git.knut.univention.de/univention/prof-services/team-enterprise/zit-sh/-/issues/56
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.31.0/bin/linux/amd64/kubectl && chmod +x ./kubectl && mv ./kubectl /usr/local/bin/kubectl
curl -LO https://get.helm.sh/helm-v3.16.2-linux-amd64.tar.gz && tar -zxvf helm-v3.16.2-linux-amd64.tar.gz && mv linux-amd64/helm /usr/local/bin/helm
curl -Lo ./kind https://github.com/kubernetes-sigs/kind/releases/download/v0.24.0/kind-linux-amd64 && chmod +x ./kind && mv ./kind /usr/local/bin/kind
apt install --yes docker.io
kind create cluster
kubectl create namespace as8
apt update
apt install --yes jq
apt install --yes git
helm plugin install https://github.com/databus23/helm-diff --version 3.12.5
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace kube-system
sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq && sudo chmod +x /usr/bin/yq
apt install --yes python3-venv
# Use operations-guide mirrored by Nautilus team instead of upstream
# Parametrize this clone can be a future improvement
git clone https://git.knut.univention.de/univention/dev/projects/open-xchange/ox-operations-guide-mirror.git
cd ox-operations-guide-mirror
python3 -mvenv v
v/bin/pip install --upgrade pip wheel
v/bin/pip install -r requirements.txt
#JUST_UCS
sed -i "s/} | additional_script_vars/} or additional_script_vars/" render.py
sed -i "s/retvars |=/retvars = retvars or/" render.py
sed -i "s/vars | get_additional_script_vars/vars or get_additional_script_vars/" render.py
sed -i "s/list\[str\]/list/" render.py
#JUST_UCS
cat <<EOF >values.yaml
render_sh: true
generic_script_target: "sh"
generic_script_interpreter: "bash"
sys_prefix: "/usr"
assignment_dollar: ""
assignment_dollar_env: "export "
dollar_null: ""
echo: "echo"
noop: "true"
EOF

v/bin/python render.py --values values.yaml

# cd rendered/lab
cd rendered/values
# JUST_UCS
# bump version https://www.oxpedia.org/wiki/index.php?title=AppSuite:Versioning_and_Numbering#2025
# This remove the pining of the version for the appsuite, this brings unexpected updates.
sed -i -E 's|oci://registry.open-xchange.com/appsuite/charts/appsuite --version [0-9]\.[0-9]{1,2}\.[0-9]{1,3} |oci://registry.open-xchange.com/appsuite/charts/appsuite |g' install.sh
sed -i 's|AVERAGE_CONTEXT_SIZE: "200"|AVERAGE_CONTEXT_SIZE: "200"\n    /opt/open-xchange/etc/AdminUser.properties:\n       USERNAME_CHANGEABLE: "true"|g' values.yaml

# activate deputy permission provisioning
sed -i 's|open-xchange-drive-client-windows: disabled|open-xchange-drive-client-windows: disabled\n      open-xchange-deputy: enabled\n|g' values.yaml
# the content in this line can be done using another way to configure the core-mw files. check https://git.knut.univention.de/univention/dev/projects/open-xchange/connector/-/merge_requests/238/diffs#e7889d94c1408d69cc80d018fca34b82edc0d3c4_102_107
# It will require some testing.
sed -i 's|com.openexchange.hostname: "as8.lab.test"|com.openexchange.hostname: "as8.lab.test"\n    com.openexchange.dovecot.doveadm.endpoints: "http://dovecot-ce:8080/doveadm/v1"\n    com.openexchange.dovecot.doveadm.endpoints.totalConnections: "100"\n    com.openexchange.dovecot.doveadm.endpoints.readTimeout: "20000"\n    com.openexchange.dovecot.doveadm.endpoints.maxConnectionsPerRoute: "0"\n    com.openexchange.dovecot.doveadm.endpoints.connectTimeout: "5000"\n    com.openexchange.dovecot.doveadm.enabled: "true"\n    com.openexchange.deputy.enabled: "true"\n    com.openexchange.deputy.provider.imap.doveadm.personalNamespace: "/"\n    com.openexchange.deputy.provider.imap.doveadm.sharedNamespace: "shared/"\n    com.openexchange.deputy.provider.imap.doveadm.publicNamespace: "shared/"\n    com.openexchange.dovecot.doveadm.apiSecret: "secret"\n|g' values.yaml

# workaround for bitnami moving their images, this may break easily.
sed -i 's|  usePasswordFiles: false|  usePasswordFiles: false\nimage:\n  repository: bitnamilegacy/redis\nglobal:\n  security:\n    allowInsecureImages: true|g' values.bitnami-redis-core-mw-cache.yaml
sed -i 's|  usePasswordFiles: false|  usePasswordFiles: false\nimage:\n  repository: bitnamilegacy/redis\nglobal:\n  security:\n    allowInsecureImages: true|g' values.bitnami-redis-core-mw-session-store.yaml
sed -i 's|  usePasswordFiles: false|  usePasswordFiles: false\nimage:\n  repository: bitnamilegacy/redis\nglobal:\n  security:\n    allowInsecureImages: true|g' values.bitnami-redis-core-ui-mw.yaml
sed -i 's|  usePasswordFiles: false|  usePasswordFiles: false\nimage:\n  repository: bitnamilegacy/redis\nglobal:\n  security:\n    allowInsecureImages: true|g' values.bitnami-redis-switchboard.yaml

printf '  image:\n    repository: bitnamilegacy/redis-sentinel' >> values.bitnami-redis-core-mw-session-store.yaml
printf '  image:\n    repository: bitnamilegacy/redis-sentinel' >> values.bitnami-redis-core-ui-mw.yaml
printf '  image:\n    repository: bitnamilegacy/redis-sentinel' >> values.bitnami-redis-switchboard.yaml

sed -i 's/doveadm_api_key:.*$/doveadm_api_key: "secret"/g' values.dovecot-ce.secret.yaml
sed -i 's/    com.openexchange.filestore.s3client.s3.accessKey: /    com.openexchange.dovecot.doveadm.apiSecret: "secret"\n    com.openexchange.filestore.s3client.s3.accessKey: /g' values.secret.yaml

/root/ox-operations-guide-mirror/rendered/values/install.sh

cluster_ip="$(kubectl get nodes -o wide | awk '/kind-control-plane/ {print $6}')"
ucr set "hosts/static/$cluster_ip=as8.lab.test"

# certs
cp ox-operations-guide-mirror/rendered/values/cacert.pem /usr/share/ca-certificates/clustercert.crt && update-ca-certificates
univention-certificate new -name as8.lab.test -days 500
ucr set apache2/vhosts/as8.lab.test/443/aliases=as8.lab.test apache2/vhosts/as8.lab.test/443/enabled=1 apache2/vhosts/as8.lab.test/443/ssl/certificate=/etc/univention/ssl/as8.lab.test/cert.pem apache2/vhosts/as8.lab.test/443/ssl/key=/etc/univention/ssl/as8.lab.test/private.key apache2/vhosts/as8.lab.test/443/ssl/certificatechain=/etc/univention/ssl/ucsCA/CAcert.pem
systemctl restart apache2

cp cacert.pem /usr/local/share/ca-certificates/cluster.crt
update-ca-certificates

# for debugging only
wget https://github.com/derailed/k9s/releases/download/v0.32.7/k9s_linux_amd64.deb && apt install ./k9s_linux_amd64.deb && rm k9s_linux_amd64.deb

echo "DONE" >>/root/ox8_deployed

# configure apache2
a2enmod proxy proxy_http proxy_balancer expires deflate headers rewrite mime setenvif lbmethod_byrequests
cat > /etc/apache2/conf-available/proxy_http.conf <<- EOF
<IfModule mod_proxy_http.c>
   ProxyRequests Off
   ProxyStatus On
   # When enabled, this option will pass the Host: line from the incoming request to the proxied host.
   ProxyPreserveHost On
   # Please note that the servlet path to the soap API has changed:
   <Location /webservices>
       # restrict access to the soap provisioning API
       Order Allow,Deny
       Allow from all
   </Location>

   <Location /appsuite>
       # restrict access to the soap provisioning API
       Order Allow,Deny
       Allow from all
   </Location>

   # The old path is kept for compatibility reasons
   <Location /servlet/axis2/services>
       Order Deny,Allow
       Deny from all
       Allow from 127.0.0.1
   </Location>

   # Enable the balancer manager mentioned in
   # https://oxpedia.org/wiki/index.php?title=AppSuite:Running_a_cluster#Updating_a_Cluster
   <IfModule mod_status.c>
     <Location /balancer-manager>
       SetHandler balancer-manager
       Order Allow,Deny
       Allow from all
     </Location>
   </IfModule>

   <Proxy balancer://oxcluster>
       Order allow,deny
       # multiple server setups need to have the hostname inserted instead localhost
       BalancerMember https://as8.lab.test:30443 timeout=100 smax=0 ttl=60 retry=60 loadfactor=50 route=APP1
       # Enable and maybe add additional hosts running OX here
       # BalancerMember http://oxhost2:8009 timeout=100 smax=0 ttl=60 retry=60 loadfactor=50 route=APP2
      ProxySet stickysession=JSESSIONID|jsessionid scolonpathdelim=On
      SetEnv proxy-initial-not-pooled
      SetEnv proxy-sendchunked
   </Proxy>

  # Alternatively select one or more hosts of your cluster to be restricted to handle only eas/usm requests
  <Proxy balancer://eas_oxcluster>
     Order allow,deny
     Allow from all
     # multiple server setups need to have the hostname inserted instead localhost
     BalancerMember https://as8.lab.test_sync:30443 timeout=1900 smax=0 ttl=60 retry=60 loadfactor=50 route=APP1
     # Enable and maybe add additional hosts running OX here
     # BalancerMember http://oxhost2:8009 timeout=1900  smax=0 ttl=60 retry=60 loadfactor=50 route=APP2
     ProxySet stickysession=JSESSIONID|jsessionid scolonpathdelim=On
     SetEnv proxy-initial-not-pooled
     SetEnv proxy-sendchunked
  </Proxy>

  ProxyPass /ajax balancer://oxcluster/ajax
  ProxyPass /appsuite balancer://oxcluster/appsuite
  ProxyPass /drive balancer://oxcluster/drive
  ProxyPass /infostore balancer://oxcluster/infostore
  ProxyPass /realtime balancer://oxcluster/realtime
  ProxyPass /servlet balancer://oxcluster/servlet
  ProxyPass /webservices balancer://oxcluster/webservices

  ProxyPass /usm-json balancer://eas_oxcluster/usm-json
  ProxyPass /Microsoft-Server-ActiveSync balancer://eas_oxcluster/Microsoft-Server-ActiveSync

</IfModule>
EOF

cat > /etc/apache2/sites-available/000-default.conf <<- EOF
<VirtualHost *:80>
       IncludeOptional /etc/apache2/ucs-sites.conf.d/*.conf

       ServerAdmin webmaster@localhost

       DocumentRoot /var/www/html
       <Directory /var/www/html>
               Options -Indexes +FollowSymLinks +MultiViews
               AllowOverride None
               Order allow,deny
               allow from all
               RedirectMatch ^/$ /appsuite/
       </Directory>
       <Directory /var/www/html/appsuite>
               Options None +SymLinksIfOwnerMatch
               AllowOverride Indexes FileInfo
       </Directory>
</VirtualHost>
EOF

a2enmod proxy proxy_http proxy_balancer expires deflate headers rewrite mime setenvif lbmethod_byrequests
a2enconf proxy_http.conf
systemctl restart apache2.service

# test doveadm connection
# echo "secret"|base64  # -> c2VjcmV0
kubectl exec -n as8 "$(kubectl get pods -n as8 | grep mw-default | awk '{print $1}' | head -n1)" -it -- bash -c 'curl -v -H "Authorization: X-Dovecot-API c2VjcmV0" http://dovecot-ce:8080/doveadm/v1'

# This adds the cluster ip to the ox-core-mw pod. Otherwise it can't resolve as8.lab.test
kubectl patch deployment as8-core-mw-default \
  -n as8 \
  --type merge \
  -p "{
    \"spec\": {
      \"template\": {
        \"spec\": {
          \"hostAliases\": [
            {
              \"ip\": \"${cluster_ip}\",
              \"hostnames\": [\"as8.lab.test\"]
            }
          ]
        }
      }
    }
  }"
