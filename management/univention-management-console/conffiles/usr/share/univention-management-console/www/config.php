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

# Programmaufruf (die Variable wir in folgenden String eingefügt "$run > /temp_dir/session_id" )
#$run="./examples/dummy.pl";

$https = "0";
if (isset( $_SERVER["HTTPS"])) {
	$https = "1";
}

$http_host='';
if (isset( $_SERVER["HTTP_HOST"])) {
	$http_host = $_SERVER["HTTP_HOST"];
}

@!@
run='$run="/usr/bin/python2.4 /usr/share/univention-management-console/frontend/univention-console-frontend.py '
if baseConfig.has_key('umc/web/debug/level'):
	debug='-d %s '%baseConfig['umc/web/debug/level']
else:
	debug='-d 0 '
if baseConfig.has_key('umc/web/language'):
	lang = baseConfig['umc/web/language']
	if lang.find( '_' ) > -1:
		lang = '-l %s' % lang[ : lang.find( '_' ) ]
	else:
		lang = '-l %s' % lang
else:
	lang='-l de_DE.utf8'
tail='";'
if baseConfig.has_key('umc/web/timeout'):
	try:
		time = int(baseConfig['umc/web/timeout'])
		if time  > 2147483647:
			time = 2147483647
		elif time <= 30:
			# minimum timeout is 30 seconds
			time = 900
	except:
		time = 900
else:
	time = 900

timeout = '-t %d ' % time


run=run+" -e $https -x $http_host "
run=run+debug
run=run+timeout
run=run+lang
run=run+tail
print run
@!@

#$run="/usr/share/univention-admin/uniconf-client";

# gewaehlte Sprache fuer die Oberflaeche
@!@
if baseConfig.has_key('umc/web/language'):
	lang = baseConfig['umc/web/language']
	print '$language="%s";' % lang
else:
	print '$language="de_DE.utf8";'
@!@

# Zeichensatz des Input- & Output-XML
$encoding="UTF-8";    //ISO-8859-1  oder UTF-8

# Debug-Modus ( on / off )
$debugger = "off";

# kein Menu an der linken Seite
$layout_type = "menuless";

?>
