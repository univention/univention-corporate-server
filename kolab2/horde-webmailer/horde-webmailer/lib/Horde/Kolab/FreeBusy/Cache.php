<?php
/**
 * Caching for the Kolab free/busy data.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * @package Kolab_FreeBusy
 */

/** We require the iCalendar library to build the free/busy list */
require_once 'Horde/iCalendar.php';
require_once 'Horde/iCalendar/vfreebusy.php';

/**
 * The Horde_Kolab_FreeBusy_Cache:: class provides functionality to store
 * prepared free/busy data for quick retrieval.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache {

    /**
     * The directory that should be used for caching.
     *
     * @var string
     */
    var $_cache_dir;

    /**
     * Constructor.
     *
     * @param string  $cache_dir  The cache directory we should use.
     */
    function Horde_Kolab_FreeBusy_Cache($cache_dir)
    {
        $this->_cache_dir = $cache_dir;
    }

    /**
     * Update the cache information for a calendar.
     *
     * @param Horde_Kolab_FreeBusy_Access $access The object holding the
     *                                      relevant access
     *                                      parameters.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function store($access)
    {
        global $conf;

        /* Now we really need the free/busy library */
        require_once 'Horde/Kolab/FreeBusy/Imap.php';

        $fb = &new Horde_Kolab_FreeBusy_Imap();

        $result = $fb->connect($access->imap_folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $fbpast = $fbfuture = null;
        if (!empty($access->server_object)) {
            $result = $access->server_object->get(KOLAB_ATTR_FBPAST);
            if (!is_a($result, 'PEAR_Error')) {
                $fbpast = $result;
            }
        }
        if (!empty($access->owner_object)) {
            $result = $access->owner_object->get(KOLAB_ATTR_FBFUTURE);
            if (!is_a($result, 'PEAR_Error')) {
                $fbfuture = $result;
            }
        }

        $vCal = $fb->generate(null, null,
                              !empty($fbpast)?$fbpast:0,
                              !empty($fbfuture)?$fbfuture:60,
                              $access->owner,
                              $access->owner_object->get(KOLAB_ATTR_CN));
        if (is_a($vCal, 'PEAR_Error')) {
            $vCal;
        }

        $fbfilename = $this->_getFilename($access->folder, $access->owner);

        $c_pvcal = &new Horde_Kolab_FreeBusy_Cache_File_pvcal($this->_cache_dir, $fbfilename);

        if (!empty($conf['fb']['use_acls'])) {
            $c_acl   = &new Horde_Kolab_FreeBusy_Cache_File_acl($this->_cache_dir, $fbfilename);
            $c_xacl  = &new Horde_Kolab_FreeBusy_Cache_File_xacl($this->_cache_dir, $fbfilename);
        }

        /* missing data means delete the cache files */
        if (empty($vCal)) {
            Horde::logMessage(sprintf("No events. Purging cache %s.",
                                      $fbfilename),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $result = $c_pvcal->purge();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!empty($conf['fb']['use_acls'])) {
            $result = $c_acl->purge();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $result = $c_xacl->purge();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            }
        } else {
            $result = $c_pvcal->storePVcal($vCal);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $relevance = $fb->getRelevance();
            if (is_a($relevance, 'PEAR_Error')) {
                return $relevance;
            }

            if (!empty($conf['fb']['use_acls'])) {
                $acl = $fb->getACL();
                if (is_a($acl, 'PEAR_Error')) {
                    return $acl;
                }

                /** 
                 * Only store the acl information if the current user
                 * has admin rights on the folder and can actually
                 * retrieve the full ACL information.
                 *
                 * A folder that does not have admin rights for a user
                 * will not be considered relvant for that user unless
                 * it has been triggered by the folder owner before.
                 */
                $append = false;
                if (isset($acl[$access->user])) {
                    $myacl = $acl[$access->user];
                    if (strpos($myacl, 'a') !== false) {
                        $append = true;
                    }
                }

                $result = $c_acl->storeACL($acl, $relevance, $append);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                $xacl = $fb->getExtendedACL();
                if (is_a($xacl, 'PEAR_Error')) {
                    return $xacl;
                }

                $result = $c_xacl->storeXACL($xacl, $acl);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            } else {
                $acl = null;
            }

            Horde::logMessage(sprintf("Horde_Kolab_FreeBusy_Cache::store(file=%s, relevance=%s, acl=%s, xacl=%s)",
                                      $fbfilename, $relevance, $acl, $xacl),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }
        return true;
    }

    /**
     * Load partial free/busy data.
     *
     * @param Horde_Kolab_FreeBusy_Access $access   The object holding the
     *                                        relevant access
     *                                        parameters.
     * @param boolean               $extended Should the data hold the extended
     *                                        free/busy information?
     *
     * @return Horde_iCalendar|PEAR_Error The free/busy data of a
     *                                    single calendar.
     */
    function &loadPartial(&$access, $extended)
    {
        global $conf;

        $file = $this->_getFilename($access->folder, $access->owner);

        if (!empty($conf['fb']['use_acls'])) {
            $aclcache = &Horde_Kolab_FreeBusy_Cache_DB_acl::singleton('acl',
                                                                      $this->_cache_dir);
            if ($extended) {
                $extended = $this->_allowExtended($file, $access);
            }
        }

        $c_pvcal = &new Horde_Kolab_FreeBusy_Cache_File_pvcal($this->_cache_dir, $file);
        $pvCal = $c_pvcal->loadPVcal($extended);
        if (is_a($pvCal, 'PEAR_Error')) {
            return $pvCal;
        }
        return $pvCal;
    }

    /**
     * Load the complete free/busy data of a user.
     *
     * @param Horde_Kolab_FreeBusy_Access $access   The object holding the
     *                                        relevant access
     *                                        parameters.
     * @param boolean               $extended Should the data hold the extended
     *                                        free/busy information?
     *
     * @return Horde_iCalendar|PEAR_Error The free/busy data for a user.
     */
    function &load(&$access, $extended)
    {
        global $conf;

        /* Which files will we access? */
        if (!empty($conf['fb']['use_acls'])) {
            $aclcache = &Horde_Kolab_FreeBusy_Cache_DB_acl::singleton('acl', $this->_cache_dir);
            $files = $aclcache->get($access->owner);
            if (is_a($files, 'PEAR_Error')) {
                return $files;
            }
        } else {
            $file_uid = str_replace("\0", '', str_replace(".", "^", $access->owner));
            $files = array();
            $this->findAll_readdir($file_uid, $conf['fb']['cache_dir'].'/'.$file_uid, $files);
        }

        $owner = $access->owner;
        if (ereg('(.*)@(.*)', $owner, $regs)) {
            $owner = $regs[2] . '/' . $regs[1];
        }
        $user = $access->user;
        if (ereg('(.*)@(.*)', $user, $regs)) {
            $user = $regs[2] . '/' . $regs[1];
        }
        $c_file = str_replace("\0", '', str_replace('.', '^', $user . '/' . $owner));

        $c_vcal = &new Horde_Kolab_FreeBusy_Cache_File_vcal($this->_cache_dir,
							    $c_file, $extended);

        /* If the current vCal cache did not expire, we can deliver it */
        if (!$c_vcal->expired($files)) {
            return $c_vcal->loadVcal();
        }

        // Create the new iCalendar.
        $vCal = &new Horde_iCalendar();
        $vCal->setAttribute('PRODID', '-//kolab.org//NONSGML Kolab Server 2//EN');
        $vCal->setAttribute('METHOD', 'PUBLISH');

        // Create new vFreebusy.
        $vFb = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        $params = array();

        $cn = $access->owner_object->get(KOLAB_ATTR_CN);
        if (!empty($cn) || is_a($cn, 'PEAR_Error')) {
            $params['cn'] = $access->owner_object->get(KOLAB_ATTR_CN);
        }
        $vFb->setAttribute('ORGANIZER', 'MAILTO:' . $access->owner, $params);

        $vFb->setAttribute('DTSTAMP', time());
        if (isset($_SERVER['SERVER_NAME'])) {
            $host = $_SERVER['SERVER_NAME'];
        } else {
            $host = 'localhost';
        }
        if (isset($_SERVER['REQUEST_URI'])) {
            $uri = $_SERVER['REQUEST_URI'];
        } else {
            $uri = '/';
        }
        $vFb->setAttribute('URL', 'http://' . $host . $uri);

        $mtimes = array();
        foreach ($files as $file) {
            if ($extended && !empty($conf['fb']['use_acls'])) {
                $extended_pvc = $this->_allowExtended($file, $access);
            } else {
                $extended_pvc = $extended;
            }
            $c_pvcal = &new Horde_Kolab_FreeBusy_Cache_File_pvcal($this->_cache_dir, $file);
            $pvCal = $c_pvcal->loadPVcal($extended_pvc);
            if (is_a($pvCal, 'PEAR_Error')) {
                Horde::logMessage(sprintf("Ignoring partial free/busy file %s: %s)",
                                          $file, $pvCal->getMessage()),
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
                continue;
            }
            $pvFb = &$pvCal->findComponent('vfreebusy');
            if( !$pvFb ) {
                Horde::logMessage(sprintf("Could not find free/busy info in file %s.)",
                                          $file), __FILE__, __LINE__, PEAR_LOG_INFO);
                continue;
            }
            if ($ets = $pvFb->getAttributeDefault('DTEND', false) !== false) {
                // PENDING(steffen): Make value configurable
                if ($ets < time()) {
                    Horde::logMessage(sprintf("Free/busy info in file %s is too old.)",
                                              $file), __FILE__, __LINE__, PEAR_LOG_INFO);
                    $c_pvcal->purge();
                    continue;
                }
            }
            $vFb->merge($pvFb);

            /* Store last modification time */
            $mtimes[$file] = array($c_pvcal->getFile(), $c_pvcal->getMtime());
        }

        if (!empty($conf['fb']['remote_servers'])) {
            $remote_vfb = $this->_fetchRemote($conf['fb']['remote_servers'],
                                              $access);
            if (is_a($remote_vfb, 'PEAR_Error')) {
                Horde::logMessage(sprintf("Ignoring remote free/busy files: %s)",
                                          $remote_vfb->getMessage()),
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
            } else {
                $vFb->merge($remote_vfb);
            }
        }

        if (!(boolean)$vFb->getBusyPeriods()) {
            /* No busy periods in fb list. We have to add a
             * dummy one to be standards compliant
             */
            $vFb->setAttribute('COMMENT', 'This is a dummy vfreebusy that indicates an empty calendar');
            $vFb->addBusyPeriod('BUSY', 0,0, null);
        }

        $vCal->addComponent($vFb);

        $c_vcal->storeVcal($vCal, $mtimes);

        return $vCal;
    }

    /**
     * Is extended access to the given file allowed?
     *
     * @param string                $file     Name of the cache file.
     * @param Horde_Kolab_FreeBusy_Access $access   The object holding the
     *                                        relevant access
     *                                        parameters.
     *
     * @return boolean|PEAR_Error True if extended access is allowed.
     */
    function _allowExtended($file, &$access)
    {
        if (!isset($access->user_object)) {
            Horde::logMessage(sprintf("Extended attributes on folder %s disallowed for unknown user.",
                                      $access->folder, $access->user), __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return false;
        }

        $xaclcache = &Horde_Kolab_FreeBusy_Cache_DB_xacl::singleton('xacl', $this->_cache_dir);

        /* Check if the calling user has access to the extended information of
         * the folder we are about to integrate into the free/busy data.
         */
        $groups = $access->user_object->getGroupAddresses();
        if (is_a($groups, 'PEAR_Error')) {
            return $groups;
        }

        $groups[] = $access->user;
        foreach ($groups as $id) {
            if ($xaclcache->has($file, $id)) {
                return true;
            }
        }
        Horde::logMessage(sprintf("Extended attributes on folder %s disallowed for user %s.",
                                  $access->folder, $access->user), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return false;
    }

    /**
     * Get a cache file name depending on the owner of the free/busy
     * data.
     *
     * @param string  $folder  Name of the calendar folder.
     * @param string  $owner   Owner of the calendar folder.
     *
     * @return string Name of the correspoding cache file.
     */
    function _getFilename($folder, $owner)
    {
        if (ereg('(.*)@(.*)', $owner, $regs)) {
            $owner = $regs[2] . '/' . $regs[1];
        }

        return str_replace("\0", '', str_replace('.', '^', $owner . '/' . $folder));
    }

    /**
     * Retrieve external free/busy data.
     *
     * @param array                 $servers  The remote servers to query
     * @param Horde_Kolab_FreeBusy_Access $access   The object holding the
     *                                        relevant access
     *                                        parameters.
     *
     * @return Horde_iCalender The remote free/busy information.
     */
    function &_fetchRemote($servers, $access)
    {
        $vFb = null;

        foreach ($servers as $server) {

            $url = 'https://' . urlencode($access->user) . ':' . urlencode($access->pass)
            . '@' . $server . $_SERVER['REQUEST_URI'];
            $remote = @file_get_contents($url);
            if (!$remote) {
                $message = sprintf("Unable to read free/busy information from %s",
                                   'https://' . urlencode($access->user) . ':XXX'
                                   . '@' . $server . $_SERVER['REQUEST_URI']);
                Horde::logMessage($message, __FILE__, __LINE__, PEAR_LOG_INFO);
            }

            $rvCal = &new Horde_iCalendar();
            $result = $rvCal->parsevCalendar($remote);

            if (is_a($result, 'PEAR_Error')) {
                $message = sprintf("Unable to parse free/busy information from %s: %s",
                                   'https://' . urlencode($access->user) . ':XXX'
                                   . '@' . $server . $_SERVER['REQUEST_URI'],
                                   $result->getMessage());
                Horde::logMessage($message, __FILE__, __LINE__, PEAR_LOG_INFO);
            }

            $rvFb = &$rvCal->findComponent('vfreebusy');
            if (!$pvFb) {
                $message = sprintf("Unable to find free/busy information in data from %s.",
                                   'https://' . urlencode($access->user) . ':XXX'
                                   . '@' . $server . $_SERVER['REQUEST_URI']);
                Horde::logMessage($message, __FILE__, __LINE__, PEAR_LOG_INFO);
            }
            if ($ets = $rvFb->getAttributeDefault('DTEND', false) !== false) {
                // PENDING(steffen): Make value configurable
                if ($ets < time()) {
                    $message = sprintf("free/busy information from %s is too old.",
                                       'https://' . urlencode($access->user) . ':XXX'
                                       . '@' . $server . $_SERVER['REQUEST_URI']);
                    Horde::logMessage($message, __FILE__, __LINE__, PEAR_LOG_INFO);
                }
            }
            if (!empty($vFb)) {
                $vFb->merge($rvFb);
            } else {
                $vFb = $rvFb;
            }
        }
        return $vFb;
    }

    function findAll_readdir($uid, $dirname, &$lst) {
        if ($dir = @opendir($dirname)) {
            while (($file = readdir($dir)) !== false) {
                if ($file == "." || $file == "..")
                    continue;

                $full_path = $dirname."/".$file;

                if (is_file($full_path) && preg_match("/(.*)\.x?pvc$/", $file, $matches))
                    $lst[] = $uid."/".$matches[1];
                else if(is_dir($full_path))
                    $this->findAll_readdir($uid."/".$file, $full_path, $lst);
            }
            closedir($dir);
        }
    }
};

/**
 * A berkeley db based cache for free/busy data.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_DB {

    /**
     * The directory that should be used for caching.
     *
     * @var string
     */
    var $_cache_dir;

    /**
     * The resource handle into the database.
     *
     * @var resource
     */
    var $_db = false;

    /**
     * The format of the database.
     *
     * @var string
     */
    var $_dbformat;

    /**
     * The type of this cache.
     *
     * @var string
     */
    var $_type = '';

    /**
     * The directory that should be used for caching.
     *
     * @var string
     */
    function Horde_Kolab_FreeBusy_Cache_DB($cache_dir) {
        global $conf;

        $this->_cache_dir = $cache_dir;

        if (!empty($conf['fb']['dbformat'])) {
            $this->_dbformat = $conf['fb']['dbformat'];
        } else {
            $this->_dbformat = 'db4';
        }

        /* make sure that a database really exists before accessing it */
        if (!file_exists($this->_cache_dir . '/' . $this->_type . 'cache.db')) {
            $result = $this->_open();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $this->_close();
        }

    }

    /**
     * Open the database.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _open()
    {
        if ($this->_db !== false) {
            return true;
        }

        $dbfile = $this->_cache_dir . '/' . $this->_type . 'cache.db';
        $this->_db = dba_open($dbfile, 'cd', $this->_dbformat);
        if ($this->_db === false) {
            return PEAR::raiseError(sprintf("Unable to open freebusy cache db %s", $dbfile));
        }
        return true;
    }

    /**
     * Close the database.
     */
    function _close()
    {
        if ($this->_db !== false) {
            dba_close($this->_db);
        }
        $this->_db = false;
    }

    /**
     * Set a cache file as irrelevant for a user.
     *
     * @param string $filename The cache file to remove.
     * @param string $uid      The user ID.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _remove($filename, $uid)
    {
        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (dba_exists($uid, $this->_db)) {
            $lst = dba_fetch($uid, $this->_db);
            $lst = split(',', $lst);
            $lst = array_diff($lst, array($filename));
            $result = dba_replace($uid, join(',', $lst), $this->_db);
            if ($result === false) {
                $result = PEAR::raiseError(sprintf("Unable to set db value for uid %s", $uid));
            }
        }
        $this->_close();

        return $result;
    }

    /**
     * Set a cache file as relevant for a user.
     *
     * @param string $filename The cache file to add.
     * @param string $uid      The user ID.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _add($filename, $uid)
    {
        if (empty($filename)) {
            return true;
        }

        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (dba_exists($uid, $this->_db)) {
            $lst = dba_fetch($uid, $this->_db);
            $lst = split(',', $lst);
            $lst[] = $filename;
            $result = dba_replace($uid, join(',', array_keys(array_flip($lst))), $this->_db);
            if ($result === false) {
                $result = PEAR::raiseError(sprintf("Unable to set db value for uid %s", $uid));
            }
        } else {
            $result = dba_insert($uid, $filename, $this->_db);
            if ($result === false) {
                $result = PEAR::raiseError(sprintf("Unable to set db value for uid %s", $uid));
            }
        }
        $this->_close();

        return $result;
    }

    /**
     * Is the cache file relevant for the user?
     *
     * @param string $filename The cache file.
     * @param string $uid      The user ID.
     *
     * @return boolean|PEAR_Error True if the cache file is relevant.
     */
    function has($filename, $uid)
    {
        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = false;
        if (dba_exists($uid, $this->_db)) {
            $lst = dba_fetch($uid, $this->_db);
            $lst = split(',', $lst);
            $result = in_array($filename, $lst);
        }
        $this->_close();

        return $result;
    }

    /**
     * Get the full list of relevant cache files for a uid.
     *
     * @param string $uid      The user ID.
     *
     * @return array|PEAR_Error The list of cache files.
     */
    function get($uid)
    {
        $result = $this->_open();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = array();
        if (dba_exists($uid, $this->_db)) {
            $lst = dba_fetch($uid, $this->_db);
            $lst = split(',', $lst);
            $result = array_filter($lst, array($this, '_notEmpty'));
        }
        $this->_close();

        return $result;
    }

    /**
     * Check if the value is set.
     *
     * @param mixed $value  The value to check.
     *
     * @return boolean True if the value is set.
     */
    function _notEmpty($value)
    {
        return !empty($value);
    }

    /**
     * Attempts to return a reference to a concrete FreeBusyACLCache
     * instance. It will only create a new instance if no
     * FreeBusyACLCache instance currently exists.
     *
     * This method must be invoked as:
     *   <code>$var = &FreeBusyACLCache::singleton($cache_dir);</code>
     *
     * @static
     *
     * @param string $type       The type of the cache.
     * @param string $cache_dir  The directory for storing the cache.
     *
     * @return FreeBusyACLCache The concrete FreeBusyACLCache
     *                          reference, or false on an error.
     */
    function &singleton($type, $cache_dir)
    {
        static $cachedb = array();

        $signature = $type . $cache_dir;

        if (empty($cachedb[$signature])) {
            $class = 'Horde_Kolab_FreeBusy_Cache_DB_' . $type;
            $cachedb[$signature] = new $class($cache_dir);
        }

        return $cachedb[$signature];
    }
}

/**
 * A berkeley db based cache for free/busy data that holds relevant
 * cache files based on folder ACLs.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_DB_acl extends Horde_Kolab_FreeBusy_Cache_DB {

    /**
     * The type of this cache.
     *
     * @var string
     */
    var $_type = 'acl';

    /**
     * Store permissions on a calender folder.
     *
     * @param string $filename The cache file representing the calendar folder.
     * @param array  $acl      The new ACL.
     * @param array  $oldacl   The old ACL.
     * @param mixed  $perm     False if all permissions should be revoked, a
     *                         single character specifying allowed access
     *                         otherwise.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function store($filename, $acl, $oldacl, $perm)
    {
        /* We remove the filename from all users listed in the old ACL first */
        foreach ($oldacl as $user => $ac) {
            $result = $this->_remove($filename, $user);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        /* Now add the filename for all users with the correct permissions */
        if ($perm !== false ) {
            foreach ($acl as $user => $ac) {
                if (strpos($ac, $perm) !== false) {
                    if (!empty($user)) {
                        $result = $this->_add($filename, $user);
                        if (is_a($result, 'PEAR_Error')) {
                            return $result;
                        }
                    }
                }
            }
        }

        return true;
    }
}

/**
 * A berkeley db based cache for free/busy data that holds relevant
 * cache files based on extended folder ACLs.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_DB_xacl extends Horde_Kolab_FreeBusy_Cache_DB {

    /**
     * The type of this cache.
     *
     * @var string
     */
    var $_type = 'xacl';

    /**
     * Store permissions on a calender folder.
     *
     * @param string $filename The cache file representing the calendar folder.
     * @param array  $xacl     The new extended ACL.
     * @param array  $oldxacl  The old extended ACL.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function store($filename, $xacl, $oldxacl)
    {
        $xacl = split(' ', $xacl);
        $oldxacl = split(' ', $oldxacl);
        $both = array_intersect($xacl, $oldxacl);

        /* Removed access rights */
        foreach (array_diff($oldxacl, $both) as $uid) {
            if (!empty($uid)) {
                $result = $this->_remove($filename, $uid);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        }

        /* Added access rights */
        foreach (array_diff($xacl, $both) as $uid) {
            if (!empty($uid)) {
                $result = $this->_add($filename, $uid);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
        }

        return true;
    }
}

/**
 * A representation of a cache file.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_File {

    /**
     * The suffix of this cache file.
     *
     * @var string
     */
    var $_suffix = '';

    /**
     * Name of the cache file.
     *
     * @var string
     */
    var $_filename;

    /**
     * Full path to the cache file.
     *
     * @var string
     */
    var $_file;

    /**
     * Cache file version.
     *
     * @var int
     */
    var $_version = 1;

    /**
     * Construct the Horde_Kolab_FreeBusy_Cache_File instance.
     *
     * @param string $cache_dir The path to the cache direcory.
     * @param string $filename  The file name of the cache file.
     * @param string $suffix    The suffix of the cache file name.
     */
    function Horde_Kolab_FreeBusy_Cache_File($cache_dir, $filename, $suffix = null)
    {
        if (!empty($suffix)) {
            $this->_suffix = $suffix;
        }

        $this->_cache_dir = $cache_dir;
        $this->_filename  = $filename;
        $this->_file = $this->_cache_dir . '/' . $this->_filename . '.' . $this->_suffix;
    }

    /**
     * Get the full path to the cache file.
     *
     * @return string The full path to the file.
     */
    function getFile()
    {
        return $this->_file;
    }

    /**
     * Clean the cache file contents.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function purge()
    {
        if (file_exists($this->_file)) {
            $result = @unlink($this->_file);
            if (!$result) {
                return PEAR::raiseError(sprintf("Failed removing file %s",
                                                $this->_file));
            }
        }
        return true;
    }

    /**
     * Store data in the cache file.
     *
     * @param mixed $data A reference to the data object.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function store(&$data)
    {
        /* Create directories if missing */
        $fbdirname = dirname($this->_file);
        if (!is_dir($fbdirname)) {
            $result = $this->_makeTree($fbdirname);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        /* Store the cache data */
        $fh = fopen($this->_file, 'w');
        if (!$fh) {
            return PEAR::raiseError(sprintf("Failed creating cache file %s!",
                                            $this->_file));
        }
        fwrite($fh, serialize(array('version' => $this->_version,
                                    'data' => $data)));
        fclose($fh);
        return true;
    }

    /**
     * Load data from the cache file.
     *
     * @return mixed|PEAR_Error The data retrieved from the cache file.
     */
    function &load()
    {
        $file = @file_get_contents($this->_file);
        if ($file === false) {
            return PEAR::raiseError(sprintf("%s failed reading cache file %s!",
                                            get_class($this), $this->_file));
        }
        $cache = @unserialize($file);
        if ($cache === false) {
            return PEAR::raiseError(sprintf("%s failed to unserialize cache data from file %s!",
                                            get_class($this), $this->_file));
        }
        if (!isset($cache['version'])) {
            return PEAR::raiseError(sprintf("Cache file %s lacks version data!",
                                            $this->_file));
        }
        $this->_version = $cache['version'];
        if (!isset($cache['data'])) {
            return PEAR::raiseError(sprintf("Cache file %s lacks data!",
                                            $this->_file));
        }
        if ($cache['version'] != $this->_version) {
            return PEAR::raiseError(sprintf("Cache file %s has version %s while %s is required!",
                                            $this->_file, $cache['version'], $this->_version));
        }
        return $cache['data'];
    }

    /**
     * Generate a tree of directories.
     *
     * @param string $dirname The path to a directory that should exist.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _maketree($dirname)
    {
        $base = substr($dirname, 0, strrpos($dirname, '/'));
        $base = str_replace(".", "^", $base);
        if (!empty($base) && !is_dir($base)) {
            $result = $this->_maketree($base);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        if (!file_exists($dirname)) {
            $result = @mkdir($dirname, 0755);
            if (!$result) {
                return PEAR::raiseError(sprintf("Error creating directory %s", $dirname));
            }
        }
        return true;
    }
}

/**
 * A cache file for partial free/busy information.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_File_pvcal extends Horde_Kolab_FreeBusy_Cache_File {

    /**
     * The suffix of this cache file.
     *
     * @var string
     */
    var $_suffix = 'pvc';

    /**
     * Store partial free/busy infomation in the cache file.
     *
     * @param Horde_iCalendar $pvcal A reference to the data object.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function storePVcal(&$pvcal)
    {
        return $this->store($pvcal);
    }

    /**
     * Load partial free/busy data from the cache file.
     *
     * @param boolean $extended Should the extended information be retrieved?
     *
     * @return Horde_iCalendar|PEAR_Error The data retrieved from the cache file.
     */
    function &loadPVcal($extended)
    {
        $pvcal = $this->load();
        if (is_a($pvcal, 'PEAR_Error')) {
            return $pvcal;
        }
        if (!$extended) {
            $components = &$pvcal->getComponents();
            foreach ($components as $component) {
                if ($component->getType() == 'vFreebusy') {
                    $component->_extraParams = array();
                }
            }
        }
        return $pvcal;
    }

    /**
     * Return the last modification date of the cache file.
     *
     * @return int The last modification date.
     */
    function getMtime()
    {
        return filemtime($this->_file);
    }
}

/**
 * A cache file for complete free/busy information.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_File_vcal extends Horde_Kolab_FreeBusy_Cache_File {

    /**
     * The suffix of this cache file.
     *
     * @var string
     */
    var $_suffix = 'vc';

    /**
     * Cache file version.
     *
     * @var int
     */
    var $_version = 2;

    /**
     * Cached data.
     *
     * @var array
     */
    var $_data;

    /**
     * Construct the Horde_Kolab_FreeBusy_Cache_File_vcal instance.
     *
     * @param string  $cache_dir The path to the cache direcory.
     * @param string  $filename  The file name of the cache file.
     * @param boolean $extended  Does the cache hold extended data?
     */
    function Horde_Kolab_FreeBusy_Cache_File_vcal($cache_dir, $filename, $extended)
    {
        $extension = empty($extended) ? 'vc' : 'xvc';
        parent::Horde_Kolab_FreeBusy_Cache_File($cache_dir, $filename, $extension);
    }

    /**
     * Store free/busy infomation in the cache file.
     *
     * @param Horde_iCalendar $vcal   A reference to the data object.
     * @param array           $mtimes A list of modification times for the 
     *                                partial free/busy cache times.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function storeVcal(&$vcal, &$mtimes)
    {
        $data = array('vcal' => $vcal,
                      'mtimes' => $mtimes);
        return $this->store($data);
    }

    /**
     * Load the free/busy information from the cache.
     *
     * @return Horde_iCalendar|PEAR_Error The retrieved free/busy information.
     */
    function &loadVcal()
    {
        if ($this->_data) {
            return $this->_data;
        }

        $result = $this->load();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_data = $result['vcal'];

        return $this->_data;
    }

    /**
     * Check if the cached free/busy expired.
     *
     * @param array $files A list of partial free/busy cache files.
     *
     * @return boolean|PEAR_Error True if the cache expired.
     */
    function expired($files)
    {
        $result = $this->load();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Check the cache version */
        if ($this->_version < 2) {
            return true;
        }

        $this->_data = $result['vcal'];

        /* Files changed? */
        $keys = array_keys($result['mtimes']);
        $changes = array_diff($keys, $files);
        if (count($keys) != count($files) || !empty($changes)) {
            return true;
        }

        /* Check the file mtimes */
        foreach ($files as $file) {
            if (filemtime($result['mtimes'][$file][0]) != $result['mtimes'][$file][1]) {
                return true;
            }
        }

        /* Older than three days? */
        $components = $this->_data->getComponents();
        foreach ($components as $component) {
            if ($component->getType() == 'vFreebusy') {
                $attr = $component->getAttribute('DTSTAMP');
                if (!empty($attr) && !is_a($attr, 'PEAR_Error')) {
                    //Should be configurable
                    if (time() - (int)$attr > 259200) {
                        return true;
                    }
                }
            }
        }

        return false;
    }
}

