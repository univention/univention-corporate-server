<?php
/**
 * Horde base inclusion file.
 *
 * This file brings in all of the dependencies that Horde
 * framework-level scripts will need, and sets up objects that all
 * scripts use.
 *
 * Note: This base file does _not_ check authentication, so as to
 * avoid an infinite loop on the Horde login page. You'll need to do
 * it yourself in framework-level pages.
 *
 * The following global variables are used:
 *   $no_compress  -  Controls whether the page should be compressed
 *
 * $Horde: horde/lib/base.php,v 1.40.10.8 2009-01-06 15:24:51 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

// Check for a prior definition of HORDE_BASE (perhaps by an
// auto_prepend_file definition for site customization).
if (!defined('HORDE_BASE')) {
    define('HORDE_BASE', dirname(__FILE__) . '/..');
}

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

// Registry.
$session_control = Util::nonInputVar('session_control');
if ($session_control == 'none') {
    $registry = &Registry::singleton(HORDE_SESSION_NONE);
} elseif ($session_control == 'readonly') {
    $registry = &Registry::singleton(HORDE_SESSION_READONLY);
} else {
    $registry = &Registry::singleton();
}
if (is_a(($pushed = $registry->pushApp('horde', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}
$conf = &$GLOBALS['conf'];
@define('HORDE_TEMPLATES', $registry->get('templates'));

// Notification System.
$notification = &Notification::singleton();
$notification->attach('status');

// Menu System.
require_once 'Horde/Menu.php';

// Compress output
if (!Util::nonInputVar('no_compress')) {
    Horde::compressOutput();
}
