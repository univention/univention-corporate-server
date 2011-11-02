<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<!--
   Univention Management Console VNC
    PHP script for the web access

   Copyright 2011 Univention GmbH

   http://www.univention.de/

   All rights reserved.

   The source code of this program is made available
   under the terms of the GNU Affero General Public License version 3
   (GNU AGPL V3) as published by the Free Software Foundation.

   Binary versions of this program provided by Univention to you as
   well as other copyrighted, protected or trademarked materials like
   Logos, graphics, fonts, specific documentations and configurations,
   cryptographic keys etc. are subject to a license agreement between
   you and Univention and not subject to the GNU AGPL V3.

   In the case you use this program under the terms of the GNU AGPL V3,
   the program is provided in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   GNU Affero General Public License for more details.

   You should have received a copy of the GNU Affero General Public
   License with the Debian GNU/Linux or Univention distribution in file
   /usr/share/common-licenses/AGPL-3; if not, see
   <http://www.gnu.org/licenses/>.
-->
<html>
  <title>
	VNC-Desktop auf <?php print $_SERVER["SERVER_ADDR"]; ?>
  </title>
  <?php if ($_GET["port"]) { ?>
  <body>
	<p align="center">
	  <applet archive="TightVncViewer.jar"
			  code="com.tightvnc.vncviewer.VncViewer"
			  width="100%" height="100%">
		<param name="SOCKETFACTORY" value="com.tightvnc.vncviewer.SshTunneledSocketFactory">
		<param name="SSHHOST" value=<?php print $_SERVER["SERVER_ADDR"]; ?>>
		<param name="HOST" value="localhost">
		<param name="PORT" value=<?php print $_GET["port"]; ?>>
	  </applet>
	</p>
	<?php } else { ?>

	Das passende VNC-Display konnte nicht gefunden werden. Bitte pr&uuml;fen Sie, ob der VNC-Server gestartet wurde.

	<?php } ?>
  </body>
</html>
