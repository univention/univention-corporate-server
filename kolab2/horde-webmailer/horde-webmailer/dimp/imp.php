<?php
/**
 * imp.php - performs an AJAX-requested action and returns the DIMP-specific
 * JSON object
 *
 * $Horde: dimp/imp.php,v 1.194.2.38 2009-05-18 22:48:32 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function _generateDeleteResult($folder, $indices, $change)
{
    $result = new stdClass;
    $result->folder = $folder;
    $result->uids = $indices;
    $result->remove = ($GLOBALS['prefs']->getValue('hide_deleted') ||
                       $GLOBALS['prefs']->getValue('use_trash'));
    $result->cacheid = _cacheID($folder);

    if ($change) {
        $result->viewport = _getListMessages($folder, true);
    }

    $poll = _getPollInformation($folder);
    if (!empty($poll)) {
        $result->poll = $poll;
    }

    return $result;
}

function _cacheID($folder)
{
    require_once IMP_BASE . '/lib/Mailbox.php';
    $imp_mailbox = &IMP_Mailbox::singleton($folder);
    return $imp_mailbox->getCacheId();
}

function _changed($folder, $compare, $indices = array(), $nothread = false)
{
    if (_cacheID($folder) != $compare) {
        return true;
    }

    return (!empty($indices) &&
            (!$nothread && _threadUidChanged($folder, $indices)));
}

function _threadUidChanged($folder, $indices)
{
    $sort = IMP::getSort($folder);
    if ($sort['by'] == SORTTHREAD) {
        require_once IMP_BASE . '/lib/Mailbox.php';
        foreach ($indices as $mbox => $mbox_array) {
            $imp_mailbox = &IMP_Mailbox::singleton($mbox);
            $threadob = $imp_mailbox->getThreadOb();
            foreach ($mbox_array as $val) {
                if ($threadob->getThreadBase($val) !== false) {
                    return true;
                }
            }
        }
    }

    return false;
}

function _getListMessages($folder, $change)
{
    $args = array(
        'cacheid' => Util::getPost('cacheid'),
        'filter' => Util::getPost('filter'),
        'folder' => $folder,
        'searchfolder' => Util::getPost('searchfolder'),
        'searchmsg' => Util::getPost('searchmsg'),
    );

    $search = Util::getPost('search');
    if (!empty($search)) {
        $search = Horde_Serialize::unserialize($search, SERIALIZE_JSON);
        $args += array(
            'search_uid' => $search->imapuid,
            'search_view' => $search->view,
            'search_before' => intval(Util::getPost('search_before')),
            'search_after' => intval(Util::getPost('search_after'))
        );
    } else {
        $args += array(
            'slice_rownum' => intval(Util::getPost('rownum')),
            'slice_start' => intval(Util::getPost('slice_start')),
            'slice_end' => intval(Util::getPost('slice_end'))
        );
    }

    require_once DIMP_BASE . '/lib/Views/ListMessages.php';
    $list_msg = new DIMP_Views_ListMessages();
    $res = $list_msg->ListMessages($args);
    // TODO: This can potentially be optimized for arrival time sort - if the
    // cache ID changes, we know the changes must occur at end of mailbox.
    if (Util::getPost('purge') || $change) {
        $res->update = true;
    }

    $req_id = Util::getPost('request_id');
    if (!is_null($req_id)) {
        $res->request_id = $req_id;
    }

    return $res;
}

function _getIdxString($indices)
{
    $i = each($indices);
    return reset($i['value']) . IMP_IDX_SEP . $i['key'];
}

function _getPollInformation($mbox)
{
    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();
    $elt = $imptree->get($mbox);
    if ($imptree->isPolled($elt)) {
        $info = $imptree->getElementInfo($mbox);
        return array($mbox => isset($info['unseen']) ? $info['unseen'] : 0);
    }
    return array();
}

function _getQuota()
{
    if (isset($_SESSION['imp']['quota']) &&
        is_array($_SESSION['imp']['quota'])) {
        $quotadata = IMP::quotaData(false);
        if (!empty($quotadata)) {
            require_once IMP_BASE . '/lib/Template.php';
            $t = new IMP_Template(DIMP_TEMPLATES . '/imp/');
            $t->set('img', Horde::img('quotauncover.gif', '', array('width' => 99 - $quotadata['percent'], 'height' => '10'), $GLOBALS['registry']->getImageDir('dimp')));
            $t->set('msg', $quotadata['message']);
            return $t->fetch('quota.html');
        }
    }

    return null;
}

// Need to load Util:: to give us access to Util::getPathInfo().
if (!defined('HORDE_BASE')) {
    define('HORDE_BASE', dirname(__FILE__) . '/..');
}
require_once HORDE_BASE . '/lib/core.php';
$action = basename(Util::getPathInfo());
if (empty($action)) {
    // This is the only case where we really don't return anything, since
    // the frontend can be presumed not to make this request on purpose.
    // Other missing data cases we return a response of boolean false.
    exit;
}

// The following actions do not need write access to the session and
// should be opened read-only for performance reasons.
if (in_array($action, array('chunkContent', 'Html2Text', 'Text2Html', 'GetReplyData'))) {
    $session_control = 'readonly';
}

$authentication = 'none';
$dimp_logout = ($action == 'LogOut');
$load_imp = true;
$session_timeout = 'json';
@define('AUTH_HANDLER', true);
@define('DIMP_BASE', dirname(__FILE__));
require_once DIMP_BASE . '/lib/base.php';
require_once 'Horde/Serialize.php';

// Process common request variables.
$folder = Util::getPost('folder');
$indices = IMP::parseIndicesList(Horde_Serialize::unserialize(Util::getPost('uid'), SERIALIZE_JSON));
$cacheid = Util::getPost('cacheid');

// Open an output buffer to ensure that we catch errors that might break JSON
// encoding.
ob_start();

$result = false;

switch ($action) {
case 'CreateFolder':
    if (empty($folder)) {
        break;
    }

    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();
    $imptree->eltDiffStart();

    require_once IMP_BASE . '/lib/Folder.php';
    $imp_folder = &IMP_Folder::singleton();

    $new = String::convertCharset($folder, NLS::getCharset(), 'UTF7-IMAP');
    $new = $imptree->createMailboxName(Util::getPost('parent'), $new);
    if (is_a($new, 'PEAR_Error')) {
        $notification->push($new, 'horde.error');
        $result = false;
    } else {
        $result = $imp_folder->create($new, $prefs->getValue('subscribe'));
        if ($result) {
            $result = DIMP::getFolderResponse($imptree);
        }
    }
    break;

case 'DeleteFolder':
    if (empty($folder)) {
        break;
    }

    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();
    $imptree->eltDiffStart();

    require_once IMP_BASE . '/lib/Folder.php';
    $imp_folder = &IMP_Folder::singleton();
    $result = $imp_folder->delete(array($folder));
    if ($result) {
        $result = DIMP::getFolderResponse($imptree);
    }
    break;

case 'RenameFolder':
    $old = Util::getPost('old_name');
    $new_parent = Util::getPost('new_parent');
    $new = Util::getPost('new_name');
    if (!$old || !$new) {
        break;
    }

    require_once 'Horde/String.php';
    $new = String::convertCharset($new, NLS::getCharset(), 'UTF7-IMAP');

    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();
    $imptree->eltDiffStart();

    require_once IMP_BASE . '/lib/Folder.php';
    $imp_folder = &IMP_Folder::singleton();

    $new = $imptree->createMailboxName($new_parent, $new);
    if (is_a($new, 'PEAR_Error')) {
        $notification->push($new, 'horde.error');
        $result = false;
    } elseif ($old != $new) {
        $result = $imp_folder->rename($old, $new);
        if ($result) {
            $result = DIMP::getFolderResponse($imptree);
        }
    }
    break;

case 'EmptyFolder':
    if (empty($folder)) {
        break;
    }

    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $imp_message->emptyMailbox(array($folder));
    $result = new stdClass;
    $result->mbox = $folder;
    break;

case 'MarkFolderSeen':
case 'MarkFolderUnseen':
    if (empty($folder)) {
        break;
    }

    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $result = $imp_message->flagAllInMailbox(array('seen'),
                                             array($folder),
                                             $action == 'MarkFolderSeen');
    if ($result) {
        $result = new stdClass;
        $result->mbox = $folder;

        $poll = _getPollInformation($folder);
        if (!empty($poll)) {
            $result->poll = array($folder => $poll[$folder]['u']);
        }
    }
    break;

case 'ListFolders':
    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();
    $result = DIMP::getFolderResponse($imptree, array('a' => $imptree->folderList(IMPTREE_FLIST_CONTAINER), 'c' => array(), 'd' => array()));

    $quota = _getQuota();
    if (!is_null($quota)) {
        $result['quota'] = $quota;
    }
    break;

case 'PollFolders':
    $result = new stdClass;

    require_once IMP_BASE . '/lib/Fetchmail.php';
    $fm_account = new IMP_Fetchmail_Account();
    $fm_count = $fm_account->count();
    if (!empty($fm_count)) {
        IMP_Fetchmail::fetchMail(range(0, $fm_count - 1));
    }

    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();

    $result->poll = array();
    foreach ($imptree->getPollList(true) as $val) {
        if ($info = $imptree->getElementInfo($val)) {
            $result->poll[$val] = $info['unseen'];
        }
    }

    if (!empty($folder) && _changed($folder, $cacheid)) {
        $result->viewport = _getListMessages($folder, true);
    }

    $quota = _getQuota();
    if (!is_null($quota)) {
        $result->quota = $quota;
    }
    break;

case 'ListMessages':
    if (empty($folder)) {
        break;
    }

    /* Change sort preferences if necessary. */
    $sortby = Util::getPost('sortby');
    $sortdir = Util::getPost('sortdir');
    if (!is_null($sortby) || !is_null($sortdir)) {
        IMP::setSort($sortby, $sortdir, $folder);
    }

    $result = new stdClass;

    if (Util::getPost('rangeslice')) {
        require_once DIMP_BASE . '/lib/Views/ListMessages.php';
        $list_msg = new DIMP_Views_ListMessages();
        $result->viewport = $list_msg->getSlice($folder, intval(Util::getPost('start')) - 1, intval(Util::getPost('length')));
        $result->viewport->request_id = Util::getPost('request_id');
        $result->viewport->type = 'slice';
    } else {
        $changed = _changed($folder, $cacheid);
        if (!Util::getPost('checkcache') || $changed) {
            $result->viewport = _getListMessages($folder, $changed);
        }
    }
    break;

