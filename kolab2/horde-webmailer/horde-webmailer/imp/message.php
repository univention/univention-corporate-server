<?php
/**
 * $Horde: imp/message.php,v 2.560.4.61 2009-02-17 07:32:12 slusarz Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

function _returnToMailbox($startIndex = null, $actID = null)
{
    global $actionID, $from_message_page, $start;

    $actionID = null;
    $from_message_page = true;
    $start = null;

    if ($startIndex !== null) {
        $start = $startIndex;
    }
    if ($actID !== null) {
        $actionID = $actID;
    }
}

function _moveAfterAction()
{
    return (($_SESSION['imp']['base_protocol'] != 'pop3') &&
            !IMP::hideDeletedMsgs() &&
            !$GLOBALS['prefs']->getValue('use_trash'));
}

require_once dirname(__FILE__) . '/lib/base.php';
require_once IMP_BASE . '/lib/Mailbox.php';
require_once IMP_BASE . '/lib/Template.php';

/* Make sure we have a valid index. */
$imp_mailbox = &IMP_Mailbox::singleton($imp_mbox['mailbox'], $imp_mbox['index']);
if (!$imp_mailbox->isValidIndex()) {
    _returnToMailbox(null, 'message_missing');
    require IMP_BASE . '/mailbox.php';
    exit;
}

$flagged_unseen = false;
$printer_friendly = false;

/* Set the current time zone. */
NLS::setTimeZone();

/* Initialize the user's identities. */
require_once 'Horde/Identity.php';
$user_identity = &Identity::singleton(array('imp', 'imp'));

/* Run through action handlers. */
$actionID = Util::getFormData('actionID');
if ($actionID && ($actionID != 'print_message')) {
    $result = IMP::checkRequestToken('imp.message', Util::getFormData('message_token'));
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result);
        $actionID = null;
    }
}

switch ($actionID) {
case 'blacklist':
case 'whitelist':
    require_once IMP_BASE . '/lib/Filter.php';
    $imp_filter = new IMP_Filter();
    $idx = $imp_mailbox->getIMAPIndex();
    if ($actionID == 'blacklist') {
        $imp_filter->blacklistMessage(array($idx['mailbox'] => array($idx['index'])));
    } else {
        $imp_filter->whitelistMessage(array($idx['mailbox'] => array($idx['index'])));
    }
    break;

case 'print_message':
    $printer_friendly = true;
    IMP::printMode(true);
    break;

case 'delete_message':
case 'undelete_message':
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    if ($actionID == 'undelete_message') {
        $imp_message->undelete($imp_mailbox);
    } else {
        $imp_message->delete($imp_mailbox);
        if ($prefs->getValue('mailbox_return')) {
            _returnToMailbox($imp_mailbox->getMessageIndex());
            require IMP_BASE . '/mailbox.php';
            exit;
        }
        if (_moveAfterAction()) {
            $imp_mailbox->setIndex(1, 'offset');
        }
    }
    break;

case 'move_message':
case 'copy_message':
    if (($targetMbox = Util::getFormData('targetMbox')) !== null) {
        require_once IMP_BASE . '/lib/Message.php';
        $imp_message = &IMP_Message::singleton();

        $action = ($actionID == 'move_message') ? IMP_MESSAGE_MOVE : IMP_MESSAGE_COPY;

        if (Util::getFormData('newMbox', 0) == 1) {
            $targetMbox = String::convertCharset(IMP::folderPref($targetMbox, true), NLS::getCharset(), 'UTF7-IMAP');
            $newMbox = true;
        } else {
            $newMbox = false;
        }
        $imp_message->copy($targetMbox, $action, $imp_mailbox, $newMbox);
        if ($prefs->getValue('mailbox_return')) {
            _returnToMailbox($imp_mailbox->getMessageIndex());
            require IMP_BASE . '/mailbox.php';
            exit;
        }
    }
    break;

case 'spam_report':
case 'notspam_report':
    $action = str_replace('_report', '', $actionID);
    require_once IMP_BASE . '/lib/Spam.php';
    $imp_spam = new IMP_Spam();
    switch ($imp_spam->reportSpam($imp_mailbox, $action)) {
    case 1:
        if (_moveAfterAction()) {
            $imp_mailbox->setIndex(1, 'offset');
        }
        break;
    }
    if ($prefs->getValue('mailbox_return')) {
        _returnToMailbox($imp_mailbox->getMessageIndex());
        require IMP_BASE . '/mailbox.php';
        exit;
    }
    break;

case 'flag_message':
    $flag = Util::getFormData('flag');
    if ($flag) {
        if ($flag[0] == '0') {
            $flag = substr($flag, 1);
            $set = false;
            if (strtolower($flag) == 'seen') {
                $flagged_unseen = true;
            }
        } else {
            $set = true;
        }
        require_once IMP_BASE . '/lib/Message.php';
        $imp_message = &IMP_Message::singleton();
        $imp_message->flag(array($flag), $imp_mailbox, $set);
        if ($prefs->getValue('mailbox_return')) {
            _returnToMailbox($imp_mailbox->getMessageIndex());
            require IMP_BASE . '/mailbox.php';
            exit;
        }
    }
    break;

case 'add_address':
    $contact_link = IMP::addAddress(Util::getFormData('address'), Util::getFormData('name'));
    if (is_a($contact_link, 'PEAR_Error')) {
        $notification->push($contact_link);
    } else {
        $notification->push(sprintf(_("Entry \"%s\" was successfully added to the address book"), $contact_link), 'horde.success', array('content.raw'));
    }
    break;

case 'strip_attachment':
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $result = $imp_message->stripPart($imp_mailbox, Util::getFormData('imapid'));
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    }

    break;

