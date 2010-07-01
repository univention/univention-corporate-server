<?php
// $Horde: imp/scripts/custom_login.php,v 1.6.10.4 2007-12-20 14:00:36 jan Exp $

// CUSTOMIZE THIS
define('IMP_BASE', '..');

define('AUTH_HANDLER', true);
$authentication = 'none';
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/config/servers.php';

/* Set up the password encryption token. */
Secret::setKey('imp');

/* Use the first server defined in servers.php. */
// CUSTOMIZE THIS

$server_key = 'localhost';

$server_value = $servers[$server_key]['server'];
$port_value = $servers[$server_key]['port'];
$protocol_value = $servers[$server_key]['protocol'];
$smtphost_value = $servers[$server_key]['smtphost'];
$smtpport_value = $servers[$server_key]['smtpport'];
$url = '/';
// $url = '/' . $registry->get('initial_page','horde');

?>

<!-- CUSTOMIZE THIS -->
<form action="<?php echo Horde::applicationUrl('redirect.php') ?>" method="post">
User: <input name="imapuser" type="text" size="20" /><br />
Pass: <input name="pass" type="password" size="20" /><br />
<input type="hidden" name="server" value="<?php echo $server_value ?>" />
<input type="hidden" name="port" value="<?php echo $port_value ?>" />
<input type="hidden" name="protocol" value="<?php echo $protocol_value ?>" />
<input type="hidden" name="smtphost" value="<?php echo $smtphost_value ?>" />
<input type="hidden" name="smtpport" value="<?php echo $smtpport_value ?>" />
<input type="hidden" name="url" value="<?php echo $url ?>" />
<input type="submit" value="Log in" />
</form>
