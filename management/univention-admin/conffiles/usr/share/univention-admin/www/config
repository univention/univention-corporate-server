<?php
# Maximales alter temporärer Dateien in Sekunden. Bei überschreiten wird gelöscht.
# $temp_age=180;
$temp_age=800;

# Verzeichnis zur temporären Speicherung der XML-Dokumente
# Muss ein Unterverzeichnis sein, da alle Dateien die seit $temp_age nicht
# mehr benutzt werden, gelöscht werden.
$temp_dir="/tmp/webui/";	

# Zugriffsrechte des temporären Verzeichnis als oktalwert
$temp_mode=0700;

# Programmaufruf (die Variable wir in folgenden String eingefügt "$run > /temp_dir/session_id" )
#$run="./examples/dummy.pl";
@!@
run='$run="/usr/bin/python2.4 -O /usr/share/univention-admin/uniconf/univention-admin.py '
if baseConfig.has_key('admin/web/debug/level'):
        debug='-d %s '%baseConfig['admin/web/debug/level']
else:
        debug='-d 0 '
if baseConfig.has_key('admin/web/language'):
        lang='-l %s'%baseConfig['admin/web/language']
else:
        lang='-l de'
tail='";'

if baseConfig.has_key('admin/timeout'):
        try:
                time = int(baseConfig['admin/timeout'])
        except:
                time = 300
else:
        time = 300

if time  > 2147483647:
        timeout='-t 2147483647 '
else:
        timeout='-t %s '%baseConfig['admin/timeout']

run=run+debug
run=run+timeout
run=run+lang
run=run+tail
print run
@!@
#$run="/usr/share/univention-admin/uniconf-client";

# gewaehlte Sprache fuer die Oberflaeche
@!@
if baseConfig.has_key('admin/web/language'):
	print '$language="%s";'%baseConfig['admin/web/language']
else:
	print '$language="de";'
@!@
# Zeichensatz des Input- & Output-XML
$encoding="UTF-8";    //ISO-8859-1  oder UTF-8

# Debug-Modus ( on / off )
$debugger = "off";

?>
