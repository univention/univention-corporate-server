<?php
/**
 * $Horde: imp/lib/Maintenance/Task/purge_trash.php,v 1.23.10.13 2009-01-06 15:24:10 jan Exp $
 *
 * Maintenance module that purges old messages in the Trash folder.
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_Maintenance
 */
class Maintenance_Task_purge_trash extends Maintenance_Task {

    /**
     * Purge old messages in the Trash folder.
     *
     * @return boolean  Whether any messages were purged from the Trash folder.
     */
    function doMaintenance()
    {
        global $prefs, $notification;

        /* If we aren't using a Trash folder or if there is no Trash
           folder set, just return. */
        $trash_folder = IMP::folderPref($prefs->getValue('trash_folder'), true);
        if (!$prefs->getValue('use_trash') || !$trash_folder) {
            return false;
        }

        /* Make sure the Trash folder exists. */
        require_once IMP_BASE . '/lib/Folder.php';
        $imp_folder = &IMP_Folder::singleton();
        if (!$imp_folder->exists($trash_folder)) {
            return false;
        }

        /* Get the current UNIX timestamp minus the number of days
           specified in 'purge_trash_keep'.  If a message has a
           timestamp prior to this value, it will be deleted. */
        $del_time = date("r", time() - ($prefs->getValue('purge_trash_keep') * 86400));

        /* Open the Trash mailbox and get the list of messages older
           than 'purge_trash_keep' days. */
        require_once IMP_BASE . '/lib/Message.php';
        $imp_imap = &IMP_IMAP::singleton();
        $imp_message = &IMP_Message::singleton();
        $imp_imap->changeMbox($trash_folder, IMP_IMAP_AUTO);
        $msg_ids = @imap_search($imp_imap->stream(), "BEFORE \"$del_time\"", SE_UID);
        if (empty($msg_ids)) {
            return false;
        }

        /* Go through the message list and delete the messages. */
        $indices = array($trash_folder => $msg_ids);
        if ($imp_message->delete($indices, true)) {
            $msgcount = count($msg_ids);
            if ($msgcount == 1) {
                $notification->push(_("Purging 1 message from Trash folder."), 'horde.message');
            } else {
                $notification->push(sprintf(_("Purging %d messages from Trash folder."), $msgcount), 'horde.message');
            }
        }

        return true;
    }

    /**
     * Return information for the maintenance function.
     *
     * @return string  Description of what the operation is going to do during
     *                 this login.
     */
    function describeMaintenance()
    {
        return sprintf(_("All messages in your \"%s\" folder older than %s days will be permanently deleted."),
                       IMP::displayFolder(IMP::folderPref($GLOBALS['prefs']->getValue('trash_folder'), true)),
                       $GLOBALS['prefs']->getValue('purge_trash_keep'));
    }

}
