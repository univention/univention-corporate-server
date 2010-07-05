<?php
/**
 * Implementation of the Quota API for IMAP servers with a unix quota command.
 * This requires a modified "quota" command that allows the httpd server
 * account to get quotas for other users. It also requires that your
 * web server and imap server be the same server or at least have shared
 * authentication and file servers (e.g. via NIS/NFS).  And last, it (as
 * written) requires the POSIX PHP extensions.
 *
 * You must configure this driver in horde/imp/config/servers.php.  The
 * driver supports the following parameters:
 *   'quota_path' => Path to the quota binary - REQUIRED
 *   'grep_path'  => Path to the grep binary - REQUIRED
 *   'partition'  => If all user mailboxes are on a single partition, the
 *                   partition label.  By default, quota will determine
 *                   quota information using the user's home directory value.
 *
 * $Horde: imp/lib/Quota/command.php,v 1.11.10.17 2009-01-06 15:24:11 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Eric Rostetter <eric.rostetter@physics.utexas.edu>
 * @package IMP_Quota
 */
class IMP_Quota_command extends IMP_Quota {

    /**
     * Constructor
     *
     * @param array $params  Hash containing connection parameters.
     */
    function IMP_Quota_command($params = array())
    {
        $params = array_merge(array('quota_path' => 'quota',
                                    'grep_path'  => 'grep',
                                    'partition'  => null),
                              $params);
        parent::IMP_Quota($params);
    }

    /**
     * Get the disk block size, if possible.
     *
     * We try to find out the disk block size from stat(). If not
     * available, stat() should return -1 for this value, in which
     * case we default to 1024 (for historical reasons). There are a
     * large number of reasons this may fail, such as OS support,
     * SELinux interference, the file being > 2 GB in size, the file
     * we're referring to not being readable, etc.
     */
    function blockSize()
    {
        $results = stat(__FILE__);
        if ($results['blksize'] > 1) {
            $blocksize = $results['blksize'];
        } else {
            $blocksize = 1024;
        }
        return $blocksize;
    }

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
        $imap_user = $_SESSION['imp']['user'];
        if (empty($this->_params['partition'])) {
            $passwd_array = posix_getpwnam($imap_user);
            list($junk, $search_string, $junk) = explode('/', $passwd_array['dir']);
        } else {
            $search_string = $this->_params['partition'];
        }
        $cmdline = $this->_params['quota_path'] . ' -u ' . $imap_user . ' | ' .
                   $this->_params['grep_path'] . ' ' . $search_string;
        exec($cmdline, $quota_data, $return_code);
        if (($return_code == 0) && (count($quota_data) == 1)) {
           $quota = split("[[:blank:]]+", trim($quota_data[0]));
           $blocksize = $this->blockSize();
           return array('usage' => $quota[1] * $blocksize,
                        'limit' => $quota[2] * $blocksize);
        }
        return PEAR::raiseError(_("Unable to retrieve quota"), 'horde.error');
    }

}
