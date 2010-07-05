<?php
/**
 * Implementation of the Quota API for Mercury/32 IMAP servers.
 * For reading Quota, read size folder user.
 *
 * Requires the following parameter settings in imp/servers.php:
 * 'quota' => array(
 *     'driver' => 'mercury32',
 *     'params' => array(
 *         'mail_user_folder' => 'c:/mercry/mail'
 *     )
 * );
 *
 * 'mail_user_folder' --  The path to folder mail mercury
 *
 *****************************************************************************
 * PROBLEM TO ACCESS NETWORK DIRECOTRY
 *****************************************************************************
 * Matt Grimm
 * 06-Jun-2003 10:25
 *
 * Thought I could help clarify something with accessing network shares on a
 * Windows network (2000 in this case), running PHP 4.3.2 under Apache 2.0.44.
 * However you are logged into the Windows box, your Apache service must be
 * running under an account which has access to the share.  The easiest (and
 * probably least safe) way for me was to change the user for the Apache
 * service to the computer administrator (do this in the service properties,
 * under the "Log On" tab).  After restarting Apache, I could access mapped
 * drives by their assigned drive letter ("z:\\") or regular shares by their
 * UNC path ("\\\\shareDrive\\shareDir").
 *****************************************************************************
 *
 * $Horde: imp/lib/Quota/mercury32.php,v 1.1.10.12 2009-01-06 15:24:11 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Frank Lupo <frank_lupo@email.it>
 * @package IMP_Quota
 */
class IMP_Quota_mercury32 extends IMP_Quota {

    /**
     * Get quota information (used/allocated), in bytes.
     *
     * @return mixed  An associative array.
     *                'limit' = Maximum quota allowed
     *                'usage' = Currently used portion of quota (in bytes)
     *                Returns PEAR_Error on failure.
     */
    function getQuota()
    {
        $quota = null;

        $dir_path = $this->_params['mail_user_folder'] . '/' . $_SESSION['imp']['user'] . '/';
        if ($dir = @opendir($dir_path)) {
            while (($file = readdir($dir)) !== false) {
                $quota += filesize($dir_path . $file);
            }
            closedir($dir);

            if ($quota !== null) {
                return array('usage' => $quota, 'limit' => 0);
            }
        }
        return PEAR::raiseError(_("Unable to retrieve quota"), 'horde.error');
    }

}
