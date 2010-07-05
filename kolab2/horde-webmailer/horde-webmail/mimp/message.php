<?php
/**
 * $Horde: mimp/message.php,v 1.62.2.12 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

function _moveAfterAction()
{
    return (($_SESSION['imp']['base_protocol'] != 'pop3') &&
            !IMP::hideDeletedMsgs() &&
            !$GLOBALS['prefs']->getValue('use_trash'));
}

function _buildDisplayAddress($headers, $field)
{
    /* Make sure this is a valid object address field. */
    $array = $headers->getOb($field);
    if (empty($array) || !is_array($array)) {
        return;
    }

    $addr_array = array();

    foreach ($headers->getAddressesFromObject($array) as $ob) {
        if (!empty($ob->address)) {
            // BC: $ob->display did not appear until IMP 4.2.1
            if (stristr($ob->host, 'UNKNOWN') !== false || !isset($ob->display)) {
                $addr_array[] = $ob->address;
            } else {
                $addr_array[] = $ob->display;
            }
        }
    }

    $headers->setValue($field, empty($addr_array) ? _("Undisclosed Recipients") : implode(', ', $addr_array));
}

$load_imp = true;
@define('MIMP_BASE', dirname(__FILE__));
require_once MIMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Mailbox.php';

/* Make sure we have a valid index. */
$imp_mailbox = IMP_Mailbox::singleton($imp_mbox['mailbox'], $imp_mbox['index']);
if (!$imp_mailbox->isValidIndex()) {
    header('Location: ' . Util::addParameter(MIMP::generateMIMPUrl('mailbox.php', $imp_mbox['mailbox']), array('a' => 'm'), null, false));
    exit;
}

/* Set the current time zone. */
NLS::setTimeZone();

/* Run through action handlers */
$actionID = Util::getFormData('a');
switch ($actionID) {
// 'd' = delete message
// 'u' = undelete message
case 'd':
case 'u':
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    if ($actionID == 'u') {
        $imp_message->undelete($imp_mailbox);
    } else {
        $result = IMP::checkRequestToken('mimp.message', Util::getFormData('mt'));
        if (is_a($result, 'PEAR_Error')) {
            $notification->push($result);
        } else {
            $imp_message->delete($imp_mailbox);
            if ($prefs->getValue('mailbox_return')) {
                header('Location: ' . Util::addParameter(MIMP::generateMIMPUrl('mailbox.php', $imp_mbox['mailbox']), array('s' => $imp_mailbox->getMessageIndex()), null, false));
                exit;
            }
            if (_moveAfterAction()) {
                $imp_mailbox->setIndex(1, 'offset');
            }
        }
    }
    break;
}

/* We may have done processing that has taken us past the end of the
 * message array, so we will return to mailbox.php if that is the
 * case. */
if (!$imp_mailbox->isValidIndex()) {
    header('Location: ' . Util::addParameter(MIMP::generateMIMPUrl('mailbox.php', $imp_mbox['mailbox']), array('s' => $imp_mailbox->getMessageIndex()), null, false));
    exit;
}

/* Now that we are done processing the messages, get the index and
 * array index of the current message. */
$index_array = $imp_mailbox->getIMAPIndex();
$index = $index_array['index'];
$mailbox_name = $index_array['mailbox'];

/* If we grab the headers before grabbing body parts, we'll see when a
   message is unread. */
require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
$msg_cache = &IMP_MessageCache::singleton();
$cache_entry = $msg_cache->retrieve($mailbox_name, array($index), 1 | 32);
$ob = reset($cache_entry);
$ob_seen = $ob->seen;
$imp_headers = &Util::cloneObject($ob->header);

/* Parse MIME info. */
require_once MIMP_BASE . '/lib/MIME/Contents.php';
$mimp_contents = &MIMP_Contents::singleton($index . IMP_IDX_SEP . $mailbox_name);

/* Update the message flag, if necessary. */
$use_pop = ($_SESSION['imp']['base_protocol'] == 'pop3');
if (!$use_pop && !$ob->seen) {
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $imp_message->flag(array('seen'), $imp_mailbox, true);
}

