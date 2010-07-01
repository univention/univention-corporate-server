<?php
/**
 * $Horde: imp/lib/Mailbox.php,v 1.76.10.76 2009-03-04 21:16:02 slusarz Exp $
 *
 * @package IMP
 */

define('IMP_MAILBOX_DELETE', 0);
define('IMP_MAILBOX_EXPUNGE', 1);
define('IMP_MAILBOX_UPDATE', 2);
define('IMP_MAILBOX_FLAG', 3);

/**
 * The IMP_Mailbox:: class contains all code related to handling mailbox
 * access.
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_Mailbox {

    /**
     * The mailbox to work with.
     *
     * @var string
     */
    var $_mailbox;

    /**
     * The location in the sorted array we are at.
     *
     * @var integer
     */
    var $_arrayIndex = null;

    /**
     * The location of the last message we were at.
     *
     * @var integer
     */
    var $_lastArrayIndex = null;

    /**
     * Has _buildMailbox() been called?
     *
     * @var boolean
     */
    var $_build = false;

    /**
     * The array of sorted indices.
     *
     * @var array
     */
    var $_sorted = array();

    /**
     * The array of information about the sorted indices list.
     * Entries:
     *  'm' = Mailbox (if not exist, then use current mailbox)
     *
     * @var array
     */
    var $_sortedInfo = array();

    /**
     * If the cache has expired, make note so we know when to update vs.
     * overwrite.
     *
     * @var boolean
     */
    var $_cacheexpire = false;

    /**
     * Is this a search malbox?
     *
     * @var boolean
     */
    var $_searchmbox;

    /**
     * Attempts to return a reference to a concrete IMP_Mailbox instance.
     * It will only create a new instance if no IMP_Mailbox instance with
     * the same parameters currently exists.
     *
     * This method must be invoked as:
     *   $var = &IMP_Mailbox::singleton($mailbox[, $index]);
     *
     * @param string $mailbox  See IMP_Mailbox constructor.
     * @param integer $index   See IMP_Mailbox constructor.
     *
     * @return mixed  The created concrete IMP_Mailbox instance, or false
     *                on error.
     */
    function &singleton($mailbox, $index = null)
    {
        static $instances = array();

        if (!isset($instances[$mailbox])) {
            $instances[$mailbox] = new IMP_Mailbox($mailbox, $index);
        } elseif ($index !== null) {
            $instances[$mailbox]->setIndex($index);
        }

        return $instances[$mailbox];
    }

    /**
     * Constructor.
     *
     * @param string $mailbox  The mailbox to work with.
     * @param integer $index   The index of the current message. This will
     *                         cause IMP_Message to update the various message
     *                         arrays after each action.
     */
    function IMP_Mailbox($mailbox, $index = null)
    {
        $this->_mailbox = $mailbox;
        $this->_searchmbox = $GLOBALS['imp_search']->isSearchMbox($mailbox);

        /* Initialize mailbox. */
        if (!$this->_setSorted(1)) {
            $this->_buildMailbox();
        }

        if ($index !== null) {
            $this->setIndex($index);
        }
    }

    /**
     * The mailbox this object works with.
     *
     * @return string  A mailbox name.
     */
    function getMailboxName()
    {
        return $this->_mailbox;
    }

    /**
     * Build the array of message information.
     *
     * @since IMP 4.2
     *
     * @param array $msgnum    An array of message numbers.
     * @param mixed $preview   Include preview information?  If empty, add no
     *                         preview information. If 1, uses value from
     *                         prefs.  If 2, forces addition of preview info.
     * @param boolean $header  Return IMP_Header information?
     *
     * @return array  An array with information on the requested messages.
     * <pre>
     * Key: array index in current sorted mailbox array
     * Value: stdClass object - see IMP_MessageCache::retrieve() for fields
     * </pre>
     */
    function getMailboxArray($msgnum, $preview = false, $header = false)
    {
        $this->_buildMailbox();

        $mboxes = $overview = array();

        /* Build the list of mailboxes and messages. */
        foreach ($msgnum as $i) {
            --$i;
            /* Make sure that the index is actually in the slice of messages
               we're looking at. If we're hiding deleted messages, for
               example, there may be gaps here. */
            if (isset($this->_sorted[$i])) {
                $mboxname = ($this->_searchmbox) ? $this->_sortedInfo[$i]['m'] : $this->_mailbox;
                if (!isset($mboxes[$mboxname])) {
                    $mboxes[$mboxname] = array();
                }
                $mboxes[$mboxname][$this->_sorted[$i]] = $i;
            }
        }

        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
        $msg_cache = &IMP_MessageCache::singleton();

        $mask = 1 | 4 | 128;
        if ($preview) {
            $mask |= ($preview === 2) ? 64 : 16;
        }
        if ($header) {
            $mask |= 32;
        }

        /* Retrieve information from each mailbox. */
        foreach ($mboxes as $mbox => $ids) {
            /* We can save an IMAP search call if we can use the cached value
             * of the mailbox arrival. */
            $arrival = $this->_getCache($mbox, 'arrival');
            if ($arrival === false) {
                $mask |= 2;
            }
            $imapOverview = $msg_cache->retrieve($mbox, array_keys($ids), $mask);
            foreach ($imapOverview as $uid => $ob) {
                if (!is_object($ob)) {
                    continue;
                }
                $num = $ids[$uid] + 1;
                $overview[$num] = &Util::cloneObject($ob);
                if ($arrival !== false) {
                    $overview[$num]->msgno = $arrival[$uid] + 1;
                }
            }

            /* Cache arrival list, if necessary.  Just use getMailboxArrival()
             * since $msg_cache->retrieve() has already done the IMAP
             * access and the results have been cached. */
            if ($arrival === false) {
                require_once IMP_BASE . '/lib/IMAP/Cache.php';
                $imap_cache = &IMP_IMAP_Cache::singleton();
                $this->_setCache($mbox, 'update', 'arrival', array_flip($imap_cache->getMailboxArrival($mbox)));
            }
        }

        /* Sort via the sorted array index. */
        ksort($overview);

        return $overview;
    }

    /**
     * Builds the sorted list of messages in the mailbox.
     *
     * @access private
     */
    function _buildMailbox()
    {
        if ($this->_build) {
            return;
        }
        $this->_build = true;

        $uid = (!empty($this->_sorted) && ($this->_arrayIndex !== null)) ? $this->_sorted[$this->_arrayIndex] : null;

        /* Attempt to retrieve information from the cache. */
        if ($this->_searchmbox) {
            $query = null;
            if (IMP::hideDeletedMsgs()) {
                require_once IMP_BASE . '/lib/IMAP/Search.php';
                $query = new IMP_IMAP_Search_Query();
                $query->deleted(false);
            }

            $this->_sorted = $this->_sortedInfo = array();
            foreach ($GLOBALS['imp_search']->runSearch($query, $this->_mailbox) as $val) {
                list($idx, $mbox) = explode(IMP_IDX_SEP, $val);
                $this->_sorted[] = $idx;
                $this->_sortedInfo[] = array('m' => $mbox);
            }
            $this->_setSorted(4);
        } elseif (!$this->_setSorted(2)) {
            $sortpref = IMP::getSort($this->_mailbox);

            if ($sortpref['by'] == SORTTHREAD) {
                $threadob = $this->getThreadOb();
                $this->_sorted = $threadob->messageList((bool)$sortpref['dir']);
            } else {
                if ($sortpref['by'] == SORTARRIVAL) {
                    require_once IMP_BASE . '/lib/IMAP/Cache.php';
                    $imap_cache = &IMP_IMAP_Cache::singleton();
                    $this->_sorted = $imap_cache->getMailboxArrival($this->_mailbox);
                    if ($sortpref['dir']) {
                        $this->_sorted = array_reverse($this->_sorted);
                    }
                } else {
                    require_once IMP_BASE . '/lib/IMAP/Search.php';
                    $imap_search = &IMP_IMAP_Search::singleton(array('pop3' => ($_SESSION['imp']['base_protocol'] == 'pop3')));
                    $query = new IMP_IMAP_Search_Query();
                    if (($_SESSION['imp']['base_protocol'] != 'pop3') &&
                        IMP::hideDeletedMsgs()) {
                        $query->deleted(false);
                    }
                    $this->_sorted = $imap_search->searchSortMailbox($query, null, $this->_mailbox, $sortpref['by'], $sortpref['dir']);
                    if (is_a($this->_sorted, 'PEAR_Error')) {
                        $this->_sorted = array();
                    }
                }
            }
            $this->_setSorted(4);
        }

        /* Set the index now. */
        if ($uid !== null) {
            $this->setIndex($uid);
        }
    }

    /**
     * Get the list of new messages in the mailbox (IMAP RECENT flag, with
     * UNDELETED if we're hiding deleted messages).
     *
     * @param boolean $count  Return a count of new messages, rather than
     *                        the entire message list?
     *
     * @return integer  The number of new messages in the mailbox.
     */
    function newMessages($count = false)
    {
        return $this->_msgFlagSearch('recent', $count);
    }

    /**
     * Get the list of unseen messages in the mailbox (IMAP UNSEEN flag, with
     * UNDELETED if we're hiding deleted messages).
     *
     * @param boolean $count  Return a count of unseen messages, rather than
     *                        the entire message list?
     *
     * @return array  The list of unseen messages.
     */
    function unseenMessages($count = false)
    {
        return $this->_msgFlagSearch('unseen', $count);
    }

    /**
     * Do a search on a mailbox in the most efficient way available.
     *
     * @access private
     *
     * @param string $type    The search type - either 'recent' or 'unseen'.
     * @param boolean $count  Return a count of unseen messages, rather than
     *                        the entire message list?
     *
     * @return mixed  If $count is true, the number of messages.  If $count is
     *                false, a list of message UIDs.
     */
    function _msgFlagSearch($type, $count)
    {
        if (!$this->_searchmbox && !empty($this->_sorted)) {
            require_once IMP_BASE . '/lib/IMAP/Cache.php';
            $imap_cache = &IMP_IMAP_Cache::singleton();
            $delhide = IMP::hideDeletedMsgs();
            if (!$count || $delhide) {
                /* We must manually do a search if we are hiding deleted
                 * messages or we are explicitly being asked to return a list
                 * of messages. */
                $new = $imap_cache->getMailboxArrival($this->_mailbox, $delhide, $type);
                return ($count) ? count($new) : $new;
            } else {
                /* Just use imap_status() results if we are not hiding deleted
                 * messages. Saves an imap_search() call. */
                $status = $imap_cache->getStatus(null, $this->_mailbox);
                return $status->$type;
            }
        }

        return ($count) ? 0 : array();
    }

    /**
     * Returns the current message array index. If the array index has
     * run off the end of the message array, will return the last index.
     *
     * @return integer  The message array index.
     */
    function getMessageIndex()
    {
        if ($this->_arrayIndex === null) {
            $index = ($this->_lastArrayIndex === null) ? 0 : $this->_lastArrayIndex;
        } else {
            $index = $this->_arrayIndex;
        }

        return $index + 1;
    }

    /**
     * Returns the current message count of the mailbox.
     *
     * @return integer  The mailbox message count.
     */
    function getMessageCount()
    {
        if (!$GLOBALS['imp_search']->isVFolder($this->_mailbox)) {
            $this->_buildMailbox();
        }
        return count($this->_sorted);
    }

    /**
     * Checks to see if the current index is valid.
     * This function is only useful if an index was passed to the constructor.
     *
     * @return boolean  True if index is valid, false if not.
     */
    function isValidIndex()
    {
        $this->_sortIfNeeded();
        return ($this->_arrayIndex !== null);
    }

    /**
     * Returns IMAP mbox/UID information on a message.
     *
     * @param integer $offset  The offset from the current message.
     *
     * @return array  'index'   -- The message index.
     *                'mailbox' -- The mailbox.
     */
    function getIMAPIndex($offset = 0)
    {
        $index = $this->_arrayIndex + $offset;

        /* If the offset would put us out of array index, return now. */
        if (!isset($this->_sorted[$index])) {
            return array();
        }

        return array(
            'index' => $this->_sorted[$index],
            'mailbox' => ($this->_searchmbox) ? $this->_sortedInfo[$index]['m'] : $this->_mailbox
        );
    }

    /**
     * Update the current mailbox if an action has been performed on the
     * current message index.
     *
     * @param integer $action  The action to perform.
     * @param array $indices   The list of indices to update. See
     *                         IMP::parseIndicesList() for format.
     */
    function updateMailbox($action, $indices = null)
    {
        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();

        switch ($action) {
        case IMP_MAILBOX_DELETE:
            if (IMP::hideDeletedMsgs()) {
                /* Nuke message from sorted list if hidden. */
                if ($this->_removeMsgs($indices)) {
                    $imap_cache->expireCache($this->_mailbox, 2 | 4);
                    $this->_setSorted(4);
                }
            } else {
                $imap_cache->expireCache($this->_mailbox, 4);
            }
            break;

        case IMP_MAILBOX_EXPUNGE:
            if ($this->_removeMsgs($indices)) {
                $imap_cache->expireCache($this->_mailbox, 2 | 4);
                $this->_setSorted(4);

                /* For POP3 mailboxes, on expunge we need to login/logout since
                 * c-client caches the message indices. */
                if ($_SESSION['imp']['base_protocol'] == 'pop3') {
                    $imp_imap = &IMP_IMAP::singleton();
                    $imp_imap->reopen();

                    $this->_build = false;
                    $this->_buildMailbox();
                }
            }
            break;

        case IMP_MAILBOX_UPDATE:
            /* Since we are manually asking for a mailbox update, we need to
             * expire the cache. */
            $imap_cache->expireCache($this->_mailbox, 1 | 2 | 4);
            $this->_build = false;
            $this->_buildMailbox();
            break;

        case IMP_MAILBOX_FLAG:
            $imap_cache->expireCache($this->_mailbox, 2 | 4);
            break;
        }
    }

    /**
     * Using the preferences and the current mailbox, determines the messages
     * to view on the current page.
     *
     * @param integer $page       The page number currently being displayed.
     * @param integer $start      The starting message number.
     * @param integer $page_size  Override the maxmsgs preference and specify
     *                            the page size.
     *
     * @return stdClass  An object with the following fields:
     * <pre>
     * 'anymsg'     -  Are there any messages at all in mailbox? E.g. If
     *                 'msgcount' is 0, there may still be hidden deleted
     *                 messages.
     * 'begin'      -  The beginning message number of the page.
     * 'end'        -  The ending message number of the page.
     * 'index'      -  The index of the starting message.
     * 'msgcount'   -  The number of viewable messages in the current mailbox.
     * 'page'       -  The current page number.
     * 'pagecount'  -  The number of pages in this mailbox.
     * </pre>
     */
    function buildMailboxPage($page = 0, $start = 0, $page_size = null)
    {
        $this->_buildMailbox();
        $msgcount = $this->getMessageCount();

        if ($page_size === null) {
            $page_size = $GLOBALS['prefs']->getValue('max_msgs');
        }

        if ($msgcount > $page_size) {
            $pageCount = ceil($msgcount / (($page_size > 0) ? $page_size : 20));

            /* Determine which page to display. */
            if (empty($page) || strcspn($page, '0123456789')) {
                if (!empty($start)) {
                    /* Messages set this when returning to a mailbox. */
                    $page = ceil($start / $page_size);
                } else {
                    /* Search for the last visited page first. */
                    if (isset($_SESSION['cache']['mbox_page'][$this->_mailbox])) {
                        $page = $_SESSION['cache']['mbox_page'][$this->_mailbox];
                    } else {
                        $startpage = $GLOBALS['prefs']->getValue('mailbox_start');
                        switch ($startpage) {
                        case IMP_MAILBOXSTART_FIRSTPAGE:
                            $page = 1;
                            break;

                        case IMP_MAILBOXSTART_LASTPAGE:
                            $page = $pageCount;
                            break;

                        case IMP_MAILBOXSTART_FIRSTUNSEEN:
                        case IMP_MAILBOXSTART_LASTUNSEEN:
                            $sortpref = IMP::getSort($this->_mailbox);
                            if (!$sortpref['limit'] &&
                                !$this->_searchmbox &&
                                ($query = $this->unseenMessages())) {
                                $sortednew = array_keys(array_intersect($this->_sorted, $query));
                                $first_new = ($startpage == IMP_MAILBOXSTART_FIRSTUNSEEN) ?
                                    array_shift($sortednew) :
                                    array_pop($sortednew);
                                $page = ceil(($first_new + 1) / $page_size);
                            }
                            break;
                        }
                    }
                }

                if (empty($page)) {
                    if (!isset($sortpref)) {
                        $sortpref = IMP::getSort($this->_mailbox);
                    }
                    $page = $sortpref['dir'] ? 1 : $pageCount;
                }
            }

            /* Make sure we're not past the end or before the beginning, and
               that we have an integer value. */
            $page = intval($page);
            if ($page > $pageCount) {
                $page = $pageCount;
            } elseif ($page < 1) {
                $page = 1;
            }

            $begin = (($page - 1) * $page_size) + 1;
            $end = $begin + $page_size - 1;
            if ($end > $msgcount) {
                $end = $msgcount;
            }
        } else {
            $begin = 1;
            $end = $msgcount;
            $page = 1;
            $pageCount = 1;
        }

        $beginIndex = ($this->_searchmbox) ? ($begin - 1) : $this->_arrayIndex;

        /* If there are no viewable messages, check for deleted messages in
           the mailbox. */
        $anymsg = true;
        if (($msgcount == 0) && !$this->_searchmbox) {
            require_once IMP_BASE . '/lib/IMAP/Cache.php';
            $imap_cache = &IMP_IMAP_Cache::singleton();
            $status = $imap_cache->getStatus(null, $this->_mailbox);
            if ($status && ($status->messages == 0)) {
                $anymsg = false;
            }
        }

        /* Store the page value now. */
        $_SESSION['cache']['mbox_page'][$this->_mailbox] = $page;

        $ob = new stdClass;
        $ob->anymsg    = $anymsg;
        $ob->begin     = $begin;
        $ob->end       = $end;
        $ob->index     = $beginIndex;
        $ob->msgcount  = $msgcount;
        $ob->page      = $page;
        $ob->pagecount = $pageCount;

        return $ob;
    }

    /**
     * Updates the sorted messages array.
     *
     * @access private
     *
     * @param integer $mask  A bitmask for the following actions:
     * <pre>
     * 1 = Set sorted list from cache entry without checking cache expiration.
     * 2 = Set sorted list from cache entry while checking cache expiration.
     * 4 = Update cache entry with current sorted information.
     * 8 = Create new cache entry with current sorted information.
     * </pre>
     *
     * @return boolean  Returns true if message list was sucessfully retrieved
     *                  from the cache.
     */
    function _setSorted($mask)
    {
        if (($mask & 1) || ($mask & 2)) {
            $data = $this->_getCache($this->_mailbox, 'msgl', $mask & 2);
            if ($data === false) {
                if ($mask & 2) {
                    $this->_cacheexpire = true;
                }
                return false;
            }
            $this->_sorted = $data['s'];
            if ($this->_searchmbox) {
                $this->_sortedInfo = $data['m'];
            }
        } else {
            $this->_setCache($this->_mailbox, ($mask & 4 && !$this->_cacheexpire) ? 'update' : 'store', 'msgl', array('m' => $this->_sortedInfo, 's' => $this->_sorted));
            $this->_cacheexpire = false;
        }

        return true;
    }

    /**
     * Updates the message array index.
     *
     * @param integer $data  If $type is 'offset', the number of messages to
     *                       increase array index by.  If type is 'uid',
     *                       sets array index to the value of the given
     *                       message index.
     * @param string $type   Either 'offset' or 'uid'.
     */
    function setIndex($data, $type = 'uid')
    {
        if ($type == 'offset') {
            if ($this->_arrayIndex !== null) {
                $this->_lastArrayIndex = $this->_arrayIndex;
                $this->_arrayIndex += $data;
                if (empty($this->_sorted[$this->_arrayIndex])) {
                    $this->_arrayIndex = null;
                }
                $this->_sortIfNeeded();
            }
        } elseif ($type == 'uid') {
            $this->_arrayIndex = $this->_lastArrayIndex = $this->getArrayIndex($data);
        }
    }

    /**
     * Get the IMP_Thread object for the current mailbox.
     *
     * @return IMP_Thread  The IMP_Thread object for the current mailbox.
     */
    function getThreadOb()
    {
        require_once IMP_BASE . '/lib/IMAP/Thread.php';

        $ob = $this->_getCache($this->_mailbox, 'thread');
        if ($ob === false) {
            $imp_imap = &IMP_IMAP::singleton();
            $imp_imap->changeMbox($this->_mailbox, IMP_IMAP_AUTO);
            $ref_array = @imap_thread($imp_imap->stream(), SE_UID);
            if (!is_array($ref_array)) {
                $ref_array = array();
            }
            $ob = new IMP_Thread($ref_array);
            $this->_setCache($this->_mailbox, 'update', 'thread', serialize($ob));
        } else {
            $ob = unserialize($ob);
        }

        return $ob;
    }

    /**
     * Determines if a resort is needed, and, if necessary, performs
     * the resort.
     *
     * @access private
     */
    function _sortIfNeeded()
    {
        if (($this->_arrayIndex !== null) &&
            !$this->_searchmbox &&
            !$this->getIMAPIndex(1)) {
            $this->_build = false;
            $this->_buildMailbox();
        }
    }

    /**
     * Returns the current sorted array without the given messages.
     *
     * @access private
     *
     * @param array $msgs  The indices to remove.
     *
     * @return boolean  True if sorted array was updated without a call to
     *                  _buildMailbox().
     */
    function _removeMsgs($msgs)
    {
        if (empty($msgs)) {
            return;
        }

        if (!($msgList = IMP::parseIndicesList($msgs))) {
            $msgList = array($this->_mailbox => $msgs);
        }

        $msgcount = 0;
        $sortcount = count($this->_sorted);

        /* Remove the current entry and recalculate the range. */
        foreach ($msgList as $key => $val) {
            $arrival = $this->_getCache($key, 'arrival');
            foreach ($val as $index) {
                $val = $this->getArrayIndex($index, $key);
                if ($arrival !== false && isset($this->_sorted[$val])) {
                    unset($arrival[$this->_sorted[$val]]);
                }
                unset($this->_sorted[$val]);
                if ($this->_searchmbox) {
                    unset($this->_sortedInfo[$val]);
                }
                ++$msgcount;
            }
            if ($arrival !== false) {
                $this->_setCache($key, 'update', 'arrival', $arrival);
            }
        }

        $this->_sorted = array_values($this->_sorted);
        if ($this->_searchmbox) {
            $this->_sortedInfo = array_values($this->_sortedInfo);
        }

        /* Update the current array index to its new position in the message
         * array. */
        $this->setIndex(0, 'offset');

        /* If we have a sortlimit, it is possible the sort prefs will have
         * changed after messages are expunged. */
        if (!empty($GLOBALS['conf']['server']['sort_limit']) &&
            ($sortcount > $GLOBALS['conf']['server']['sort_limit']) &&
            (($sortcount - $msgcount) <= $GLOBALS['conf']['server']['sort_limit'])) {
            $this->updateMailbox(IMP_MAILBOX_UPDATE);
            return false;
        }

        return true;
    }

    /**
     * Returns the array index of the given message UID.
     *
     * @param integer $uid   The message UID.
     * @param integer $mbox  The message mailbox (defaults to the current
     *                       mailbox).
     *
     * @return integer  The array index of the location of the message UID in
     *                  the current mailbox.
     */
    function getArrayIndex($uid, $mbox = null)
    {
        $aindex = null;

        if ($this->_searchmbox) {
            if ($mbox === null) {
                $mbox = $GLOBALS['imp_mbox']['thismailbox'];
            }

            /* Need to compare both mbox name and message UID to obtain the
             * correct array index since there may be duplicate UIDs. */
            foreach (array_keys($this->_sorted, $uid) as $key) {
                if ($this->_sortedInfo[$key]['m'] == $mbox) {
                    $aindex = $key;
                    break;
                }
            }
        } else {
            /* array_search() returns false on no result. We will set an
             * unsuccessful result to NULL. */
            if (($aindex = array_search($uid, $this->_sorted)) === false) {
                $aindex = null;
            }
        }

        return $aindex;
    }

    /**
     * Returns a raw sorted list of the mailbox.
     *
     * @since IMP 4.2
     *
     * @return array  An array with two keys: 's' = sorted UIDS list, 'm' =
     *                sorted mailboxes list.
     */
    function getSortedList()
    {
        $this->_buildMailbox();

        /* For exterior use, the array needs to begin numbering at 1. */
        $s = $this->_sorted;
        array_unshift($s, 0);
        unset($s[0]);
        $m = $this->_sortedInfo;
        array_unshift($m, 0);
        unset($m[0]);
        return array('s' => $s, 'm' => $m);
    }

    /**
     * Returns a unique identifier for the current mailbox status.
     *
     * @since IMP 4.2
     *
     * @return string  The cache ID string, which will change when the status
     *                 of the mailbox changes.
     */
    function getCacheID()
    {
        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();
        return $imap_cache->getCacheID(IMP::serverString($this->_mailbox));
    }

    /**
     * Returns cached IMAP data.
     *
     * @access private
     *
     * @param string $mbox    The mailbox name.
     * @param string $type    The data to return (arrival, msgl, thread).
     * @param boolean $check  Check for updated mailbox?
     *
     * @return mixed  The data requested or false if not available.
     */
    function _getCache($mbox, $type, $check = true)
    {
        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();

        $ob = $imap_cache->getCache(null, IMP::serverString($mbox), $type, $check);
        if (($ob !== false) &&
            in_array($type, array('arrival', 'msgl'))) {
            $ob = (IMP::hideDeletedMsgs() == $ob['hd']) ? $ob['d'] : false;
        }
        return $ob;
    }

    /**
     * Stores IMAP data.
     *
     * @access private
     *
     * @param string $mbox  The mailbox name.
     * @param string $mode  The update mode (store, update).
     * @param string $type  The data to return (arrival, msgl, thread).
     * @param mixed $data   The data to store.
     */
    function _setCache($mbox, $mode, $type, $data)
    {
        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();

        if (in_array($type, array('arrival', 'msgl'))) {
            $data = array($type => array('hd' => IMP::hideDeletedMsgs(), 'd' => $data));
        } else {
            $data = array($type => $data);
        }
        call_user_func_array(array(&$imap_cache, ($mode == 'store') ? 'storeCache' : 'updateCache'), array(null, IMP::serverString($mbox), $data));
    }

}
