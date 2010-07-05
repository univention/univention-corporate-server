<?php
/**
 * $Horde: mnemo/notepads/edit.php,v 1.2.2.3 2009-01-06 15:25:00 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('MNEMO_BASE', dirname(dirname(__FILE__)));
require_once MNEMO_BASE . '/lib/base.php';
require_once MNEMO_BASE . '/lib/Forms/EditNotepad.php';

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

$vars = Variables::getDefaultVariables();
$notepad = $mnemo_shares->getShare($vars->get('n'));
if (is_a($notepad, 'PEAR_Error')) {
    $notification->push($notepad, 'horde.error');
    header('Location: ' . Horde::applicationUrl('notepads/', true));
    exit;
}
$form = new Mnemo_EditNotepadForm($vars, $notepad);

// Execute if the form is valid.
if ($form->validate($vars)) {
    $original_name = $notepad->get('name');
    $result = $form->execute();
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } else {
        if ($notepad->get('name') != $original_name) {
            $notification->push(sprintf(_("The notepad \"%s\" has been renamed to \"%s\"."), $original_name, $notepad->get('name')), 'horde.success');
        } else {
            $notification->push(sprintf(_("The notepad \"%s\" has been saved."), $original_name), 'horde.success');
        }
    }

    header('Location: ' . Horde::applicationUrl('notepads/', true));
    exit;
}

$vars->set('name', $notepad->get('name'));
$vars->set('description', $notepad->get('desc'));

$params = @unserialize($notepad->get('params'));
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
require MNEMO_TEMPLATES . '/common-header.inc';
require MNEMO_TEMPLATES . '/menu.inc';
echo $form->renderActive($form->getRenderer(), $vars, 'edit.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
