<?php
/**
 * Maintenance module that deletes old linked attachments.
 *
 * $Horde: imp/lib/Maintenance/Task/delete_attachments_monthly.php,v 1.4.10.6 2007-12-20 13:59:28 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Andrew Coleman <mercury@appisolutions.net>
 * @package Horde_Maintenance
 */
class Maintenance_Task_delete_attachments_monthly extends Maintenance_Task {

    /**
     * Purges the old linked attachment folders.
     *
     * @return boolean  Whether any old attachments were deleted.
     */
    function doMaintenance()
    {
        global $conf, $prefs;

        require_once IMP_BASE . '/lib/Compose.php';
        require_once 'Horde/Auth.php';
        require_once 'VFS.php';

        /* Find the UNIX timestamp of the last second that we will not
         * purge. */
        $del_time = gmmktime(0, 0, 0, date('n') - $prefs->getValue('delete_attachments_monthly_keep'), 1, date('Y'));

        $vfs = &VFS::singleton($conf['vfs']['type'], Horde::getDriverConfig('vfs', $conf['vfs']['type']));
        $path = IMP_VFS_LINK_ATTACH_PATH . '/' . Auth::getAuth();

        /* Make sure cleaning is done recursively. */
        $files = $vfs->listFolder($path, null, true, false, true);
        if (is_a($files, 'PEAR_Error') || !is_array($files)) {
            return false;
        }

        foreach ($files as $dir) {
            $filetime = (isset($dir['date'])) ? $dir['date'] : intval(basename($dir['name']));
            if ($del_time > $filetime) {
                $vfs->deleteFolder($path, $dir['name'], true);
            }
        }

        return true;
    }

    /**
     * Returns information for the maintenance function.
     *
     * @return string  Description of what the operation is going to do during
     *                 this login.
     */
    function describeMaintenance()
    {
        return sprintf(_("All old linked attachments more than %s months old will be deleted."), $GLOBALS['prefs']->getValue('delete_attachments_monthly_keep'));
    }

}