case 'strip_all':
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $result = $imp_message->stripPart($imp_mailbox);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    }

    break;
}

/* Token to use in requests */
$message_token = IMP::getRequestToken('imp.message');

/* We may have done processing that has taken us past the end of the
 * message array, so we will return to mailbox.php if that is the
 * case. */
if (!$imp_mailbox->isValidIndex()) {
    _returnToMailbox($imp_mailbox->getMessageIndex());
    require IMP_BASE . '/mailbox.php';
    exit;
}

/* Now that we are done processing, get the index and array index of
 * the current message. */
$index_array = $imp_mailbox->getIMAPIndex();
$index = $index_array['index'];
$mailbox_name = $index_array['mailbox'];

/* Get the IMP_Headers:: object. */
require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
$msg_cache = &IMP_MessageCache::singleton();
$cache_entry = $msg_cache->retrieve($mailbox_name, array($index), 1 | 32);
$ob = reset($cache_entry);
if ($ob === false) {
    require IMP_BASE . '/mailbox.php';
    exit;
}
$ob_seen = $ob->seen;
$imp_headers = &Util::cloneObject($ob->header);

/* Parse MIME info and create the body of the message. */
require_once IMP_BASE . '/lib/MIME/Contents.php';
$imp_contents = &IMP_Contents::singleton($index . IMP_IDX_SEP . $mailbox_name);

/* Update the message flag, if necessary. */
$use_pop = ($_SESSION['imp']['base_protocol'] == 'pop3');
if (!$use_pop && !$ob->seen && !$flagged_unseen) {
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $imp_message->flag(array('seen'), $imp_mailbox, true);
}

/* Determine if we should generate the attachment strip links or
 * not. */
if ($prefs->getValue('strip_attachments')) {
    $imp_contents->setStripLink(true, $message_token);
}

/* Don't show summary links if we are printing the message. */
$imp_contents->showSummaryLinks(!$printer_friendly);

if (!$imp_contents->buildMessage()) {
    _returnToMailbox(null, 'message_missing');
    require IMP_BASE . '/mailbox.php';
    exit;
}

$attachments = $imp_contents->getAttachments();
$msgText = $imp_contents->getMessage();

require_once IMP_BASE . '/lib/UI/Message.php';
$imp_ui = new IMP_UI_Message();

/* Develop the list of Headers to display now. We will deal with the
 * 'basic' header information first since there are various
 * manipulations we do to them. */
$basic_headers = $imp_ui->basicHeaders();
$msgAddresses = array();

