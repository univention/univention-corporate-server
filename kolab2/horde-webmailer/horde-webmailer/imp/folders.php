<?php
/**
 * $Horde: imp/folders.php,v 2.309.2.47 2009-10-12 22:36:33 slusarz Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Anil Madhavapeddy <avsm@horde.org>
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Michael Slusarz <slusarz@horde.org>
 */

/**
 * Utility function to return a url for the various images.
 */
function _image($name, $alt, $type)
{
    static $cache = array();

    $val = ($type == 'folder') ? $name['value'] : $name;
    if (!empty($cache[$type][$val])) {
        return $cache[$type][$val];
    }

    if ($type == 'folder') {
        $cache[$type][$val] = Horde::img($name['icon'], $name['alt'], 'style="vertical-align:middle"', $name['icondir']);
    } else {
        $cache[$type][$val] = Horde::img('tree/' . $name, $alt, 'style="vertical-align:middle"', $GLOBALS['registry']->getImageDir('horde'));
    }

    return $cache[$type][$val];
}

require_once dirname(__FILE__) . '/lib/base.php';
require_once IMP_BASE . '/lib/Folder.php';
require_once IMP_BASE . '/lib/IMAP/Tree.php';
require_once IMP_BASE . '/lib/Template.php';
require_once 'Horde/Help.php';
Horde::addScriptFile('prototype.js', 'imp', true);
Horde::addScriptFile('folders.js', 'imp', true);

/* Redirect back to the mailbox if folder use is not allowed. */
if (!$conf['user']['allow_folders']) {
    $notification->push(_("Folder use is not enabled."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('mailbox.php', true));
    exit;
}

/* Decide whether or not to show all the unsubscribed folders */
$subscribe = $prefs->getValue('subscribe');
$showAll = (!$subscribe || $_SESSION['imp']['showunsub']);

/* Get the base URL for this page. */
$folders_url = Horde::selfUrl();

/* Initialize the IMP_Folder object. */
$imp_folder = &IMP_Folder::singleton();

/* Initialize the IMP_Tree object. */
$imptree = &IMP_Tree::singleton();

$folder_list = Util::getFormData('folder_list', array());

/* Set the URL to refresh the page to in the META tag */
$refresh_url = Horde::applicationUrl('folders.php', true);
$refresh_time = $prefs->getValue('refresh_time');

/* Run through the action handlers. */
$actionID = Util::getFormData('actionID');
if ($actionID) {
    $result = IMP::checkRequestToken('imp.folders', Util::getFormData('folders_token'));
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result);
        $actionID = null;
    }
}

