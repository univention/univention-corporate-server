<?php

require_once 'Horde/MIME/Structure.php';
require_once IMP_BASE . '/lib/MIME/Headers.php';

/**
 * The IMP_MessageCache:: class contains all functions related to caching
 * information about RFC 2822 messages across sessions.
 *
 * $Horde: imp/lib/IMAP/MessageCache.php,v 1.1.2.13 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.2
 * @package IMP
 */
class IMP_MessageCache {

    /**
     * The Horde_Cache object to use.
     *
     * @var Horde_Cache
     */
    var $_cache;

    /**
     * The list of items to save on shutdown.
     *
     * @var array
     */
    var $_save;

    /**
     * The working data for the current pageload.  All changes take place to
     * this data.
     *
     * @var array
     */
    var $_data = array();

    /**
     * The list of cache slices loaded.
     *
     * @var array
     */
    var $_loaded = array();

    /**
     * The mapping of UIDs to slices.
     *
     * @var array
     */
    var $_slicemap = array();

    /**
     * The default slicesize to use.
     *
     * @var integer
     */
    var $_slicesize = 100;

    /**
     * Attempts to return a reference to a concrete IMP_MessageCache instance.
     * It will only create a new instance if no IMP_MessageCache instance with
     * the same parameters currently exists.
     *
     * This method must be invoked as: $var = &IMP_MessageCache::singleton();
     *
     * @return mixed  The created concrete IMP_MessageCache instance, or false
     *                on error.
     */
    function &singleton()
    {
        static $instance;

        if (!isset($instance)) {
            $instance = new IMP_MessageCache();
        }

        return $instance;
    }

    /**
     * Constructor.
     */
    function IMP_MessageCache()
    {
        if (empty($GLOBALS['conf']['msgcache']['use_msgcache'])) {
            return;
        }

        $driver = $GLOBALS['conf']['cache']['driver'];
        if ($driver == 'none') {
            return;
        }

        require_once 'Horde/Cache.php';
        require_once 'Horde/Serialize.php';

        /* Initialize the Cache object. */
        $this->_cache = &Horde_Cache::singleton($driver, Horde::getDriverConfig('cache', $driver));
        if (is_a($this->_cache, 'PEAR_Error')) {
            Horde::fatal($this->_cache, __FILE__, __LINE__);
        }

        /* Memcache is the only cache backend where size matters - if we have
         * a bunch of large data objects, it will quickly fill up the
         * available slab allocations. Use a smaller size object instead. */
        if ($driver == 'memcache') {
            $this->_slicesize = 25;
        }

        /* Determine the serialization configuration once per session. */
        if (!isset($_SESSION['imp']['msgcache'])) {
            $ptr = &$GLOBALS['conf']['msgcache'];
            $_SESSION['imp']['msgcache'] = array(
                'compress' => null,
                'lifetime' => empty($ptr['lifetime']) ? 0 : $ptr['lifetime'],
                'prune' => array(),
            );
            if (!empty($ptr['use_compress'])) {
                require_once HORDE_BASE . '/lib/version.php';
                switch ($ptr['compress']['method']) {
                case 'gzip':
                    if (Horde_Serialize::hasCapability(SERIALIZE_GZ_COMPRESS) &&
                        (version_compare(HORDE_VERSION, '3.1.0') >= 0)) {
                        $_SESSION['imp']['msgcache']['compress'] = SERIALIZE_GZ_DEFLATE;
                    } else {
                        Horde::logMessage('Could not use gzip compression in IMP_MessageCache::.', __FILE__, __LINE__, PEAR_LOG_NOTICE);
                    }
                    break;

                case 'lzf':
                    if (defined('SERIALIZE_LZF') &&
                        Horde_Serialize::hasCapability(SERIALIZE_LZF)) {
                        $_SESSION['imp']['msgcache']['compress'] = SERIALIZE_LZF;
                    } else {
                        Horde::logMessage('Could not use lzf compression in IMP_MessageCache::.', __FILE__, __LINE__, PEAR_LOG_NOTICE);
                    }
                    break;
                }
            }
        }
    }