$imp_headers->setValueByFunction('date', array('nl2br', array($imp_headers, 'addLocalTime'), 'htmlspecialchars'));

/* Get the title/mailbox label of the mailbox page. */
$page_label = IMP::getLabel($imp_mbox['mailbox']);

/* Process the subject now. */
if (($subject = $imp_headers->getValue('subject'))) {
    /* Filter the subject text, if requested. */
    $subject = IMP::filterText($subject);

    require_once 'Horde/Text.php';
    $imp_headers->setValue('subject', Text::htmlSpaces($subject));

    $title = sprintf(_("%s: %s"), $page_label, $subject);
    $shortsub = htmlspecialchars($subject);
} else {
    $shortsub = _("[No Subject]");
    $imp_headers->addHeader('Subject', $shortsub);
    $title = sprintf(_("%s: %s"), $page_label, $shortsub);
}

/* See if the 'X-Priority' header has been set. */
switch ($imp_headers->getXpriority()) {
case 'high':
    $imp_headers->addHeader('Priority', Horde::img('mail_priority_high.png', _("High Priority")) . '&nbsp;' . $imp_headers->getValue('x-priority'));
    break;

case 'low':
    $imp_headers->addHeader('Priority', Horde::img('mail_priority_low.png', _("Low Priority")) . '&nbsp;' . $imp_headers->getValue('x-priority'));
    break;
}

/* Determine if all/list headers needed. */
$all_headers = Util::getFormData('show_all_headers');
$list_headers = Util::getFormData('show_list_headers');

/* Get the rest of the headers if all headers are requested. */
$user_hdrs = $imp_ui->getUserHeaders();

if ($all_headers || !empty($user_hdrs)) {
    $full_h = $imp_headers->getAllHeaders();
    foreach ($full_h as $head => $val) {
        /* Skip the X-Priority header if we have already dealt with
         * it. */
        if ((stristr($head, 'x-priority') !== false) &&
            $imp_headers->getValue('priority')) {
            unset($full_h[$head]);
        } elseif ($imp_headers->alteredHeader($head)) {
            $full_h[$head] = $imp_headers->getValue($head);
        } elseif (is_array($val)) {
            $val = array_map('htmlspecialchars', $val);
            $full_h[$head] = '<ul style="margin:0;padding-left:15px"><li>' . implode("</li>\n<li>", $val) . '</li></ul>';
        } else {
            $full_h[$head] = htmlspecialchars($val);
        }
    }
    ksort($full_h);
}

/* Display the user-specified headers for the current identity. */
$custom_hdrs = array();
if (!empty($user_hdrs) && !$all_headers) {
    foreach ($user_hdrs as $user_hdr) {
        foreach ($full_h as $head => $val) {
            if (stristr($head, $user_hdr) !== false) {
                $custom_hdrs[$head] = $val;
            }
        }
    }
}

/* For the self URL link, we can't trust the index in the query string as it
 * may have changed if we deleted/copied/moved messages. We may need other
 * stuff in the query string, so we need to do an add/remove of 'index'. */
$selfURL = Util::removeParameter(Horde::selfUrl(true), array('index', 'actionID', 'mailbox', 'thismailbox'));
$selfURL = IMP::generateIMPUrl($selfURL, $imp_mbox['mailbox'], $index, $mailbox_name);
$selfURL = html_entity_decode(Util::addParameter($selfURL, 'message_token', $message_token));
$headersURL = htmlspecialchars(Util::removeParameter($selfURL, array('show_all_headers', 'show_list_headers')));

/* Get the starting index for the current message and the message
 * count. */
$msgindex = $imp_mailbox->getMessageIndex();
$msgcount = $imp_mailbox->getMessageCount();

/* Generate previous/next links. */
$prev_msg = $imp_mailbox->getIMAPIndex(-1);
if ($prev_msg) {
    $prev_url = IMP::generateIMPUrl('message.php', $imp_mbox['mailbox'], $prev_msg['index'], $prev_msg['mailbox']);
}
$next_msg = $imp_mailbox->getIMAPIndex(1);
if ($next_msg) {
    $next_url = IMP::generateIMPUrl('message.php', $imp_mbox['mailbox'], $next_msg['index'], $next_msg['mailbox']);
}

