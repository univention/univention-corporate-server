<?php
/**
 * The Horde_Cache_file:: class provides a filesystem implementation of the
 * Horde caching system.
 *
 * Optional values for $params:
 *   'dir'          The directory to store the cache files in.
 *   'prefix'       The filename prefix to use for the cache files.
 *
 * $Horde: framework/Cache/Cache/file.php,v 1.26 2004/04/29 15:16:41 jan Exp $
 *
 * Copyright 1999-2004 Anil Madhavapeddy <anil@recoil.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Cache
 */
class Horde_Cache_file extends Horde_Cache {

    /**
     * The location of the temp directory.
     *
     * @var string $dir
     */
    var $_dir;

    /**
     * The filename prefix for cache files.
     *
     * @var string $prefix
     */
    var $_prefix = 'cache_';

    /**
     * Construct a new Horde_Cache_file object.
     *
     * @access public
     *
     * @param array $params  Parameter array.
     */
    function Horde_Cache_file($params = array())
    {
        if (array_key_exists('dir', $params) && @is_dir($params['dir'])) {
            $this->_dir = $params['dir'];
        } else {
            require_once 'Horde/Util.php';
            $this->_dir = Util::getTempDir();
        }

        if (array_key_exists('prefix', $params)) {
            $this->_prefix = $params['prefix'];
        }
    }

    /**
     * Attempts to store an object to the filesystem.
     *
     * @access protected
     *
     * @param string $oid  Object ID used as the caching key.
     * @param mixed $data  Data to store in the cache.
     *
     * @return boolean  True on success, false on failure.
     */
    function _store($oid, $data)
    {
        require_once 'Horde/Util.php';
        $filename = $this->_oidToFile($oid);
        $tmp_file = Util::getTempFile('HordeCache', true, $this->_dir);

        if ($fd = fopen($tmp_file, 'w')) {
            if (fwrite($fd, $data) < strlen($data)) {
                fclose($fd);
                return false;
            } else {
                fclose($fd);
                @rename($tmp_file, $filename);
            }
        }
    }

    /**
     * Attempts to retrieve a cached object from the filesystem and
     * return it to the caller.
     *
     * @access protected
     *
     * @param string  $oid        Object ID to query.
     * @param integer $lifetime   Lifetime of the object in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function _fetch($oid, $lifetime = 1)
    {
        $filename = $this->_oidToFile($oid);
        if ($this->_isValid($filename, $lifetime)) {
            $fd = @fopen($filename, 'r');
            if ($fd) {
                $data = fread($fd, filesize($filename));
                fclose($fd);
                return $data;
            }
        }

        /* Nothing cached, return failure. */
        return false;
    }

    /**
     * Attempts to directly output a cached object from the
     * filesystem.
     *
     * @access protected
     *
     * @param string  $oid        Object ID to query.
     * @param integer $lifetime   Lifetime of the object in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function _output($oid, $lifetime = 1)
    {
        $filename = $this->_oidToFile($oid);
        if ($this->_isValid($filename, $lifetime)) {
            $fd = @fopen($filename, 'r');
            if ($fd) {
                fpassthru($fd);
                return true;
            }
        }

        /* Nothing cached, return failure. */
        return false;
    }

    /**
     * Check to see if the object exists in the cache, and whether or
     * not it's expired. If it has expired, delete it.
     *
     * @param string  $filename  The file to check.
     * @param integer $lifetime  The max age (in seconds) of the object.
     *
     * @return boolean  Whether or not there is a current copy of the object
     *                  in the cache.
     */
    function _isValid($filename, $lifetime)
    {
        /* An object exists in the cache */
        if (file_exists($filename)) {
            /* 0 means no expire. */
            if ($lifetime == 0) {
                return true;
            }

            $lastmod = filemtime($filename);

            /* If the object has been created after the supplied
             * value, the object is valid. */
            if (time() - $lifetime <= $lastmod) {
                return true;
            } else {
                @unlink($filename);
            }
        }

        return false;
    }

    /**
     * Map an object ID to a unique filename.
     *
     * @access private
     *
     * @param string $oid  Object ID
     *
     * @return string  Fully qualified filename.
     */
    function _oidToFile($oid)
    {
        return $this->_dir . '/' . $this->_prefix . md5($oid);
    }

}
