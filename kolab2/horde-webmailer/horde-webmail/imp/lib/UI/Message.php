<?php
/**
 * The IMP_UI_Message:: class is designed to provide a place to dump common
 * code shared among IMP's various UI views for the message page.
 *
 * $Horde: imp/lib/UI/Message.php,v 1.10.2.5 2009-01-06 15:24:12 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 * @since   IMP 4.2
 */
class IMP_UI_Message {

    /**
     */
    function basicHeaders()
    {
        return array(
            'date'      =>  _("Date"),
            'from'      =>  _("From"),
            'to'        =>  _("To"),
            'cc'        =>  _("Cc"),
            'bcc'       =>  _("Bcc"),
            'reply-to'  =>  _("Reply-To"),
            'subject'   =>  _("Subject")
        );
    }

    /**
     */
    function getUserHeaders()
    {
        $user_hdrs = $GLOBALS['prefs']->getValue('mail_hdr');

        /* Split the list of headers by new lines and sort the list of headers
         * to make sure there are no duplicates. */
        if (is_array($user_hdrs)) {
            $user_hdrs = implode("\n", $user_hdrs);
        }
        $user_hdrs = trim($user_hdrs);
        if (empty($user_hdrs)) {
            return $user_hdrs;
        }

        $user_hdrs = str_replace(':', '', $user_hdrs);
        $user_hdrs = preg_split("/[\n\r]+/", $user_hdrs);
        $user_hdrs = array_map('trim', $user_hdrs);
        $user_hdrs = array_filter(array_keys(array_flip($user_hdrs)));
        natcasesort($user_hdrs);

        return $user_hdrs;
    }

    /**
     */
    function MDNCheck($headers, $confirmed = false)
    {
        if (!$GLOBALS['prefs']->getValue('disposition_send_mdn')) {
            return;
        }

        /* Check to see if an MDN has been requested. */
        require_once 'Horde/MIME/MDN.php';
        $mdn = new MIME_MDN($headers);
        if ($mdn->getMDNReturnAddr()) {
            require_once IMP_BASE . '/lib/Maillog.php';
            $msg_id = $headers->getValue('message-id');

            /* See if we have already processed this message. */
            if (!IMP_Maillog::sentMDN($msg_id, 'displayed')) {
                /* See if we need to query the user. */
                if ($mdn->userConfirmationNeeded() && !$confirmed) {
                    return true;
                } else {
                    /* Send out the MDN now. */
                    $result = $mdn->generate(false, $confirmed, 'displayed');
                    if (!is_a($result, 'PEAR_Error')) {
                        IMP_Maillog::log('mdn', $msg_id, 'displayed');
                    }
                    if ($GLOBALS['conf']['sentmail']['driver'] != 'none') {
                        require_once IMP_BASE . '/lib/Sentmail.php';
                        $sentmail = IMP_Sentmail::factory();
                        $sentmail->log('mdn', '', $mdn->getMDNReturnAddr(), !is_a($result, 'PEAR_Error'));
                    }
                }
            }
        }

        return false;
    }

}
