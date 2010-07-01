<?php
/**
 * Maintenance module that deletes old sent-mail folders.
 *
 * $Horde: imp/lib/Maintenance/Task/delete_sentmail_monthly.php,v 1.18.10.12 2009-01-06 15:24:10 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_Maintenance
 */
class Maintenance_Task_delete_sentmail_monthly extends Maintenance_Task {

    /**
     * Purge the old sent-mail folders.
     *
     * @return boolean  Whether any sent-mail folders were deleted.
     */
    function doMaintenance()
    {
        global $notification, $prefs;

        /* Get list of all folders, parse through and get the list of all
           old sent-mail folders. Then sort this array according to
           the date. */
        include_once 'Horde/Identity.php';
        include_once IMP_BASE . '/lib/Folder.php';

        $identity = &Identity::singleton(array('imp', 'imp'));
        $imp_folder = &IMP_Folder::singleton();
        $sent_mail_folders = $identity->getAllSentmailFolders();

        $folder_array = array();
        $old_folders = $imp_folder->flist();

        foreach (array_keys($old_folders) as $k) {
            foreach ($sent_mail_folders as $folder) {
                if (preg_match('/^' . str_replace('/', '\/', $folder) . '-([^-]+)-([0-9]{4})$/i', $k, $regs)) {
                    $folder_array[$k] = String::convertCharset((is_numeric($regs[1])) ? mktime(0, 0, 0,$regs[1], 1, $regs[2]) : strtotime("$regs[1] 1, $regs[2]"), NLS::getCharset(), 'UTF7-IMAP');
                }
            }
        }
        arsort($folder_array, SORT_NUMERIC);

        /* See if any folders need to be purged. */
        $purge_folders = array_slice(array_keys($folder_array), $prefs->getValue('delete_sentmail_monthly_keep'));
        if (count($purge_folders)) {
            $notification->push(_("Old sent-mail folders being purged."), 'horde.message');

            /* Delete the old folders now. */
            if ($imp_folder->delete($purge_folders, true)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Return information for the maintenance function.
     *
     * @return string  Description of what the operation is going to do during
     *                 this login.
     */
    function describeMaintenance()
    {
        global $prefs;

        return sprintf(_("All old sent-mail folders more than %s months old will be deleted."), $prefs->getValue('delete_sentmail_monthly_keep'));
    }

}
