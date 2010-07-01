<?php
/**
 * $Horde: turba/addressbooks/index.php,v 1.1.2.5 2009-01-06 15:27:41 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('TURBA_BASE', dirname(dirname(__FILE__)));
require_once TURBA_BASE . '/lib/base.php';

// Exit if this isn't an authenticated user, or if there's no source
// configured for shares.
if (!Auth::getAuth() || empty($_SESSION['turba']['has_share'])) {
    require TURBA_BASE . '/'
        . ($browse_source_count ? basename($prefs->getValue('initial_page')) : 'search.php');
    exit;
}

$browse_url_base = Horde::applicationUrl($browse_source_count ? basename($prefs->getValue('initial_page')) : 'search.php');
$edit_url_base = Horde::applicationUrl('addressbooks/edit.php');
$perms_url_base = Horde::url($registry->get('webroot', 'horde') . '/services/shares/edit.php?app=turba', true);
$delete_url_base = Horde::applicationUrl('addressbooks/delete.php');

// Get the shares owned by the current user, and figure out what we will
// display the share name as to the user.
$addressbooks = Turba::listShares(true);
$sorted_addressbooks = array();
foreach ($addressbooks as $addressbook) {
    if (!isset($cfgSources[$addressbook->getName()])) {
        continue;
    }
    $sorted_addressbooks[$addressbook->getName()] = $addressbook->get('name');
}
asort($sorted_addressbooks);

$browse_img = Horde::img('turba.png', _("Browse"), null, $registry->getImageDir('turba'));
$edit_img = Horde::img('edit.png', _("Edit"), null, $registry->getImageDir('horde'));
$perms_img = Horde::img('perms.png', _("Change Permissions"), null, $registry->getImageDir('horde'));
$delete_img = Horde::img('delete.png', _("Delete"), null, $registry->getImageDir('horde'));

Horde::addScriptFile('popup.js', 'horde', true);
Horde::addScriptFile('tables.js', 'turba', true);
$title = _("Manage Address Books");
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/menu.inc';
require TURBA_TEMPLATES . '/addressbook_list.php';
require $registry->get('templates', 'horde') . '/common-footer.inc';