case 'MoveMessage':
case 'CopyMessage':
    $to = Util::getPost('tofld');
    if (!$to || empty($indices)) {
        break;
    }

    if ($action == 'MoveMessage') {
        $change = _changed($folder, $cacheid, $indices);
    }

    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $result = $imp_message->copy($to,
                                 $action == 'MoveMessage'
                                     ? IMP_MESSAGE_MOVE
                                     : IMP_MESSAGE_COPY,
                                 $indices);
    if ($result) {
        if ($action == 'MoveMessage') {
            $result = _generateDeleteResult($folder, $indices, $change);
            // Need to manually set remove to 'true' since we want to remove
            // message from the list no matter the current pref settings.
            $result->remove = true;
        }

        // Update poll information for destination folder if necessary.
        // Poll information for current folder will be added by
        // _generateDeleteResult() call above.
        $poll = _getPollInformation($to);
        if (!empty($poll)) {
            if (!isset($result->poll)) {
                $result->poll = array();
            }
            $result->poll = array_merge($result->poll, $poll);
        }
    }
    break;

case 'MarkMessage':
    $flag = Util::getPost('messageFlag');
    if (!$flag || empty($indices)) {
        break;
    }
    if ($flag[0] == '-') {
        $flag = substr($flag, 1);
        $set = false;
    } else {
        $set = true;
    }

    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $result = $imp_message->flag(array($flag), $indices, $set);
    if ($result) {
        $result = new stdClass;
    }
    break;

