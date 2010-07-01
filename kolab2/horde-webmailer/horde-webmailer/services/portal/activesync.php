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

require_once 'Horde/Kolab/Storage.php';
$folder = Kolab_Storage::getFolder('INBOX');
$result = $folder->getActiveSync();
$devices = isset($result['DEVICE']) ? $result['DEVICE'] : null;

$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'save':
    if (Util::getFormData('delete')) {
        $deviceids = array_keys(Util::getFormData('delete'));
        $deviceid = $deviceids[0];
        $result = $folder->deleteActiveSyncDevice($deviceid);
        if (is_a($result, 'PEAR_Error')) {
            $notification->push(_("Error deleting device:")
                                . ' ' . $result->getMessage(),
                                'horde.error');
        } else {
            $notification->push(sprintf(_("Deleted ActiveSync device \"%s\"."),
                                        $deviceid),
                                'horde.success');
            unset($devices[$deviceid]);
        }
    } else {
        $modes = Util::getFormData('mode_select', array());
        foreach ($modes as $deviceid => $mode) {
            $devices[$deviceid]['MODE'] = $mode;
        }
        $data = array('DEVICE' => $devices);
        $result = $folder->setActiveSyncDeviceData($data, 'DEVICE');
        if (is_a($result, 'PEAR_Error')) {
            $notification->push(_("Error storing synchronization modes:")
                                . ' ' . $result->getMessage(),
                                'horde.error');
        } else {
            $notification->push(_("Synchronization modes stored successfully."),
                                'horde.success');
        }
    }
}

/* Show the header. */
require_once 'Horde/Prefs/UI.php';
$result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'horde');
if (!is_a($result, 'PEAR_Error')) {
    extract($result);
}
$app = 'horde';
$chunk = Util::nonInputVar('chunk');
Prefs_UI::generateHeader('activesync', $chunk);

require HORDE_TEMPLATES . '/activesync/activesync.inc';
if (!$chunk) {
    require HORDE_TEMPLATES . '/common-footer.inc';
}