    /**
     * Create the unique ID used to store the data in the cache
     *
     * @access private
     *
     * @param string $mailbox  The mailbox to cache.
     * @param mixed $slice     The mailbox slice ID.
     *
     * @return string  The cache ID.
     */
    function _getCacheID($mailbox, $slice)
    {
        /* Cache ID = prefix | username | mailbox | slice */
        return 'imp_mailboxcache|' . $_SESSION['imp']['uniquser'] . '|' . $mailbox . '|' . $slice;
    }

    /**
     * Returns the UID validity timestamp of the given mailbox.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox to query.
     *
     * @return integer  The UID validity timestamp.
     */
    function _getUIDValidity($mailbox)
    {
        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();
        $status = $imap_cache->getStatus(null, $mailbox);
        return (!empty($status)) ? $status->uidvalidity : false;
    }

    /**
     * Retrieve the imap overview information for the given mailbox and
     * message IDs.
     *
     * @param string $mailbox  An IMAP mailbox string.
     * @param array $uids      The list of message IDS to retrieve overview
     *                         information for.
     * @param integer $mask    A bitmask indicating the fields that should be
     *                         added to the message data. The bitmasks are
     *                         as follows:
     * <pre>
     * 1 =  imap_fetch_overview() information
     *       FIELDS: subject, from, to, date, message_id, references,
     *               in_reply_to, size, uid, flagged, answered, deleted, seen,
     *               draft
     * 2 =   IMAP mailbox arrival information
     *       FIELDS: msgno
     *       NOTE: This option ALWAYS requires an access to the IMAP server to
     *             obtain the message list (sorted by arrival).
     * 4 =   Mailbox information
     *       FIELDS: mailbox
     * 8 =   Mesage structure information (MIME_Message:: object)
     *       FIELDS: structure
     * 16 =  Cached preview data (using prefs value)
     *       FIELDS: preview
     * 32 =  Header information (IMP_Headers:: object)
     *       FIELDS: header
     * 64 =  Cached preview data (overrides prefs value)
     *       FIELDS: preview
     * 128 = Cached IMP_UI_Mailbox::getFrom() data
     *       FIELDS: getfrom
     * </pre>
     *
     * @return array  An array of stdClass objects with the UID of the message
     *                as the key; the stdClass objects contain the fields
     *                requested via the $mask parameter or false if the UID
     *                does not exist on the server.
     */
    function retrieve($mailbox, $uids, $mask = 0)
    {
        if (empty($uids) || ($mask == 0)) {
            return array();
        }

        $avail_ids = $this->_loadUIDs($mailbox, $uids);
        $bad_ids = $return_array = $save = array();
        $prev_unread = false;

        $imp_imap = &IMP_IMAP::singleton();
        $imp_imap->changeMbox($mailbox, IMP_IMAP_AUTO);
        $stream = $imp_imap->stream();

        $mptr = &$this->_data[$mailbox];

        /* Obtain imap_fetch_overview() information. */
        if ($mask & 1) {
            $get_ids = array_diff($uids, $avail_ids);
            foreach ($avail_ids as $val) {
                if (!isset($mptr[$val]->uid)) {
                    $get_ids[] = $val;
                }
            }

            /* Grab any new overview information we may need. */
            if (!empty($get_ids)) {
                $old_error = error_reporting(0);
                $overview = imap_fetch_overview($stream, implode(',', $get_ids), FT_UID);
                error_reporting(0);

                reset($overview);
                while (list(,$val) = each($overview)) {
                    if (isset($mptr[$val->uid])) {
                        $ptr = &$mptr[$val->uid];
                        foreach (get_object_vars($val) as $key => $var) {
                            $ptr->$key = $var;
                        }
                    } else {
                        $mptr[$val->uid] = $val;
                        $ptr = &$mptr[$val->uid];
                    }

                    // There should not be any 8bit characters here.  If there
                    // is, we either need to convert from the default charset
                    // or replace with question marks.
                    foreach (array('subject', 'from', 'to') as $val2) {
                        if (!isset($ptr->$val2)) {
                            continue;
                        }

                        if (!empty($GLOBALS['mime_headers']['default_charset'])) {
                            $ptr->$val2 = String::convertCharset($ptr->$val2, $GLOBALS['mime_headers']['default_charset']);
                        } else {
                            $ptr->$val2 = preg_replace('/[\x80-\xff]/', '?', $ptr->$val2);
                        }
                    }

                    if (isset($this->_cache)) {
                        unset($ptr->msgno, $ptr->recent);
                    }
                    $save[] = $val->uid;
                }

                /* This is the list of IDs that are invalid. */
                if (count($save) != count($get_ids)) {
                    $bad_ids = array_values(array_diff($get_ids, $save));
                    foreach ($bad_ids as $val) {
                        unset($uids[$val]);
                    }
                }
            }
            $prev_unread = $GLOBALS['prefs']->getValue('preview_show_unread');
        }

        /* Add 'structure' information. */
        if ($mask >= 8) {
            foreach ($uids as $val) {
                $ptr = &$mptr[$val];
                if ($mask & 8) {
                    // Check for invalid data.
                    if (isset($ptr->structure) && !is_object($ptr->structure)) {
                        unset($ptr->structure);
                    }

                    if (!isset($ptr->structure)) {
                        $old_error = error_reporting(0);
                        $structure = imap_fetchstructure($stream, $val, FT_UID);
                        error_reporting($old_error);

                        /* Only retrieve if there is a valid structure. */
                        if ($structure) {
                            $ptr->structure = MIME_Structure::parse($structure);
                            $save[] = $val;
                        }
                    }
                }

                if (($mask & 16) || ($mask & 64)) {
                    if (isset($ptr->preview)) {
                        if ($prev_unread && !($mask & 64) && $ptr->seen) {
                            unset($ptr->preview);
                            $save[] = $val;
                        }
                    } else {
                        if (!$prev_unread || !$ptr->seen || ($mask & 64)) {
                            list($ptr->preview, $ptr->preview_cut) = $this->_generatePreview($mailbox, $val);
                            $save[] = $val;
                        }
                    }
                }

                if ($mask & 32) {
                    // Check for invalid data.
                    if (isset($ptr->header) && !is_object($ptr->header)) {
                        unset($ptr->header);
                    }

                    if (!isset($ptr->header)) {
                        $ptr->header = new IMP_Headers($val);
                        $ptr->header->buildHeaders();
                        $save[] = $val;
                    }
                }
            }
        }

        if ($mask & 128) {
            require_once 'Horde/Identity.php';
            require_once IMP_BASE . '/lib/UI/Mailbox.php';
            $identity = &Identity::singleton(array('imp', 'imp'));
            $imp_ui = new IMP_UI_Mailbox($mailbox, NLS::getCharset(), $identity);
        }

        /* Get the return array now. */
        foreach ($uids as $val) {
            if (isset($mptr[$val])) {
                $vptr = &$mptr[$val];
                if (($mask & 128) && !isset($vptr->getfrom)) {
                    $vptr->getfrom = $imp_ui->getFrom($vptr);
                    $save[] = $val;
                }
                $return_array[$val] = $vptr;
                if ($mask & 4) {
                    $return_array[$val]->mailbox = $mailbox;
                }
            }
        }

        /* Determine if we need to add additional fields to the data. */
        if (isset($this->_cache) && ($mask & 2)) {
            require_once IMP_BASE . '/lib/IMAP/Cache.php';
            $imap_cache = &IMP_IMAP_Cache::singleton();
            foreach ($imap_cache->getMailboxArrival($mailbox) as $key => $val) {
                if (isset($return_array[$val])) {
                    $return_array[$val]->msgno = ++$key;
                }
            }
        }

        $this->_saveMailbox($mailbox, $save);

        /* Readd "bad" IDs now. */
        foreach ($bad_ids as $val) {
            $return_array[$val] = false;
        }

        return $return_array;
    }

