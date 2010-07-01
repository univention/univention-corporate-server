<?php
/**
 * DIMP Compose page.
 *
 * List of potential parameters:
 *   'popup' - Explicitly mark window as popup. Needed if compose page is
 *             opened from a page other than the base DIMP page.
 *   TODO
 *
 * $Horde: dimp/compose.php,v 1.97.2.21 2009-01-06 15:22:36 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 * @author Michael Slusarz <slusarz@horde.org>
 */

function _removeAutoSaveDraft($index)
{
    if (empty($index)) {
        return;
    }
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $idx_array = array($index . IMP_IDX_SEP . IMP::folderPref($GLOBALS['prefs']->getValue('drafts_folder'), true));
    $imp_message->delete($idx_array, true);
}

$load_imp = true;
@define('DIMP_BASE', dirname(__FILE__));
require_once DIMP_BASE . '/lib/base.php';
require_once 'Horde/Identity.php';

/* The headers of the message. */
$header = array();
foreach (array('to', 'cc', 'bcc', 'subject', 'in_reply_to', 'references') as $v) {
    $header[$v] = rawurldecode(Util::getFormData($v, ''));
}

$action = Util::getFormData('action');
$get_sig = true;
$msg = '';

$identity = &Identity::singleton(array('imp', 'imp'));
if (!$prefs->isLocked('default_identity')) {
    $identity_id = Util::getFormData('identity');
    if ($identity_id !== null) {
        $identity->setDefault($identity_id);
    }
}

/* Set the current time zone. */
NLS::setTimeZone();

/* Initialize the IMP_Compose:: object. */
require_once IMP_BASE . '/lib/Compose.php';
$imp_compose = &IMP_Compose::singleton(Util::getFormData('messageCache'));

/* Init IMP_UI_Compose:: object. */
require_once IMP_BASE . '/lib/UI/Compose.php';
$imp_ui = new IMP_UI_Compose();

