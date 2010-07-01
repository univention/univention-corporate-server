<?php

require_once 'Horde/IMAP/Cache.php';

/**
 * The IMP_IMAP_Cache:: class extends Horde's IMAP_Cache:: class to add extra
 * IMP-specific functionality.
 *
 * $Horde: imp/lib/IMAP/Cache.php,v 1.36.2.6 2009-03-10 05:46:40 slusarz Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.2
 * @package Horde_IMAP
 */
class IMP_IMAP_Cache extends IMAP_Cache {

    /**
     * The cached results of imap_status() calls.
     *
     * @var array
     */
    var $_statuscache = array();

    /**
     * Cached results for the imap_search() call to determine arrival time.
     *
     * @var $_arrival
     */
    var $_arrival = array();

    /**
     * Has the shutdown function been registered?
     *
     * @var mixed
     */
    var $_tosave = false;

    /**
     * Use Horde_Cache?
     *
     * @var boolean
     */
    var $_usecache = false;

    /**
     * Returns a reference to the global IMP_IMAP_Cache object, only creating
     * it if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $imap_cache = &IMP_IMAP_Cache::singleton();
     *
     * @return IMP_IMAP_Cache  The global IMP_IMAP_Cache instance.
     */
    function &singleton()
    {
        static $object;

        if (!isset($object)) {
            $object = new IMP_IMAP_Cache();
        }

        return $object;
    }

    /**
     * Constructor
     */
    function IMP_IMAP_Cache()
    {
        $this->_usecache = !empty($GLOBALS['conf']['mlistcache']['use_mlistcache']) &&
                           ($GLOBALS['conf']['cache']['driver'] != 'none');

        parent::IMAP_Cache();
    }

    /**
     * Get data from the cache.
     *
     * @param resource $imap   The IMAP resource stream (not needed).
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     * @param string $key      The name of a specific entry to return.
     * @param boolean $check   Check for updated mailbox?
     *
     * @return mixed  The data requested, or false if not available.
     */
    function getCache($imap, $mailbox, $key = null, $check = true)
    {
        $imp_imap = &IMP_IMAP::singleton();
        $res = parent::getCache($imp_imap->stream(), $mailbox, $key, $check);
        if ($this->_usecache &&
            ($res === false) &&
            !isset($this->_cache[$mailbox])) {
            require_once 'Horde/Cache.php';
            $cache = &Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'], Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
            $res = $cache->get($this->_getHordeCacheID($mailbox), $GLOBALS['conf']['mlistcache']['lifetime']);
            if (($res === false) || !strval($res)) {
                $this->_cache[$mailbox] = array('d' => array(), 'k' => null);
            } else {
                require_once 'Horde/Serialize.php';
                $this->_cache[$mailbox] = Horde_Serialize::unserialize($res, SERIALIZE_BASIC);
                $res = parent::getCache($imp_imap->stream(), $mailbox, $key, $check);
                Horde::logMessage('Retrieved ' . $mailbox . ' from cache.', __FILE__, __LINE__, PEAR_LOG_DEBUG);
            }
        }
        return $res;
    }

    /**
     * Store data in the cache.
     *
     * @param resource $imap   The IMAP resource stream (not needed).
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     * @param array $values    The data to add to the cache.
     */
    function storeCache($imap, $mailbox, $values = array())
    {
        $this->_cache[$mailbox] = array(
            'k' => $this->_getCacheID($imap, $mailbox),
            'd' => $values
        );
        $this->_saveCache($mailbox);
    }

    /**
     * Store data in the cache, preserving any data already in the cache
     * entry and not altering the current cache key.
     *
     * @param resource $imap   The IMAP resource stream (not needed).
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     * @param array $values    The data to add to the cache.
     */
    function updateCache($imap, $mailbox, $values = array())
    {
        if (isset($this->_cache[$mailbox])) {
            $ptr = &$this->_cache[$mailbox];
            $ptr['d'] = array_merge($ptr['d'], $values);
            $this->_saveCache($mailbox);
        } else {
            $this->storeCache($imap, $mailbox, $values);
        }
    }

    /**
     * Flag cached entries as expired.
     *
     * @param string $mailbox  A mailbox name.
     * @param integer $mask    A bitmask for the following updates:
     * <pre>
     * 1 = Expire cache entries
     * 2 = Expire imap_status() entries
     * 4 = Expire getMailboxArrival() entries
     * </pre>
     */
    function expireCache($mailbox, $mask = 0)
    {
        $full_mailbox = IMP::serverString($mailbox);

        if ($mask & 1) {
            unset($this->_cache[$full_mailbox]);
            $this->_saveCache($full_mailbox);
        }

        if ($mask & 2) {
            unset($this->_statuscache[$full_mailbox]);
        }

        if ($mask & 4) {
            unset($this->_arrival[$mailbox]);
        }
    }

