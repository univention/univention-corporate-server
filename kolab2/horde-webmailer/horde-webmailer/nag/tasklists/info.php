<?php
/**
 * $Horde: nag/tasklists/info.php,v 1.1.2.4 2009-01-06 15:25:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('NAG_BASE', dirname(dirname(__FILE__)));
require_once NAG_BASE . '/lib/base.php';
require_once 'Horde/Identity.php';
require_once 'Horde/RPC.php';
if (@include_once 'HTTP/WebDAV/Server.php') {
    require_once 'Horde/RPC/webdav.php';
}

// Exit if this isn't an authenticated user.
if (!Auth::getAuth()) {
    exit;
}

$tasklist = $nag_shares->getShare(Util::getFormData('t'));
if (is_a($tasklist, 'PEAR_Error')) {
    exit;
}

$webdav = is_callable(array('HTTP_WebDAV_Server_Horde', 'DELETE'));
$subscribe_url = $webdav ?
    Horde::url($registry->get('webroot', 'horde') . '/rpc.php/nag/', true, -1) . $tasklist->get('owner') . '/' . $tasklist->getName() . '.ics':
    Util::addParameter(Horde::applicationUrl('ics.php', true, -1), 't', $tasklist->getName());

$identity = &Identity::singleton('none', $tasklist->get('owner'));
$owner_name = $identity->getValue('fullname');
if (trim($owner_name) == '') {
    $owner_name = Auth::removeHook(Auth::getAuth());
}


require NAG_TEMPLATES . '/tasklist_info.php';
