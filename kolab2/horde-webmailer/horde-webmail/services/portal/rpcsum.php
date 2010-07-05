<?php
/**
 * $Horde: horde/services/portal/rpcsum.php,v 2.26.6.8 2009-01-06 15:27:33 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/RPC.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

$rpc_servers = @unserialize($prefs->getValue('remote_summaries'));
if (!is_array($rpc_servers)) {
    $rpc_servers = array();
}

$actionID = Util::getFormData('actionID');

// Handle clients without javascript.
if (is_null($actionID)) {
    if (Util::getPost('edit')) {
        $actionID = 'edit';
    } elseif (Util::getPost('save')) {
        $actionID = 'save';
    } elseif (Util::getPost('delete')) {
        $actionID = 'delete';
    }
}

/* Run through the action handlers */
switch ($actionID) {
case 'save':
    if (($to_edit = Util::getFormData('edit_server')) == null) {
        $to_edit = count($rpc_servers);
        $rpc_servers[] = array();
    }
    $rpc_servers[$to_edit]['url']    = Util::getFormData('url');
    $rpc_servers[$to_edit]['user']   = Util::getFormData('user');
    $rpc_servers[$to_edit]['passwd'] = Util::getFormData('passwd');
    $prefs->setValue('remote_summaries', serialize($rpc_servers));
    $prefs->store();
    $notification->push(sprintf(_("The server \"%s\" has been saved."), $rpc_servers[$to_edit]['url']), 'horde.success');
    break;

case 'delete':
    $to_delete = Util::getFormData('server');
    if ($to_delete != -1) {
        $deleted_server = $rpc_servers[$to_delete]['url'];
        $server_list = array();
        for ($i = 0; $i < count($rpc_servers); $i++) {
            if ($i == $to_delete) {
                continue;
            }
            $server_list[] = $rpc_servers[$i];
        }
        $prefs->setValue('remote_summaries', serialize($server_list));
        $chosenColumns = explode(';', $prefs->getValue('show_summaries'));
        if ($chosenColumns != array('')) {
            $newColumns = array();
            foreach ($chosenColumns as $chosenColumn) {
                $chosenColumn = explode(',', $chosenColumn);
                $remote = explode('|', $chosenColumn[0]);
                if (count($remote) != 3 || $remote[2] == $deleted_server) {
                    $newColumns[] = implode(',', $chosenColumn);
                }
            }
            $prefs->setValue('show_summaries', implode(';', $newColumns));
        }
        $prefs->store();
        $rpc_servers = $server_list;
        $notification->push(sprintf(_("The server \"%s\" has been deleted."), $deleted_server), 'horde.success');
    } else {
        $notification->push(_("You must select an server to be deleted."), 'horde.warning');
    }
    break;
}

/* Show the header. */
require_once 'Horde/Prefs/UI.php';
$result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'horde');
if (!is_a($result, 'PEAR_Error')) {
    extract($result);
}
$app = 'horde';
$chunk = Util::nonInputVar('chunk');
Prefs_UI::generateHeader('remote', $chunk);

require HORDE_TEMPLATES . '/rpcsum/rpcsum.inc';
if (!$chunk) {
    require HORDE_TEMPLATES . '/common-footer.inc';
}
