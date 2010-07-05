<?php

require_once 'Horde/IMAP/Sort.php';

/**
 * The IMP_IMAP_Sort:: class extends the IMAP_Sort class in order to
 * provide necessary bug fixes to ensure backwards compatibility with Horde
 * 3.0.
 *
 * $Horde: imp/lib/IMAP/Sort.php,v 1.1.2.5 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.1
 * @package Horde_IMAP
 */
class IMP_IMAP_Sort extends IMAP_Sort {

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

}
