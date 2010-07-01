<?php
/**
 * $Horde: kronolith/calendars/edit.php,v 1.3.2.3 2009-01-06 15:24:44 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('KRONOLITH_BASE', dirname(dirname(__FILE__)));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once KRONOLITH_BASE . '/lib/Forms/EditCalendar.php';

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    header('Location: ' . Horde::applicationUrl($prefs->getValue('defaultview') . '.php', true));
    exit;
}

$vars = Variables::getDefaultVariables();
$calendar = $kronolith_shares->getShare($vars->get('c'));
if (is_a($calendar, 'PEAR_Error')) {
    $notification->push($calendar, 'horde.error');
    header('Location: ' . Horde::applicationUrl('calendars/', true));
    exit;
}
$form = new Kronolith_EditCalendarForm($vars, $calendar);

// Execute if the form is valid.
if ($form->validate($vars)) {
    $original_name = $calendar->get('name');
    $result = $form->execute();
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } else {
        if ($calendar->get('name') != $original_name) {
            $notification->push(sprintf(_("The calendar \"%s\" has been renamed to \"%s\"."), $original_name, $calendar->get('name')), 'horde.success');
        } else {
            $notification->push(sprintf(_("The calendar \"%s\" has been saved."), $original_name), 'horde.success');
        }
    }

    header('Location: ' . Horde::applicationUrl('calendars/', true));
    exit;
}

$vars->set('name', $calendar->get('name'));
$vars->set('description', $calendar->get('desc'));
$params = @unserialize($calendar->get('params'));
if (isset($params['fbrelevance'])) {
    $vars->set('fbrelevance', $params['fbrelevance']);
}
if (isset($params['activesync'])) {
    if ($params['activesync']['NAMESPACE'] == Horde_Kolab_Storage_Namespace::PERSONAL) {
        $default = 1;
    } else {
        $default = 0;
    }
    require_once 'Horde/Kolab/Storage.php';
    $folder = Kolab_Storage::getFolder('INBOX');
    $result = $folder->getActiveSync();
    $devices = isset($result['DEVICE']) ? $result['DEVICE'] : null;
    if (!empty($devices)) {
        $folders = $params['activesync']['FOLDER'];
        $vars->set('activesync_devices', implode('|', array_keys($devices)));
        foreach ($devices as $id => $config) {
            $vars->set('activesync_' . $id, isset($folders[$id]['S']) ? $folders[$id]['S'] : $default);
        }
        $form->activeSyncSegment($devices);
    }
}
$title = $form->getTitle();
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/menu.inc';
echo $form->renderActive($form->getRenderer(), $vars, 'edit.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