switch ($actionID) {
case 'collapse_folder':
case 'expand_folder':
    $folder = Util::getFormData('folder');
    if (!empty($folder)) {
        ($actionID == 'expand_folder') ? $imptree->expand($folder) : $imptree->collapse($folder);
    }
    break;

case 'expand_all_folders':
    $imptree->expandAll();
    break;

case 'collapse_all_folders':
    $imptree->collapseAll();
    break;

case 'rebuild_tree':
    $imp_folder->clearFlistCache();
    $imptree->init();
    break;

case 'expunge_folder':
    if (!empty($folder_list)) {
        require_once IMP_BASE . '/lib/Message.php';
        $imp_message = &IMP_Message::singleton();
        $imp_message->expungeMailbox(array_flip($folder_list));
    }
    break;

case 'delete_folder':
    if (!empty($folder_list)) {
        $imp_folder->delete($folder_list);
    }
    break;

case 'delete_search_query':
    $queryid = Util::getFormData('queryid');
    if (!empty($queryid)) {
        $imp_search->deleteSearchQuery($queryid);
    }
    break;

case 'download_folder':
case 'download_folder_zip':
    if (!empty($folder_list)) {
        $mbox = $imp_folder->generateMbox($folder_list, false);
        if ($actionID == 'download_folder') {
            $browser->downloadHeaders($folder_list[0] . '.mbox', null, false, strlen($mbox));
        } else {
            require_once 'Horde/Compress.php';
            $horde_compress = &Horde_Compress::singleton('zip');
            $mbox = $horde_compress->compress(array(array('data' => $mbox, 'name' => $folder_list[0] . '.mbox')));
            $browser->downloadHeaders($folder_list[0] . '.zip', 'application/zip', false, strlen($mbox));
        }
        echo $mbox;
        exit;
    }
    break;

case 'import_mbox':
    $import_folder = Util::getFormData('import_folder');
    if (!empty($import_folder)) {
        $res = Browser::wasFileUploaded('mbox_upload', _("mailbox file"));
        if (!is_a($res, 'PEAR_Error')) {
            $res = $imp_folder->importMbox($import_folder, $_FILES['mbox_upload']['tmp_name']);
            $mbox_name = basename(Util::dispelMagicQuotes($_FILES['mbox_upload']['name']));
            if ($res === false) {
                $notification->push(sprintf(_("There was an error importing %s."), $mbox_name), 'horde.error');
            } else {
                $notification->push(sprintf(_("Imported %d messages from %s."), $res, $mbox_name), 'horde.success');
            }
        } else {
            $notification->push($res);
        }
        $actionID = null;
    } else {
        $refresh_time = null;
    }
    break;

case 'create_folder':
    $new_mailbox = Util::getFormData('new_mailbox');
    if (!empty($new_mailbox)) {
        $new_mailbox = String::convertCharset($new_mailbox, NLS::getCharset(), 'UTF7-IMAP');
        $new_mailbox = $imptree->createMailboxName(array_shift($folder_list), $new_mailbox);
        if (is_a($new_mailbox, 'PEAR_Error')) {
            $notification->push($new_mailbox);
        } else {
            $imp_folder->create($new_mailbox, $subscribe);
        }
    }
    break;

case 'rename_folder':
    // $old_names already in UTF7-IMAP
    $old_names = array_map('trim', explode("\n", Util::getFormData('old_names')));
    $new_names = array_map('trim', explode("\n", Util::getFormData('new_names')));

    $iMax = count($new_names);
    if (!empty($new_names) &&
        !empty($old_names) &&
        ($iMax == count($old_names))) {
        for ($i = 0; $i < $iMax; ++$i) {
            $old_ns = IMP::getNamespace($old_names[$i]);
            $new = trim($new_names[$i], $old_ns['delimiter']);

            /* If this is a personal namespace, then anything goes as far as
             * the input. Just append the personal namespace to it. For
             * others, add the  */
            if (($old_ns['type'] == 'personal') ||
                ($old_ns['name'] &&
                 (stripos($new_names[$i], $old_ns['name']) !== 0))) {
                $new = $old_ns['name'] . $new;
            }

            $imp_folder->rename($old_names[$i], String::convertCharset($new, NLS::getCharset(), 'UTF7-IMAP'));
        }
    }
    break;

case 'subscribe_folder':
case 'unsubscribe_folder':
    if (!empty($folder_list)) {
        if ($actionID == 'subscribe_folder') {
            $imp_folder->subscribe($folder_list);
        } else {
            $imp_folder->unsubscribe($folder_list);
        }
    } else {
        $notification->push(_("No folders were specified"), 'horde.message');
    }
    break;

case 'toggle_subscribed_view':
    if ($subscribe) {
        $showAll = !$showAll;
        $_SESSION['imp']['showunsub'] = $showAll;
        $imptree->showUnsubscribed($showAll);
    }
    break;

case 'poll_folder':
case 'nopoll_folder':
    if (!empty($folder_list)) {
        ($actionID == 'poll_folder') ? $imptree->addPollList($folder_list) : $imptree->removePollList($folder_list);
        $imp_search->createVINBOXFolder();
    }
    break;

case 'folders_empty_mailbox':
    if (!empty($folder_list)) {
        include_once IMP_BASE . '/lib/Message.php';
        $imp_message = &IMP_Message::singleton();
        $imp_message->emptyMailbox($folder_list);
    }
    break;

case 'mark_folder_seen':
case 'mark_folder_unseen':
    if (!empty($folder_list)) {
        include_once IMP_BASE . '/lib/Message.php';
        $imp_message = &IMP_Message::singleton();
        $imp_message->flagAllInMailbox(array('seen'), $folder_list, ($actionID == 'mark_folder_seen'));
    }
    break;

case 'login_compose':
    $open_compose_window = IMP::openComposeWin();
    break;

case 'delete_folder_confirm':
case 'folders_empty_mailbox_confirm':
    if (!empty($folder_list)) {
        $loop = array();
        $rowct = 0;
        foreach ($folder_list as $val) {
            if (!empty($conf['server']['fixed_folders']) &&
                in_array(IMP::folderPref($val, false), $conf['server']['fixed_folders'])) {
                $notification->push(sprintf(_("The folder \"%s\" may not be deleted."), IMP::displayFolder($val)), 'horde.error');
                continue;
            }
            $data = array(
                'class' => (++$rowct % 2) ? 'item0' : 'item1',
                'name' => htmlspecialchars(IMP::displayFolder($val)),
                'val' => htmlspecialchars($val)
            );
            $loop[] = $data;
        }
        if (!count($loop)) {
            break;
        }

        $title = _("Folder Actions - Confirmation");
        require IMP_TEMPLATES . '/common-header.inc';
        IMP::menu();

        $template = new IMP_Template();
        $template->setOption('gettext', true);
        $template->set('delete', ($actionID == 'delete_folder_confirm'));
        $template->set('empty', ($actionID == 'folders_empty_mailbox_confirm'));
        $template->set('folders', $loop);
        $template->set('folders_url', $folders_url);
        $template->set('folders_token', IMP::getRequestToken('imp.folders'));
        echo $template->fetch(IMP_TEMPLATES . '/folders/folders_confirm.html');

        require $registry->get('templates', 'horde') . '/common-footer.inc';
        exit;
    }
    break;

case 'mbox_size':
    if (!empty($folder_list)) {
        $title = _("Folder Sizes");
        Horde::addScriptFile('tables.js', 'imp', true);
        require IMP_TEMPLATES . '/common-header.inc';
        IMP::menu();
        IMP::status();
        IMP::quota();

        $loop = array();
        $rowct = $sum = 0;

        require_once IMP_BASE . '/lib/Message.php';
        $imp_message = &IMP_Message::singleton();

        foreach ($folder_list as $val) {
            $size = $imp_message->sizeMailbox($val, false);
            $data = array(
                'class' => (++$rowct % 2) ? 'item0' : 'item1',
                'name' => htmlspecialchars(IMP::displayFolder($val)),
                'size' => sprintf(_("%.2fMB"), $size / (1024 * 1024)),
                'sort' => $size
            );
            $sum += $size;
            $loop[] = $data;
        }

        $template = new IMP_Template();
        $template->setOption('gettext', true);
        $template->set('folders', $loop);
        $template->set('folders_url', $folders_url);
        $template->set('folders_sum', sprintf(_("%.2fMB"), $sum / (1024 * 1024)));
        echo $template->fetch(IMP_TEMPLATES . '/folders/folders_size.html');

        require $registry->get('templates', 'horde') . '/common-footer.inc';
        exit;
    }
    break;
}

