<?php
/**
 * Implementation of the Quota API for IMAP servers.
 *
 * $Horde: imp/lib/Quota/imap.php,v 1.2.2.3 2009-01-06 15:24:11 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package IMP_Quota
 */
class IMP_Quota_imap extends IMP_Quota {

    /**
     * Get quota information (used/allocated), in bytes.
     *
     * @return mixed  An associative array.
     *                'limit' = Maximum quota allowed
     *                'usage' = Currently used portion of quota (in bytes)
     *                Returns PEAR_Error on failure.
     */
    function getQuota()
    {
        $imp_imap = &IMP_IMAP::singleton();
        $quota = @imap_get_quotaroot($imp_imap->stream(),
                                     $GLOBALS['imp_search']->isSearchMbox($GLOBALS['imp_mbox']['mailbox']) ? 'INBOX' : $GLOBALS['imp_mbox']['mailbox']);

        if (is_array($quota)) {
            if (count($quota)) {
                if (isset($quota['limit'])) {
                    return array('usage' => $quota['usage'] * 1024, 'limit' => $quota['limit'] * 1024);
                } elseif (isset($quota['STORAGE']['limit'])) {
                    return array('usage' => $quota['STORAGE']['usage'] * 1024, 'limit' => $quota['STORAGE']['limit'] * 1024);
                }
            }
            return array('usage' => 0, 'limit' => 0);
        }

        return PEAR::raiseError(_("Unable to retrieve quota"), 'horde.error');
    }

}