/**
 * A cache file for ACLs. This serves as a buffer between the DB based
 * ACL storage and is required to hold the old ACL list for updates to
 * the DB based cache.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_File_acl extends Horde_Kolab_FreeBusy_Cache_File {

    /**
     * The suffix of this cache file.
     *
     * @var string
     */
    var $_suffix = 'acl';

    /**
     * Link to the ACL stored in a data base.
     *
     * @var Horde_Kolab_FreeBusy_Cache_DB
     */
    var $_acls;

    /**
     * Construct the Horde_Kolab_FreeBusy_Cache_File_acl instance.
     *
     * @param string $cache_dir The path to the cache direcory.
     * @param string $filename  The file name of the cache file.
     */
    function Horde_Kolab_FreeBusy_Cache_File_acl($cache_dir, $filename)
    {
        $this->_acls = &Horde_Kolab_FreeBusy_Cache_DB::singleton('acl', $cache_dir);
        parent::Horde_Kolab_FreeBusy_Cache_File($cache_dir, $filename, 'acl');
    }

    /**
     * Clean the cache file contents.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function purge()
    {
        $oldacl = $this->load();
        if (is_a($oldacl, 'PEAR_Error')) {
            $oldacl = array();
        }

        $result = $this->_acls->store($this->_filename, array(), $oldacl, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return parent::purge();
    }

    /**
     * Store a new ACL.
     *
     * @param array  $acl       The new ACL.
     * @param string $relevance Folder relevance.
     * @param string $append    Should old entries be purged?
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function storeACL(&$acl, $relevance, $append = false)
    {
        if (!$append) {
            $oldacl = $this->load();
            if (is_a($oldacl, 'PEAR_Error')) {
                $oldacl = array();
            }
            $acl = array_merge($oldacl, $acl);
        } else {
            $oldacl = array();
        }

        /* Handle relevance */
        switch ($relevance) {
        case 'readers':
            $perm = 'r';
            break;
        case 'nobody':
            $perm = false;
            break;
        case 'admins':
        default:
            $perm = 'a';
        }

        $result = $this->_acls->store($this->_filename, $acl, $oldacl, $perm);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->store($acl);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }
}