/* Token to use in requests */
$folders_token = IMP::getRequestToken('imp.folders');

$folders_url = Util::addParameter($folders_url, 'folders_token', $folders_token);

$title = _("Folder Navigator");
require IMP_TEMPLATES . '/common-header.inc';
if ($_SESSION['imp']['default_view'] != 'dimp') {
    IMP::menu();
}
IMP::status();
IMP::quota();

if ($_SESSION['imp']['file_upload'] && ($actionID == 'import_mbox')) {
    /* Prepare import template. */
    $i_template = new IMP_Template();
    $i_template->setOption('gettext', true);
    $i_template->set('folders_url', $folders_url);
    $i_template->set('import_folder', $folder_list[0]);
    $i_template->set('folder_name', htmlspecialchars(String::convertCharset($folder_list[0], 'UTF7-IMAP'), ENT_COMPAT, NLS::getCharset()));
    $i_template->set('folders_token', $folders_token);
    echo $i_template->fetch(IMP_TEMPLATES . '/folders/import.html');
    require $registry->get('templates', 'horde') . '/common-footer.inc';
    exit;
}

/* Build the folder tree. */
list($raw_rows, $newmsgs, $displayNames) = $imptree->build();

$fullNames = array();
foreach ($raw_rows as $key => $val) {
    $tmp = IMP::displayFolder($val['value'], true);
    if ($tmp != $displayNames[$key]) {
        $fullNames[$key] = $tmp;
    }
}

require_once IMP_BASE . '/lib/JSON.php';
IMP::addInlineScript(array(
    'var displayNames = ' . IMP_Serialize_JSON::encode(String::convertCharset($displayNames, NLS::getCharset()), 'utf-8'),
    'var fullNames = ' . IMP_Serialize_JSON::encode(String::convertCharset($fullNames, NLS::getCharset()), 'utf-8'),
));

