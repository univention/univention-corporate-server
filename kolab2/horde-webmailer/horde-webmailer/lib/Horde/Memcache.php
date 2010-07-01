<?php
/**
 * The max storage size of the memcache server.  This should be slightly
 * smaller than the actual value due to overhead.  By default, the max slab
 * size of memcached (as of 1.1.2) is 1 MB.
 */
define('MEMCACHE_MAX_SIZE', 1000000);

/**
 * The Horde_memcache:: class provides easy access for Horde code to a
 * centrally configured memcache installation.
 *
 * memcached website: http://www.danga.com/memcached/
 *
 * $Horde: framework/Memcache/lib/Horde/Memcache.php,v 1.1.2.7 2009-07-23 20:29:44 slusarz Exp $
 *
 * Configuration parameters (set in $conf['memcache']):<pre>
 *   'compression' - Compress data inside memcache?
 *                   DEFAULT: false
 *   'c_threshold' - The minimum value length before attempting to compress.
 *                   DEFAULT: none
 *   'hostspec'    - The memcached host(s) to connect to.
 *                   DEFAULT: 'localhost'
 *   'large_items' - Allow storing large data items (larger than
 *                   MEMCACHE_MAX_SIZE)?
 *                   DEFAULT: true
 *   'persistent'  - Use persistent DB connections?
 *                   DEFAULT: false
 *   'prefix'      - The prefix to use for the memcache keys.
 *                   DEFAULT: 'horde'
 *   'port'        - The port(s) memcache is listening on. Leave empty or set
 *                   to 0 if using UNIX sockets.
 *                   DEFAULT: 11211
 *   'weight'      - The weight to use for each memcached host.
 *                   DEFAULT: none (equal weight to all servers)
 * </pre>
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @category Horde
 * @author  Michael Slusarz <slusarz@curecanti.org>
 * @author  Didi Rieder <adrieder@sbox.tugraz.at>
 * @since   Horde 3.2
 * @package Horde_Memcache
 */
class Horde_Memcache {

    /**
     * Memcache object.
     *
     * @var Memcache
     */
    var $_memcache;

    /**
     * Memcache defaults.
     *
     * @var array
     */
    var $_params = array(
        'compression' => 0,
        'hostspec' => 'localhost',
        'large_items' => true,
        'persistent' => false,
        'port' => 11211,
    );

    /**
     * Allow large data items?
     *
     * @var boolean
     */
    var $_large = true;

    /**
     * A list of items known not to exist.
     *
     * @var array
     */
    var $_noexist = array();

    /**
     * Singleton.
     */
    function &singleton()
    {
        static $instance;

        if (!isset($instance)) {
            $instance = new Horde_Memcache();
        }

        return $instance;
    }

