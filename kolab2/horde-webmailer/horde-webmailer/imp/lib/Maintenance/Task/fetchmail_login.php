<?php
/**
 * $Horde: imp/lib/Maintenance/Task/fetchmail_login.php,v 1.5.12.11 2009-01-06 15:24:10 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * Maintenance module that fetch mail upon login
 *
 * @author  Nuno Loureiro <nuno@co.sapo.pt>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_Maintenance
 */
class Maintenance_Task_fetchmail_login extends Maintenance_Task {

    /**
     * The style of the maintenance page output.
     *
     * @var integer
     */
    var $_display_type = MAINTENANCE_OUTPUT_CONFIRM;

    /**
     * Fetch email from other accounts.
     */
    function doMaintenance()
    {
        require_once IMP_BASE . '/lib/Fetchmail.php';
        $fm_account = &new IMP_Fetchmail_Account();

        /* If the user wants to fetch emails from other accounts on login,
         * go get those messages now. */
        if ($fm_account->count()) {
            $fm_list = array();

            foreach ($fm_account->getAll('loginfetch') as $id => $val) {
                if ($val) {
                    $fm_list[] = $id;
                }
            }

            if (!empty($fm_list)) {
                IMP_Fetchmail::fetchMail($fm_list);
            }
        }
    }

    /**
     * Returns the summary of the accounts to fetch email from.
     *
     * @return string  The summary of the accounts to fetch email from.
     */
    function describeMaintenance()
    {
        $str  = _("You are about to fetch email from the following account(s):");
        $str .= "\n<blockquote>\n";

        require_once IMP_BASE . '/lib/Fetchmail.php';
        $fm_account = &new IMP_Fetchmail_Account();
        if ($fm_account->count()) {
            foreach ($fm_account->getAll('loginfetch') as $id => $val) {
                if ($val) {
                    $str .= " - " . $fm_account->getValue('id', $id) . "<br />\n";
                }
            }
        }

        $str .= "\n</blockquote>\n<strong>" . _("Note that this can take some time") . ".</strong>\n";

        return $str;
    }

}
