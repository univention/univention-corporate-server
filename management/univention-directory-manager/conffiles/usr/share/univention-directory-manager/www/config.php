<?php

@%@BCWARNING=// @%@

# Maximales alter temporärer Dateien in Sekunden. Bei überschreiten wird gelöscht.
# $temp_age=180;
$temp_age=800;

# Verzeichnis zur temporären Speicherung der XML-Dokumente
# Muss ein Unterverzeichnis sein, da alle Dateien die seit $temp_age nicht
# mehr benutzt werden, gelöscht werden.
$temp_dir="/tmp/webui/";

# Zugriffsrechte des temporären Verzeichnis als oktalwert
$temp_mode=0700;

# Pruefen ob die Webseite uber HTTPS aufgerufen wurde oder nicht
$https = "0";
if (isset( $_SERVER["HTTPS"])) {
         $https = "1";
}

# Programmaufruf (die Variable wir in folgenden String eingefügt "$run > /temp_dir/session_id" )
#$run="./examples/dummy.pl";
@!@
run='$run="/usr/bin/python2.4 /usr/share/univention-directory-manager/uniconf/univention-directory-manager.py '
if baseConfig.has_key('directory/manager/web/debug/level'):
        debug='-d %s '%baseConfig['directory/manager/web/debug/level']
else:
        debug='-d 0 '
if baseConfig.has_key('directory/manager/web/language'):
        lang='-l %s'%baseConfig['directory/manager/web/language']
else:
        lang='-l de_DE.utf8'
tail='";'

if baseConfig.has_key('directory/manager/timeout'):
        try:
                time = int(baseConfig['directory/manager/timeout'])
        except:
                time = 300
else:
        time = 300

if time  > 2147483647:
        timeout='-t 2147483647 '
else:
        timeout='-t %s '%baseConfig['directory/manager/timeout']

run=run+" -e $https "
run=run+debug
run=run+timeout
run=run+lang
run=run+tail
print run
@!@
#$run="/usr/share/univention-directory/manager/uniconf-client";

# gewaehlte Sprache fuer die Oberflaeche
@!@
if baseConfig.has_key('directory/manager/web/language'):
	print '$language="%s";'%baseConfig['directory/manager/web/language']
else:
	print '$language="de_DE.utf8";'
@!@
# Zeichensatz des Input- & Output-XML
$encoding="UTF-8";    //ISO-8859-1  oder UTF-8

# Debug-Modus ( on / off )
$debugger = "off";

?>
