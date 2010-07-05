<?php
/**
 * IMAP_Sort provides functions for sorting lists of IMAP mailboxes/folders.
 *
 * $Horde: framework/IMAP/IMAP/Sort.php,v 1.6.8.17 2009-01-06 15:23:11 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Sort {

    /**
     * The delimiter character to use.
     *
     * @var string
     */
    var $_delimiter;

    /**
     * Should we sort with 'INBOX' at the front of the list?
     *
     * @var boolean
     */
    var $_sortinbox;

    /**
     * Constructor.
     *
     * @param string $delimiter  The delimiter used to separate mailboxes.
     */
    function IMAP_Sort($delimiter)
    {
        $this->_delimiter = $delimiter;
    }

    /**
     * Sort a list of mailboxes (by value).
     *
     * @param array &$mbox    The list of mailboxes to sort.
     * @param boolean $inbox  When sorting, always put 'INBOX' at the head of
     *                        the list?
     * @param boolean $index  Maintain index association?
     */
    function sortMailboxes(&$mbox, $inbox = true, $index = false)
    {
        $this->_sortinbox = $inbox;
        if ($index) {
            uasort($mbox, array(&$this, '_mbox_cmp'));
        } else {
            usort($mbox, array(&$this, '_mbox_cmp'));
        }
    }

    /**
     * Sort a list of mailboxes (by key).
     *
     * @param array &$mbox    The list of mailboxes to sort, with the keys
     *                        being the mailbox names.
     * @param boolean $inbox  When sorting, always put 'INBOX' at the head of
     *                        the list?
     */
    function sortMailboxesByKey(&$mbox, $inbox = true)
    {
        $this->_sortinbox = $inbox;
        uksort($mbox, array(&$this, '_mbox_cmp'));
    }

    /**
     * Hierarchical folder sorting function (used with usort()).
     *
     * @access private
     *
     * @param string $a  Comparison item 1.
     * @param string $b  Comparison item 2.
     *
     * @return integer  See usort().
     */
    function _mbox_cmp($a, $b)
    {
        /* Always return INBOX as "smaller". */
        if ($this->_sortinbox) {
            if (strcasecmp($a, 'INBOX') == 0) {
                return -1;
            } elseif (strcasecmp($b, 'INBOX') == 0) {
                return 1;
            }
        }

        $a_parts = explode($this->_delimiter, $a);
        $b_parts = explode($this->_delimiter, $b);

        $a_count = count($a_parts);
        $b_count = count($b_parts);

        $iMax = min($a_count, $b_count);

        for ($i = 0; $i < $iMax; $i++) {
            if ($a_parts[$i] != $b_parts[$i]) {
                /* If only one of the folders is under INBOX, return it as
                 * "smaller". */
                if ($this->_sortinbox && ($i == 0)) {
                    $a_base = (strcasecmp($a_parts[0], 'INBOX') == 0);
                    $b_base = (strcasecmp($b_parts[0], 'INBOX') == 0);
                    if ($a_base && !$b_base) {
                        return -1;
                    } elseif (!$a_base && $b_base) {
                        return 1;
                    }
                }
                $cmp = strnatcasecmp($a_parts[$i], $b_parts[$i]);
                if ($cmp == 0) {
                    return strcmp($a_parts[$i], $b_parts[$i]);
                }
                return $cmp;
            }
        }

        return ($a_count - $b_count);
    }

}
