<?php
/**
 * IMP base inclusion file. This file brings in all of the dependencies that
 * every IMP script will need, and sets up objects that all scripts use.
 *
 * The following variables, defined in the script that calls this one, are
 * used:
 *   $authentication  - The type of authentication to use:
 *                      'horde' - Only use horde authentication
 *                      'none'  - Do not authenticate
 *                      Default - Authenticate to IMAP/POP server
 *   $no_compress     - Controls whether the page should be compressed
 *   $noset_impview   - Don't set viewmode variable.
 *   $session_control - Sets special session control limitations
 *
 * $Horde: imp/lib/base.php,v 1.79.10.21 2009-01-06 15:24:04 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package IMP
 */

// Check for a prior definition of HORDE_BASE.
if (!defined('HORDE_BASE')) {
    define('HORDE_BASE', dirname(__FILE__) . '/../..');
}

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

$session_control = Util::nonInputVar('session_control');
switch ($session_control) {
case 'netscape':
    if ($browser->isBrowser('mozilla')) {
        session_cache_limiter('private, must-revalidate');
    }
    break;
}

// Registry.
if ($session_control == 'none') {
    $registry = &Registry::singleton(HORDE_SESSION_NONE);
} elseif ($session_control == 'readonly') {
    $registry = &Registry::singleton(HORDE_SESSION_READONLY);
} else {
    $registry = &Registry::singleton();
}

// Is this the compose page? Look for a form value that only IMP's compose
// page generates.
$compose_page = Util::getFormData('compose_requestToken');

// We explicitly do not check application permissions for the compose
// and login/recompose pages, since those are handled below and need to fall
// through to IMP-specific code.
$auth_check = !(defined('AUTH_HANDLER') || $compose_page);
if (is_a(($pushed = $registry->pushApp('imp', $auth_check)), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}
$conf = &$GLOBALS['conf'];
if (!defined('IMP_TEMPLATES')) {
    define('IMP_TEMPLATES', $registry->get('templates'));
}

// Find the base file path of IMP.
if (!defined('IMP_BASE')) {
    define('IMP_BASE', dirname(__FILE__) . '/..');
}

// Notification system.
require_once IMP_BASE . '/lib/Notification/Listener/status.php';
$notification = &Notification::singleton();
$notification->attach('status', null, 'Notification_Listener_status_imp');
// TODO: BC check.
if (@include_once 'Horde/Notification/Listener/audio.php') {
    $notification->attach('audio');
}

// IMP libraries.
require_once IMP_BASE . '/lib/IMP.php';
require_once IMP_BASE . '/lib/IMAP.php';

// Horde libraries.
require_once 'Horde/Secret.php';

// Start compression.
if (!Util::nonInputVar('no_compress')) {
    Horde::compressOutput();
}

// If IMP isn't responsible for Horde auth, and no one is logged into
// Horde, redirect to the login screen. If this is a compose window
// that just timed out, give the user a chance to recover their
// message.
if (!(Auth::isAuthenticated() || (Auth::getProvider() == 'imp'))) {
    if ($compose_page) {
        $RECOMPOSE = true;
        require IMP_BASE . '/login.php';
        exit;
    } elseif (!IMP::recomposeLogin()) {
        Horde::authenticationFailureRedirect();
    }
}

$authentication = Util::nonInputVar('authentication');
if ($authentication === null) {
    $authentication = 0;
}
if ($authentication !== 'none') {
    // If we've gotten to this point and have valid login credentials
    // but don't actually have an IMP session, then we need to go
    // through redirect.php to ensure that everything gets set up
    // properly. Single-signon and transparent authentication setups
    // are likely to trigger this case.
    if (empty($_SESSION['imp'])) {
        if ($compose_page) {
            $RECOMPOSE = true;
            require IMP_BASE . '/login.php';
        } else {
            require IMP_BASE . '/redirect.php';
        }
        exit;
    }

    if ($compose_page) {
        if (!IMP::checkAuthentication(true, ($authentication === 'horde'))) {
            $RECOMPOSE = true;
            require IMP_BASE . '/login.php';
            exit;
        }
    } else {
        IMP::checkAuthentication(false, ($authentication === 'horde'));
    }

    // Set viewmode.
    if (!Util::nonInputVar('noset_impview')) {
        $_SESSION['imp']['viewmode'] = 'imp';
    }
}

// Initialize global $imp_mbox array.
$GLOBALS['imp_mbox'] = IMP::getCurrentMailboxInfo();

// Initialize IMP_Search object.
require_once IMP_BASE . '/lib/Search.php';
if (isset($_SESSION['imp']) && strpos($GLOBALS['imp_mbox']['mailbox'], IMP_SEARCH_MBOX) === 0) {
    $GLOBALS['imp_search'] = new IMP_Search(array('id' => $GLOBALS['imp_mbox']['mailbox']));
} else {
    $GLOBALS['imp_search'] = new IMP_Search();
}

if ((IMP::loginTasksFlag() === 2) &&
    !defined('AUTH_HANDLER') &&
    !strstr($_SERVER['PHP_SELF'], 'maintenance.php')) {
    require_once IMP_BASE . '/lib/Session.php';
    IMP_Session::loginTasks();
}

// Set default message character set, if necessary
if (isset($prefs) && ($def_charset = $prefs->getValue('default_msg_charset'))) {
    $GLOBALS['mime_structure']['default_charset'] = $def_charset;
    $GLOBALS['mime_headers']['default_charset'] = $def_charset;
}
