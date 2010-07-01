<?php
/**
 * ShowMessage view logic.
 *
 * $Horde: dimp/lib/Views/ShowMessage.php,v 1.70.2.22 2009-01-06 15:22:40 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package DIMP
 */

require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
require_once IMP_BASE . '/lib/MIME/Contents.php';
require_once IMP_BASE . '/lib/MIME/Headers.php';
require_once IMP_BASE . '/lib/UI/Message.php';

class DIMP_Views_ShowMessage {

    /**
     * @var string
     */
    var $_imagedir;

    /**
     * Constructor.
     */
    function DIMP_Views_ShowMessage()
    {
        $this->_imagedir = $GLOBALS['registry']->getImageDir('dimp');
    }

    /**
     * Builds a string containing a list of addresses.
     *
     * @access private
     *
     * @param IMP_Headers &$headers  The headers object.
     * @param string $field          The address field to parse.
     * @param boolean $set           Set the associated header with the return
     *                               string?
     *
     * @return string  String containing the formatted address list.
     */
    function _buildAddressLinks(&$headers, $field, $set = false)
    {
        /* Make sure this is a valid object address field. */
        $array = $headers->getOb($field);
        if (empty($array) || !is_array($array)) {
            return;
        }

        $addr_array = array();

        foreach ($headers->getAddressesFromObject($array) as $ob) {
            if (empty($ob->address) || empty($ob->inner)) {
                continue;
            }

            /* If this is an incomplete e-mail address, don't link to
             * anything. */
            $result = false;
            if (!empty($GLOBALS['conf']['hooks']['addressformatting'])) {
                $result = Horde::callHook('_dimp_hook_addressformatting', array($ob), 'dimp');
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    $result = false;
                } else {
                    $addr_array[] = $result;
                }
            }
            if ($result === false) {
                if (stristr($ob->host, 'UNKNOWN') !== false) {
                    $addr_array[] = $ob->address;
                } else {
                    // BC: $ob->display appeared in IMP 4.2.1
                    $addr_array[] = '<a class="address" personal="' . htmlspecialchars($ob->personal) . '" email="' . htmlspecialchars($ob->inner) . '" address="' . htmlspecialchars($ob->address) . '">' . htmlspecialchars(isset($ob->display) ? $ob->display : $ob->address) . Horde::img('popdown.png', '', array(), $this->_imagedir) . '</a>';
                }
            }
        }

        /* If left with an empty address list, inform the user that the
         * recipient list is purposely "undisclosed". */
        if (empty($addr_array)) {
            $ret = _("Undisclosed Recipients");
        } else {
            /* Build the address line. */
            $addr_count = count($addr_array);
            $ret = implode(', ', $addr_array);
            if ($addr_count > 15) {
                $ret = '<span>' .
                    '<span class="largeaddrlist">' . htmlspecialchars(sprintf("[Show Addresses - %d recipients]", $addr_count)) . '</span>' .
                    '<span class="largeaddrlist" style="display:none">' . htmlspecialchars(_("[Hide Addresses]")) . '</span>' .
                    '<span class="dispaddrlist" style="display:none">' .
                    $ret . '</span></span>';
            }
        }

        /* Set the header value, if requested. */
        if ($set) {
            $headers->setValue($field, $ret);
        }

