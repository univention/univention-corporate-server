bugzilla --bugzilla https://forge.univention.org/bugzilla/xmlrpc.cgi query --outputformat '%{id}: %{target_milestone} %{summary}' -b $(tr '\n' ',' < missing)
git log 4.4-6..@ --oneline  | grep 'Bug #' | sed 's/.*Bug #//g; s/[,? :].*//' | sort | uniq  | while read line; do  grep -q "$line" changelog-5.0-0.xml || echo $line; done > missing