/* Generate the mailbox link. */
$mailbox_url = Util::addParameter(IMP::generateIMPUrl('mailbox.php', $imp_mbox['mailbox']), 'start', $msgindex);

/* Generate the view link. */
$view_link = IMP::generateIMPUrl('view.php', $imp_mbox['mailbox'], $index, $mailbox_name);

/* Generate the link to ourselves. */
$message_url = Horde::applicationUrl('message.php');
$self_link = Util::addParameter(IMP::generateIMPUrl('message.php', $imp_mbox['mailbox'], $index, $mailbox_name),
                                array('start' => $msgindex,
                                      'message_token' => $message_token));

Horde::addScriptFile('prototype.js', 'imp', true);
Horde::addScriptFile('popup.js', 'imp', true);
Horde::addScriptFile('message.js', 'imp', true);
require IMP_TEMPLATES . '/common-header.inc';

/* Check for the presence of mailing list information. */
$list_info = $imp_headers->getListInformation();

/* See if the mailing list information has been requested to be displayed. */
if ($list_info['exists'] && ($list_headers || $all_headers)) {
    $imp_headers->parseAllListHeaders();
}

/* Build From address links. */
$imp_headers->buildAddressLinks('from', $self_link, true, !$printer_friendly);

/* Add country/flag image. Try X-Originating-IP first, then fall back
 * on the sender's domain name. */
if (!$printer_friendly) {
    $from_img = '';
    $origin_host = str_replace(array('[', ']'), '', $imp_headers->getValue('X-Originating-IP'));
    if (is_array($origin_host)) {
        $from_img = '';
        foreach ($origin_host as $host) {
            $from_img .= NLS::generateFlagImageByHost($host) . ' ';
        }
        trim($from_img);
    } elseif ($origin_host) {
        $from_img = NLS::generateFlagImageByHost($origin_host);
    }
    if (empty($from_img)) {
        $from_ob = IMP::parseAddressList($imp_headers->getFromAddress());
        if (is_array($from_ob) && !empty($from_ob)) {
            $from_ob = array_shift($from_ob);
            $origin_host = $from_ob->host;
            $from_img = NLS::generateFlagImageByHost($origin_host);
        }
    }
    if (!empty($from_img)) {
        $imp_headers->setValue('from', $imp_headers->getValue('from') . '&nbsp;' . $from_img);
    }
}

/* Build To/Cc/Bcc links. */
foreach (array('to', 'cc', 'bcc') as $val) {
    $msgAddresses[] = $imp_headers->getValue($val);
    $imp_headers->buildAddressLinks($val, $self_link, true, !$printer_friendly);
}

/* Build Reply-To address links. */
if (($reply_to = $imp_headers->buildAddressLinks('reply-to', $self_link, false, !$printer_friendly))) {
    if (!($from = $imp_headers->getValue('from')) || ($from != $reply_to)) {
        $imp_headers->setValue('Reply-to', $reply_to);
    } else {
        $imp_headers->removeHeader('reply-to');
    }
}

/* Determine if we need to show the Reply to All link. */
$addresses = array_keys($user_identity->getAllFromAddresses(true));
$show_reply_all = true;
if (!MIME::addrArray2String(array_merge($imp_headers->getOb('to'), $imp_headers->getOb('cc')), $addresses)) {
    $show_reply_all = false;
}

/* Retrieve any history information for this message. */
if (!$printer_friendly && !empty($conf['maillog']['use_maillog'])) {
    require_once IMP_BASE . '/lib/Maillog.php';
    IMP_Maillog::displayLog($imp_headers->getValue('message-id'));

    /* Do MDN processing now. */
    if ($imp_ui->MDNCheck($ob->header, Util::getFormData('mdn_confirm'))) {
        $confirm_link = Horde::link(htmlspecialchars(Util::addParameter($selfURL, 'mdn_confirm', 1))) . _("HERE") . '</a>';
        $notification->push(sprintf(_("The sender of this message is requesting a Message Disposition Notification from you when you have read this message. Please click %s to send the notification message."), $confirm_link), 'horde.message', array('content.raw'));
    }
}