    /**
     * Load the given mailbox by either regenerating from the cache or using
     * the current in-memory cache.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox to load.
     * @param array $uids      The UIDs to load.
     */
    function _loadMailbox($mailbox, $uids)
    {
        if (isset($this->_cache)) {
            if (!isset($this->_data[$mailbox]['__uidvalid'])) {
                $this->_data[$mailbox]['__uidvalid'] = $this->_getUIDValidity($mailbox);
            }

            foreach (array_keys(array_flip($this->_getCacheSlices($mailbox, $uids))) as $val) {
                $this->_loadMailboxSlice($mailbox, $val);
            }
        } else {
            if (!isset($this->_data[$mailbox])) {
                $this->_data[$mailbox] = array();
            }
        }
    }

    /**
     * Load the given mailbox by regenerating from the cache slices.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox to load.
     * @param integer $slice   The slice to load.
     */
    function _loadMailboxSlice($mailbox, $slice)
    {
        /* Get the unique cache identifier for this mailbox. */
        $cache_id = $this->_getCacheID($mailbox, $slice);

        if (!empty($this->_loaded[$cache_id])) {
            return;
        }
        $this->_loaded[$cache_id] = true;
        $prune = &$_SESSION['imp']['msgcache']['prune'];

        if (!isset($this->_data[$mailbox])) {
            $this->_data[$mailbox] = array();
        }

        /* Attempt to grab data from the cache. */
        $data = $this->_cache->get($cache_id, $_SESSION['imp']['msgcache']['lifetime']);
        if ($data == false) {
            $prune[$cache_id] = true;
            return;
        }

        $data = Horde_Serialize::unserialize($data, SERIALIZE_BASIC);
        if (is_array($data)) {
            $uidvalid = empty($data['__uidvalid']) ? 0 : $data['__uidvalid'];
            unset($data['__uidvalid']);

            /* Check UID validity and do garbage collection. */
            if (!$uidvalid ||
                ($uidvalid != $this->_data[$mailbox]['__uidvalid'])) {
                $purge = array_keys($data);
                $this->_cache->expire($cache_id);
            } else {
                /* Perform garbage collection on slice once a login. */
                if (!isset($prune[$cache_id])) {
                    $imap_cache = &IMP_IMAP_Cache::singleton();
                    $all_uids = $imap_cache->getMailboxArrival($mailbox, false);
                    $changed = false;
                    foreach (array_diff(array_keys($data), $all_uids) as $val) {
                        unset($data[$val]);
                        $changed = true;
                    }
                    if ($changed) {
                        $this->_saveMailbox($mailbox, array_keys($data));
                    }
                }
                $this->_data[$mailbox] += $data;
                Horde::logMessage('Retrieved slice ' . $slice . ' of message data from ' . $mailbox . ' in cache. [User: ' . $_SESSION['imp']['uniquser'] . ']', __FILE__, __LINE__, PEAR_LOG_DEBUG);
            }
        }
        $prune[$cache_id] = true;
    }