case 'DeleteMessage':
case 'UndeleteMessage':
    if (empty($indices)) {
        break;
    }

    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    if ($action == 'DeleteMessage') {
        $change = _changed($folder, $cacheid, $indices, !$prefs->getValue('hide_deleted') && !$prefs->getValue('use_trash'));
        $result = $imp_message->delete($indices);
        if ($result) {
            $result = _generateDeleteResult($folder, $indices, $change);
        }
    } else {
        $result = $imp_message->undelete($indices);
        if ($result) {
            $result = new stdClass;
        }
    }
    break;

case 'AddContact':
    $email = Util::getPost('email');
    $name = Util::getPost('name');
    // Allow $name to be empty.
    if (empty($email)) {
        break;
    }

    $result = IMP::addAddress($email, $name);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
        $result = false;
    } else {
        $result = true;
        $notification->push(sprintf(_("%s was successfully added to your address book."), $name ? $name : $email), 'horde.success');
    }
    break;

case 'ReportSpam':
case 'ReportHam':
    $change = _changed($folder, $cacheid, $indices);
    require_once IMP_BASE . '/lib/Spam.php';
    $spam = new IMP_Spam();
    $result = $spam->reportSpam($indices,
                                $action == 'ReportSpam' ? 'spam' : 'notspam');
    if ($result) {
        $result = _generateDeleteResult($folder, $indices, $change);
        // If $result is non-zero, then we know the message has been removed
        // from the current mailbox.
        $result->remove = true;
    }
    break;