/* Everything below here is related to preparing the output. */
if (!$printer_friendly) {
    IMP::menu();
    IMP::status();
    IMP::quota();

    /* Set the status information of the message. */
    $identity = $status = null;
    if (!$use_pop) {
        if ($msgAddresses) {
            $identity = $user_identity->getMatchingIdentity($msgAddresses);
            if (($identity !== null) ||
                $user_identity->getMatchingIdentity($msgAddresses, false) !== null) {
                $status .= Horde::img('mail_personal.png', _("Personal"), array('title' => _("Personal")));
            }
            if ($identity === null) {
                $identity = $user_identity->getDefault();
            }
        }

        /* Set status flags. */
        if (!$ob_seen) {
            $status .= Horde::img('mail_unseen.png', _("Unseen"), array('title' => _("Unseen")));
        }
        $flag_array = array(
            'answered' => _("Answered"),
            'draft'    => _("Draft"),
            'flagged'  => _("Flagged For Followup"),
            'deleted'  => _("Deleted")
        );
        foreach ($flag_array as $flag => $desc) {
            if ($ob->$flag) {
                $status .= Horde::img('mail_' . $flag . '.png', $desc, array('title' => $desc));
            }
        }
    }

    /* If this is a search mailbox, display a link to the parent mailbox of the
     * message in the header. */
    $h_page_label = htmlspecialchars($page_label);
    $header_label = $h_page_label;
    if (isset($imp_search) && $imp_search->isSearchMbox()) {
        $header_label .= ' [' . Horde::link(Util::addParameter(Horde::applicationUrl('mailbox.php'), 'mailbox', $mailbox_name)) . IMP::displayFolder($mailbox_name) . '</a>]';
    }

    /* Prepare the navbar top template. */
    $t_template = new IMP_Template();
    $t_template->set('message_url', $message_url);
    $t_template->set('form_input', Util::formInput());
    $t_template->set('mailbox', htmlspecialchars($imp_mbox['mailbox']));
    $t_template->set('thismailbox', htmlspecialchars($mailbox_name));
    $t_template->set('start', htmlspecialchars($msgindex));
    $t_template->set('index', htmlspecialchars($index));
    $t_template->set('label', sprintf(_("%s: %s"), $header_label, $shortsub));
    $t_template->set('msg_count', sprintf(_("(%d&nbsp;of&nbsp;%d)"), $msgindex, $msgcount));
    $t_template->set('status', $status);
    $t_template->set('message_token', $message_token);

    echo $t_template->fetch(IMP_TEMPLATES . '/message/navbar_top.html');

    /* Prepare the navbar navigate template. */
    $n_template = new IMP_Template();
    $n_template->setOption('gettext', true);
    $n_template->set('usepop', $use_pop);
    $n_template->set('id', 1);

    if ($conf['user']['allow_folders']) {
        $n_template->set('move', Horde::widget('#', _("Move to folder"), 'widget', '', "transfer('move_message', 1); return false;", _("Move"), true));
        $n_template->set('copy', Horde::widget('#', _("Copy to folder"), 'widget', '', "transfer('copy_message', 1); return false;", _("Copy"), true));
        $n_template->set('options', IMP::flistSelect(_("This message to"), true, array(), null, true, true, false, true));
    }

    $n_template->set('back_to', Horde::widget($mailbox_url, sprintf(_("Back to %s"), $h_page_label), 'widget', '', '', sprintf(_("Bac_k to %s"), $h_page_label), true));

    $rtl = !empty($nls['rtl'][$language]);
    if (Util::nonInputVar('prev_url')) {
        $n_template->set('prev', Horde::link($prev_url, _("Previous Message")));
        $n_template->set('prev_img', Horde::img($rtl ? 'nav/right.png' : 'nav/left.png', $rtl ? '>' : '<', '', $registry->getImageDir('horde')));
    } else {
        $n_template->set('prev_img', Horde::img($rtl ? 'nav/right-grey.png' : 'nav/left-grey.png', '', '', $registry->getImageDir('horde')));
    }

    if (Util::nonInputVar('next_url')) {
        $n_template->set('next', Horde::link($next_url, _("Next Message")));
        $n_template->set('next_img', Horde::img($rtl ? 'nav/left.png' : 'nav/right.png', $rtl ? '<' : '>', '', $registry->getImageDir('horde')));
    } else {
        $n_template->set('next_img', Horde::img($rtl ? 'nav/left-grey.png' : 'nav/right-grey.png', '', '', $registry->getImageDir('horde')));
    }

    echo $n_template->fetch(IMP_TEMPLATES . '/message/navbar_navigate.html');

    /* Prepare the navbar actions template. */
    $a_template = new IMP_Template();
    $a_template->setOption('gettext', true);
    $compose_params = array('index' => $index, 'identity' => $identity, 'thismailbox' => $mailbox_name);
    if (!$prefs->getValue('compose_popup')) {
        $compose_params += array('start' => $msgindex, 'mailbox' => $imp_mbox['mailbox']);
    }

    if ($ob->deleted) {
        $a_template->set('delete', Horde::widget(Util::addParameter($self_link, 'actionID', 'undelete_message'), _("Undelete"), 'widget', '', '', _("Undelete"), true));
    } else {
        $a_template->set('delete', Horde::widget(Util::addParameter($self_link, 'actionID', 'delete_message'), _("Delete"), 'widget', '', ($use_pop) ? "return window.confirm('" . addslashes(_("Are you sure you wish to PERMANENTLY delete these messages?")) . "');" : '', _("_Delete"), true));
    }

    $a_template->set('reply', Horde::widget(IMP::composeLink(array(), array('actionID' => 'reply') + $compose_params), _("Reply"), 'widget hasmenu', '', '', _("_Reply"), true));
    $a_template->set('reply_sender', Horde::widget(IMP::composeLink(array(), array('actionID' => 'reply') + $compose_params), _("To Sender"), 'widget', '', '', _("To Sender"), true));

    if ($list_info['reply_list']) {
        $a_template->set('reply_list', Horde::widget(IMP::composeLink(array(), array('actionID' => 'reply_list') + $compose_params), _("To List"), 'widget', '', '', _("To _List"), true));
    }

    if ($show_reply_all) {
        $a_template->set('show_reply_all', Horde::widget(IMP::composeLink(array(), array('actionID' => 'reply_all') + $compose_params), _("To All"), 'widget', '', '', _("To _All"), true));
    }

    $a_template->set('forward', Horde::widget(IMP::composeLink(array(), array('actionID' => $prefs->getValue('forward_default')) + $compose_params), _("Forward"), 'widget hasmenu', '', '', _("Fo_rward"), true));
    $a_template->set('forwardall', Horde::widget(IMP::composeLink(array(), array('actionID' => 'forward_all') + $compose_params), _("Entire Message"), 'widget', '', '', _("Entire Message"), true));
    $a_template->set('forwardbody', Horde::widget(IMP::composeLink(array(), array('actionID' => 'forward_body') + $compose_params), _("Body Text Only"), 'widget', '', '', _("Body Text Only"), true));
    $a_template->set('forwardattachments', Horde::widget(IMP::composeLink(array(), array('actionID' => 'forward_attachments') + $compose_params), _("Body Text with Attachments"), 'widget', '', '', _("Body Text with Attachments"), true));

    $a_template->set('redirect', Horde::widget(IMP::composeLink(array(), array('actionID' => 'redirect_compose') + $compose_params), _("Redirect"), 'widget', '', '', _("Redirec_t"), true));

    if (isset($imp_search) && !$imp_search->searchMboxID()) {
        $a_template->set('show_thread', Horde::widget(Util::addParameter(IMP::generateIMPUrl('thread.php', $imp_mbox['mailbox'], $index, $mailbox_name), array('start' => $msgindex)), _("View Thread"), 'widget', '', '', _("_View Thread"), true));
    }

    if ($registry->hasMethod('mail/blacklistFrom')) {
        $a_template->set('blacklist', Horde::widget(Util::addParameter($self_link, 'actionID', 'blacklist'), _("Blacklist"), 'widget', '', '', _("_Blacklist"), true));
    }

    if ($registry->hasMethod('mail/whitelistFrom')) {
        $a_template->set('whitelist', Horde::widget(Util::addParameter($self_link, 'actionID', 'whitelist'), _("Whitelist"), 'widget', '', '', _("_Whitelist"), true));
    }

    if (!empty($conf['user']['allow_view_source'])) {
        $base_part = $imp_contents->getMIMEMessage();
        $a_template->set('view_source', $imp_contents->linkViewJS($base_part, 'view_source', _("_Message Source"), _("Message Source"), 'widget', array(), true));
    }

    if (!empty($conf['user']['allow_resume_all']) ||
        (!empty($conf['user']['allow_resume_all_in_drafts']) &&
         $mailbox_name == IMP::folderPref($prefs->getValue('drafts_folder'), true)) ||
        $ob->draft) {
        $a_template->set('resume', Horde::widget(IMP::composeLink(array(), array('actionID' => 'draft') + $compose_params), _("Resume"), 'widget', '', '', _("Resume"), true));
    }

    $imp_params = IMP::getIMPMboxParameters($imp_mbox['mailbox'], $index, $mailbox_name);
    $a_template->set('save_as', Horde::widget(Horde::downloadUrl($subject, array_merge(array('actionID' => 'save_message'), $imp_params)), _("Save as"), 'widget', '', '', _("Sa_ve as"), 2));

    $print_params = array_merge(array('actionID' => 'print_message'), $imp_params);
    $a_template->set('print', Horde::widget(Util::addParameter(IMP::generateIMPUrl('message.php', $imp_mbox['mailbox']), $print_params), _("Print"), 'widget', '_blank', IMP::popupIMPString('message.php', $print_params) . 'return false;', _("_Print"), true));

    if ($conf['spam']['reporting'] &&
        ($conf['spam']['spamfolder'] ||
         ($mailbox_name != IMP::folderPref($prefs->getValue('spam_folder'), true)))) {
        $a_template->set('spam', Horde::widget('#', _("Report as Spam"), 'widget', '', "message_submit('spam_report'); return false;", _("Report as Spam"), true));
    }

    if ($conf['notspam']['reporting'] &&
        (!$conf['notspam']['spamfolder'] ||
         ($mailbox_name == IMP::folderPref($prefs->getValue('spam_folder'), true)))) {
        $a_template->set('notspam', Horde::widget('#', _("Report as Innocent"), 'widget', '', "message_submit('notspam_report'); return false;", _("Report as Innocent"), true));
    }

    $a_template->set('redirect', Horde::widget(IMP::composeLink(array(), array('actionID' => 'redirect_compose') + $compose_params), _("Redirect"), 'widget', '', '', _("Redirec_t"), true));

    $a_template->set('headers', Horde::widget('#', _("Headers"), 'widget hasmenu', '', '', _("Headers"), true));
    if ($all_headers || $list_headers) {
        $a_template->set('common_headers', Horde::widget($headersURL, _("Show Common Headers"), 'widget', '', '', _("Show Common Headers"), true));
    }
    if (!$all_headers) {
        $a_template->set('all_headers', Horde::widget(Util::addParameter($headersURL, 'show_all_headers', 1), _("Show All Headers"), 'widget', '', '', _("Show All Headers"), true));
    }
    if ($list_info['exists'] && !$list_headers) {
        $a_template->set('list_headers', Horde::widget(Util::addParameter($headersURL, 'show_list_headers', 1), _("Show Mailing List Information"), 'widget', '', '', _("Show Mailing List Information"), true));
    }

    echo $a_template->fetch(IMP_TEMPLATES . '/message/navbar_actions.html');
}

