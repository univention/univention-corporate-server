<?php
/**
 * $Horde: horde/services/snooze.php,v 1.2.2.3 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Alarm.php';

$alarm = Horde_Alarm::factory();
$id = Util::getPost('alarm');
$snooze = Util::getPost('snooze');

if ($id && $snooze) {
    if (is_a($result = $alarm->snooze($id, Auth::getAuth(), (int)$snooze), 'PEAR_Error')) {
        header('HTTP/1.0 500 ' . $result->getMessage());
        exit;
    }
} else {
    header('HTTP/1.0 400 Bad Request');
    exit;
}
