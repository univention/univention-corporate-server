<?php
/**
 * $Horde: imp/lib/Maintenance/Task/purge_spam.php,v 1.6.2.3 2009-01-06 15:24:10 jan Exp $
 *
 * Maintenance module that purges old messages in the Spam folder.  Based on
 * the purge_trash task, written by Michael Slusarz <slusarz@horde.org>.
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Matt Selsky <selsky@columbia.edu>
 * @since   IMP 4.2
 * @package Horde_Maintenance
 */
class Maintenance_Task_purge_spam extends Maintenance_Task {

    /**
     * Purge old messages in the Spam folder.
     *
     * @return boolean  Whether any messages were purged from the Spam folder.
     */
    function doMaintenance()
    {
        global $prefs, $notification;

        /* If there is no Spam folder set, just return. */
        $spam_folder = IMP::folderPref($prefs->getValue('spam_folder'), true);
        if (!$spam_folder) {
            return false;
        }

        /* Make sure the Spam folder exists. */
        require_once IMP_BASE . '/lib/Folder.php';
        $imp_folder = &IMP_Folder::singleton();
        if (!$imp_folder->exists($spam_folder)) {
            return false;
        }

        /* Get the current UNIX timestamp minus the number of days
           specified in 'purge_spam_keep'.  If a message has a
           timestamp prior to this value, it will be deleted. */
        $del_time = date("r", time() - ($prefs->getValue('purge_spam_keep') * 86400));

        /* Open the Spam mailbox and get the list of messages older
           than 'purge_spam_keep' days. */
        require_once IMP_BASE . '/lib/Message.php';
        $imp_imap = &IMP_IMAP::singleton();
        $imp_message = &IMP_Message::singleton();
        $imp_imap->changeMbox($spam_folder, IMP_IMAP_AUTO);
        $msg_ids = @imap_search($imp_imap->stream(), "BEFORE \"$del_time\"", SE_UID);
        if (empty($msg_ids)) {
            return false;
        }

        /* Go through the message list and delete the messages. */
        $indices = array($spam_folder => $msg_ids);
        if ($imp_message->delete($indices, true)) {
            $msgcount = count($msg_ids);
            if ($msgcount == 1) {
                $notification->push(_("Purging 1 message from Spam folder."), 'horde.message');
            } else {
                $notification->push(sprintf(_("Purging %d messages from Spam folder."), $msgcount), 'horde.message');
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
                       IMP::displayFolder(IMP::folderPref($GLOBALS['prefs']->getValue('spam_folder'), true)),
                       $GLOBALS['prefs']->getValue('purge_spam_keep'));
    }

}