case 'Blacklist':
case 'Whitelist':
    if (empty($indices)) {
        break;
    }

    require_once IMP_BASE . '/lib/Filter.php';
    $imp_filter = new IMP_Filter();
    if ($action == 'Whitelist') {
        $imp_filter->whitelistMessage($indices, false);
    } else {
        $change = _changed($folder, $cacheid, $indices);
        if ($imp_filter->blacklistMessage($indices, false)) {
            $result = _generateDeleteResult($folder, $indices, $change);
        }
    }
    break;

case 'ShowPreview':
    if (count($indices) != 1) {
        break;
    }

    $ptr = each($indices);
    $args = array(
        'folder' => $ptr['key'],
        'index' => reset($ptr['value']),
        'preview' => true,
    );

    require_once DIMP_BASE . '/lib/Views/ShowMessage.php';
    $show_msg = new DIMP_Views_ShowMessage();
    $result = (object) $show_msg->showMessage($args);
    break;

case 'Html2Text':
    require_once 'Horde/Text/Filter.php';
    $result = new stdClass;
    // Need to replace line endings or else IE won't display line endings
    // properly.
    $result->text = str_replace("\n", "\r\n", Text_Filter::filter(Util::getPost('text'), 'html2text'));
    break;

case 'Text2Html':
    require_once 'Horde/Text/Filter.php';
    $result = new stdClass;
    $result->text = Text_Filter::filter(Util::getPost('text'), 'text2html', array('parselevel' => TEXT_HTML_MICRO_LINKURL, 'class' => null, 'callback' => null));
    break;

