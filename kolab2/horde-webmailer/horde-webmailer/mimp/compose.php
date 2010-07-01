<?php
/**
 * $Horde: mimp/compose.php,v 1.75.2.8 2009-04-17 06:21:02 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

function &_getMIMPContents($index, $mailbox)
{
    $res = false;
    if (empty($index)) {
        return $res;
    }
    require_once MIMP_BASE . '/lib/MIME/Contents.php';
    $mimp_contents = &MIMP_Contents::singleton($index . IMP_IDX_SEP . $mailbox);
    if (is_a($mimp_contents, 'PEAR_Error')) {
        $GLOBALS['notification']->push(_("Could not retrieve the message from the mail server."), 'horde.error');
        return $res;
    }
    return $mimp_contents;
}

$load_imp = true;
@define('MIMP_BASE', dirname(__FILE__));
require_once MIMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Compose.php';
require_once 'Horde/Identity.php';
require_once 'Horde/MIME/Part.php';

/* The message text. */
$msg = '';

/* The headers of the message. */
$header = array(
    'bcc' => '',
    'cc' => '',
    'in_reply_to' => Util::getFormData('in_reply_to'),
    'references' => Util::getFormData('references'),
    'subject' => '',
    'to' => '',
);

/* Set the current identity. */
$identity = &Identity::singleton(array('imp', 'imp'));
if (!$prefs->isLocked('default_identity')) {
    $identity_id = Util::getFormData('identity');
    if ($identity_id !== null) {
        $identity->setDefault($identity_id);
    }
}

$sent_mail_folder = $identity->getValue('sent_mail_folder');
$index = Util::getFormData('index');
$thismailbox = Util::getFormData('thismailbox');

/* Set the current time zone. */
NLS::setTimeZone();

/* Initialize the IMP_Compose:: object. */
$oldMessageCacheID = Util::getFormData('messageCache');
$imp_compose = &IMP_Compose::singleton($oldMessageCacheID);

/* Run through the action handlers. */
$actionID = Util::getFormData('a');
switch ($actionID) {
// 'd' = draft
case 'd':
    $result = $imp_compose->resumeDraft($index . IMP_IDX_SEP . $thismailbox);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } else {
        $msg = $result['msg'];
        $header = array_merge($header, $result['header']);
        if (($result['identity'] !== null) &&
            ($result['identity'] != $identity->getDefault()) &&
            !$prefs->isLocked('default_identity')) {
            $identity->setDefault($result['identity']);
            $sent_mail_folder = $identity->getValue('sent_mail_folder');
        }
    }
    break;

case _("Expand Names"):
    $action = Util::getFormData('action');
    require_once IMP_BASE . '/lib/UI/Compose.php';
    $imp_ui = new IMP_UI_Compose();
    $header['to'] = $imp_ui->expandAddresses(Util::getFormData('to'), $imp_compose);
    if ($action !== 'rc') {
        if ($prefs->getValue('compose_cc')) {
            $header['cc'] = $imp_ui->expandAddresses(Util::getFormData('cc'), $imp_compose);
        }
        if ($prefs->getValue('compose_bcc')) {
            $header['bcc'] = $imp_ui->expandAddresses(Util::getFormData('bcc'), $imp_compose);
        }
    }
    if ($action !== null) {
        $actionID = $action;
    }
    break;

// 'r' = reply
// 'rl' = reply to list
// 'ra' = reply to all
case 'r':
case 'ra':
case 'rl':
    if (!($mimp_contents = &_getMIMPContents($index, $thismailbox))) {
        break;
    }
    $actions = array('r' => 'reply', 'ra' => 'reply_all', 'rl' => 'reply_list');
    $reply_msg = $imp_compose->replyMessage($actions[$actionID], $mimp_contents, Util::getFormData('to'));
    $header = $reply_msg['headers'];
    break;

// 'f' = forward
case 'f':
    if (!($mimp_contents = &_getMIMPContents($index, $thismailbox))) {
        break;
    }
    $fwd_msg = $imp_compose->forwardMessage($mimp_contents);
    $header = $fwd_msg['headers'];
    break;

