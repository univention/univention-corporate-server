<?php
/**
 * IMAP_Sort provides functions for sorting lists of IMAP mailboxes/folders.
 *
 * $Horde: framework/IMAP/IMAP/Sort.php,v 1.2 2004/05/27 14:41:59 jan Exp $
 *
 * Copyright 2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Sort {

    /**
     * The delimiter character to use.
     *
     * @var string $_delimiter
     */
    var $_delimiter = '/';

    /**
     * Should we sort with 'INBOX' at the front of the list?
     *
     * @var boolean $_sortinbox
     */
    var $_sortinbox;

    /**
     * Constructor.
     *
     * @access public
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
     * @access public
     *
     * @param array &$mbox             The list of mailboxes to sort.
     * @param optional boolean $inbox  When sorting, always put 'INBOX' at
     *                                 the head of the list?
     */
    function sortMailboxes(&$mbox, $inbox = true)
    {
        $this->_sortinbox = $inbox;
        usort($mbox, array($this, '_mbox_cmp'));
    }

    /**
     * Sort a list of mailboxes (by key).
     *
     * @access public
     *
     * @param array &$mbox             The list of mailboxes to sort, with
     *                                 the keys being the mailbox names.
     * @param optional boolean $inbox  When sorting, always put 'INBOX' at
     *                                 the head of the list?
     */
    function sortMailboxesByKey(&$mbox, $inbox = true)
    {
        $this->_sortinbox = $inbox;
        uksort($mbox, array($this, '_mbox_cmp'));
    }

    /**
     * Hierarchical folder sorting function (used with usort()).
     *
     * @access private
     *
     * @param string $a  Comparison item #1.
     * @param string $b  Comparison item #2.
     *
     * @return integer  See usort().
     */
    function _mbox_cmp($a, $b)
    {
        /* Always return INBOX as "smaller". */
        if ($this->_sortinbox) {
            if (String::upper($a) == 'INBOX') {
                return -1;
            } elseif (String::upper($b) == 'INBOX') {
                return 1;
            }
        }

        $a_parts = explode($this->_delimiter, $a);
        $b_parts = explode($this->_delimiter, $b);

        $iMax = min(count($a_parts), count($b_parts));
        for ($i = 0; $i < $iMax; $i++) {
            if ($a_parts[$i] != $b_parts[$i]) {
                return strnatcasecmp($a_parts[$i], $b_parts[$i]);
            }
        }

        return count($a_parts) - count($b_parts);
    }

}