    /**
     * Given a list of UIDs, determine the slices that need to be loaded.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox.
     * @param array $uids      A list of UIDs.
     * @param boolean $set     Set the slice information in $_slicemap?
     *
     * @return array  UIDs as the keys, the slice number as the value.
     */
    function _getCacheSlices($mailbox, $uids, $set = false)
    {
        $cache_id = $this->_getCacheID($mailbox, 'slicemap');

        if (!isset($this->_slicemap[$mailbox])) {
            $this->_slicemap[$mailbox] = array('__count' => 0);
            $data = $this->_cache->get($cache_id, $_SESSION['imp']['msgcache']['lifetime']);
            if ($data != false) {
                $slice = Horde_Serialize::unserialize($data, SERIALIZE_BASIC);
                if (is_array($slice)) {
                    $this->_slicemap[$mailbox] = $slice;
                }
            }
        }

        $lookup = array();
        if (!empty($uids)) {
            $ptr = &$this->_slicemap[$mailbox];
            $pcount = $ptr['__count'];
            foreach ($uids as $val) {
                if (isset($ptr[$val])) {
                    $lookup[$val] = $ptr[$val];
                } else {
                    $lookup[$val] = intval($pcount++ / $this->_slicesize);
                    if ($set) {
                        $ptr[$val] = $lookup[$val];
                    }
                }
            }
            if ($set) {
                $ptr['__count'] = $pcount;
            }
        }
        return $lookup;
    }

