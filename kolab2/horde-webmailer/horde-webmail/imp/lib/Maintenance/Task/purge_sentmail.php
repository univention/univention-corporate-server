<?php
/**
 * $Horde: imp/lib/Maintenance/Task/purge_sentmail.php,v 1.9.2.3 2009-01-06 15:24:10 jan Exp $
 *
 * Maintenance module that purges old messages in the sent-mail folder.
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   IMP 4.2
 * @package Horde_Maintenance
 */
class Maintenance_Task_purge_sentmail extends Maintenance_Task {

    /**
     * Purge old messages in the sent-mail folder.
     *
     * @return boolean  Whether any messages were purged from the sent-mail
     *                  folder.
     */
    function doMaintenance()
    {
        global $prefs, $notification;

        require_once IMP_BASE . '/lib/Folder.php';
        require_once IMP_BASE . '/lib/Message.php';
        $imp_folder = &IMP_Folder::singleton();
        $imp_imap = &IMP_IMAP::singleton();
        $imp_message = &IMP_Message::singleton();

        $folder_list = Maintenance_Task_purge_sentmail::_getFolders();

        /* Get the current UNIX timestamp minus the number of days specified
         * in 'purge_sentmail_keep'.  If a message has a timestamp prior to
         * this value, it will be deleted. */
        $del_time = date('r', time() - ($prefs->getValue('purge_sentmail_keep') * 86400));

        foreach ($folder_list as $sentmail_folder) {
            /* Make sure the sent-mail folder exists. */
            if (!$imp_folder->exists($sentmail_folder)) {
                continue;
            }

            /* Open the sent-mail mailbox and get the list of messages older
             * than 'purge_sentmail_keep' days. */
            $imp_imap->changeMbox($sentmail_folder, IMP_IMAP_AUTO);
            $msg_ids = @imap_search($imp_imap->stream(), "BEFORE \"$del_time\"", SE_UID);
            if (empty($msg_ids)) {
                continue;
            }

            /* Go through the message list and delete the messages. */
            $indices = array($sentmail_folder => $msg_ids);
            if ($imp_message->delete($indices, true)) {
                $msgcount = count($msg_ids);
                if ($msgcount == 1) {
                    $notification->push(sprintf(_("Purging 1 message from sent-mail folder %s."), IMP::displayFolder($sentmail_folder)), 'horde.message');
                } else {
                    $notification->push(sprintf(_("Purging %d messages from sent-mail folder."), $msgcount, IMP::displayFolder($sentmail_folder)), 'horde.message');
                }
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
        $folder_list = array_map(array('IMP', 'displayFolder'),
                                 Maintenance_Task_purge_sentmail::_getFolders());

        return sprintf(_("All messages in the folder(s) \"%s\" older than %s days will be permanently deleted."),
                       implode(', ', $folder_list),
                       $GLOBALS['prefs']->getValue('purge_sentmail_keep'));
    }

    /**
     * Returns the list of sent-mail folders.
     *
     * @return array  All sent-mail folders.
     */
    function _getFolders()
    {
        include_once 'Horde/Identity.php';
        $identity = &Identity::singleton(array('imp', 'imp'));
        return $identity->getAllSentmailfolders();
    }

}
