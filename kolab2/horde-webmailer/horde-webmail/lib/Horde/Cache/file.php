<?php
/**
 * The Horde_Cache_file:: class provides a filesystem implementation of the
 * Horde caching system.
 *
 * Optional parameters:<pre>
 *   'dir'     The base directory to store the cache files in.
 *   'prefix'  The filename prefix to use for the cache files.
 *   'sub'     An integer. If non-zero, the number of subdirectories to
 *             create to store the file (i.e. PHP's session.save_path).</pre>
 *
 * $Horde: framework/Cache/Cache/file.php,v 1.28.10.21 2009-01-06 15:22:56 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 1.3
 * @package Horde_Cache
 */
class Horde_Cache_file extends Horde_Cache {

    /**
     * The location of the temp directory.
     *
     * @var string
     */
    var $_dir;

    /**
     * The filename prefix for cache files.
     *
     * @var string
     */
    var $_prefix = 'cache_';

    /**
     * The subdirectory level the cache files should live at.
     *
     * @var integer
     */
    var $_sub = 0;

    /**
     * List of key to filename mappings.
     *
     * @var array
     */
    var $_file = array();

    /**
     * Construct a new Horde_Cache_file object.
     *
     * @param array $params  Parameter array.
     */
    function Horde_Cache_file($params = array())
    {
        if (!empty($params['dir']) && @is_dir($params['dir'])) {
            $this->_dir = $params['dir'];
        } else {
            require_once 'Horde/Util.php';
            $this->_dir = Util::getTempDir();
        }

        foreach (array('prefix', 'sub') as $val) {
            if (isset($params[$val])) {
                $name = '_' . $val;
                $this->$name = $params[$val];
            }
        }

        /* Only do garbage collection if asked for, and then only 0.1% of the
         * time we create an object. */
        if (rand(0, 999) == 0) {
            register_shutdown_function(array(&$this, '_doGC'));
        }

        parent::Horde_Cache($params);
    }

