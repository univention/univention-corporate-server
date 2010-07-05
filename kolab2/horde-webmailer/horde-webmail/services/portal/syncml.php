<?php
/**
 * $Horde: horde/services/portal/syncml.php,v 1.3.2.15 2009-01-06 15:27:33 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Karsten Fourmont <karsten@horde.org>
 */

require_once dirname(__FILE__) . '/../../lib/base.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

require_once 'SyncML/Backend.php';
$backend = SyncML_Backend::factory('Horde');

$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'deleteanchor':
    $deviceid = Util::getFormData('deviceid');
    $db = Util::getFormData('db');
    $result = $backend->removeAnchor(Auth::getAuth(), $deviceid, $db);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(_("Error deleting synchronization session:")
                            . ' ' . $result->getMessage(),
                            'horde.error');
    } else {
        $notification->push(sprintf(_("Deleted synchronization session for device \"%s\" and database \"%s\"."),
                                    $deviceid, $db),
                            'horde.success');
    }
    break;

case 'deleteall':
    $result = $backend->removeAnchor(Auth::getAuth());
    if (is_a($result, 'PEAR_Error')) {
        $notification->push(_("Error deleting synchronization sessions:")
                            . ' ' . $result->getMessage(),
                            'horde.error');
    } else {
        $notification->push(_("All synchronization sessions deleted."),
                            'horde.success');
    }
    break;
}

$devices = $backend->getUserAnchors(Auth::getAuth());

/* Show the header. */
require_once 'Horde/Prefs/UI.php';
$result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'horde');
if (!is_a($result, 'PEAR_Error')) {
    extract($result);
}
$app = 'horde';
$chunk = Util::nonInputVar('chunk');
Prefs_UI::generateHeader('syncml', $chunk);

require HORDE_TEMPLATES . '/syncml/syncml.inc';
if (!$chunk) {
    require HORDE_TEMPLATES . '/common-footer.inc';
}