if (!$mimp_contents->buildMessage()) {
    header('Location: ' . Util::addParameter(MIMP::generateMIMPUrl('mailbox.php', $mailbox_name), array('a' => 'm'), null, false));
    exit;
}

require_once IMP_BASE . '/lib/UI/Message.php';
$imp_ui = new IMP_UI_Message();

/* Develop the list of Headers to display now. We will deal with the
 * 'basic' header information first since there are various
 * manipulations we do to them. */
$basic_headers = $imp_ui->basicHeaders();
$msgAddresses = '';

$imp_headers->setValueByFunction('date', array('nl2br'));
$reply_to = $imp_headers->getValue('reply_to');
if (!($from = $imp_headers->getValue('from')) || ($from != $reply_to)) {
    $imp_headers->setValue('Reply-to', $reply_to);
} else {
    $imp_headers->removeHeader('reply-to');
}

/* Process the subject now. */
if (($subject = $imp_headers->getValue('subject'))) {
    /* Filter the subject text, if requested. */
    $subject = IMP::filterText($subject);

    $imp_headers->setValue('subject', $subject);

    /* Generate the shortened subject text. */
    if (String::length($subject) > $conf['mailbox']['max_subj_chars']) {
        $subject = String::substr($subject, 0, $conf['mailbox']['max_subj_chars']) . '...';
    }
    $title = $subject;
    $shortsub = $subject;
} else {
    $shortsub = _("[No Subject]");
    $imp_headers->addHeader('Subject', $shortsub);
    $title = $shortsub;
}

/* Check for the presence of mailing list information. */
$list_info = $imp_headers->getListInformation();

/* See if the 'X-Priority' header has been set. */
if (($priority = $imp_headers->getValue('x-priority'))) {
    $imp_headers->addHeader('Priority', $priority);
}

/* Build From/To/Cc/Bcc links. */
foreach (array('from', 'to', 'cc', 'bcc') as $val) {
    if ($val != 'from') {
        $msgAddresses .= $imp_headers->getOb($val);
    }
    _buildDisplayAddress($imp_headers, $val);
}

/* Set the status information of the message. */
$status = '';
$identity = null;
$addresses = array();
if (!$use_pop) {
    if (isset($msgAddresses)) {
        require_once 'Horde/Identity.php';
        $user_identity = &Identity::singleton(array('imp', 'imp'));
        $addresses = $user_identity->getAllFromAddresses();

        $default = $user_identity->getDefault();
        if (isset($addresses[$default]) &&
            strstr(String::lower($msgAddresses), String::lower($addresses[$default]))) {
            $status .= '+';
            $identity = (int)$default;
        } else {
            unset($addresses[$default]);
            foreach ($addresses as $id => $address) {
                if (strstr(String::lower($msgAddresses), String::lower($address))) {
                    $status .= '+';
                    $identity = (int)$id;
                    break;
                }
            }
        }
    }

    /* Set status flags. */
    if (!$ob_seen) {
        $status .= 'N';
    }
    $flag_array = array(
        'answered'  => 'r',
        'draft'     => '',
        'flagged' => '!',
        'deleted'   => 'd'
    );
    foreach ($flag_array as $flag => $val) {
        if ($ob->$flag) {
            $status .= $val;
        }
    }
}

/* Generate previous/next links. */
$prev_msg = $imp_mailbox->getIMAPIndex(-1);
if ($prev_msg) {
    $prev_link = MIMP::generateMIMPUrl('message.php', $imp_mbox['mailbox'], $prev_msg['index'], $prev_msg['mailbox']);
}
$next_msg = $imp_mailbox->getIMAPIndex(1);
if ($next_msg) {
    $next_link = MIMP::generateMIMPUrl('message.php', $imp_mbox['mailbox'], $next_msg['index'], $next_msg['mailbox']);
}

/* Get the starting index for the current message and the message count. */
$msgindex = $imp_mailbox->getMessageIndex();
$msgcount = $imp_mailbox->getMessageCount();

