<?php
/**
 * MIMP base inclusion file. This file brings in all of the
 * dependencies that every MIMP script will need and sets up objects
 * that all scripts use.
 *
 * The following global variables are used:
 *   $debug          - Output text/plain version of page for debugging?
 *   $load_imp       - Load IMP's base file?
 *   $no_compress    - Controls whether the page should be compressed
 *   $noset_impview  - Don't set viewmode variable.
 *
 * $Horde: mimp/lib/base.php,v 1.37.2.5 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

// Registry.
$registry = &Registry::singleton();
if (is_a(($pushed = $registry->pushApp('mimp', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}

$conf = &$GLOBALS['conf'];
@define('MIMP_BASE', dirname(__FILE__) . '/..');
@define('IMP_BASE', $registry->get('fileroot', 'imp'));

// If an IMP session has not been created yet, redirect to IMP's redirect.php
// to login and create the session.
require_once IMP_BASE . '/lib/IMP.php';
if (!IMP::checkAuthentication(true)) {
    header('Location: ' . Util::addParameter(Horde::url($registry->get('webroot', 'imp'). '/redirect.php'), array('autologin' => IMP::canAutoLogin(), 'url' => Horde::selfUrl(true)), null, false));
    exit;
}

@define('MIMP_TEMPLATES', $registry->get('templates'));

// Set viewmode.
if (!Util::nonInputVar('noset_impview')) {
    $_SESSION['imp']['viewmode'] = 'mimp';
}
$GLOBALS['noset_impview'] = true;

// Notification system. Specifically detach any existing 'status' listener
// since IMP may have already defined one.
if ($_SESSION['imp']['viewmode'] == 'mimp') {
    require_once 'Horde/Notification/Listener/mobile.php';
    $notification = &Notification::singleton();
    $notification->detach('status');
    $GLOBALS['l'] = &$notification->attach('status', null, 'Notification_Listener_mobile');
}

// MIMP base library.
require_once MIMP_BASE . '/lib/MIMP.php';

// Mobile markup renderer.
require_once 'Horde/Mobile.php';
$debug = Util::nonInputVar('debug');
$GLOBALS['m'] = new Horde_Mobile(null, $debug);
$GLOBALS['m']->set('debug', !empty($debug));

// Start compression.
if (!Util::nonInputVar('no_compress')) {
    Horde::compressOutput();
}

// Find the base webroot of MIMP.
$mimp_webroot = $GLOBALS['registry']->get('webroot', 'mimp');
if (substr($mimp_webroot, -1) != '/') {
    $mimp_webroot .= '/';
}
@define('MIMP_WEBROOT', $mimp_webroot);

// Load IMP's base file
if (Util::nonInputVar('load_imp')) {
    $mimp_conf = $conf;
    $mimp_prefs = &Util::cloneObject($prefs);
    require IMP_BASE . '/lib/base.php';
    require_once 'Horde/Array.php';
    $conf = Horde_Array::array_merge_recursive_overwrite($conf, $mimp_conf);
}