    /**
     * Given a list of UIDs, unpacks the messages from stored cache data and
     * returns the list of UIDs that exist in the cache.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox.
     * @param array $uids      The list of UIDs to load.
     *
     * @return array  The list of UIDs with cache entries.
     */
    function _loadUIDs($mailbox, $uids)
    {
        $this->_loadMailbox($mailbox, $uids);
        if (count($this->_data[$mailbox]) == 0) {
            return array();
        }

        $compress = isset($this->_cache) ? $_SESSION['imp']['msgcache']['compress'] : null;
        $loaded = array();
        $ptr = &$this->_data[$mailbox];

        foreach ($uids as $val) {
            if (isset($ptr[$val])) {
                if (is_object($ptr[$val])) {
                    $loaded[] = $val;
                } elseif (!is_null($compress)) {
                    $ptr[$val] = Horde_Serialize::unserialize($ptr[$val], array($compress, SERIALIZE_BASIC));
                    if (is_a($ptr[$val], 'PEAR_Error')) {
                        unset($ptr[$val]);
                    } else {
                        $loaded[] = $val;
                    }
                } else {
                    unset($ptr[$val]);
                }
            }
        }

        return $loaded;
    }

    /**
     * Register mailbox data to be saved to cache at the end of a pageload.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox to save.
     * @param array $uids      A specific list of UIDs that have been altered.
     *                         in the given mailbox.
     */
    function _saveMailbox($mailbox, $uids)
    {
	    if (!isset($this->_cache) || empty($uids)) {
            return;
        }

        if (!isset($this->_save)) {
            register_shutdown_function(array(&$this, '_addCacheShutdown'));
        }

        $this->_save[$mailbox] = isset($this->_save[$mailbox]) ? array_merge($this->_save[$mailbox], $uids) : $uids;
    }

    /**
     * Update message flags in the cache.
     *
     * @param string $mailbox  The mailbox.
     * @param array $uids      The list of message UIDs to update.
     * @param array $flags     The flags to set. Valid arguments:
     *                         seen, deleted, flagged, answered, draft
     * @param boolean $set     True to set the flag, false to clear flag.
     */
    function updateFlags($mailbox, $uids, $flags, $set)
    {
        $uids = $this->_loadUIDs($mailbox, $uids);
        if (empty($uids)) {
            return;
        }

        $save = array();

        foreach ($uids as $id) {
            foreach (array_map(array('String', 'lower'), $flags) as $val) {
                $newval = intval($set);
                if (!isset($this->_data[$mailbox][$id]->$val) ||
                    $this->_data[$mailbox][$id]->$val != $newval) {
                    $this->_data[$mailbox][$id]->$val = $newval;
                    $save[] = $id;
                }
            }
        }

        $this->_saveMailbox($mailbox, $save);
    }

    /**
     * Delete messages in the cache.
     *
     * @param string $mailbox  The mailbox.
     * @param array $uids      The list of message UIDs to delete.
     */
    function deleteMsgs($mailbox, $uids)
    {
        $this->_loadMailbox($mailbox, $uids);
        if (count($this->_data[$mailbox]) == 0) {
            return;
        }

        $save = array();

        foreach ($uids as $id) {
            if (isset($this->_data[$mailbox][$id])) {
                $save[] = $id;
            }
            if (isset($this->_data[$mailbox])) {
                unset($this->_data[$mailbox][$id]);
            }
            if (isset($this->_slicemap[$mailbox][$id])) {
                unset($this->_slicemap[$mailbox][$id]);
            }
        }

        if (isset($this->_cache) && !empty($save)) {
            // Check for slices with less than 5 entries.
            // Ignore the last slice (since it hasn't been filled yet)
            $ptr = &$this->_slicemap[$mailbox];
            foreach (array_diff(array_keys(array_flip($this->_getCacheSlices($mailbox, $save))), array(end($ptr))) as $slice) {
                $keys = array_keys($ptr, $slice);
                if ($keys < 5) {
                    foreach ($keys as $val) {
                        unset($ptr[$val]);
                    }
                    $save += $keys;
                }
            }
            $this->_saveMailbox($mailbox, $save);
        }
    }