/* Generate the mailbox link. */
$mailbox_link = Util::addParameter(MIMP::generateMIMPUrl('mailbox.php', $imp_mbox['mailbox']), array('s' => $msgindex));
$self_link = MIMP::generateMIMPUrl('message.php', $imp_mbox['mailbox'], $index, $mailbox_name);

/* Create the body of the message. */
$msgText = $mimp_contents->getMessage();

/* Display the first 250 characters, or display the entire message? */
if ($mimp_prefs->getValue('preview_msg') && !Util::getFormData('fullmsg')) {
    $msgText = String::substr($msgText, 0, 250) . " [...]\n";
    $fullmsg_link = new Horde_Mobile_link(_("View Full Message"), Util::addParameter($self_link, array('fullmsg' => 1)));
}

/* Create message menu. */
$menu = new Horde_Mobile_card('o', _("Menu"));
$mset = &$menu->add(new Horde_Mobile_linkset());

if ($ob->deleted) {
    $mset->add(new Horde_Mobile_link(_("Undelete"), Util::addParameter($self_link, array('a' => 'u'))));
} else {
    $mset->add(new Horde_Mobile_link(_("Delete"), Util::addParameter($self_link, array('a' => 'd', 'mt' => IMP::getRequestToken('mimp.message')))));
}

$compose_params = array('index' => $index, 'identity' => $identity, 'thismailbox' => $mailbox_name);

/* Add compose actions (Reply, Reply List, Reply All, Forward,
 * Redirect). */
$items = array(MIMP::composeLink(array(), array('a' => 'r') + $compose_params) => _("Reply"));

if ($list_info['reply_list']) {
    $items[MIMP::composeLink(array(), array('a' => 'rl') + $compose_params)] = _("Reply to List");
}

if (MIME::addrArray2String(array_merge($imp_headers->getOb('to'), $imp_headers->getOb('cc')), $addresses)) {
    $items[MIMP::composeLink(array(), array('a' => 'ra') + $compose_params)] = _("Reply All");
}

$items[MIMP::composeLink(array(), array('a' => 'f') + $compose_params)] = _("Forward");
$items[MIMP::composeLink(array(), array('a' => 'rc') + $compose_params)] = _("Redirect");

foreach ($items as $link => $label) {
    $mset->add(new Horde_Mobile_link($label, $link));
}

if (isset($next_link)) {
    $mset->add(new Horde_Mobile_link(_("Next"), $next_link));
}
if (isset($prev_link)) {
    $mset->add(new Horde_Mobile_link(_("Prev"), $prev_link));
}

$mset->add(new Horde_Mobile_link(sprintf(_("To %s"), IMP::getLabel($mailbox_name)), $mailbox_link));

MIMP::addMIMPMenu($mset, 'message');

$m->set('title', $title);

$c = &$m->add(new Horde_Mobile_card('m', $status . ' ' . $title . ' ' . sprintf(_("(%d of %d)"), $msgindex, $msgcount)));
$c->softkey('#o', _("Menu"));

$l->setMobileObject($c);
$notification->notify(array('listeners' => 'status'));

$null = null;
$hb = &$c->add(new Horde_Mobile_block($null));

foreach ($basic_headers as $head => $str) {
    if ($val = $imp_headers->getValue($head)) {
        $all_to = false;
        $hb->add(new Horde_Mobile_text($str . ': ', array('b')));
        if ((String::lower($head) == 'to') &&
            !Util::getFormData('allto') &&
            (($pos = strpos($val, ',')) !== false)) {
            $val = String::substr($val, 0, strpos($val, ','));
            $all_to = true;
        }
        $t = &$hb->add(new Horde_Mobile_text($val . (($all_to) ? ' ' : "\n")));
        if ($all_to) {
            $hb->add(new Horde_Mobile_link('[' . _("Show All") . ']', Util::addParameter($self_link, array('allto' => 1))));
            $t = &$hb->add(new Horde_Mobile_text("\n"));
        }
        $t->set('linebreaks', true);
    }
}

$mimp_contents->getAttachments($hb);

$t = &$c->add(new Horde_Mobile_text($msgText));
$t->set('linebreaks', true);

if (isset($fullmsg_link)) {
    $c->add($fullmsg_link);
}

$m->add($menu);
$m->display();
