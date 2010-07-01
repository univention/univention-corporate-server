<?php
/**
 * DIMP base inclusion file. This file brings in all of the
 * dependencies that every DIMP script will need and sets up objects
 * that all scripts use.
 *
 * The following global variables are used:
 *   $dimp_logout      - Logout and redirect to the login page.
 *   $load_imp         - Load IMP's base file?
 *   $no_compress      - Controls whether the page should be compressed
 *   $noset_impview    - Don't set viewmode variable.
 *   $session_control  - Sets special session control limitations
 *   $session_timeout  - What to do on session timeout?  Default is to output
 *                       the login page; also 'json' and 'none'.
 *
 * $Horde: dimp/lib/base.php,v 1.33.2.9 2009-01-06 15:22:38 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

if (!defined('HORDE_BASE')) {
    define('HORDE_BASE', dirname(__FILE__) . '/../..');
}

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

// Registry.
$s_ctrl = null;
switch (Util::nonInputVar('session_control')) {
case 'none':
    $s_ctrl = HORDE_SESSION_NONE;
    break;

case 'readonly':
    $s_ctrl = HORDE_SESSION_READONLY;
    break;
}
$registry = &Registry::singleton($s_ctrl);

// Find the base file path of DIMP and IMP.
if (!defined('DIMP_BASE')) {
    define('DIMP_BASE', dirname(__FILE__) . '/..');
}
if (!defined('IMP_BASE')) {
    define('IMP_BASE', $registry->get('fileroot', 'imp'));
}

if (is_a(($pushed = $registry->pushApp('dimp', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}

if (!defined('DIMP_TEMPLATES')) {
    define('DIMP_TEMPLATES', $registry->get('templates'));
}

// Set viewmode.
if (!Util::nonInputVar('noset_impview')) {
    $_SESSION['imp']['viewmode'] = 'dimp';
}
$GLOBALS['noset_impview'] = true;

// Notification system.
if ($_SESSION['imp']['viewmode'] == 'dimp') {
    require_once DIMP_BASE . '/lib/Notification/Listener/status.php';
    $notification = &Notification::singleton();
    // It is possible IMP may have attached its status handler already if doing
    // autoload authentication.
    $notification->detach('status');
    $GLOBALS['dimp_listener'] = &$notification->attach('status', null, 'Notification_Listener_status_dimp');
}

// IMP/DIMP base libraries.
require_once IMP_BASE . '/lib/IMP.php';
require_once DIMP_BASE . '/lib/DIMP.php';

// Handle logout requests
if (Util::nonInputVar('dimp_logout')) {
    IMP::redirect(str_replace('&amp;', '&', IMP::getLogoutUrl()));
}

// Handle session timeouts
if (!IMP::checkAuthentication(true)) {
    switch (Util::nonInputVar('session_timeout')) {
    case 'json':
        $notification->push(null, 'dimp.timeout');
        IMP::sendHTTPResponse(DIMP::prepareResponse(), 'json');

    case 'none':
        exit;

    default:
        IMP::redirect(Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'imp') . '/redirect.php'), 'url', Horde::selfUrl(true)));
    }
}

// Start compression.
if (!Util::nonInputVar('no_compress')) {
    Horde::compressOutput();
}

$GLOBALS['dimp_conf'] = $GLOBALS['conf'];
$GLOBALS['dimp_prefs'] = &Util::cloneObject($GLOBALS['prefs']);

// Load IMP's base file?
if (Util::nonInputVar('load_imp')) {
    require IMP_BASE . '/lib/base.php';
    require_once 'Horde/Array.php';
    $GLOBALS['conf'] = Horde_Array::array_merge_recursive_overwrite($GLOBALS['conf'], $GLOBALS['dimp_conf']);
}