case 'GetForwardData':
    require_once IMP_BASE . '/lib/Compose.php';
    require_once IMP_BASE . '/lib/MIME/Contents.php';
    require_once IMP_BASE . '/lib/UI/Compose.php';
    require_once 'Horde/MIME/Message.php';
    $header = array();
    $msg = $header = null;
    $idx_string = _getIdxString($indices);

    $imp_compose = &IMP_Compose::singleton(Util::getPost('imp_compose'));
    $imp_contents = &IMP_Contents::singleton($idx_string);
    $imp_ui = new IMP_UI_Compose();
    $fwd_msg = $imp_ui->getForwardData($imp_compose, $imp_contents, Util::getPost('type'), $idx_string);
    $header = $fwd_msg['headers'];
    $header['replytype'] = 'forward';

    $result = new stdClass;
    // Can't open read-only since we need to store the message cache id.
    $result->imp_compose = $imp_compose->getMessageCacheId();
    $result->fwd_list = DIMP::getAttachmentInfo($imp_compose);
    $result->body = $fwd_msg['body'];
    $result->header = $header;
    $result->format = $fwd_msg['format'];
    $result->identity = $fwd_msg['identity'];
    break;

case 'GetReplyData':
    require_once IMP_BASE . '/lib/Compose.php';
    require_once IMP_BASE . '/lib/MIME/Contents.php';
    $imp_compose = &IMP_Compose::singleton(Util::getPost('imp_compose'));
    $imp_contents = &IMP_Contents::singleton(_getIdxString($indices));
    $reply_msg = $imp_compose->replyMessage(Util::getPost('type'), $imp_contents);
    $header = $reply_msg['headers'];
    $header['replytype'] = 'reply';

    $result = new stdClass;
    $result->format = $reply_msg['format'];
    $result->body = $reply_msg['body'];
    $result->header = $header;
    $result->identity = $reply_msg['identity'];
    break;

case 'DeleteDraft':
    $index = Util::getPost('index');
    if (empty($indices)) {
        break;
    }
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $idx_array = array($index . IMP_IDX_SEP . IMP::folderPref($prefs->getValue('drafts_folder'), true));
    $imp_message->delete($idx_array, true);
    break;

case 'DeleteAttach':
    $atc = Util::getPost('atc_indices');
    if (!is_null($atc)) {
        require_once IMP_BASE . '/lib/Compose.php';
        $imp_compose = &IMP_Compose::singleton(Util::getPost('imp_compose'));
        $imp_compose->deleteAttachment($atc);
    }
    break;

case 'ShowPortal':
    // Load the block list. Blocks are located in $dimp_block_list.
    // KEY: Block label  VALUE: Horde_Block object
    require DIMP_BASE . '/config/portal.php';

    $blocks = $linkTags = array();
    $css_load = array('dimp' => true);
    foreach ($dimp_block_list as $title => $block) {
        if (is_a($block['ob'], 'Horde_Block')) {
            $app = $block['ob']->getApp();
            $content = ((empty($css_load[$app])) ? Horde::styleSheetLink($app, '', false) : '') . $block['ob']->getContent();
            $css_load[$app] = true;
            // Don't do substitutions on our own blocks.
            if ($app != 'dimp') {
                $content = preg_replace('/<a href="([^"]+)"/',
                                        '<a onclick="DimpBase.go(\'app:' . $app . '\', \'$1\');return false"',
                                        $content);
                if (preg_match_all('/<link .*?rel="stylesheet".*?\/>/',
                                   $content, $links)) {
                    $content = str_replace($links[0], '', $content);
                    foreach ($links[0] as $link) {
                        if (preg_match('/href="(.*?)"/', $link, $href)) {
                            $linkOb = new stdClass;
                            $linkOb->href = $href[1];
                            if (preg_match('/media="(.*?)"/', $link, $media)) {
                                $linkOb->media = $media[1];
                            }
                            $linkTags[] = $linkOb;
                        }
                    }
                }
            }
            if (!empty($content)) {
                $entry = array(
                    'app' => $app,
                    'content' => $content,
                    'title' => $title,
                    'class' => empty($block['class']) ? 'headerbox' : $block['class'],
                );
                if (!empty($block['domid'])) {
                    $entry['domid'] = $block['domid'];
                }
                if (!empty($block['tag'])) {
                    $entry[$block['tag']] = true;
                }
                $blocks[] = $entry;
            }
        }
    }

    $result = new stdClass;
    $result->portal = '';
    if (!empty($blocks)) {
        require_once IMP_BASE . '/lib/Template.php';
        $t = new IMP_Template(DIMP_TEMPLATES . '/imp/');
        $t->set('block', $blocks);
        $result->portal = $t->fetch('portal.html');
    }
    $result->linkTags = $linkTags;
    break;