$atc_display = $prefs->getValue('attachment_display');
$show_parts = (!empty($attachments) && (($atc_display == 'list') || ($atc_display == 'both')));
$downloadall_link = $imp_contents->getDownloadAllLink();
$hdrs = array();
$i = 1;

/* Prepare the main message template. */
$m_template = new IMP_Template();
if ($all_headers) {
    foreach ($full_h as $head => $val) {
        if (in_array($head, $basic_headers)) {
            $val = $imp_headers->getValue($head);
        }
        $hdrs[] = array('name' => $head, 'val' => $val, 'i' => (++$i % 2));
    }
} else {
    foreach ($basic_headers as $head => $str) {
        if ($val = $imp_headers->getValue($head)) {
            $hdrs[] = array('name' => $str, 'val' => $val, 'i' => (++$i % 2));
        }
    }
}

if (!empty($user_hdrs) && count($custom_hdrs) > 0) {
    foreach ($custom_hdrs as $head => $val) {
        $hdrs[] = array('name' => $head, 'val' => $val, 'i' => (++$i % 2));
    }
}

if ($list_headers && $list_info['exists']) {
    foreach ($imp_headers->listHeaders() as $head => $str) {
        if ($val = $imp_headers->getValue($head)) {
            $hdrs[] = array('name' => $str, 'val' => $val, 'i' => (++$i % 2));
        }
    }
}

