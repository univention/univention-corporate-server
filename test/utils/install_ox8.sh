#!/bin/bash

set -e

if [ $# -ne 1 ]; then
  echo "First parameter must be LDAP server IP"
fi

LDAP_SERVER="$1"
LDAP_BASE="$(ucr get ldap/base)"

# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# This script is really hard to maintain due to how it works with YAML files.
# Pined versions, etc.

# install OX 8 (kubernetes)
# see https://git.knut.univention.de/univention/prof-services/team-enterprise/zit-sh/-/issues/56
curl -LO https://dl.k8s.io/release/v1.36.0/bin/linux/amd64/kubectl && chmod +x ./kubectl && mv ./kubectl /usr/local/bin/kubectl
curl -LO https://get.helm.sh/helm-v3.16.2-linux-amd64.tar.gz && tar -zxvf helm-v3.16.2-linux-amd64.tar.gz && mv linux-amd64/helm /usr/local/bin/helm
curl -Lo ./kind https://github.com/kubernetes-sigs/kind/releases/download/v0.24.0/kind-linux-amd64 && chmod +x ./kind && mv ./kind /usr/local/bin/kind

# for debugging only
curl -LO https://github.com/derailed/k9s/releases/download/v0.50.18/k9s_linux_amd64.deb && apt install ./k9s_linux_amd64.deb && rm k9s_linux_amd64.deb

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
curl -Lo ./yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && chmod +x ./yq && mv ./yq /usr/local/bin/yq
apt install --yes python3-venv
# Use operations-guide mirrored by Nautilus team instead of upstream
# Parametrize this clone can be a future improvement
git clone --depth 1 --branch "ci-0.0.2" https://git.knut.univention.de/univention/dev/projects/open-xchange/ox-operations-guide-mirror.git

cd ox-operations-guide-mirror
python3 -mvenv v
v/bin/pip install --upgrade pip wheel
v/bin/pip install -r requirements.txt

PASSWORD_DOVEADM="$(openssl rand -base64 18)"

cat <<EOF >values.yaml
as_hostname: "as8.lab.test"
render_sh: true
generic_script_target: "sh"
generic_script_interpreter: "bash"
sys_prefix: "/usr"
assignment_dollar: ""
assignment_dollar_env: "export "
dollar_null: ""
echo: "echo"
noop: "true"
do_provisioning: false
redis_deployment_mode: lab
deputy_enabled: true
contacts_provider_ldap_enabled: true
enable_username_editable: true
external_tls_termination: true

switchboard_enabled: false

use_ldap: true
use_ldap_resolver: true
ldap_server_host: "${LDAP_SERVER}"
ldap_server_scheme: ldap
ldap_server_port: "389"
as_hostname_dc: "${LDAP_BASE}"
ldap_binddn_appsuite: "uid=Administrator,cn=users,${LDAP_BASE}"
ldap_binddn_dovecot: "uid=Administrator,cn=users,${LDAP_BASE}"
ldap_basedn: "${LDAP_BASE}"

mail_server: "dovecot-ce:143"
mail_login_source: mail

attribute_sources:
  userName:
    ldap: uid
    claim: ox_username
  contextName:
    ldap: oxContextIDNum
    claim: ox_contextname
  mailboxName:
    ldap: mailPrimaryAddress
    claim: dc_username

core_mw_extra_properties:
  # enable shared accounts
  com.openexchange.sharedaccount.enabled: "true"
  # the shared accounts are only virtual and not backed by a real LDAP user -> use the technical account for the login
  com.openexchange.mail.secondary.passwordSource: "global"
  # Additional configuration related to the deputy feature
  com.openexchange.dovecot.doveadm.enabled: "true"
  com.openexchange.dovecot.doveadm.endpoints: "http://dovecot-ce:8080/doveadm/v1"
  com.openexchange.dovecot.doveadm.endpoints.totalConnections: "100"
  com.openexchange.dovecot.doveadm.endpoints.maxConnectionsPerRoute: "0"
  com.openexchange.dovecot.doveadm.endpoints.readTimeout: "20000"
  com.openexchange.dovecot.doveadm.endpoints.connectTimeout: "5000"
  com.openexchange.dovecot.doveadm.apiSecret: "${PASSWORD_DOVEADM}"
  com.openexchange.deputy.provider.imap.doveadm.personalNamespace: "/"
  com.openexchange.deputy.provider.imap.doveadm.sharedNamespace: "shared/"
  com.openexchange.deputy.provider.imap.doveadm.publicNamespace: "shared/"
  # Requirements for OX-Connector
  com.openexchange.user.enforceUniqueDisplayName: "false"
  com.openexchange.folderstorage.database.preferDisplayName: "false"
EOF

if [ "${OX_APP_SUITE_CHART_VERSION}" != "" ]; then
    echo "Using OX app suite chart version: ${OX_APP_SUITE_CHART_VERSION}"
    yq -i \
        ".dependencies |= map(select(.name == \"appsuite\").version = \"${OX_APP_SUITE_CHART_VERSION}\")" \
        dependencies.yml
fi

mkdir -p "./rendered/values/"

v/bin/python vault.py -c -v "./rendered/values/vault.json" -s "dovecot.doveconf.doveadm_api_key=${PASSWORD_DOVEADM}"
# ldap.readpw.appsuite (password of oxSystemUser is used for authentication)
v/bin/python vault.py -c -v "./rendered/values/vault.json" -s "ldap.readpw.appsuite=univention"
# ldap.readpw.dovecot (password of oxSystemUser is used for authentication)
v/bin/python vault.py -c -v "./rendered/values/vault.json" -s "ldap.readpw.dovecot=univention"

v/bin/python render.py --values values.yaml

# mail_server variable is used in appsuite and postfix but postfix does not support port so remove it manually
yq -i ".postconf.lmtp_target = \"dovecot-ce\"" rendered/values/values.postfix.yaml

# workaround for bitnami moving their images
yq -i ".image.repository = \"bitnamilegacy/redis\"" rendered/values/values.bitnami-redis.yaml

# more cpu for middleware -> not needed features
yq -i ".core-guidedtours.enabled = false" rendered/values/values.yaml
yq -i ".core-user-guide.enabled = false" rendered/values/values.yaml

# doveconf.ldap.uri (bug? hardcoded to: uri: ldap://slapd:389/ )
yq -i ".doveconf.ldap.uri = \"ldap://${LDAP_SERVER}:389/\"" rendered/values/values.dovecot-ce.yaml

cd rendered/values

# run install in a subshell it might change environment, sometimes kubectl is no longer found after calling it
(./install.sh)

cluster_ip="$(kubectl get nodes -o wide | awk '/kind-control-plane/ {print $6}')"
ucr set "hosts/static/$cluster_ip=as8.lab.test"

# certs
cp cacert.pem /usr/local/share/ca-certificates/cluster.crt
update-ca-certificates

univention-certificate new -name as8.lab.test -days 500
ucr set apache2/vhosts/as8.lab.test/443/aliases=as8.lab.test apache2/vhosts/as8.lab.test/443/enabled=1 apache2/vhosts/as8.lab.test/443/ssl/certificate=/etc/univention/ssl/as8.lab.test/cert.pem apache2/vhosts/as8.lab.test/443/ssl/key=/etc/univention/ssl/as8.lab.test/private.key apache2/vhosts/as8.lab.test/443/ssl/certificatechain=/etc/univention/ssl/ucsCA/CAcert.pem
systemctl restart apache2

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
       BalancerMember http://as8.lab.test:30080 timeout=100 smax=0 ttl=60 retry=60 loadfactor=50 route=APP1
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
     BalancerMember http://as8.lab.test_sync:30080 timeout=1900 smax=0 ttl=60 retry=60 loadfactor=50 route=APP1
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