    /**
     * Attempts to retrieve cached data from the filesystem and return it to
     * the caller.
     *
     * @param string  $key       Cache key to fetch.
     * @param integer $lifetime  Lifetime of the data in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function get($key, $lifetime = 1)
    {
        if ($this->exists($key, $lifetime)) {
            $filename = $this->_keyToFile($key);
            $size = filesize($filename);
            if (!$size) {
                return '';
            }
            $old_error = error_reporting(0);
            $data = file_get_contents($filename);
            error_reporting($old_error);
            return $data;
        }

        /* Nothing cached, return failure. */
        return false;
    }

    /**
     * Attempts to store data to the filesystem.
     *
     * @param string $key        Cache key.
     * @param mixed  $data       Data to store in the cache. (MUST BE A STRING)
     * @param integer $lifetime  Data lifetime. @since Horde 3.2
     *
     * @return boolean  True on success, false on failure.
     */
    function set($key, $data, $lifetime = null)
    {
        require_once 'Horde/Util.php';
        $filename = $this->_keyToFile($key, true);
        $tmp_file = Util::getTempFile('HordeCache', true, $this->_dir);
        if (isset($this->_params['umask'])) {
            chmod($tmp_file, 0666 & ~$this->_params['umask']);
        }

        if (function_exists('file_put_contents')) {
            if (file_put_contents($tmp_file, $data) === false) {
                return false;
            }
        } elseif ($fd = fopen($tmp_file, 'w')) {
            $res = fwrite($fd, $data);
            fclose($fd);
            if ($res < strlen($data)) {
                return false;
            }
        } else {
            return false;
        }

        @rename($tmp_file, $filename);

        $lifetime = $this->_getLifetime($lifetime);
        if ($lifetime != $this->_params['lifetime']) {
            // This may result in duplicate entries in horde_cache_gc, but we
            // will take care of these whenever we do GC and this is quicker
            // than having to check every time we access the file.
            $fp = fopen($this->_dir . '/horde_cache_gc', 'a');
            fwrite($fp, $filename . "\t" . (empty($lifetime) ? 0 : time() + $lifetime) . "\n");
            fclose($fp);
        }

        return true;
    }

    /**
     * Checks if a given key exists in the cache, valid for the given
     * lifetime. If it exists but is expired, delete the file.
     *
     * @param string  $key       Cache key to check.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return boolean  Existance.
     */
    function exists($key, $lifetime = 1)
    {
        $filename = $this->_keyToFile($key);

        /* Key exists in the cache */
        if (file_exists($filename)) {
            /* 0 means no expire. */
            if ($lifetime == 0) {
                return true;
            }

            /* If the file was been created after the supplied value,
             * the data is valid (fresh). */
            if (time() - $lifetime <= filemtime($filename)) {
                return true;
            } else {
                @unlink($filename);
            }
        }

        return false;
    }

    /**
     * Expire any existing data for the given key.
     *
     * @param string $key  Cache key to expire.
     *
     * @return boolean  Success or failure.
     */
    function expire($key)
    {
        $filename = $this->_keyToFile($key);
        return @unlink($filename);
    }

    /**
     * Attempts to directly output a cached object.
     *
     * @param string  $key       Object ID to query.
     * @param integer $lifetime  Lifetime of the object in seconds.
     *
     * @return boolean  True if output or false if no object was found.
     */
    function output($key, $lifetime = 1)
    {
        if (!$this->exists($key, $lifetime)) {
            return false;
        } else {
            $filename = $this->_keyToFile($key);
            return @readfile($filename);
        }
    }

    /**
     * Map a cache key to a unique filename.
     *
     * @access private
     *
     * @param string $key     Cache key.
     * @param string $create  Create path if it doesn't exist?
     *
     * @return string  Fully qualified filename.
     */
    function _keyToFile($key, $create = false)
    {
        if ($create || !isset($this->_file[$key])) {
            $dir = $this->_dir . '/';
            $sub = '';
            $md5 = md5($key);
            if (!empty($this->_sub)) {
                $max = min($this->_sub, strlen($md5));
                for ($i = 0; $i < $max; $i++) {
                    $sub .= $md5[$i];
                    if ($create && !is_dir($dir . $sub)) {
                        if (!mkdir($dir . $sub)) {
                            $sub = '';
                            break;
                        }
                    }
                    $sub .= '/';
                }
            }
            $this->_file[$key] = $dir . $sub . $this->_prefix . $md5;
        }

        return $this->_file[$key];
    }

    /**
     * Do garbage collection needed for the driver.
     *
     * @access private
     */
    function _doGC()
    {
        $filename = $this->_dir . '/horde_cache_gc';
        $excepts = array();

        if (file_exists($filename)) {
            $flags = defined('FILE_IGNORE_NEW_LINES') ? FILE_IGNORE_NEW_LINES : 0;
            $gc_file = file($filename, $flags);
            array_pop($gc_file);
            reset($gc_file);
            while (list(,$data) = each($gc_file)) {
                if (!$flags) {
                    $data = rtrim($data);
                }
                $parts = explode("\t", $data, 2);
                $excepts[$parts[0]] = $parts[1];
            }
        }

        $this->_gcDir($this->_dir, $excepts);

        $out = '';
        foreach ($excepts as $key => $val) {
            $out .= $key . "\t" . $val . "\n";
        }

        if (function_exists('file_put_contents')) {
            file_put_contents($filename, $out);
        } else {
            $fp = fopen($filename, 'w');
            fwrite($fp, $out);
            fclose($fp);
        }
    }

    /**
     * @private
     */
    function _gcDir($dir, &$excepts)
    {
        $d = @dir($dir);
        if (!$d) {
            return PEAR::raiseError('permission denied to ' . $dir);
        }

        $c_time = time();

        while (($entry = $d->read()) !== false) {
            $path = $dir . '/' . $entry;
            if (($entry == '.') || ($entry == '..')) {
                continue;
            }

            if (strpos($entry, $this->_prefix) === 0) {
                $d_time = isset($excepts[$path]) ? $excepts[$path] : $this->_params['lifetime'];
                if (!empty($d_time) &&
                    (($c_time - $d_time) > filemtime($path))) {
                    @unlink($path);
                    unset($excepts[$path]);
                }
            } elseif (!empty($this->_sub) && is_dir($path)) {
                $this->_gcDir($path, $excepts);
            }
        }
        $d->close();
    }

}