if ($val = $imp_headers->getValue('priority')) {
    $hdrs[] = array('name' => _("Priority"), 'val' => $val, 'i' => (++$i % 2));
}

if ($show_parts || ($downloadall_link && !$printer_friendly)) {
    $val = '';
    if ($show_parts) {
        $val = '<table cellspacing="2">' . $attachments . '</table>';
    }
    if ($downloadall_link && !$printer_friendly) {
        $val .= Horde::link($downloadall_link, _("Download All Attachments (in .zip file)")) . _("Download All Attachments (in .zip file)") . ' ' . Horde::img('compressed.png', _("Download All Attachments (in .zip file)"), '', $registry->getImageDir('horde') . '/mime') . '</a>';
        if ($prefs->getValue('strip_attachments')) {
            $url = Util::removeParameter(Horde::selfUrl(true), array('actionID'));
            $url = html_entity_decode(Util::addParameter($url, array('actionID' => 'strip_all', 'message_token' => $message_token)));
            $val .= '<br />' . Horde::link(htmlspecialchars($url), _("Strip All Attachments"), null, null, "return window.confirm('" . addslashes(_("Are you sure you wish to PERMANENTLY delete all attachments?")) . "');") . _("Strip All Attachments") . ' ' . Horde::img('delete.png', _("Strip Attachments"), null, $registry->getImageDir('horde')) . '</a>';
        }
    }
    $hdrs[] = array('name' => _("Part(s)"), 'val' => $val, 'i' => (++$i % 2));
}

