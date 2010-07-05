<?php
/**
 * $Horde: kronolith/calendars/index.php,v 1.1.2.4 2009-01-06 15:24:44 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

/**
 * Show just the beginning and end of long URLs.
 */
function shorten_url($url, $separator = '...', $first_chunk_length = 35, $last_chunk_length = 15)
{
    $url_length = strlen($url);
    $max_length = $first_chunk_length + strlen($separator) + $last_chunk_length;

    if ($url_length > $max_length) {
        return substr_replace($url, $separator, $first_chunk_length, -$last_chunk_length);
    }

    return $url;
}

@define('KRONOLITH_BASE', dirname(dirname(__FILE__)));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/RPC.php';
if (@include_once 'HTTP/WebDAV/Server.php') {
    require_once 'Horde/RPC/webdav.php';
}

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    header('Location: ' . Horde::applicationUrl($prefs->getValue('defaultview') . '.php'));
    exit;
}

$webdav = is_callable(array('HTTP_WebDAV_Server_Horde', 'DELETE'));
$rewrite = isset($conf['urls']['pretty']) &&
    $conf['urls']['pretty'] == 'rewrite';
$edit_url_base = Horde::applicationUrl('calendars/edit.php');
$remote_edit_url_base = Horde::applicationUrl('calendars/remote_edit.php');
$delete_url_base = Horde::applicationUrl('calendars/delete.php');
$remote_unsubscribe_url_base = Horde::applicationUrl('calendars/remote_unsubscribe.php');
$perms_url_base = Horde::applicationUrl('perms.php', true);
$display_url_base = Horde::applicationUrl('month.php', true, -1);
$subscribe_url_base = $webdav ?
    Horde::url($registry->get('webroot', 'horde')
               . ($rewrite ? '/rpc/kronolith/' : '/rpc.php/kronolith/'),
               true, -1) :
    Util::addParameter(Horde::applicationUrl('ics.php', true, -1), 'c', '');

$calendars = array();
$sorted_calendars = array();
$my_calendars = Kronolith::listCalendars(true);
foreach ($my_calendars as $calendar) {
    $calendars[$calendar->getName()] = $calendar;
    $sorted_calendars[$calendar->getName()] = $calendar->get('name');
}
$remote_calendars = unserialize($prefs->getValue('remote_cals'));
foreach ($remote_calendars as $calendar) {
    $calendars[$calendar['url']] = $calendar;
    $sorted_calendars[$calendar['url']] = $calendar['name'];
}
asort($sorted_calendars);

$edit_img = Horde::img('edit.png', _("Edit"), null, $registry->getImageDir('horde'));
$perms_img = Horde::img('perms.png', _("Change Permissions"), null, $registry->getImageDir('horde'));
$delete_img = Horde::img('delete.png', _("Delete"), null, $registry->getImageDir('horde'));

Horde::addScriptFile('popup.js', 'horde', true);
Horde::addScriptFile('tables.js', 'kronolith', true);
$title = _("Manage Calendars");
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/menu.inc';
require KRONOLITH_TEMPLATES . '/calendar_list.php';
require $registry->get('templates', 'horde') . '/common-footer.inc';
