# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

create_proxy_http_conf () {
  local UCS_IP="$1"
  cat > /etc/apache2/conf-available/proxy_http.conf <<- EOF
<IfModule mod_proxy_http.c>
   ProxyRequests Off
   ProxyStatus On
   # When enabled, this option will pass the Host: line from the incoming request to the proxied host.
   ProxyPreserveHost On
   # Please note that the servlet path to the soap API has changed:
   <Location /webservices>
       # restrict access to the soap provisioning API
       Order Deny,Allow
       Deny from all
       Allow from 127.0.0.1
       # you might add more ip addresses / networks here
       Allow from $UCS_IP
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
       Order Deny,Allow
       Deny from all
       Allow from 127.0.0.1
     </Location>
   </IfModule>

   <Proxy balancer://oxcluster>
       Order deny,allow
       Allow from all
       # multiple server setups need to have the hostname inserted instead localhost
       BalancerMember http://localhost:8009 timeout=100 smax=0 ttl=60 retry=60 loadfactor=50 route=APP1
       # Enable and maybe add additional hosts running OX here
       # BalancerMember http://oxhost2:8009 timeout=100 smax=0 ttl=60 retry=60 loadfactor=50 route=APP2
      ProxySet stickysession=JSESSIONID|jsessionid scolonpathdelim=On
      SetEnv proxy-initial-not-pooled
      SetEnv proxy-sendchunked
   </Proxy>

   # The standalone documentconverter(s) within your setup (if installed)
   # Make sure to restrict access to backends only
   # See: https://httpd.apache.org/docs/$YOUR_VERSION/mod/mod_authz_host.html#allow for more infos
   #<Proxy balancer://oxcluster_docs>
   #    Order Deny,Allow
   #    Deny from all
   #    Allow from backend1IP
   #    BalancerMember http://converter_host:8009 timeout=100 smax=0 ttl=60 retry=60 loadfactor=50 keepalive=On  route=APP3
   #    ProxySet stickysession=JSESSIONID|jsessionid scolonpathdelim=On
   #	   SetEnv proxy-initial-not-pooled
   #    SetEnv proxy-sendchunked
   #</Proxy>
   # Define another Proxy Container with different timeout for the sync clients. Microsoft recommends a minimum value of 15 minutes.
   # Setting the value lower than the one defined as com.openexchange.usm.eas.ping.max_heartbeat in eas.properties will lead to connection
   # timeouts for clients.  See https://support.microsoft.com/?kbid=905013 for additional information.
   #
   # NOTE for Apache versions < 2.4:
   # When using a single node system or using BalancerMembers that are assigned to other balancers please add a second hostname for that
   # BalancerMember's IP so Apache can treat it as additional BalancerMember with a different timeout.
   #
   # Example from /etc/hosts: 127.0.0.1	localhost localhost_sync
   #
  # Alternatively select one or more hosts of your cluster to be restricted to handle only eas/usm requests
  <Proxy balancer://eas_oxcluster>
     Order deny,allow
     Allow from all
     # multiple server setups need to have the hostname inserted instead localhost
     BalancerMember http://localhost_sync:8009 timeout=1900 smax=0 ttl=60 retry=60 loadfactor=50 route=APP1
     # Enable and maybe add additional hosts running OX here
     # BalancerMember http://oxhost2:8009 timeout=1900  smax=0 ttl=60 retry=60 loadfactor=50 route=APP2
     ProxySet stickysession=JSESSIONID|jsessionid scolonpathdelim=On
     SetEnv proxy-initial-not-pooled
     SetEnv proxy-sendchunked
  </Proxy>

  # When specifying additional mappings via the ProxyPass directive be aware that the first matching rule wins. Overlapping urls of
  # mappings have to be ordered from longest URL to shortest URL.
  #
  # Example:
  #   ProxyPass /ajax      balancer://oxcluster_with_100s_timeout/ajax
  #   ProxyPass /ajax/test balancer://oxcluster_with_200s_timeout/ajax/test
  #
  # Requests to /ajax/test would have a timeout of 100s instead of 200s
  #
  # See:
  # - https://httpd.apache.org/docs/current/mod/mod_proxy.html#proxypass Ordering ProxyPass Directives
  # - https://httpd.apache.org/docs/current/mod/mod_proxy.html#workers Worker Sharing
  ProxyPass /ajax balancer://oxcluster/ajax
  ProxyPass /appsuite/api balancer://oxcluster/ajax
  ProxyPass /drive balancer://oxcluster/drive
  ProxyPass /infostore balancer://oxcluster/infostore
  ProxyPass /realtime balancer://oxcluster/realtime
  ProxyPass /servlet balancer://oxcluster/servlet
  ProxyPass /webservices balancer://oxcluster/webservices

  #ProxyPass /documentconverterws balancer://oxcluster_docs/documentconverterws

  ProxyPass /usm-json balancer://eas_oxcluster/usm-json
  ProxyPass /Microsoft-Server-ActiveSync balancer://eas_oxcluster/Microsoft-Server-ActiveSync

</IfModule>
EOF
}