case 'chunkContent':
    $chunk = basename(Util::getPost('chunk'));
    if (!empty($chunk)) {
        $result = new stdClass;
        $result->chunk = Util::bufferOutput('include', DIMP_TEMPLATES . '/chunks/' . $chunk . '.php');
    }
    break;

case 'PurgeDeleted':
    $change = _changed($folder, $cacheid, $indices);
    if (!$change) {
        $sort = IMP::getSort($folder);
        $change = ($sort['by'] == SORTTHREAD);
    }
    require_once IMP_BASE . '/lib/Message.php';
    $imp_message = &IMP_Message::singleton();
    $expunged = $imp_message->expungeMailbox(array($folder => 1));
    if (!empty($expunged[$folder])) {
        $expunge_count = count($expunged[$folder]);
        $display_folder = IMP::displayFolder($folder);
        if ($expunge_count == 1) {
            $notification->push(sprintf(_("1 message was purged from \"%s\"."),  $display_folder), 'horde.success');
        } else {
            $notification->push(sprintf(_("%s messages were purged from \"%s\"."), $expunge_count, $display_folder), 'horde.success');
        }
        $result = _generateDeleteResult($folder, $expunged, $change);
        // Need to manually set remove to 'true' since we want to remove
        // message from the list no matter the current pref settings.
        $result->remove = true;
    }
    break;

case 'ModifyPollFolder':
    if (empty($folder)) {
        break;
    }

    $add = Util::getPost('add');

    require_once IMP_BASE . '/lib/IMAP/Tree.php';
    $imptree = &IMP_Tree::singleton();

    $result = new stdClass;
    $result->add = (bool) $add;
    $result->folder = $folder;

    if ($add) {
        $imptree->addPollList($folder);
        if ($info = $imptree->getElementInfo($folder)) {
            $result->poll = array($folder => $info['unseen']);
        }
    } else {
        $imptree->removePollList($folder);
    }
    break;

case 'SendMDN':
    $index = Util::getPost('index');
    if (empty($folder) || empty($index)) {
        break;
    }

    /* Get the IMP_Headers:: object. */
    require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
    $msg_cache = &IMP_MessageCache::singleton();
    $cache_entry = $msg_cache->retrieve($folder, array($index), 32);
    $ob = reset($cache_entry);
    if ($ob === false) {
        break;
    }

    require_once IMP_BASE . '/lib/UI/Message.php';
    $imp_ui = new IMP_UI_Message();
    $imp_ui->MDNCheck($ob->header, true);
    break;

case 'iTip':
    $selection = Util::getPost('selection');
    $component = Util::getPost('component');
    $action = str_replace('_', '-', $selection);
    $_POST['action'] = array($component => $action);

    if (empty($indices)) {
        break;
    }
    $idx_string = _getIdxString($indices);

    /* Parse MIME info and create the body of the message. */
    require_once IMP_BASE . '/lib/MIME/Contents.php';
    $imp_contents = &IMP_Contents::singleton($idx_string);

    $cr = !$imp_contents->buildMessage();

    if (is_a($cr, 'PEAR_Error')) {
        $notification->push($cr, 'horde.error');
    }

    break;
}

// Clear the output buffer that we started above, and log any unexpected
// output at a DEBUG level.
$errors = ob_get_clean();
if ($errors) {
    Horde::logMessage('DIMP: unexpected output: ' .
                      $errors, __FILE__, __LINE__, PEAR_LOG_DEBUG);
}

// Send the final result.
IMP::sendHTTPResponse(DIMP::prepareResponse($result), 'json');
