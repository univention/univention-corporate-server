#!/bin/bash
#
# script to script UMCP-requests via HTTP
#
username=Administrator
password=password
host=www.example.com
key=""

# prints a HTTP POST command
# parameters:
# - url (e.g., 'command/mymodule/myfunc', 'auth', 'get/ucr')
# - json options (optional, e.g., '{"username":"...", "password":"..."}')
function umcp {
url="$1"
if [ -z "$2" ]; then
        json='{"options":{}}'
else
        json='{"options":'"$2"'}'
fi
echo "POST http://${host}/$url HTTP/1.1
Host: ${host}
User-Agent: Mozilla/5.0 (X11; Linux i686; rv:6.0.2) Gecko/20100101 Firefox/6.0.2
Content-Type: application/json
X-Requested-With:XMLHttpRequest
Content-Length: ${#json}
Cookie: UMCLang=de-DE; UMCSessionId=$key; UMCUsername=$username

$json"
}

# sends data from STDIN to the host
function send {
        nc -q 1 ${host} 80
}

# pretty prints JSON data in HTTP reponses
function prettyprint {
python -c "
import sys, json
for line in sys.stdin: 
        if line.startswith('{'):
                print json.dumps(json.loads(line), sort_keys=True, indent=4)
                print
        else:
                print line.strip()
"
}

# authenticate at UMCP server
function authenticate {
	key=$(umcp auth '{"username":"'$username'", "password":"'$password'"}' | send | sed -n 's/^.*UMCSessionId=\([^;]*\).*$/\1/p')
	echo "got session key: $key"
}

# examples
authenticate

# synchronous requests
(
umcp get/modules/list | send | prettyprint
umcp set '{"locale":"de"}'
) | send

# asynchronous requests
umcp get/ucr '["domainname","hostname"]' | send &
umcp get/ucr '["server/role"]' | send &

