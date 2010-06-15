<?php
/**
 * Turba base inclusion file.
 *
 * $Horde: turba/lib/base.php,v 1.58 2004/04/07 14:43:52 chuck Exp $
 *
 * This file brings in all of the dependencies that every Turba script
 * will need, and sets up objects that all scripts use.
 */

// Check for a prior definition of HORDE_BASE (perhaps by an
// auto_prepend_file definition for site customization).
if (!defined('HORDE_BASE')) {
    @define('HORDE_BASE', dirname(__FILE__) . '/../..');
}

// Load the Horde Framework core, and set up inclusion paths.
require_once HORDE_BASE . '/lib/core.php';

// Registry.
$registry = &Registry::singleton();
if (is_a(($pushed = $registry->pushApp('turba', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}
$conf = &$GLOBALS['conf'];
@define('TURBA_TEMPLATES', $registry->getParam('templates'));

// Notification system.
$notification = &Notification::singleton();
$notification->attach('status');

// Find the base file path of Turba.
@define('TURBA_BASE', dirname(__FILE__) . '/..');

// Turba base library.
require_once TURBA_BASE . '/lib/Turba.php';

// Turba sources configuration.
require TURBA_BASE . '/config/sources.php';
$GLOBALS['cfgSources'] = Turba::permissionsFilter($cfgSources, 'source');

// Help.
require_once 'Horde/Help.php';

/* Start compression, if requested. */
Horde::compressOutput();
