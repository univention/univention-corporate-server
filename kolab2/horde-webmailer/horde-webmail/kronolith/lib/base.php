<?php
/**
 * Kronolith base inclusion file.
 *
 * This file brings in all of the dependencies that every Kronolith
 * script will need, and sets up objects that all scripts use.
 *
 * The following global variables are used:
 *   $session_control - Sets special session control limitations
 *   $no_compress     - Controls whether the page should be compressed
 *
 * $Horde: kronolith/lib/base.php,v 1.117.8.17 2009-08-12 22:28:12 jan Exp $
 *
 * @package Kronolith
 */

/* Check for a prior definition of HORDE_BASE (perhaps by an auto_prepend_file
 * definition for site customization). */
if (!defined('HORDE_BASE')) {
    define('HORDE_BASE', dirname(__FILE__) . '/../..');
}

/* Load the Horde Framework core, and set up inclusion paths. */
require_once HORDE_BASE . '/lib/core.php';

/* Registry. */
$session_control = Util::nonInputVar('session_control');
if ($session_control == 'none') {
    $registry = &Registry::singleton(HORDE_SESSION_NONE);
} elseif ($session_control == 'readonly') {
    $registry = &Registry::singleton(HORDE_SESSION_READONLY);
} else {
    $registry = &Registry::singleton();
}

if (is_a(($pushed = $registry->pushApp('kronolith', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}
$conf = &$GLOBALS['conf'];
define('KRONOLITH_TEMPLATES', $registry->get('templates'));

/* Find the base file path of Kronolith. */
if (!defined('KRONOLITH_BASE')) {
    define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
}

/* Horde framework libraries. */
require_once 'Horde/Date.php';
require_once 'Horde/Help.php';
require_once 'Horde/History.php';

/* Notification system. */
$notification = &Notification::singleton();
$notification->attach('status');

/* Kronolith base library. */
require_once KRONOLITH_BASE . '/lib/Kronolith.php';
require_once KRONOLITH_BASE . '/lib/Driver.php';
require_once KRONOLITH_BASE . '/lib/Recurrence.php';

/* Categories. */
require_once 'Horde/Prefs/CategoryManager.php';
$GLOBALS['cManager'] = new Prefs_CategoryManager();
$GLOBALS['cManager_fgColors'] = $GLOBALS['cManager']->fgColors();

/* PEAR Date_Calc. */
require_once 'Date/Calc.php';

/* Start compression, if requested. */
if (!Util::nonInputVar('no_compress')) {
    Horde::compressOutput();
}

/* Set the timezone variable, if available. */
NLS::setTimeZone();

/* Create a calendar backend object. */
$GLOBALS['kronolith_driver'] = &Kronolith_Driver::factory();

/* Create a share instance. */
require_once 'Horde/Share.php';
$GLOBALS['kronolith_shares'] = &Horde_Share::singleton($registry->getApp());

Kronolith::initialize();

/* Do maintenance operations - need to check for a number of conditions to be
 * sure that we aren't here due to alarm notifications (which would occur after
 * headers are sent), we aren't on any of the portal pages, and that we haven't
 * already performed maintenance.
 */
require_once 'Horde/Maintenance.php';
if (Kronolith::loginTasksFlag() &&
    !strstr($_SERVER['PHP_SELF'], 'maintenance.php') &&
    !headers_sent() && !defined('AUTH_HANDLER') &&
    $GLOBALS['prefs']->getValue('do_maintenance'))   {

    Kronolith::loginTasksFlag(2);
    $maint = &Maintenance::factory('kronolith', array('last_maintenance' => $GLOBALS['prefs']->getValue('last_kronolith_maintenance')));
    if (!$maint) {
        $GLOBALS['notification']->push(_("Could not execute maintenance operations."), 'horde.warning');
    } else {
       $maint->runMaintenance();
    }
    Kronolith::loginTasksFlag(0);

} elseif (Util::getFormData(MAINTENANCE_DONE_PARAM) &&
          Kronolith::loginTasksFlag()) {

        $maint = &Maintenance::factory('kronolith', array('last_maintenance' => $GLOBALS['prefs']->getValue('last_kronolith_maintenance')));
        if (!$maint) {
            $GLOBALS['notification']->push(_("Could not execute maintenance operations."), 'horde.warning');
        } else {
           $maint->runMaintenance();
        }
        Kronolith::loginTasksFlag(0);

}
