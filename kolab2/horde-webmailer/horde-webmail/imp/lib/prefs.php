<?php
/**
 * $Horde: imp/lib/prefs.php,v 1.3.10.32 2009-01-06 15:24:04 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Horde_Prefs
 */

define('IMP_PREF_NO_FOLDER', '%nofolder');
define('IMP_PREF_VTRASH', '%vtrash');

function handle_sentmailselect($updated)
{
    global $conf, $prefs, $identity;

    if ($conf['user']['allow_folders'] &&
        !$prefs->isLocked('sent_mail_folder')) {
        $sent_mail_folder = Util::getFormData('sent_mail_folder');
        $sent_mail_new = String::convertCharset(Util::getFormData('sent_mail_new'), NLS::getCharset(), 'UTF7-IMAP');
        $sent_mail_default = $prefs->getValue('sent_mail_folder');
        if (empty($sent_mail_folder) && !empty($sent_mail_new)) {
            $sent_mail_folder = IMP::appendNamespace($sent_mail_new);
        } elseif (($sent_mail_folder == '-1') && !empty($sent_mail_default)) {
            $sent_mail_folder = IMP::appendNamespace($sent_mail_default);
        }
        if (!empty($sent_mail_folder)) {
            include_once IMP_BASE . '/lib/Folder.php';
            $imp_folder = &IMP_Folder::singleton();
            if (!$imp_folder->exists($sent_mail_folder)) {
                $imp_folder->create($sent_mail_folder, $prefs->getValue('subscribe'));
            }
        }
        $identity->setValue('sent_mail_folder', IMP::folderPref($sent_mail_folder, false));
        $updated = true;
    }

    return $updated;
}

function handlefolders($updated, $pref, $folder, $new)
{
    global $conf, $prefs;

    if ($conf['user']['allow_folders']) {
        $folder = Util::getFormData($folder);
        if (isset($folder) && !$prefs->isLocked($pref)) {
            $new = String::convertCharset(Util::getFormData($new), NLS::getCharset(), 'UTF7-IMAP');
            if ($folder == IMP_PREF_NO_FOLDER) {
                $prefs->setValue($pref, '');
            } else {
                if (empty($folder) && !empty($new)) {
                    $folder = IMP::appendNamespace($new);
                    include_once IMP_BASE . '/lib/Folder.php';
                    $imp_folder = &IMP_Folder::singleton();
                    if (!$imp_folder->create($folder, $prefs->getValue('subscribe'))) {
                        $folder = null;
                    }
                }
                if (!empty($folder)) {
                    $prefs->setValue($pref, IMP::folderPref($folder, false));
                    $updated = true;
                }
            }
        }
    }

    return $updated;
}

function handle_folderselect($updated)
{
    return $updated | handlefolders($updated, 'drafts_folder', 'drafts', 'drafts_new');
}

function handle_trashselect($updated)
{
    global $prefs;
    $ret = true;

    if (Util::getFormData('trash') == IMP_PREF_VTRASH) {
        if ($prefs->isLocked('use_vtrash')) {
            $ret = false;
        } else {
            $prefs->setValue('use_vtrash', 1);
            $prefs->setValue('trash_folder', '');
        }
    } else {
        if ($prefs->isLocked('trash_folder')) {
            $ret = false;
        } else {
            $ret = $updated | handlefolders($updated, 'trash_folder', 'trash', 'trash_new');
            if ($ret) {
                $prefs->setValue('use_vtrash', 0);
                $prefs->setDirty('trash_folder', true);
            }
        }
    }

    return $ret;
}

function handle_sourceselect($updated)
{
    global $prefs;

    $search_sources = Util::getFormData('search_sources');
    if ($search_sources !== null) {
        $prefs->setValue('search_sources', $search_sources);
        $updated = true;
    }

    $search_fields_string = Util::getFormData('search_fields_string');
    if ($search_fields_string !== null) {
        $prefs->setValue('search_fields', $search_fields_string);
        $updated = true;
    }

    $add_source = Util::getFormData('add_source');
    if ($add_source !== null) {
        $prefs->setValue('add_source', $add_source);
        $updated = true;
    }

    return $updated;
}

function handle_initialpageselect($updated)
{
    $initial_page = Util::getFormData('initial_page');
    $GLOBALS['prefs']->setValue('initial_page', $initial_page);
    return true;
}

