<?php
/**
 * $Horde: horde/scripts/get_login.php,v 1.3.10.7 2009-01-06 15:26:19 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Joel Vandal <joel@scopserv.com>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';

$auth = &Auth::singleton($conf['auth']['driver']);

// Check for GET auth.
if (empty($_GET['user']) || !$auth->authenticate($_GET['user'], array('password' => $_GET['pass']))) {
    header('Location: ' . Horde::applicationUrl('login.php?logout_reason=logout'));
    exit;
}

header('Location: ' . Horde::applicationUrl('index.php'));