/**
 * A cache file for extended ACLs. This serves as a buffer between the
 * DB based ACL storage and is required to hold the old ACL list for
 * updates to the DB based cache.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Cache.php,v 1.17.2.5 2009-04-25 19:16:42 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Cache_File_xacl extends Horde_Kolab_FreeBusy_Cache_File {

    /**
     * The suffix of this cache file.
     *
     * @var string
     */
    var $_suffix = 'xacl';

    /**
     * Link to the ACL stored in a data base.
     *
     * @var Horde_Kolab_FreeBusy_Cache_DB
     */
    var $_xacls;

    /**
     * Construct the Horde_Kolab_FreeBusy_Cache_File_xacl instance.
     *
     * @param string $cache_dir The path to the cache direcory.
     * @param string $filename  The file name of the cache file.
     */
    function Horde_Kolab_FreeBusy_Cache_File_xacl($cache_dir, $filename)
    {
        $this->_xacls = &Horde_Kolab_FreeBusy_Cache_DB::singleton('xacl', $cache_dir);
        parent::Horde_Kolab_FreeBusy_Cache_File($cache_dir, $filename, 'xacl');
    }

    /**
     * Clean the cache file contents.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function purge()
    {
        $oldxacl = $this->load();
        if (is_a($oldxacl, 'PEAR_Error')) {
            $oldxacl = '';
        }

        $result = $this->_xacls->store($this->_filename, '', $oldxacl);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return parent::purge();
    }

    /**
     * Store a new extended ACL.
     *
     * @param array $xacl  The new extended ACL.
     * @param array $acl   General ACL for the folder.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function storeXACL(&$xacl, &$acl)
    {
        $oldxacl = $this->load();
        if (is_a($oldxacl, 'PEAR_Error')) {
            $oldxacl = '';
        }

        /* Users with read access to the folder may also access the extended information */
        foreach ($acl as $user => $ac) {
            if (strpos($ac, 'r') !== false) {
                if (!empty($user)) {
                    $xacl .= ' ' . $user;
                }
            }
        }

        $result = $this->_xacls->store($this->_filename, $xacl, $oldxacl);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->store($xacl);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }
}