/* Prepare the header template. */
$refresh_title = _("Reload View");
$head_template = new IMP_Template();
$head_template->setOption('gettext', true);
$head_template->set('title', $refresh_title);
$head_template->set('folders_url', $folders_url);
$refresh_ak = Horde::getAccessKey($refresh_title);
$refresh_title = Horde::stripAccessKey($refresh_title);
if (!empty($refresh_ak)) {
    $refresh_title .= sprintf(_(" (Accesskey %s)"), $refresh_ak);
}
$head_template->set('refresh', Horde::link($folders_url, $refresh_title, '', '', '', $refresh_title, $refresh_ak) . Horde::img('reload.png', _("Refresh"), null, $registry->getImageDir('horde')) . '</a>');
$head_template->set('folders_token', $folders_token);
echo $head_template->fetch(IMP_TEMPLATES . '/folders/head.html');

/* Prepare the actions template. */
$a_template = new IMP_Template();
$a_template->setOption('gettext', true);
$a_template->set('id', 0);
$a_template->set('javascript', $browser->hasFeature('javascript'));

if ($a_template->get('javascript')) {
    $a_template->set('check_ak', Horde::getAccessKeyAndTitle(_("Check _All/None")));
} else {
    $a_template->set('go', _("Go"));
}

$a_template->set('create_folder', !empty($GLOBALS['conf']['hooks']['permsdenied']) || (IMP::hasPermission('create_folders') && IMP::hasPermission('max_folders')));
$a_template->set('imp_view', $_SESSION['imp']['default_view'] != 'dimp');
if ($prefs->getValue('subscribe')) {
    $a_template->set('subscribe', true);
    $subToggleText = ($showAll) ? _("Hide Unsubscribed") : _("Show Unsubscribed");
    $a_template->set('toggle_subscribe', Horde::widget(Util::addParameter($folders_url, array('actionID' => 'toggle_subscribed_view', 'folders_token' => $folders_token)), $subToggleText, 'widget', '', '', $subToggleText, true));
}
$a_template->set('nav_poll', !$prefs->isLocked('nav_poll') && !$prefs->getValue('nav_poll_all'));
$a_template->set('notrash', !$prefs->getValue('use_trash'));
$a_template->set('file_upload', $_SESSION['imp']['file_upload']);
$a_template->set('help', Help::link('imp', 'folder-options'));
$a_template->set('expand_all', Horde::widget(Util::addParameter($folders_url, array('actionID' => 'expand_all_folders', 'folders_token' => $folders_token)), _("Expand All Folders"), 'widget', '', '', _("Expand All"), true));
$a_template->set('collapse_all', Horde::widget(Util::addParameter($folders_url, array('actionID' => 'collapse_all_folders', 'folders_token' => $folders_token)), _("Collapse All Folders"), 'widget', '', '', _("Collapse All"), true));

echo $a_template->fetch(IMP_TEMPLATES . '/folders/actions.html');

/* Check to see if user wants new mail notification */
if (!empty($newmsgs)) {
    /* Reopen the mailbox R/W so we ensure the 'recent' flags are cleared from
     * the current mailbox. */
    $imp_imap = &IMP_IMAP::singleton();
    foreach ($newmsgs as $mbox => $nm) {
        $imp_imap->changeMbox($mbox);
    }

    if ($prefs->getValue('nav_popup')) {
        $notification->push(IMP::getNewMessagePopup($newmsgs), 'javascript');
    }

    if (class_exists('Notification_Listener_audio')
        && ($sound = $prefs->getValue('nav_audio'))) {
        $notification->push($registry->getImageDir() . '/audio/' . $sound, 'audio');
    }
}

