<?php
$HELP_TITLE = 'Directory Manager Hilfe';

function print_help_title($lang) {
	switch($lang) {
		case 'de':
			echo 'management console hilfe';
			break;
		default: // 'en' and everything else
			echo 'management console help';
	}
}

function print_help_text($lang) {
	switch($lang) {
		case 'de':
?>
<p>Univention Management Console (UMC) ermöglicht die komfortable, webbasierte
Verwaltung des lokalen Rechners. UMC ermöglicht Dienste zu kontrollieren, die
Systemauslastung zu überprüfen sowie Systemeinstellungen einzusehen und zu
ändern.  Das Web-Interface von UMC wird im aktuellen Handbuch des Univention
Corporate Servers (UCS) detailliert beschrieben. Neben dem Handbuch können auf
der Univention-Homepage zusätzliche Dokumentationen zu Univention Corporate
Server abgerufen werden, die bei verschiedenen Themen wie der Einrichtung oder
Administration unterstützen.</p>
<p><b>Handbücher und Dokumentation:</b>
<ul>
	<li><a href="http://www.univention.de/fileadmin/download/dokumentation_2.4/handbuch_ucs24.pdf" target="_blank">Aktuelles Handbuch (PDF)</a></li>
	<li><a href="http://www.univention.de/download_doku.html" target="_blank">Zusätzliche Dokumentationen zu UCS</a></li>
</ul></p>
<p><b>Weiterführende Informationen:</b>
<ul>
	<li><a href="http://sdb.univention.de" target="_blank">Univention Supportdatenbank (SDB)</a></li>
	<li><a href="http://wiki.univention.de" target="_blank">Univention Wiki-Seite</a></li>
</ul></p>
<p><b>Unterstützung und Support:</b>
<ul>
	<li><a href="http://forum.univention.de" target="_blank">Univention Forum</a></li>
	<li><a href="http://www.univention.de/services/support/" target="_blank">Univention Supportangebote</a></li>
</ul></p>
<?php
			break;
		default: // 'en' and everything else
?>
<p>Univention Management Console (UMC) is a modularly designed, web-based
application to administrate local computers. The application allows the user to
control services, check system utilisation, and check or adjust system
parameters.  The web-based interface of UMC is described in detail the in
current manual of Univention Corporate Server (UCS). Besides the manual, the
homepage of Univention provides additional documentation for Univention
Corporate Server. These documents assist in different topics like installation
or administration.</p>
<p><b>Manual and documentation:</b>
<ul>
	<li><a href="http://www.univention.de/fileadmin/download/dokumentation_2.4/handbuch_ucs24.pdf" target="_blank">Current manual (PDF)</a></li>
	<li><a href="http://www.univention.de/download_doku.html" target="_blank">Additional documentation for UCS</a></li>
</ul></p>
<p><b>Supplementary information:</b>
<ul>
	<li><a href="http://sdb.univention.de" target="_blank">Univention support data base (SDB)</a></li>
	<li><a href="http://wiki.univention.de" target="_blank">Univention wiki site</a></li>
</ul></p>
<p><b>Support and assistance:</b>
<ul>
	<li><a href="http://forum.univention.de" target="_blank">Univention forum</a></li>
	<li><a href="http://www.univention.de/en/about-univention/contact/" target="_blank">Univention support</a></li>
</ul></p>
<?php
	}
}
?>