if (count($_POST)) {
    $result = new stdClass;
    $result->action = $action;
    $result->success = false;

    /* Update the file attachment information. */
    if ($action == 'add_attachment') {
        if ($_SESSION['imp']['file_upload'] &&
            $imp_compose->addFilesFromUpload('file_')) {
            $info = DIMP::getAttachmentInfo($imp_compose);
            $result->success = true;
            $result->info = end($info);
            $result->imp_compose = $imp_compose->getMessageCacheId();
        }
        IMP::sendHTTPResponse(DIMP::prepareResponse($result, true, false), 'js-json');
        exit;
    }

    /* Set the default charset. */
    $charset = NLS::getEmailCharset();
    if (!$prefs->isLocked('sending_charset')) {
        $charset = Util::getFormData('charset', $charset);
    }

    switch ($action) {
    case 'auto_save_draft':
    case 'save_draft':
        /* Set up the From address based on the identity. */
        $from = $identity->getFromLine(null, Util::getFormData('from'));
        if (is_a($from, 'PEAR_Error')) {
            $notification->push($from);
            break;
        }
        $header['from'] = $from;

        /* Save the draft. */
        $res = $imp_compose->saveDraft($header, Util::getFormData('message', ''), NLS::getCharset(), Util::getFormData('html'));
        if (is_a($res, 'PEAR_Error')) {
            $notification->push($res->getMessage(), 'horde.error');
        } else {
            $result->success = true;

            /* Delete existing draft. */
            _removeAutoSaveDraft(Util::getFormData('draft_index'));

            if ($action == 'auto_save_draft') {
                /* Just update the last draft index so subsequent
                 * drafts are properly replaced. */
                $result->draft_index = (int)$imp_compose->saveDraftIndex();
            } else {
                $notification->push($res);
            }
        }
        break;

    case 'send_message':
        $from = $identity->getFromLine(null, Util::getFormData('from'));
        if (is_a($from, 'PEAR_Error')) {
            $notification->push($from);
            break;
        }
        $header['from'] = $from;
        $header['replyto'] = $identity->getValue('replyto_addr');

        $header['to'] = $imp_ui->getAddressList(Util::getFormData('to'), Util::getFormData('to_list'), Util::getFormData('to_field'), Util::getFormData('to_new'));
        if ($prefs->getValue('compose_cc')) {
            $header['cc'] = $imp_ui->getAddressList(Util::getFormData('cc'), Util::getFormData('cc_list'), Util::getFormData('cc_field'), Util::getFormData('cc_new'));
        }
        if ($prefs->getValue('compose_bcc')) {
            $header['bcc'] = $imp_ui->getAddressList(Util::getFormData('bcc'), Util::getFormData('bcc_list'), Util::getFormData('bcc_field'), Util::getFormData('bcc_new'));
        }

        $message = Util::getFormData('message');
        $html = Util::getFormData('html');

        $result->reply_type = Util::getFormData('reply_type');
        $result->index = Util::getFormData('index');
        $result->reply_folder = Util::getFormData('folder');

        /* Use IMP_Tree to determine whether the sent mail folder was
         * created. */
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imptree = &IMP_Tree::singleton();
        $imptree->eltDiffStart();

        /* Create the DIMP User-Agent string. */
        require_once DIMP_BASE . '/lib/version.php';
        $useragent = 'Dynamic Internet Messaging Program (DIMP) ' . DIMP_VERSION;

        $options = array(
            'save_sent' => (($prefs->isLocked('save_sent_mail'))
                            ? $identity->getValue('save_sent_mail')
                            : (bool)Util::getFormData('save_sent_mail')),
            'sent_folder' => $identity->getValue('sent_mail_folder'),
            'save_attachments' => Util::getFormData('save_attachments_select'),
            'reply_type' => $result->reply_type,
            'reply_index' => $result->index . IMP_IDX_SEP . $result->reply_folder,
            'readreceipt' => Util::getFormData('request_read_receipt'),
            'useragent' => $useragent
        );
        $sent = $imp_compose->buildAndSendMessage($message, $header, $charset, $html, $options);

        if (is_a($sent, 'PEAR_Error')) {
            $notification->push($sent, 'horde.error');
            break;
        }
        $result->success = true;

        /* Remove any auto-saved drafts. */
        if ($prefs->getValue('auto_save_drafts') ||
            $prefs->getValue('auto_delete_drafts')) {
            _removeAutoSaveDraft(Util::getFormData('draft_index'));
            $result->draft_delete = true;
        }

        if ($sent && $prefs->getValue('compose_confirm')) {
            $notification->push(_("Message sent successfully."), 'horde.success');
        }

        $res = DIMP::getFolderResponse($imptree);
        if (!empty($res)) {
            $result->folder = $res['a'][0];
        }
    }

    IMP::sendHTTPResponse(DIMP::prepareResponse($result, !$result->success || !Util::getFormData('nonotify'), false), 'json');
    exit;
}

/* Attach spellchecker & auto completer. */
require_once DIMP_BASE . '/lib/Dimple.php';
$imp_ui->attachAutoCompleter('Dimple', array('to', 'cc', 'bcc'));
$imp_ui->attachSpellChecker('dimp');

$type = Util::getFormData('type');
$index = Util::getFormData('uid');
$folder = Util::getFormData('folder');
$show_editor = false;
$title = _("New Message");

if (in_array($type, array('reply', 'reply_all', 'reply_list', 'forward_all', 'forward_body', 'forward_attachments', 'resume'))) {
    if (!$index || !$folder) {
        $type = 'new';
    }

    require_once IMP_BASE . '/lib/MIME/Contents.php';
    $imp_contents = &IMP_Contents::singleton($index . IMP_IDX_SEP . $folder);
    if (is_a($imp_contents, 'PEAR_Error')) {
        $notification->push(_("Requested message not found."), 'horde.error');
        $index = $folder = null;
        $type = 'new';
    }
}

