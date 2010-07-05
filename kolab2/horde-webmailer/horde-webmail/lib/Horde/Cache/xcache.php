<?php
/**
 * The Horde_Cache_xcache:: class provides an XCache implementation of
 * the Horde caching system.
 *
 * $Horde: framework/Cache/Cache/xcache.php,v 1.8.2.1 2007-12-20 13:48:51 jan Exp $
 *
 * Copyright 2006-2007 Duck <duck@obala.net>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 4.0
 * @package Horde_Cache
 */
class Horde_Cache_xcache extends Horde_Cache {

    /**
     * Construct a new Horde_Cache_xcache object.
     *
     * @param array $params  Parameter array.
     */
    function Horde_Cache_xcache($params = array())
    {
        parent::Horde_Cache($params);

        if (empty($this->_params['prefix'])) {
            $this->_params['prefix'] = ($_SERVER['SERVER_NAME']) ? $_SERVER['SERVER_NAME'] : $_SERVER['HOSTNAME'];
        }
    }

    /**
     * Attempts to retrieve a piece of cached data and return it to the caller.
     *
     * @param string  $key       Cache key to fetch.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return mixed  Cached data, or false if none was found.
     */
    function get($key, $lifetime = 1)
    {
        $key = $this->_params['prefix'] . $key;
        $this->_setExpire($key, $lifetime);
        $result = xcache_get($key);
        if (!empty($result)) {
            return $result;
        } else {
            return false;
        }
    }

    /**
     * Attempts to store an object to the cache.
     *
     * @param string $key        Cache key (identifier).
     * @param mixed  $data       Data to store in the cache.
     * @param integer $lifetime  Data lifetime. @since Horde 3.2
     *
     * @return boolean  True on success, false on failure.
     */
    function set($key, $data, $lifetime = null)
    {
        $key = $this->_params['prefix'] . $key;
        $lifetime = $this->_getLifetime($lifetime);
        xcache_set($key . '_expire', time(), $lifetime);
        return xcache_set($key, $data, $lifetime);
    }

    /**
     * Checks if a given key exists in the cache, valid for the given lifetime.
     *
     * @param string  $key       Cache key to check.
     * @param integer $lifetime  Lifetime of the key in seconds.
     *
     * @return boolean  Existance.
     */
    function exists($key, $lifetime = 1)
    {
        $key = $this->_params['prefix'] . $key;
        $this->_setExpire($key, $lifetime);
        return xcache_isset($key);
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
        $key = $this->_params['prefix'] . $key;
        xcache_unset($key . '_expire');
        return xcache_unset($key);
    }

    /**
     * Set expire time on each call since memcache sets it on cache creation.
     *
     * @access private
     *
     * @param string  $key   Cache key to expire.
     * @param integer $lifetime  Lifetime of the data in seconds.
     */
    function _setExpire($key, $lifetime)
    {
        if ($lifetime == 0) {
            // don't expire
            return true;
        }

        $expire = xcache_get($key . '_expire');

        // set prune period
        if ($expire + $lifetime < time()) {
            // Expired
            xcache_unset($key . '_expire');
            xcache_unset($key);
            $lifetime = 0;
        } else {
            // Not expired..
            $lifetime = ($expire + $lifetime) - time();
        }

        return $lifetime;
    }

}