    /**
     * Saves items to the cache at shutdown.
     *
     * @access private
     */
    function _addCacheShutdown()
    {
        $compress = $_SESSION['imp']['msgcache']['compress'];
        $lifetime = $_SESSION['imp']['msgcache']['lifetime'];

        foreach ($this->_save as $mbox => $uids) {
            $dptr = &$this->_data[$mbox];
            $sptr = &$this->_slicemap[$mbox];

            $setcount = 0;

            foreach (array_keys(array_flip($this->_getCacheSlices($mbox, $uids, true))) as $slice) {
                $data = array();

                foreach (array_keys($sptr, $slice) as $uid) {
                    /* Compress individual UID entries. We will worry about
                     * error checking when decompressing (cache data will
                     * automatically be invalidated then). */
                    if (isset($dptr[$uid])) {
                        $data[$uid] = ($compress && is_object($dptr[$uid])) ? Horde_Serialize::serialize($dptr[$uid], array(SERIALIZE_BASIC, $compress)) : $dptr[$uid];
                    }
                }

                $cacheid = $this->_getCacheID($mbox, $slice);
                if (empty($data)) {
                    // If empty, we can expire the cache.
                    $this->_cache->expire($cacheid);
                } else {
                    $data['__uidvalid'] = $dptr['__uidvalid'];
                    if ($this->_cache->set($cacheid, Horde_Serialize::serialize($data, SERIALIZE_BASIC), $lifetime)) {
                        ++$setcount;
                    }
                }
            }

            if ($setcount) {
                Horde::logMessage('Stored ' . $setcount . ' slice(s) of message data from ' . $mbox . ' in cache. [User: ' . $_SESSION['imp']['uniquser'] . ']', __FILE__, __LINE__, PEAR_LOG_DEBUG);
            }

            // Save the slicemap
            $this->_cache->set($this->_getCacheID($mbox, 'slicemap'), Horde_Serialize::serialize($sptr, SERIALIZE_BASIC), $lifetime);
        }
    }

    /**
     * Generate the preview text.
     *
     * @access private
     *
     * @param string $mailbox  The mailbox.
     * @param integer $uid     The UID to generate a preview for.
     *
     * @return array  Array of the preview text and a flag if the preview has
     *                been cut down.
     */
    function _generatePreview($mailbox, $uid)
    {
        $ptext = '';
        $cut = false;

        $imp_imap = &IMP_IMAP::singleton();
        $imp_imap->changeMbox($mailbox, IMP_IMAP_READONLY);

        require_once IMP_BASE . '/lib/MIME/Contents.php';
        $imp_contents = &IMP_Contents::singleton($uid . IMP_IDX_SEP . $mailbox);
        if (is_a($imp_contents, 'PEAR_Error')) {
            return array('', false);
        }

        if (($mimeid = $imp_contents->findBody()) !== null) {
            $pmime = $imp_contents->getDecodedMIMEPart($mimeid);
            $ptext = $pmime->getContents();
            $ptext = String::convertCharset($ptext, $pmime->getCharset());
            if ($pmime->getType() == 'text/html') {
                require_once 'Horde/Text/Filter.php';
                $ptext = Text_Filter::filter($ptext, 'html2text',
                                             array('charset' => NLS::getCharset()));
            }

            $maxlen = empty($GLOBALS['conf']['msgcache']['preview_size'])
                ? $GLOBALS['prefs']->getValue('preview_maxlen')
                : $GLOBALS['conf']['msgcache']['preview_size'];
            if (String::length($ptext) > $maxlen) {
                $ptext = String::substr($ptext, 0, $maxlen) . ' ...';
                $cut = true;
            }
        }

        return array($ptext, $cut);
    }

    /**
     * Deletes mailboxes from the cache.
     *
     * @param array $mboxes  The list of mailboxes to delete.
     */
    function deleteMboxes($mboxes)
    {
        foreach ($mboxes as $val) {
            if (isset($this->_cache)) {
                $this->_getCacheSlices($val, array());
                foreach (array_keys(array_flip($this->_slicemap[$val])) as $slice) {
                    $this->_cache->expire($this->_getCacheID($val, $slice));
                }
                $this->_cache->expire($this->_getCacheID($val, 'slicemap'));
            }
            unset($this->_data[$val], $this->_loaded[$val], $this->_slicemap[$val]);
        }
    }

}
