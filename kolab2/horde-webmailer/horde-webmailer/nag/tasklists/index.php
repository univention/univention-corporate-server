<?php
/**
 * $Horde: nag/tasklists/index.php,v 1.1.2.3 2009-01-06 15:25:09 jan Exp $
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

@define('NAG_BASE', dirname(dirname(__FILE__)));
require_once NAG_BASE . '/lib/base.php';
require_once 'Horde/RPC.php';
if (@include_once 'HTTP/WebDAV/Server.php') {
    require_once 'Horde/RPC/webdav.php';
}

/* Exit if this isn't an authenticated user. */
if (!Auth::getAuth()) {
    require NAG_BASE . '/list.php';
    exit;
}

$webdav = is_callable(array('HTTP_WebDAV_Server_Horde', 'DELETE'));
$edit_url_base = Horde::applicationUrl('tasklists/edit.php');
$perms_url_base = Horde::url($registry->get('webroot', 'horde') . '/services/shares/edit.php?app=nag', true);
$delete_url_base = Horde::applicationUrl('tasklists/delete.php');
$display_url_base = Horde::applicationUrl('list.php', true, -1);
$subscribe_url_base = $webdav ?
Horde::url($registry->get('webroot', 'horde') . '/rpc.php/nag/', true, -1) :
    Util::addParameter(Horde::applicationUrl('ics.php', true, -1), 't', '');

$tasklists = Nag::listTasklists(true);
$sorted_tasklists = array();
foreach ($tasklists as $tasklist) {
    $sorted_tasklists[$tasklist->getName()] = $tasklist->get('name');
}
asort($sorted_tasklists);

$edit_img = Horde::img('edit.png', _("Edit"), null, $registry->getImageDir('horde'));
$perms_img = Horde::img('perms.png', _("Change Permissions"), null, $registry->getImageDir('horde'));
$delete_img = Horde::img('delete.png', _("Delete"), null, $registry->getImageDir('horde'));

Horde::addScriptFile('popup.js', 'horde', true);
Horde::addScriptFile('tables.js', 'nag', true);
$title = _("Manage Task Lists");
require NAG_TEMPLATES . '/common-header.inc';
require NAG_TEMPLATES . '/menu.inc';
require NAG_TEMPLATES . '/tasklist_list.php';
require $registry->get('templates', 'horde') . '/common-footer.inc';