case _("Redirect"):
    if (!($mimp_contents = &_getMIMPContents($index, $thismailbox))) {
        break;
    }

    require_once IMP_BASE . '/lib/UI/Compose.php';
    $imp_ui = new IMP_UI_Compose();

    $f_to = $imp_ui->getAddressList(Util::getFormData('to'));

    $result = $imp_ui->redirectMessage($f_to, $imp_compose, $mimp_contents, NLS::getEmailCharset());
    if (!is_a($result, 'PEAR_Error')) {
        if ($prefs->getValue('compose_confirm')) {
            $notification->push(_("Message redirected successfully."), 'horde.success');
        }
        require MIMP_BASE . '/mailbox.php';
        exit;
    }
    $actionID = 'rc';
    $notification->push($result, 'horde.error');
    break;

case _("Send"):
    $message = Util::getFormData('message', '');
    $f_to = Util::getFormData('to');
    $f_cc = $f_bcc = null;
    $header = array();

    if ($ctype = Util::getFormData('ctype')) {
        if (!($mimp_contents = &_getMIMPContents($index, $thismailbox))) {
            break;
        }

        switch ($ctype) {
        case 'reply':
            $reply_msg = $imp_compose->replyMessage('reply', $mimp_contents, $f_to);
            $msg = $reply_msg['body'];
            $message .= "\n" . $msg;
            break;

        case 'forward':
            $fwd_msg = $imp_compose->forwardMessage($mimp_contents);
            $msg = $fwd_msg['body'];
            $message .= "\n" . $msg;
            $imp_compose->attachIMAPMessage(array($index . IMP_IDX_SEP . $thismailbox), $header);
            break;
        }
    }

    $sig = $identity->getSignature();
    if (!empty($sig)) {
        $message .= "\n" . $sig;
    }

    $header['from'] = $identity->getFromLine(null, Util::getFormData('from'));
    $header['replyto'] = $identity->getValue('replyto_addr');
    $header['subject'] = Util::getFormData('subject');

    require_once IMP_BASE . '/lib/UI/Compose.php';
    $imp_ui = new IMP_UI_Compose();

    $header['to'] = $imp_ui->getAddressList(Util::getFormData('to'));
    if ($prefs->getValue('compose_cc')) {
        $header['cc'] = $imp_ui->getAddressList(Util::getFormData('cc'));
    }
    if ($prefs->getValue('compose_bcc')) {
        $header['bcc'] = $imp_ui->getAddressList(Util::getFormData('bcc'));
    }

    /* Create the DIMP User-Agent string. */
    require_once MIMP_BASE . '/lib/version.php';
    $useragent = 'Mobile Internet Messaging Program (MIMP) ' . MIMP_VERSION;

    $options = array(
        'save_sent' => $prefs->getValue('save_sent_mail'),
        'sent_folder' => $sent_mail_folder,
        'reply_type' => $ctype,
        'reply_index' => empty($index) ? null : $index . IMP_IDX_SEP . $thismailbox,
        'readreceipt' => Util::getFormData('request_read_receipt'),
        'useragent' => $useragent
    );
    $sent = $imp_compose->buildAndSendMessage($message, $header, NLS::getEmailCharset(), false, $options);

    if (is_a($sent, 'PEAR_Error')) {
        $notification->push($sent, 'horde.error');
    } elseif ($sent) {
        $notification->push(_("Message sent successfully."), 'horde.success');
        require MIMP_BASE . '/mailbox.php';
        exit;
    }
    break;
}

/* Get the message cache ID. */
$messageCacheID = $imp_compose->getMessageCacheId();

$title = _("Message Composition");
$m->set('title', $title);

$select_list = $identity->getSelectList();

/* Grab any data that we were supplied with. */
if (empty($msg)) {
    $msg = Util::getFormData('message', '');
}
foreach (array('to', 'cc', 'bcc', 'subject') as $val) {
    if (empty($header[$val])) {
        $header[$val] = Util::getFormData($val);
    }
}

$menu = &new Horde_Mobile_card('o', _("Menu"));
$mset = &$menu->add(new Horde_Mobile_linkset());
MIMP::addMIMPMenu($mset, 'compose');

if ($actionID == 'rc') {
    require MIMP_TEMPLATES . '/compose/redirect.inc';
} else {
    require MIMP_TEMPLATES . '/compose/compose.inc';
}