/* Add some further information to the $raw_rows array. */
$name_url = Util::addParameter(Horde::applicationUrl('mailbox.php'), 'no_newmail_popup', 1);
$rowct = 0;
$morembox = $rows = array();
foreach ($raw_rows as $val) {
    $val['nocheckbox'] = !empty($val['vfolder']);
    if ($_SESSION['imp']['default_view'] != 'dimp') {
        if (!empty($val['vfolder']) && ($val['value'] != IMPTREE_VFOLDER_KEY)) {
            $val['delvfolder'] = Horde::link($imp_search->deleteURL($val['value']), _("Delete Virtual Folder")) . _("Delete") . '</a>';
            $val['editvfolder'] = Horde::link($imp_search->editURL($val['value']), _("Edit Virtual Folder")) . _("Edit") . '</a>';
        }
    }

    $val['class'] = (++$rowct % 2) ? 'item0' : 'item1';

    /* Highlight line differently if folder/mailbox is unsubscribed. */
    if ($showAll &&
        $subscribe &&
        !$val['container'] &&
        !$imptree->isSubscribed($val['base_elt'])) {
        $val['class'] .= ' folderunsub';
    }

    if (!$val['container']) {
        if (!empty($val['unseen'])) {
            $val['name'] = '<strong>' . $val['name'] . '</strong>';
        }
        if ($_SESSION['imp']['default_view'] != 'dimp') {
            $val['name'] = Horde::link(Util::addParameter($name_url, 'mailbox', $val['value']), sprintf(_("View messages in %s"), ($val['vfolder']) ? $val['base_elt']['l'] : $val['display'])) . $val['name'] . '</a>';
        }
    }

    $dir2 = _image($val, null, 'folder');

    if ($val['children']) {
        $dir = Util::addParameter($folders_url, 'folder', $val['value']);
        if ($imptree->isOpen($val['base_elt'])) {
            $dir = Util::addParameter($dir, 'actionID', 'collapse_folder');
            if ($val['value'] == 'INBOX') {
                $minus_img = 'minustop.png';
            } else {
                $minus_img = ($val['peek']) ? 'minus.png' : 'minusbottom.png';
            }
            if (!empty($GLOBALS['nls']['rtl'][$GLOBALS['language']])) {
                $minus_img = 'rev-' . $minus_img;
            }
            $dir = Horde::link($dir, _("Collapse Folder")) . _image($minus_img, _("Collapse"), 'tree') . "</a>$dir2";
        } else {
            $dir = Util::addParameter($dir, 'actionID', 'expand_folder');
            if ($val['value'] == 'INBOX') {
                $plus_img = 'plustop.png';
            } else {
                $plus_img = ($val['peek']) ? 'plus.png' : 'plusbottom.png';
            }
            if (!empty($GLOBALS['nls']['rtl'][$GLOBALS['language']])) {
                $plus_img = 'rev-' . $plus_img;
            }
            $dir = Horde::link($dir, _("Expand Folder")) . _image($plus_img, _("Expand"), 'tree') . "</a>$dir2";
        }
    } else {
        if ($val['value'] == 'INBOX') {
            $join_img = ($val['peek']) ? 'joinbottom-down.png' : 'blank.png';
        } else {
            $join_img = ($val['peek']) ? 'join.png' : 'joinbottom.png';
        }
        if (!empty($GLOBALS['nls']['rtl'][$GLOBALS['language']])) {
            $join_img = 'rev-' . $join_img;
        }
        $dir = _image($join_img, '', 'tree') . $dir2;
    }

    $line = '';
    $morembox[$val['level']] = $val['peek'];
    for ($i = 0; $i < $val['level']; $i++) {
        $line .= _image(($morembox[$i]) ?
            (empty($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'line.png' : 'rev-line.png') :
            'blank.png', '', 'tree');
    }
    $val['line'] = $line . $dir;
    $rows[] = $val;
}

/* Render the rows now. */
$template = new IMP_Template();
$template->setOption('gettext', true);
$template->set('rows', $rows);
echo $template->fetch(IMP_TEMPLATES . '/folders/folders.html');

if (count($rows) > 10) {
    $a_template->set('id', 1);
    echo $a_template->fetch(IMP_TEMPLATES . '/folders/actions.html');
}

/* No need for extra template - close out the tags here. */
echo '</form></div>';

if (!empty($open_compose_window)) {
    if (!isset($options)) {
        $options = array();
    }
    Horde::addScriptFile('popup.js', 'imp', true);
    IMP::addInlineScript(IMP::popupIMPString('compose.php', array_merge(array('popup' => 1), $options, IMP::getComposeArgs())));
}

/* BC check. */
if (class_exists('Notification_Listener_audio')) {
    $notification->notify(array('listeners' => 'audio'));
}
require $registry->get('templates', 'horde') . '/common-footer.inc';