    /**
     * Returns and caches the results of an imap_status() call.
     *
     * @param resource $imap   The IMAP resource stream (not needed).
     * @param string $mailbox  A mailbox name.
     *
     * @return stdClass  The imap_status() object or the empty string.
     */
    function getStatus($imap, $mailbox)
    {
        $mailbox = IMP::serverString($mailbox);
        if (!isset($this->_statuscache[$mailbox]) &&
            !$GLOBALS['imp_search']->isSearchMbox(substr($mailbox, strpos($mailbox, '}') + 1))) {
            $imp_imap = &IMP_IMAP::singleton();
            $this->_statuscache[$mailbox] = @imap_status($imp_imap->stream(), $mailbox, SA_ALL);
            if (!$this->_statuscache[$mailbox]) {
                unset($this->_statuscache[$mailbox]);
                if ($err = imap_last_error()) {
                    Horde::logMessage($err, __FILE__, __LINE__, PEAR_LOG_NOTICE);
                }
            }
        }

        return empty($this->_statuscache[$mailbox]) ? '' : $this->_statuscache[$mailbox];
    }

    /**
     * Generate the unique ID string for the mailbox.
     *
     * @access private
     *
     * @param resource $imap   The IMAP resource stream (not needed).
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     *
     * @return string  A unique string for the current state of the mailbox.
     */
    function _getCacheID($imap, $mailbox)
    {
        $this->getStatus($imap, $mailbox);
        if (!empty($this->_statuscache[$mailbox])) {
            $ob = $this->_statuscache[$mailbox];
            $sortpref = IMP::getSort(substr($mailbox, strpos($mailbox, '}') + 1));
            return implode('|', array($ob->messages, $ob->uidnext, $ob->uidvalidity, $sortpref['by'], $sortpref['dir']));
        } else {
            return $mailbox;
        }
    }

    /**
     * Returns the list of message UIDs in arrival order.
     *
     * @param string $mailbox   The mailbox to query.
     * @param boolean $delhide  Use this value instead of the value from
     *                          IMP::hideDeleteMsgs().
     * @param string $base      The base IMAP search string - defaults to all.
     *
     * @return array  See imap_search().
     */
    function getMailboxArrival($mailbox, $delhide = null, $base = 'ALL')
    {
        $search = array(strtoupper(trim($base)));

        if ($delhide === null) {
            $delhide = IMP::hideDeletedMsgs();
        }

        if ($delhide) {
            $search[] = 'UNDELETED';
        }

        $cache_id = serialize($search);

        if (!isset($this->_arrival[$mailbox][$cache_id])) {
            $imp_imap = &IMP_IMAP::singleton();
            if ($imp_imap->changeMbox($mailbox, IMP_IMAP_AUTO)) {
                $res = @imap_search($imp_imap->stream(), implode(' ', $search), SE_UID);
                if (!isset($this->_arrival[$mailbox])) {
                    $this->_arrival[$mailbox] = array();
                }
            } else {
                $res = array();
            }
            $this->_arrival[$mailbox][$cache_id] = (empty($res)) ? array() : $res;
        }

        return $this->_arrival[$mailbox][$cache_id];
    }

    /**
     * Get the unique mailbox ID for the current mailbox status. Needed
     * because some applications (such as DIMP) may be keeping more than 1
     * copy of IMAP data (i.e. on the browser, on the server).
     *
     * @since IMP 4.2
     *
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     *
     * @return string  A unique string for the current state of the mailbox.
     */
    function getCacheID($mailbox)
    {
        return $this->_getCacheID(null, $mailbox);
    }

    /**
     * Register the shutdown save function.
     *
     * @access private
     *
     * @var string $mailbox  The mailbox item to save.
     */
    function _saveCache($mailbox)
    {
        if ($this->_tosave === false) {
            register_shutdown_function(array(&$this, '_shutdown'));
            $this->_tosave = array();
        }
        $this->_tosave[$mailbox] = true;
    }

    /**
     * Shutdown function
     *
     * @access private
     */
    function _shutdown()
    {
        if (!$this->_usecache) {
            return;
        }

        $in_session = array();

        require_once 'Horde/Cache.php';
        require_once 'Horde/Serialize.php';
        $cache = &Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'], Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
        foreach (array_keys($this->_tosave) as $val) {
            $cacheid = $this->_getHordeCacheID($val);
            if (isset($this->_cache[$val])) {
                if ($cache->set($cacheid, Horde_Serialize::serialize($this->_cache[$val], SERIALIZE_BASIC), $GLOBALS['conf']['mlistcache']['lifetime'])) {
                    Horde::logMessage('Stored ' . $val . ' in cache. [User: ' . $_SESSION['imp']['uniquser'] . ']', __FILE__, __LINE__, PEAR_LOG_DEBUG);
                }
                $in_session[] = $val;
            } else {
                $cache->expire($cacheid);
            }
        }

        /* Unset all other mailboxes in the current session. */
        foreach (array_diff(array_keys($this->_cache), $in_session) as $k) {
            unset($this->_cache[$k]);
        }
    }

    /**
     * Get the cache ID to use for Horde_Cache.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox to store.
     */
    function _getHordeCacheID($mailbox)
    {
        return 'imp_imapcache_ ' . $_SESSION['imp']['uniquser'] . '|' . $mailbox;
    }

}
