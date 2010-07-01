<?php
/**
 * $Horde: framework/Cache/Cache/memcache.php,v 1.24.2.3 2009-01-06 15:22:56 jan Exp $
 *
 * Copyright 2006-2007 Duck <duck@obala.net>
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @category Horde
 * @package Horde_Cache
 */

/** Horde_Memcache */
require_once 'Horde/Memcache.php';

/**
 * The Horde_Cache_memcache:: class provides a memcached implementation of the
 * Horde caching system.
 *
 * @author  Duck <duck@obala.net>
 * @author  Michael Slusarz <slusarz@curecanti.org>
 * @since   Horde 3.2
 * @category Horde
 * @package Horde_Cache
 */
class Horde_Cache_memcache extends Horde_Cache {

    /**
     * Horde_memcache object.
     *
     * @var Horde_Memcache
     */
    var $_memcache;

    /**
     * Cache results of expire() calls (since we will get the entire object
     * on an expire() call anyway).
     */
    var $_expirecache = array();

    /**
     * Construct a new Horde_Cache_memcache object.
     *
     * @param array $params  Parameter array.
     */
    function Horde_Cache_memcache($params = array())
    {
        $this->_memcache = &Horde_Memcache::singleton();

        parent::Horde_Cache($params);
    }

    /**
     * Attempts to retrieve cached data from the memcache and return it to
     * the caller.
     *
     * @param string $key        Cache key to fetch.
     * @param integer $lifetime  Lifetime of the data in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function get($key, $lifetime = 1)
    {
        return $this->_get($key, $lifetime);
    }

    /**
     * Attempts to retrieve cached data from the memcache.
     *
     * @access private
     *
     * @param string $key        Cache key to fetch.
     * @param integer $lifetime  Lifetime of the data in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function _get($key, $lifetime)
    {
        if (isset($this->_expirecache[$key])) {
            return $this->_expirecache[$key];
        }

        $key_list = array($key);
        if (!empty($lifetime)) {
            $key_list[] = $key . '_e';
        }

        $res = $this->_memcache->get($key_list);

        if ($res === false) {
            unset($this->_expirecache[$key]);
        } else {
            // If we can't find the expire time, assume we have exceeded it.
            if (empty($lifetime) ||
                (($res[$key . '_e'] !== false) && ($res[$key . '_e'] + $lifetime > time()))) {
                $this->_expirecache[$key] = $res[$key];
            } else {
                $res[$key] = false;
                $this->expire($key);
            }
        }
        return $res[$key];
    }

    /**
     * Attempts to store data to the memcache.
     *
     * @param string $key        Cache key.
     * @param mixed $data        Data to store in the cache.
     * @param integer $lifetime  Data lifetime. @since Horde 3.2
     *
     * @return boolean  True on success, false on failure.
     */
    function set($key, $data, $lifetime = null)
    {
        $lifetime = $this->_getLifetime($lifetime);
        if ($this->_memcache->set($key . '_e', time(), $lifetime) === false) {
            return false;
        }
        return $this->_memcache->set($key, $data, $lifetime);
    }

    /**
     * Checks if a given key exists in the cache.
     *
     * @param string $key        Cache key to check.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return boolean  Existance.
     */
    function exists($key, $lifetime = 1)
    {
        $data = $this->_get($key, $lifetime);
        return ($data !== false);
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
        unset($this->_expirecache[$key]);
        $this->_memcache->delete($key . '_e');
        return $this->_memcache->delete($key);
    }

}
