<?php
/**
 * $Horde: turba/addressbooks/edit.php,v 1.1.2.3 2009-01-06 15:27:41 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('TURBA_BASE', dirname(dirname(__FILE__)));
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Forms/EditAddressBook.php';

// Exit if this isn't an authenticated user, or if there's no source
// configured for shares.
if (!Auth::getAuth() || empty($_SESSION['turba']['has_share'])) {
    require TURBA_BASE . '/'
        . ($browse_source_count ? basename($prefs->getValue('initial_page')) : 'search.php');
    exit;
}

$vars = Variables::getDefaultVariables();
$addressbook = $turba_shares->getShare($vars->get('a'));
if (is_a($addressbook, 'PEAR_Error')) {
    $notification->push($addressbook, 'horde.error');
    header('Location: ' . Horde::applicationUrl('addressbooks/', true));
    exit;
}
$form = new Turba_EditAddressBookForm($vars, $addressbook);

// Execute if the form is valid.
if ($form->validate($vars)) {
    $original_name = $addressbook->get('name');
    $result = $form->execute();
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } else {
        if ($addressbook->get('name') != $original_name) {
            $notification->push(sprintf(_("The addressbook \"%s\" has been renamed to \"%s\"."), $original_name, $addressbook->get('name')), 'horde.success');
        } else {
            $notification->push(sprintf(_("The addressbook \"%s\" has been saved."), $original_name), 'horde.success');
        }
    }

    header('Location: ' . Horde::applicationUrl('addressbooks/', true));
    exit;
}

$vars->set('name', $addressbook->get('name'));
$vars->set('description', $addressbook->get('desc'));

$params = @unserialize($addressbook->get('params'));
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
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/menu.inc';
echo $form->renderActive($form->getRenderer(), $vars, 'edit.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