switch ($type) {
case 'reply':
case 'reply_all':
case 'reply_list':
    $reply_msg = $imp_compose->replyMessage($type, $imp_contents, Util::getFormData('to'));
    $msg = $reply_msg['body'];
    $header = $reply_msg['headers'];
    $header['replytype'] = 'reply';

    if ($type == 'reply') {
        $title = _("Reply:");
    } elseif ($type == 'reply_all') {
        $title = _("Reply to All:");
    } elseif ($type == 'reply_list') {
        $title = _("Reply to List:");
    }
    $title .= ' ' . $header['subject'];

    if ($reply_msg['format'] == 'html') {
        $show_editor = true;
    }

    if (!$prefs->isLocked('default_identity') && !is_null($reply_msg['identity'])) {
        $identity->setDefault($reply_msg['identity']);
    }
    break;

case 'forward_all':
case 'forward_body':
case 'forward_attachments':
    $fwd_msg = $imp_ui->getForwardData($imp_compose, $imp_contents, $type, $index . IMP_IDX_SEP . $folder);
    if ($type == 'forward_all') {
        $msg = '';
    } else {
        $msg = $fwd_msg['body'];
    }
    $header = $fwd_msg['headers'];
    $header['replytype'] = 'forward';
    $title = $header['title'];
    if ($fwd_msg['format'] == 'html') {
        $show_editor = true;
    }
    $type = 'forward';

    if (!$prefs->isLocked('default_identity') && !is_null($fwd_msg['identity'])) {
        $identity->setDefault($fwd_msg['identity']);
    }
    break;

case 'resume':
    $result = $imp_compose->resumeDraft($index . IMP_IDX_SEP . $folder);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result->getMessage(), 'horde.error');
    } else {
        if ($result['mode'] == 'html') {
            $show_editor = true;
        }
        $msg = $result['msg'];
        if (!is_null($result['identity']) &&
            !$prefs->isLocked('default_identity')) {
            $identity->setDefault($result['identity']);
        }
        $header = array_merge($header, $result['header']);
    }
    $get_sig = false;
    break;

case 'new':
    $rte = ($browser->hasFeature('rte') && $prefs->getValue('compose_html'));
    if ($rte) {
        $show_editor = true;
    }
    break;
}

$sig = $identity->getSignature();
if ($get_sig && !empty($sig)) {
    if ($show_editor) {
        $sig = '<p><!--begin_signature-->' . $imp_compose->text2html(trim($sig)) . '<!--end_signature--></p>';
    }

    $msg = ($identity->getValue('sig_first'))
        ? "\n" . $sig . $msg
        : $msg . "\n" . $sig;
}

$args = array(
    'folder' => $folder,
    'index' => $index,
    'messageCache' => $imp_compose->getMessageCacheId(),
    'qreply' => false,
);

require_once IMP_BASE . '/lib/Template.php';
$t = new IMP_Template(DIMP_TEMPLATES . '/imp/');
$t->setOption('gettext', true);
$t->set('title', $title);
$t->set('closelink', Horde::img('close.png', 'X', array('id' => 'compose_close'), $registry->getImageDir('horde')));

require_once DIMP_BASE . '/lib/Views/Compose.php';
$compose_view = new DIMP_Views_Compose;
$compose_result = $compose_view->showCompose($args);
$t->set('compose_html', $compose_result['html']);

/* Javscript variables to be set immediately. */
$compose_result['js'][] = 'DIMP.conf_compose.show_editor = ' . intval($show_editor);
if (Util::getFormData('popup')) {
    $compose_result['js'][] = 'DIMP.conf_compose.popup = true';
}
IMP::addInlineScript($compose_result['js']);

/* Some actions, like adding forwards, may return error messages so explicitly
 * display those messages now. */
IMP::addInlineScript(array(DIMP::notify()), 'dom');

/* Javascript to be run on DOM loaded. */
require_once 'Horde/Serialize.php';
$compose_result['js_onload'][] = 'DimpCompose.fillForm(' . Horde_Serialize::serialize($msg, SERIALIZE_JSON) . ', ' . Horde_Serialize::serialize($header, SERIALIZE_JSON) . ', "' . (($type == 'new' || $type == 'forward') ? 'to' : 'message') . '", true)';
IMP::addInlineScript($compose_result['js_onload'], 'load');

$scripts = array(
    array('compose.js', 'dimp', true)
);

DIMP::header(_("Message Composition"), $scripts);
echo $t->fetch('compose.html');
DIMP::outputJS();
echo $compose_result['jsappend'];
echo "</body>\n</html>";