function handle_encryptselect($updated)
{
    $default_encrypt = Util::getFormData('default_encrypt');
    $GLOBALS['prefs']->setValue('default_encrypt', $default_encrypt);
    return true;
}

function handle_spamselect($updated)
{
    return $updated | handlefolders($updated, 'spam_folder', 'spam', 'spam_new');
}

function handle_defaultsearchselect($updated)
{
    $default_search = Util::getFormData('default_search');
    $GLOBALS['prefs']->setValue('default_search', $default_search);
    return true;
}

function handle_soundselect($updated)
{
    return $GLOBALS['prefs']->setValue('nav_audio', Util::getFormData('nav_audio'));
}

function prefs_callback()
{
    global $prefs;

    /* Always check to make sure we have a valid trash folder if delete to
     * trash is active. */
    if (($prefs->isDirty('use_trash') || $prefs->isDirty('trash_folder')) &&
        $prefs->getValue('use_trash') &&
        !$prefs->getValue('trash_folder') &&
        !$prefs->getValue('use_vtrash')) {
        $GLOBALS['notification']->push(_("You have activated move to Trash but no Trash folder is defined. You will be unable to delete messages until you set a Trash folder in the preferences."), 'horde.warning');
    }

    if ($prefs->isDirty('use_vtrash') || $prefs->isDirty('use_vinbox')) {
        require_once IMP_BASE . '/lib/Search.php';
        $imp_search = new IMP_Search();
        $imp_search->sessionSetup(true);

        if ($prefs->isDirty('use_vtrash')) {
            require_once IMP_BASE . '/lib/IMAP/Cache.php';
            require_once IMP_BASE . '/lib/IMAP/Tree.php';
            $imap_cache = &IMP_IMAP_Cache::singleton();
            $imap_tree = &IMP_Tree::singleton();
            foreach ($imap_tree->folderList(IMPTREE_FLIST_UNSUB) as $val) {
                $imap_cache->expireCache($val, 1 | 2 | 4);
            }
        }
    }

    if ($prefs->isDirty('subscribe') || $prefs->isDirty('tree_view')) {
        require_once IMP_BASE . '/lib/Folder.php';
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imp_folder = &IMP_Folder::singleton();
        $imp_folder->clearFlistCache();
        $imptree = &IMP_Tree::singleton();
        $imptree->init();
    }

    /* If a maintenance option has been activated, we need to make sure the
     * global Horde 'do_maintenance' pref is also active. */
    if (!$prefs->isLocked('do_maintenance') &&
        !$prefs->getValue('do_maintenance')) {
        foreach (array('rename_sentmail_monthly', 'delete_sentmail_monthly', 'purge_sentmail', 'delete_attachments_monthly', 'purge_trash') as $val) {
            if ($prefs->getValue($val)) {
                $prefs->setValue('do_maintenance', true);
                break;
            }
        }
    }

    if ($prefs->isDirty('mail_domain')) {
        $maildomain = preg_replace('/[^-\.a-z0-9]/i', '', $prefs->getValue('mail_domain'));
        $prefs->setValue('maildomain', $maildomain);
        if (!empty($maildomain)) {
            $_SESSION['imp']['maildomain'] = $maildomain;
        }
    }

    if ($prefs->isDirty('compose_popup')) {
        $GLOBALS['notification']->push('if (window.parent.frames.horde_menu) window.parent.frames.horde_menu.location.reload();', 'javascript');
    }
}

require_once IMP_BASE . '/lib/Maintenance/imp.php';
$maint = &new Maintenance_IMP();
foreach (($maint->exportIntervalPrefs()) as $val) {
    $$val = &$intervals;
}

/* Make sure we have an active IMAP stream. */
if (!$GLOBALS['registry']->call('mail/getStream')) {
    header('Location: ' . Util::addParameter(Horde::applicationUrl('redirect.php'), 'url', Horde::selfUrl(true)));
    exit;
}

// BC check: check for fckeditor (Horde 3.2).
require_once 'Horde/Editor.php';
if (!is_callable(array('Horde_Editor', 'availableEditors')) ||
    !in_array('fckeditor', Horde_Editor::availableEditors())) {
    $GLOBALS['_prefs']['jseditor']['enum'] = array('xinha' => _("Xinha"));;
}
