<?php
/**
 * The IMAP_Cache:: class facilitates in caching output from the PHP imap
 * extension in the current session.
 *
 * $Horde: framework/IMAP/IMAP/Cache.php,v 1.4.12.15 2009-01-06 15:23:11 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Cache {

    /**
     * Pointer to the session cache.
     *
     * @var array
     */
    var $_cache;

    /**
     * The cached results of imap_status() calls.
     *
     * @var array
     */
    var $_statuscache = array();

    /**
     * Returns a reference to the global IMAP_Cache object, only creating
     * it if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $imap_cache = &IMAP_Cache::singleton();
     *
     * @return IMAP_Cache  The IMAP_Cache instance.
     */
    function &singleton()
    {
        static $object;

        if (!isset($object)) {
            $object = new IMAP_Cache();
        }

        return $object;
    }

    /**
     * Constructor
     */
    function IMAP_Cache()
    {
        if (!isset($_SESSION['imap_cache'])) {
            $_SESSION['imap_cache'] = array();
        }
        $this->_cache = &$_SESSION['imap_cache'];
    }

    /**
     * Get data from the cache.
     *
     * @param resource $imap   The IMAP resource stream.
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     * @param string $key      The name of a specific entry to return.
     * @param boolean $check   Check for updated mailbox?
     *
     * @return mixed  The data requested, or false if not available.
     */
    function getCache($imap, $mailbox, $key = null, $check = true)
    {
        if (isset($this->_cache[$mailbox])) {
            if (!$check || $this->checkCache($imap, $mailbox)) {
                $ptr = &$this->_cache[$mailbox];
                if (!is_null($key)) {
                    if (isset($ptr['d'][$key])) {
                        return $ptr['d'][$key];
                    }
                } else {
                    return $ptr['d'];
                }
            }
        }
        return false;
    }

    /**
     * Is the cache information up-to-date?
     *
     * @param resource $imap   The IMAP resource stream.
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     * @param boolean $update  Should the cache ID string be updated?
     *
     * @return boolean  True if cache information up-to-date, false if not.
     */
    function checkCache($imap, $mailbox, $update = false)
    {
        if (isset($this->_cache[$mailbox])) {
            $id = $this->_getCacheID($imap, $mailbox);
            if ($this->_cache[$mailbox]['k'] == $id) {
                return true;
            } elseif ($update) {
                $this->storeCache($imap, $mailbox);
            }
        } elseif ($update) {
            $this->storeCache($imap, $mailbox);
        }
        return false;
    }

    /**
     * Store data in the cache.
     *
     * @param resource $imap   The IMAP resource stream.
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     * @param array $values    The data to add to the cache.
     */
    function storeCache($imap, $mailbox, $values = array())
    {
        if (!isset($this->_cache[$mailbox])) {
            $this->_cache[$mailbox] = array('d' => array());
        }
        $ptr = &$this->_cache[$mailbox];
        $ptr = array(
            'k' => $this->_getCacheID($imap, $mailbox),
            'd' => array_merge($ptr['d'], $values)
        );
    }

    /**
     * Returns and caches the results of an imap_status() call.
     *
     * @since Horde 3.1.2
     *
     * @param resource $imap   The IMAP resource string.
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     *
     * @return stdClass  The imap_status() object or the empty string.
     */
    function getStatus($imap, $mailbox)
    {
        if (!isset($this->_statuscache[$mailbox])) {
            $this->_statuscache[$mailbox] = @imap_status($imap, $mailbox, SA_ALL);
            if (!$this->_statuscache[$mailbox]) {
                Horde::logMessage(imap_last_error(), __FILE__, __LINE__, PEAR_LOG_NOTICE);
            }
        }
        return $this->_statuscache[$mailbox];
    }

    /**
     * Generate the unique ID string for the mailbox.
     *
     * @access private
     *
     * @param resource $imap   The IMAP resource stream.
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     *
     * @return string  A unique string for the current state of the mailbox.
     */
    function _getCacheID($imap, $mailbox)
    {
        $this->getStatus($imap, $mailbox);
        if ($this->_statuscache[$mailbox]) {
            $ob = $this->_statuscache[$mailbox];
            return implode('|', array($ob->messages, $ob->uidnext, $ob->uidvalidity));
        } else {
            return $mailbox;
        }
    }

}
