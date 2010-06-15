<?php
/**
 * $Horde: horde/scripts/get_login.php,v 1.2 2004/05/25 20:38:32 chuck Exp $
 *
 * Copyright 2004 Joel Vandal <jvandal@infoteck.qc.ca>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';

$auth = &Auth::singleton($conf['auth']['driver']);

// Check for GET auth.
if (empty($_GET['user']) || !$auth->authenticate($_GET['user'], array('password' => $_GET['pass']))) {
    header('Location: ' . Horde::applicationUrl('login.php?logout_reason=logout'));
    exit;
}

header('Location: ' . Horde::applicationUrl('index.php'));