if ($printer_friendly && !empty($conf['print']['add_printedby'])) {
    $hdrs[] = array('name' => _("Printed By"), 'val' => $user_identity->getFullname() ? $user_identity->getFullname() : Auth::getAuth(), 'i' => (++$i % 2));
}

$m_template->set('headers', $hdrs);
$m_template->set('msgtext', $msgText);
echo $m_template->fetch(IMP_TEMPLATES . '/message/message.html');

if (!$printer_friendly) {
    echo '<input type="hidden" name="flag" id="flag" value="" />';
    $a_template->set('isbottom', true);
    echo $a_template->fetch(IMP_TEMPLATES . '/message/navbar_actions.html');

    $n_template->set('id', 2);
    $n_template->set('isbottom', true);
    if ($n_template->get('move')) {
        $n_template->set('move', Horde::widget('#', _("Move to folder"), 'widget', '', "transfer('move_message', 2); return false;", _("Move"), true), true);
        $n_template->set('copy', Horde::widget('#', _("Copy to folder"), 'widget', '', "transfer('copy_message', 2); return false;", _("Copy"), true));
    }
    echo $n_template->fetch(IMP_TEMPLATES . '/message/navbar_navigate.html');
}

if ($browser->hasFeature('javascript')) {
    require $registry->get('templates', 'horde') . '/contents/open_view_win.js';
    if ($printer_friendly) {
        require $registry->get('templates', 'horde') . '/javascript/print.js';
    }
}

require $registry->get('templates', 'horde') . '/common-footer.inc';