create_000_default_conf () {
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
}

assert_ox_connector_provisioning_setup () {
  local app_id="ox-connector"
  local app_root="/var/lib/univention-appcenter/apps/${app_id}"
  local subscription_file="${app_root}/runtime-secrets/provisioning-subscription.json"
  local container

  test "$(ucr get "appcenter/apps/${app_id}/status")" = "installed" || {
    echo "ERROR: ${app_id} is not marked as installed." >&2
    return 1
  }
  container="$(ucr get "appcenter/apps/${app_id}/container")"
  test -n "${container}" && test "$(docker inspect --format '{{.State.Running}}' "${container}")" = "true" || {
    echo "ERROR: ${app_id} container is not running." >&2
    return 1
  }
  test -f "${subscription_file}" &&
    test ! -L "${subscription_file}" &&
    test "$(stat -c '%U:%G:%a' -- "${subscription_file}")" = "root:root:600" || {
    echo "ERROR: managed Provisioning subscription file has unsafe ownership or permissions." >&2
    return 1
  }

  python3 - "${subscription_file}" "$(ucr get hostname)" "$(ucr get ldap/master)" <<'PY'
import importlib
import json
import sys
from urllib.parse import quote, urlsplit

import requests
import univention.admin.modules
import univention.admin.syntax

subscription_file, hostname, primary = sys.argv[1:]
with open(subscription_file, encoding="utf-8") as stream:
    record = json.load(stream)

assert record["state"] == "active"
subscription = record["subscription"]
assert subscription["name"] == f"ox-connector-{hostname}"
assert record["password"]

base_url = record["provisioning_api_base_url"].rstrip("/")
parsed_url = urlsplit(base_url)
assert parsed_url.scheme == "https"
assert parsed_url.hostname.casefold() == primary.casefold()
name = subscription["name"]
try:
    response = requests.get(
        f"{base_url}/v1/subscriptions/{quote(name, safe='')}",
        auth=(name, record["password"]),
        verify="/usr/local/share/ca-certificates/ucsCA.crt",
        allow_redirects=False,
        timeout=(2, 15),
    )
except requests.RequestException:
    raise SystemExit("limited subscriber authentication against Provisioning failed") from None
if response.status_code != 200:
    raise SystemExit("limited subscriber authentication against Provisioning failed")

remote = response.json()
for field in ("name", "realms_topics", "request_prefill"):
    assert remote[field] == subscription[field]

univention.admin.modules.update()
assert hasattr(univention.admin.syntax, "oxContextSelect")
importlib.import_module("univention.admin.handlers.oxmail.shared_account")
importlib.import_module("univention.admin.handlers.oxresources.oxresources")
print("Validated automatic OX Provisioning setup and UDM extensions.")
PY
}

assert_ox_connector_provisioning_cleanup () {
  local app_root="/var/lib/univention-appcenter/apps/ox-connector"

  test ! -e "${app_root}/runtime-secrets/provisioning-subscription.json" &&
    test ! -L "${app_root}/runtime-secrets/provisioning-subscription.json" || {
      echo "ERROR: managed Provisioning subscription credential remains after uninstall." >&2
      return 1
    }
  test ! -e "${app_root}/local/univention-provisioning-service-client" &&
    test ! -L "${app_root}/local/univention-provisioning-service-client" || {
      echo "ERROR: private Provisioning lifecycle client remains after uninstall." >&2
      return 1
    }
  echo "Validated OX Connector Provisioning cleanup."
}
