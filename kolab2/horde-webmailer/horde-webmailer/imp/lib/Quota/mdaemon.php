<?php
/**
 * Implementation of the Quota API for MDaemon servers.
 *
 * Parameters required:
 *   'app_location'  --  TODO
 *
 * $Horde: imp/lib/Quota/mdaemon.php,v 1.11.10.12 2009-01-06 15:24:11 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package IMP_Quota
 */
class IMP_Quota_mdaemon extends IMP_Quota {

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
        $userDetails = $this->_getUserDetails($_SESSION['imp']['user'], $_SESSION['imp']['maildomain']);

        if ($userDetails !== false) {
            $userHome = trim(substr($userDetails, 105, 90));
            $total = intval(substr($userDetails, 229, 6)) * 1024;

            if ($total == 0) {
                return array('usage' => 0, 'limit' => 0);
            }

            if (($taken = $this->_mailboxSize($userHome)) !== false) {
                return array('usage' => $taken, 'limit' => $total);
            }
        }

        return PEAR::raiseError(_("Unable to retrieve quota"), 'horde.error');
    }

    /**
     * Get the size of a mailbox
     *
     * @access private
     *
     * @param string $path  The full path of the mailbox to fetch the quota
     *                     for including trailing backslash.
     *
     * @return mixed  The number of bytes in the mailbox (integer) or false
     *                (boolean) on error.
     */
    function _mailboxSize($path)
    {
        $contents = file_get_contents($path . '\imap.mrk');

        $pointer = 36;
        $size = 0;
        while ($pointer < strlen($contents)) {
            $details = unpack('a17Filename/a11Crap/VSize', substr($contents, $pointer, 36));
            $size += $details['Size'];
            $pointer += 36;
        }

        /* Recursivly check subfolders. */
        $d = dir($path);
        while (($entry = $d->read()) !== false) {
            if (($entry != '.') &&
                ($entry != '..') &&
                (substr($entry, -5, 5) == '.IMAP')) {
                $size += $this->_mailboxSize($path . $entry . '\\');
            }
        }
        $d->close();

        return $size;
    }

    /**
     * Retrieve relevant line from userlist.dat.
     *
     * @param string $user   The username for which to retrieve detals.
     * @param string $realm  The realm (domain) for the user.
     *
     * @return mixed  Line from userlist.dat (string) or false (boolean).
     */
    function _getUserDetails($user, $realm)
    {
        $searchString = str_pad($realm, 45) . str_pad($user, 30);

        if (!($fp = fopen($this->_params['app_location'] . '/userlist.dat', 'rb'))) {
            return false;
        }

        while (!feof($fp)) {
            $line = fgets($fp, 4096);
            if (substr($line, 0, strlen($searchString)) == $searchString) {
                fclose($fp);
                return $line;
            }
        }
        fclose($fp);

        return false;
    }

}
