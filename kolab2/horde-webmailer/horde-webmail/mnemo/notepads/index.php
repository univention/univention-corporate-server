<?php
/**
 * $Horde: mnemo/notepads/index.php,v 1.1.2.3 2009-01-06 15:25:00 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('MNEMO_BASE', dirname(dirname(__FILE__)));
require_once MNEMO_BASE . '/lib/base.php';

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    require MNEMO_BASE . '/list.php';
    exit;
}

$edit_url_base = Horde::applicationUrl('notepads/edit.php');
$perms_url_base = Horde::url($registry->get('webroot', 'horde') . '/services/shares/edit.php?app=mnemo', true);
$delete_url_base = Horde::applicationUrl('notepads/delete.php');

$notepads = Mnemo::listNotepads(true);
$sorted_notepads = array();
foreach ($notepads as $notepad) {
    $sorted_notepads[$notepad->getName()] = $notepad->get('name');
}
asort($sorted_notepads);

$edit_img = Horde::img('edit.png', _("Edit"), null, $registry->getImageDir('horde'));
$perms_img = Horde::img('perms.png', _("Change Permissions"), null, $registry->getImageDir('horde'));
$delete_img = Horde::img('delete.png', _("Delete"), null, $registry->getImageDir('horde'));

Horde::addScriptFile('popup.js', 'horde', true);
Horde::addScriptFile('tables.js', 'mnemo', true);
$title = _("Manage Notepads");
require MNEMO_TEMPLATES . '/common-header.inc';
require MNEMO_TEMPLATES . '/menu.inc';
require MNEMO_TEMPLATES . '/notepad_list.php';
require $registry->get('templates', 'horde') . '/common-footer.inc';
