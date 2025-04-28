#!/bin/bash
# install OX 8 (kubernetes)
# see https://git.knut.univention.de/univention/prof-services/team-enterprise/zit-sh/-/issues/56
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.14.0/bin/linux/amd64/kubectl && chmod +x ./kubectl && mv ./kubectl /usr/local/bin/kubectl
curl -LO https://get.helm.sh/helm-v3.16.2-linux-amd64.tar.gz && tar -zxvf helm-v3.16.2-linux-amd64.tar.gz && mv linux-amd64/helm /usr/local/bin/helm
curl -Lo ./kind https://github.com/kubernetes-sigs/kind/releases/download/v0.24.0/kind-linux-amd64 && chmod +x ./kind && mv ./kind /usr/local/bin/kind
apt install --yes docker.io
kind create cluster
kubectl create namespace as8
apt update
apt install --yes jq
apt install  --yes git
helm plugin install https://github.com/databus23/helm-diff
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update
helm upgrade --install --set args={--kubelet-insecure-tls} metrics-server metrics-server/metrics-server --namespace kube-system
sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq && sudo chmod +x /usr/bin/yq
apt install --yes python3-venv
git clone https://gitlab.open-xchange.com/appsuite/operation-guides.git
cd operation-guides
python3 -mvenv v
v/bin/pip install --upgrade pip wheel
v/bin/pip install -r requirements.txt
#JUST_UCS
cat <<EOF >render.py.patch
--- operation-guides-orig/render.py     2024-10-18 12:57:47.140523950 +0200
+++ operation-guides/render.py  2024-10-18 12:57:16.505807054 +0200
@@ -0,0 +1 @@
+from __future__ import annotations
@@ -101 +102 @@
-    retvars = { 'generic_script_target': lang } | additional_script_vars[lang]
+    retvars = { 'generic_script_target': lang } or additional_script_vars[lang]
@@ -111 +112 @@
-        retvars |= {
+        retvars = retvars or {
@@ -138,0 +140 @@
+
@@ -210 +212 @@
-                    template.render(vars | get_additional_script_vars(lang[1:]) ) if vars['render_'+lang[1:]] else "",
+                    template.render(vars or get_additional_script_vars(lang[1:]) ) if vars['render_'+lang[1:]] else "",
EOF
patch render.py <render.py.patch
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
cat <<'EOF' >install.sh.patch
--- install.sh.orig     2024-10-19 10:13:37.540000000 +0200
+++ install.sh.new      2024-10-19 10:14:25.612000000 +0200
@@ -145 +145,9 @@
-    kubectl wait tenant -n "as8" minio --for='jsonpath={.status.currentState}=Initialized' --timeout=600s || portableExit 1
+    counter=0
+    until [ "$(kubectl get tenant -n "as8" minio -o 'jsonpath={.status.currentState}')" == "Initialized" ]; do
+        sleep 10
+        let "counter=counter+1"
+        if [ $counter -gt 60 ]; then
+            echo "Waiting to long"
+            exit 1
+        fi
+    done
EOF
patch install.sh <install.sh.patch
sed -i '/--for=create/d' install.sh
sed -i 's/cpu: 100/cpu: 50/g' install.sh
# bump version https://www.oxpedia.org/wiki/index.php?title=AppSuite:Versioning_and_Numbering#2025
sed -i -E 's|oci://registry.open-xchange.com/appsuite/charts/appsuite --version [0-9]\.[0-9]{1,2}\.[0-9]{1,3} |oci://registry.open-xchange.com/appsuite/charts/appsuite |g' install.sh
# Bug in OX templating. Workaround is to disable wopi-server
sed -i "s/^istio:/wopi-server:\n   enabled: false\nistio:/" values.yaml
sed -i 's|AVERAGE_CONTEXT_SIZE: "200"|AVERAGE_CONTEXT_SIZE: "200"\n    /opt/open-xchange/etc/AdminUser.properties:\n       USERNAME_CHANGEABLE: "true"|g' values.yaml

# activate deputy permission provisioning
cat <<'EOF' >values.yaml.patch
@@ -37,11 +37,20 @@
       open-xchange-documentconverter-client: disabled
       open-xchange-documents-backend: disabled
       open-xchange-drive-client-windows: disabled
+      open-xchange-deputy: enabled

   # using this will cause an initjob invoke initconfigdb
   enableInitialization: false

   properties:
+    com.openexchange.dovecot.doveadm.endpoints: "http://dovecot-ce:8080/doveadm/v1"
+    com.openexchange.dovecot.doveadm.endpoints.totalConnections: "100"
+    com.openexchange.dovecot.doveadm.endpoints.maxConnectionsPerRoute: "0"
+    com.openexchange.dovecot.doveadm.endpoints.readTimeout: "20000"
+    com.openexchange.dovecot.doveadm.endpoints.connectTimeout: "5000"
+    com.openexchange.dovecot.doveadm.enabled: "true"
+    com.openexchange.deputy.enabled: "true"
+    com.openexchange.deputy.adminOnly: "true"
     com.openexchange.hostname: "as8.lab.test"
     # S3 Filestore
     com.openexchange.filestore.s3client.s3.endpoint: "https://minio.as8:443"
EOF
patch values.yaml <values.yaml.patch

sed -i 's/doveadm_api_key:.*$/doveadm_api_key: "secret"/g' values.dovecot-ce.secret.yaml
sed -i 's/    com.openexchange.filestore.s3client.s3.accessKey: /    com.openexchange.dovecot.doveadm.apiSecret: "secret"\n    com.openexchange.filestore.s3client.s3.accessKey: /g' values.secret.yaml

./install.sh

# TODO FIXME: service dovecot-ce needs port 8080
# verify
# kubectl get all -n as8

cluster_ip="$(kubectl get nodes -o wide | awk '/kind-control-plane/ {print $6}')"
ucr set "hosts/static/$cluster_ip=as8.lab.test"

# certs
cp operation-guides/rendered/values/cacert.pem /usr/share/ca-certificates/clustercert.crt && update-ca-certificates
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
kubectl exec -n as8 "$(kubectl get pods -n as8 |grep mw-default|awk '{print $1}')" -it -- bash -c 'curl -v -H "Authorization: X-Dovecot-API c2VjcmV0" http://dovecot-ce:8080/doveadm/v1'
