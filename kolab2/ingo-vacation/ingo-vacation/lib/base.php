<?php
/**
 * ingo-vacation base application file.
 *
 * $Horde: ingo-vacation/lib/base.php$
 *
 * This file brings in all of the dependencies that every ingo-vacation script will
 * need, and sets up objects that all scripts use.
 *
 * Copyright 2008 Univention GmbH (http://www.univention.de/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Christoph Ebersbach <ebersbach@univention.de>
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
if (is_a(($pushed = $registry->pushApp('ingo-vacation', !defined('AUTH_HANDLER'))), 'PEAR_Error')) {
    if ($pushed->getCode() == 'permission_denied') {
        Horde::authenticationFailureRedirect();
    }
    Horde::fatal($pushed, __FILE__, __LINE__, false);
}
$conf = &$GLOBALS['conf'];
@define('INGOVACATION_TEMPLATES', $registry->get('templates'));
@define('INGO_BASE', $registry->get('fileroot', 'ingo'));

// Notification system.
$notification = &Notification::singleton();
$notification->attach('status');

// Define the base file path of ingo-vacation.
@define('INGOVACATION_BASE', dirname(__FILE__) . '/..');

// ingo-vacation base library
//require_once INGOVACATION_BASE . '/lib/Ingo-Vacation.php';

// Start output compression.
Horde::compressOutput();

// Load INGO's base file
if (Util::nonInputVar('load_ingo')) {
    $ingovacation_conf = $conf;
    $ingovacation_prefs = &Util::cloneObject($prefs);
    require INGO_BASE . '/lib/base.php';
    require_once 'Horde/Array.php';
    $conf = Horde_Array::array_merge_recursive_overwrite($conf, $ingovacation_conf);
}
