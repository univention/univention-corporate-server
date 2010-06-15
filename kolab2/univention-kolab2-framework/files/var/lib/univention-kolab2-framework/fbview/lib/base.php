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
 * $Horde: horde/lib/base.php,v 1.39 2004/05/25 21:49:38 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

// Check for a prior definition of HORDE_BASE (perhaps by an
// auto_prepend_file definition for site customization).
if (!defined('HORDE_BASE')) {
    @define('HORDE_BASE', dirname(__FILE__) . '/..');
}

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

// Registry.
if (Util::nonInputVar('session_control') == 'none') {
    $registry = &Registry::singleton(HORDE_SESSION_NONE);
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
@define('HORDE_TEMPLATES', $registry->getParam('templates'));

// Notification System.
$notification = &Notification::singleton();
$notification->attach('status');

/* Set up the menu. */
require_once 'Horde/Menu.php';
$menu = &new Menu();

// Compress output
Horde::compressOutput();
