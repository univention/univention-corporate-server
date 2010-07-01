<?php
/**
 * Ingo base inclusion file.
 * This file brings in all of the dependencies that every Ingo
 * script will need and sets up objects that all scripts use.
 *
 * The following global variables are declared by this script:
 *   $ingo_storage - The Ingo_Storage:: object to use for storing rules.
 *   $no_compress  - Controls whether the page should be compressed
 *
 * $Horde: ingo/lib/base.php,v 1.56.10.4 2009-08-12 22:28:12 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

// Check for a prior definition of HORDE_BASE (perhaps by an auto_prepend_file
// definition for site customization).
if (!defined('HORDE_BASE')) {
    @define('HORDE_BASE', dirname(__FILE__) . '/../..');
}

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

// Registry.
$registry = &Registry::singleton();
if (is_a(($pushed = $registry->pushApp('ingo', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}
$conf = &$GLOBALS['conf'];
@define('INGO_TEMPLATES', $registry->get('templates'));

// Notification system.
$notification = &Notification::singleton();
$notification->attach('status');

// Redirect the user to the Horde login page if they haven't authenticated.
if (!Auth::isAuthenticated() && !defined('AUTH_HANDLER')) {
    Horde::authenticationFailureRedirect();
}

// Find the base file path of Ingo.
@define('INGO_BASE', dirname(__FILE__) . '/..');

// Ingo base library.
require_once INGO_BASE . '/lib/Ingo.php';

// Other Horde libraries needed.
require_once 'Horde/Help.php';

// Start compression.
if (!Util::nonInputVar('no_compress')) {
    Horde::compressOutput();
}

// Load the Ingo_Storage driver. It appears in the global variable
// $ingo_storage.
require_once INGO_BASE . '/lib/Storage.php';
$GLOBALS['ingo_storage'] = Ingo_Storage::factory();

// Create the ingo session (if needed).
if (!isset($_SESSION['ingo']) || !is_array($_SESSION['ingo'])) {
    require_once INGO_BASE . '/lib/Session.php';
    Ingo_Session::createSession();
}

// Create shares if necessary.
$driver = Ingo::getDriver();
if ($driver->supportShares()) {
    require_once 'Horde/Share.php';
    $GLOBALS['ingo_shares'] = &Horde_Share::singleton($registry->getApp());
    $GLOBALS['all_rulesets'] = Ingo::listRulesets();

    /* If personal share doesn't exist then create it. */
    $signature = $_SESSION['ingo']['backend']['id'] . ':' . Auth::getAuth();
    if (!$GLOBALS['ingo_shares']->exists($signature)) {
        require_once 'Horde/Identity.php';
        $identity = &Identity::singleton();
        $name = $identity->getValue('fullname');
        if (trim($name) == '') {
            $name = Auth::removeHook(Auth::getAuth());
        }
        $share = &$GLOBALS['ingo_shares']->newShare($signature);
        $share->set('name', $name);
        $GLOBALS['ingo_shares']->addShare($share);
        $GLOBALS['all_rulesets'][$signature] = &$share;
    }

    /* Select current share. */
    $_SESSION['ingo']['current_share'] = Util::getFormData('ruleset', @$_SESSION['ingo']['current_share']);
    if (empty($_SESSION['ingo']['current_share']) ||
        empty($GLOBALS['all_rulesets'][$_SESSION['ingo']['current_share']]) ||
        !$GLOBALS['all_rulesets'][$_SESSION['ingo']['current_share']]->hasPermission(Auth::getAuth(), PERMS_READ)) {
        $_SESSION['ingo']['current_share'] = $signature;
    }
} else {
    $GLOBALS['ingo_shares'] = null;
}