        return $ret;
    }

    /**
     * Create the object used to display the message.
     *
     * @param array $args  Configuration parameters.
     * <pre>
     * 'headers' - The headers desired in the returned headers array (only used
     *             with non-preview view)
     * 'folder' - The folder name
     * 'index' - The folder index
     * 'preview' - Is this the preview view?
     * </pre>
     *
     * @return array  Array with the following keys:
     * <pre>
     * FOR BOTH MODES:
     * 'atc_download' - The download all link
     * 'atc_label' - The label to use for Attachments
     * 'atc_list' - The list (HTML code) of attachments
     * 'error' - Contains an error message (only on error)
     * 'errortype' - Contains the error type (only on error)
     * 'folder' - The IMAP folder
     * 'index' - The IMAP UID
     * 'msgtext' - The text of the message
     * 'priority' - The X-Priority of the message ('low', 'high', 'normal')
     * 'source_link' - The URL to view the message source
     * 'uid' - The unique UID of this message
     *
     * FOR PREVIEW MODE:
     * 'cc' - The CC address
     * 'from' - The From address
     * 'fulldate' - The fully formatted date
     * 'js' - Javascript code to run on display (only if the previewview
     *        hook is active)
     * 'minidate' - A miniature date
     * 'to' - The To address
     *
     * FOR NON-PREVIEW MODE:
     * 'headers' - An array of headers
     * </pre>
     */
    function showMessage($args)
    {
        $preview = !empty($args['preview']);
        $folder = $args['folder'];
        $index = $args['index'];
        $error_msg = _("Requested message not found.");

        $result = array(
            'folder' => $folder,
            'index' => $index,
            'uid' => $index . $folder,
        );

        /* Set the current time zone. */
        NLS::setTimeZone();

        /* Get the IMP_Headers:: object. */
        $msg_cache = &IMP_MessageCache::singleton();
        $cache_entry = $msg_cache->retrieve($folder, array($index), 1 | 32);
        $ob = reset($cache_entry);
        if ($ob === false) {
            $result['error'] = $error_msg;
            $result['errortype'] = 'horde.error';
            return $result;
        }

        $imp_headers = &Util::cloneObject($ob->header);

        /* Parse MIME info and create the body of the message. */
        $imp_contents = &IMP_Contents::singleton($index . IMP_IDX_SEP . $folder);
        if (is_a($imp_contents, 'PEAR_Error') ||
            !$imp_contents->buildMessage()) {
            $result['error'] = $error_msg;
            $result['errortype'] = 'horde.error';
            return $result;
        }

        /* Get the IMP_UI_Message:: object. */
        $imp_ui = new IMP_UI_Message();

        /* Update the message flag, if necessary. */
        if (($_SESSION['imp']['base_protocol'] == 'imap') && empty($ob->seen)) {
            require_once IMP_BASE . '/lib/Mailbox.php';
            require_once IMP_BASE . '/lib/Message.php';
            $imp_mailbox = &IMP_Mailbox::singleton($folder, $index);
            $imp_message = &IMP_Message::singleton();
            $imp_message->flag(array('seen'), $imp_mailbox, true);
        }

        /* Determine if we should generate the attachment strip links or
         * not. */
        if ($GLOBALS['prefs']->getValue('strip_attachments')) {
            $imp_contents->setStripLink(true);
        }

        /* Show summary links. */
        $imp_contents->showSummaryLinks(true);

        $attachments = $imp_contents->getAttachments();
        $result['msgtext'] = $imp_contents->getMessage();

        /* Build From/To/Cc/Bcc links. */
        foreach (array('from', 'to', 'cc', 'bcc') as $val) {
            $this->_buildAddressLinks($imp_headers, $val, true);
        }

        /* Build Reply-To address links. */
        if (($reply_to = $this->_buildAddressLinks($imp_headers, 'reply-to', false))) {
            if (!($from = $imp_headers->getValue('from')) || ($from != $reply_to)) {
                $imp_headers->setValue('Reply-to', $reply_to);
            } else {
                $imp_headers->removeHeader('reply-to');
            }
        }

        /* Develop the list of Headers to display now. Deal with the 'basic'
         * header information first since there are various manipulations
         * done to them. */
        $headers_list = $imp_ui->basicHeaders();
        if (empty($args['headers'])) {
            $args['headers'] = array('from', 'date', 'to', 'cc');
        }
        // TODO: When PHP 5.1.0+ is required, we can use array_intersect_key.
        $basic_headers = array();
        foreach (array_intersect(array_keys($headers_list), $args['headers']) as $v) {
            $basic_headers[$v] = $headers_list[$v];
        }

        $headers = array();
        $result['from'] = '';
        foreach ($basic_headers as $head => $str) {
            if ($val = $imp_headers->getValue($head)) {
                if ($head == 'date') {
                    /* Add local time to date header. */
                    $val = nl2br($imp_headers->addLocalTime(htmlspecialchars($val)));
                    if ($preview) {
                        $result['fulldate'] = $val;
                    }
                } elseif (in_array($head, array('from', 'to', 'cc'))) {
                    if ($preview) {
                        $result[$head] = $val;
                    }
                } elseif (!in_array($head, array('bcc', 'reply-to'))) {
                    $val = htmlspecialchars($val);
                }
                if (!$preview) {
                    $headers[] = array('id' => String::ucfirst($head), 'name' => $str, 'value' => $val);
                }
            }
        }

        /* Display the user-specified headers for the current identity. */
        if (!$preview) {
            $user_hdrs = $imp_ui->getUserHeaders();
            if (!empty($user_hdrs)) {
                $full_h = $imp_headers->getAllHeaders();
                foreach ($user_hdrs as $user_hdr) {
                    foreach ($full_h as $head => $val) {
                        if (stristr($head, $user_hdr) !== false) {
                            $headers[] = array('name' => $head, 'value' => htmlspecialchars($val));
                        }
                    }
                }
            }
            $result['headers'] = $headers;
        }

        /* Process the subject. */
        if (($subject = $imp_headers->getValue('subject'))) {
            require_once 'Horde/Text.php';
            $subject = Text::htmlSpaces(IMP::filterText($subject));
        } else {
            $subject = htmlspecialchars(_("[No Subject]"));
        }
        $result['subject'] = $subject;

        /* Get X-Priority/ */
        $result['priority'] = $imp_headers->getXpriority();


        /* Add attachment info. */
        $atc_display = $GLOBALS['prefs']->getValue('attachment_display');
        $show_parts = (!empty($attachments) && (($atc_display == 'list') || ($atc_display == 'both')));
        $downloadall_link = $imp_contents->getDownloadAllLink();

        if ($attachments && ($show_parts || $downloadall_link)) {
            $result['atc_label'] = sprintf(ngettext("%d Attachment", "%d Attachments",
                                         $imp_contents->attachmentCount()),
                                         $imp_contents->attachmentCount());
            $result['atc_download'] = ($downloadall_link) ? Horde::link($downloadall_link) . _("Save All") . '</a>' : '';
        }
        if ($show_parts) {
            $result['atc_list'] = $attachments;
        }

        // Message Source link
        if (!empty($GLOBALS['conf']['user']['allow_view_source'])) {
            $base_part = $imp_contents->getMIMEMessage();
            $result['source_link'] = Util::addParameter($imp_contents->urlView($base_part, 'view_source'), 'thismailbox', $folder);
        }

        if ($preview) {
            $curr_time = time();
            $curr_time -= $curr_time % 60;
            $ltime_val = localtime();
            $today_start = mktime(0, 0, 0, $ltime_val[4] + 1, $ltime_val[3], 1900 + $ltime_val[5]);
            $today_end = $today_start + 86400;
            if (empty($ob->date)) {
                $udate = false;
            } else {
                $ob->date = preg_replace('/\s+\(\w+\)$/', '', $ob->date);
                $udate = strtotime($ob->date, $curr_time);
            }
            if ($udate === false || $udate === -1) {
                $result['minidate'] = _("Unknown Date");
            } elseif (($udate < $today_start) || ($udate > $today_end)) {
                /* Not today, use the date. */
                $result['minidate'] = strftime($GLOBALS['prefs']->getValue('date_format'), $udate);
            } else {
                /* Else, it's today, use the time. */
                $result['minidate'] = strftime($GLOBALS['prefs']->getValue('time_format'), $udate);
            }
        }

        if ($preview && !empty($GLOBALS['conf']['hooks']['previewview'])) {
            $res = Horde::callHook('_dimp_hook_previewview', array($result), 'dimp');
            if (is_a($res, 'PEAR_Error')) {
                Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
            } else {
                $result = $res[0];
                $result['js'] = $res[1];
            }
        } elseif (!$preview && !empty($GLOBALS['conf']['hooks']['messageview'])) {
            $res = Horde::callHook('_dimp_hook_messageview', array($result), 'dimp');
            if (is_a($res, 'PEAR_Error')) {
                Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
            } else {
                $result = $res;
            }
        }

        /* Retrieve any history information for this message. */
        if (!empty($GLOBALS['conf']['maillog']['use_maillog'])) {
            if (!$preview) {
                require_once IMP_BASE . '/lib/Maillog.php';
                IMP_Maillog::displayLog($imp_headers->getValue('message-id'));
            }

            /* Do MDN processing now. */
            if ($imp_ui->MDNCheck($ob->header)) {
                $confirm_link = Horde::link('', '', '', '', 'DimpCore.doAction(\'SendMDN\',{folder:\'' . $folder . '\',index:' . $index . '}); return false;', '', '') . _("HERE") . '</a>';
                $GLOBALS['notification']->push(sprintf(_("The sender of this message is requesting a Message Disposition Notification from you when you have read this message. Click %s to send the notification message."), $confirm_link), 'dimp.request', array('content.raw'));
            }
        }

        return $result;
    }

}