    /**
     * Constructor.
     */
    function Horde_Memcache()
    {
        $this->_params = array_merge($this->_params, $GLOBALS['conf']['memcache']);
        $this->_params['prefix'] = (empty($this->_params['prefix'])) ? 'horde' : $this->_params['prefix'];
        $this->_large = !empty($this->_params['large_items']);

        $servers = array();
        $this->_memcache = new Memcache;
        for ($i = 0, $n = count($this->_params['hostspec']); $i < $n; ++$i) {
            if ($this->_memcache->addServer($this->_params['hostspec'][$i], empty($this->_params['port'][$i]) ? 0 : $this->_params['port'][$i], !empty($this->_params['persistent']), !empty($this->_params['weight'][$i]) ? $this->_params['weight'][$i] : 1)) {
                $servers[] = $this->_params['hostspec'][$i] . (!empty($this->_params['port'][$i]) ? ':' . $this->_params['port'][$i] : '');
            }
        }

        /* Check if any of the connections worked. */
        if (empty($servers)) {
            Horde::logMessage('Could not connect to any defined memcache servers.' , __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            if (!empty($this->_params['c_threshold'])) {
                $this->_memcache->setCompressThreshold($this->_params['c_threshold']);
            }

            // Force consistent hashing
            ini_set('memcache.hash_strategy', 'consistent');

            Horde::logMessage('Connected to the following memcache servers:' . implode($servers, ', '), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }
    }

    /**
     * Delete a key.
     *
     * @see Memcache::delete()
     *
     * @param string $key       The key.
     * @param integer $timeout  Expiration time in seconds.
     *
     * @return boolean  True on success.
     */
    function delete($key, $timeout = 0)
    {
        if ($this->_large) {
            /* No need to delete the oversized parts - memcache's LRU
             * algorithm will eventually cause these pieces to be recycled. */
            if (!isset($this->_noexist[$key . '_os'])) {
                $this->_memcache->delete($this->_key($key . '_os'), $timeout);
            }
        }
        if (isset($this->_noexist[$key])) {
            return false;
        }
        return $this->_memcache->delete($this->_key($key), $timeout);
    }

    /**
     * Get data associated with a key.
     *
     * @see Memcache::get()
     *
     * @param mixed $keys  The key or an array of keys.
     *
     * @return mixed  The string/array on success (return type is the type of
     *                $keys), false on failure.
     */
    function get($keys)
    {
        $key_map = $os = $os_keys = $out_array = array();
        $ret_array = true;

        if (!is_array($keys)) {
            $keys = array($keys);
            $ret_array = false;
        }
        $search_keys = $keys;

        if ($this->_large) {
            foreach ($keys as $val) {
                $os_keys[$val] = $search_keys[] = $val . '_os';
            }
        }

        foreach ($search_keys as $v) {
            $key_map[$v] = $this->_key($v);
        }

        $res = $this->_memcache->get(array_values($key_map));
        if ($res === false) {
            return false;
        }

        /* Check to see if we have any oversize items we need to get. */
        if (!empty($os_keys)) {
            foreach ($os_keys as $key => $val) {
                if (!empty($res[$key_map[$val]])) {
                    /* This is an oversize key entry. */
                    $os[$key] = $this->_getOSKeyArray($key, $res[$key_map[$val]]);
                }
            }

            if (!empty($os)) {
                $search_keys = $search_keys2 = array();
                foreach ($os as $val) {
                    $search_keys = array_merge($search_keys, $val);
                }

                foreach ($search_keys as $v) {
                    $search_keys2[] = $key_map[$v] = $this->_key($v);
                }

                $res2 = $this->_memcache->get($search_keys2);
                if ($res2 === false) {
                    return false;
                }

                /* $res should now contain the same results as if we had
                 * run a single get request with all keys above. */
                $res = array_merge($res, $res2);
            }
        }

        foreach ($key_map as $k => $v) {
            if (!isset($res[$v])) {
                $this->_noexist[$k] = true;
            }
        }

        $old_error = error_reporting(0);

        foreach ($keys as $k) {
            $out_array[$k] = false;
            if (isset($res[$key_map[$k]])) {
                $data = $res[$key_map[$k]];
                if (isset($os[$k])) {
                    foreach ($os[$k] as $v) {
                        if (isset($res[$key_map[$v]])) {
                            $data .= $res[$key_map[$v]];
                        } else {
                            $this->delete($k);
                            continue 2;
                        }
                    }
                }
                $out_array[$k] = unserialize($data);
            } elseif (isset($os[$k]) && !isset($res[$key_map[$k]])) {
                $this->delete($k);
            }
        }

        error_reporting($old_error);

        return ($ret_array) ? $out_array : reset($out_array);
    }

    /**
     * Set the value of a key.
     *
     * @see Memcache::set()
     *
     * @param string $key       The key.
     * @param string $var       The data to store.
     * @param integer $timeout  Expiration time in seconds.
     *
     * @return boolean  True on success.
     */
    function set($key, $var, $expire = 0)
    {
        $old_error = error_reporting(0);
        $var = serialize($var);
        error_reporting($old_error);

        return $this->_set($key, $var, $expire);
    }

    /**
     * Set the value of a key.
     *
     * @private
     *
     * @param string $key       The key.
     * @param string $var       The data to store (serialized).
     * @param integer $timeout  Expiration time in seconds.
     * @param integer $lent     String length of $len.
     *
     * @return boolean  True on success.
     */
    function _set($key, $var, $expire = 0, $len = null)
    {
        if (is_null($len)) {
            $len = strlen($var);
        }

        if (!$this->_large && ($len > MEMCACHE_MAX_SIZE)) {
            return false;
        }

        for ($i = 0; ($i * MEMCACHE_MAX_SIZE) < $len; ++$i) {
            $curr_key = ($i) ? ($key . '_s' . $i) : $key;
            $res = $this->_memcache->set($this->_key($curr_key), substr($var, $i * MEMCACHE_MAX_SIZE, MEMCACHE_MAX_SIZE), empty($this->_params['compression']) ? 0 : MEMCACHE_COMPRESSED, $expire);
            if ($res === false) {
                $this->delete($key);
                $i = 1;
                break;
            }
            unset($this->_noexist[$curr_key]);
        }

        if (($res !== false) && $this->_large) {
            $os_key = $this->_key($key . '_os');
            if (--$i) {
                $this->_memcache->set($os_key, $i, 0, $expire);
            } elseif (!isset($this->_noexist[$key . '_os'])) {
                $this->_memcache->delete($os_key);
            }
        }

        return $res;
    }

    /**
     * Replace the value of a key.
     *
     * @see Memcache::replace()
     *
     * @param string $key       The key.
     * @param string $var       The data to store.
     * @param integer $timeout  Expiration time in seconds.
     *
     * @return boolean  True on success, false if key doesn't exist.
     */
    function replace($key, $var, $expire = 0)
    {
        $old_error = error_reporting(0);
        $var = serialize($var);
        error_reporting($old_error);
        $len = strlen($var);

        if ($len > MEMCACHE_MAX_SIZE) {
            if ($this->_large) {
                $res = $this->_memcache->get(array($this->_key($key), $this->_key($key . '_os')));
                if (!empty($res)) {
                    return $this->_set($key, $var, $expire, $len);
                }
            }
            return false;
        }

        if ($this->_memcache->replace($this->_key($key), $var, empty($this->_params['compression']) ? 0 : MEMCACHE_COMPRESSED, $expire)) {
            if ($this->_large && !isset($this->_noexist[$key . '_os'])) {
                $this->_memcache->delete($this->_key($key . '_os'));
            }
            return true;
        }

        return false;
    }

    /**
     * Obtain lock on a key.
     *
     * @param string $key  The key to lock.
     */
    function lock($key)
    {
        /* Lock will automatically expire after 10 seconds. */
        while ($this->_memcache->add($this->_key($key . '_l'), 1, 0, 10) === false) {
            /* Wait 0.005 secs before attempting again. */
            usleep(5000);
        }
    }

    /**
     * Release lock on a key.
     *
     * @param string $key  The key to lock.
     */
    function unlock($key)
    {
        $this->_memcache->delete($this->_key($key . '_l'), 0);
    }

    /**
     * Mark all entries on a memcache installation as expired.
     */
    function flush()
    {
        $this->_memcache->flush();
    }

    /**
     * Get the statistics output from the current memcache pool.
     *
     * @return array  The output from Memcache::getExtendedStats() using the
     *                current Horde configuration values.
     */
    function stats()
    {
        return $this->_memcache->getExtendedStats();
    }

    /**
     * Obtains the md5 sum for a key.
     *
     * @access private
     *
     * @param string $key  The key.
     *
     * @return string  The corresponding memcache key.
     */
    function _key($key)
    {
        return md5($this->_params['prefix'] . $key);
    }

    /**
     * Returns the key listing of all key IDs for an oversized item.
     *
     * @access private
     *
     * @return array  The array of key IDs.
     */
    function _getOSKeyArray($key, $length)
    {
        $ret = array();
        for ($i = 0; $i < $length; ++$i) {
            $ret[] = $key . '_s' . ($i + 1);
        }
        return $ret;
    }

}
