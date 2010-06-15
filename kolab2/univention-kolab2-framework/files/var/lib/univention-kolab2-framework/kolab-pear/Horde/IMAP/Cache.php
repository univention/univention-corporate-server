<?php
/**
 * The IMAP_Cache:: class facilitates in caching output from the PHP imap
 * extension in the current session.
 *
 * $Horde: framework/IMAP/IMAP/Cache.php,v 1.4 2004/01/01 15:14:17 jan Exp $
 *
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Cache {

    /**
     * Pointer to the session cache.
     *
     * @var array $_cache
     */
    var $_cache;

    /**
     * Returns a reference to the global IMAP_Cache object, only creating
     * it if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $imap_cache = &IMAP_Cache::singleton();
     *
     * @access public
     *
     * @param optional array $params  Any parameters the constructor may need.
     *
     * @return object IMAP_Cache  The IMAP_Cache instance.
     */
    function &singleton($params = array())
    {
        static $object;

        if (!isset($object)) {
            $object = &new IMAP_Cache($params);
        }

        return $object;
    }

    /**
     * Constructor
     *
     * @access public
     *
     * @param optional array $params  Not used.
     */
    function IMAP_Cache($params = array())
    {
        if (!isset($_SESSION['imap_cache'])) {
            $_SESSION['imap_cache'] = array();
        }
        $this->_cache = &$_SESSION['imap_cache'];
    }

    /**
     * Get data from the cache.
     *
     * @access public
     *
     * @param resource &$imap          The IMAP resource stream.
     * @param string $mailbox          The full ({hostname}mailbox) mailbox
     *                                 name.
     * @param optional string $key     The name of a specific entry to return.
     * @param optional boolean $check  Check for updated mailbox?
     *
     * @return mixed  The data requested, or false if not available.
     */
    function getCache(&$imap, $mailbox, $key = null, $check = true)
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
     * @access public
     *
     * @param resource &$imap           The IMAP resource stream.
     * @param string $mailbox           The full ({hostname}mailbox) mailbox
     *                                  name.
     * @param optional boolean $update  Should the cache ID string be updated?
     *
     * @return boolean  True if cache information up-to-date, false if not. 
     */
    function checkCache(&$imap, $mailbox, $update = false)
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
     * @access public
     *
     * @param resource &$imap         The IMAP resource stream.
     * @param string $mailbox         The full ({hostname}mailbox) mailbox
     *                                name.
     * @param optional array $values  The data to add to the cache.
     */
    function storeCache(&$imap, $mailbox, $values = array())
    {
        $id = $this->_getCacheID($imap, $mailbox);
        if (!isset($this->_cache[$mailbox])) {
            $this->_cache[$mailbox] = array('k' => $id, 'd' => $values);
        } else {
            $ptr = &$this->_cache[$mailbox];
            $ptr['k'] = $id;
            $ptr['d'] = array_merge($values, $ptr['d']);
        }
    }

    /**
     * Generate the unique ID string for the mailbox.
     *
     * @access private
     *
     * @param resource &$imap  The IMAP resource stream.
     * @param string $mailbox  The full ({hostname}mailbox) mailbox name.
     *
     * @return string  A unique string for the current state of the mailbox.
     */
    function _getCacheID(&$imap, $mailbox)
    {
        $ob = @imap_status($imap, $mailbox, SA_MESSAGES | SA_RECENT | SA_UNSEEN | SA_UIDNEXT);
        return implode('|', array($ob->messages, $ob->recent, $ob->unseen, $ob->uidnext));
    }

}
