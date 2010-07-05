<?php
/**
 * The IMP_Folder:: class provides a set of methods for dealing with folders,
 * accounting for subscription, errors, etc.
 *
 * $Horde: imp/lib/Folder.php,v 1.130.10.49 2009-01-06 15:24:03 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package IMP
 */
class IMP_Folder {

    /**
     * Keep around identical lists so that we don't hit the server more that
     * once in the same page for the same thing.
     *
     * @var array
     */
    var $_listCache = array();

    /**
     * Returns a reference to the global IMP_Folder object, only creating it
     * if it doesn't already exist. This ensures that only one IMP_Folder
     * instance is instantiated for any given session.
     *
     * This method must be invoked as:<code>
     *   $imp_folder = &IMP_Folder::singleton();
     * </code>
     *
     * @return IMP_Folder  The IMP_Folder instance.
     */
    function &singleton()
    {
        static $folder;

        if (!isset($folder)) {
            $folder = new IMP_Folder();
        }

        return $folder;
    }

    /**
     * Lists folders.
     *
     * @param boolean $sub   Should we list only subscribed folders?
     * @param array $filter  An list of mailboxes that should be left out of
     *                       the list.
     *
     * @return array  An array of folders, where each array alement is an
     *                associative array containing three values: 'val', with
     *                entire folder name after the server specification;
     *                'label', with the full-length folder name meant for
     *                display and 'abbrev', containing a shortened (26
     *                characters max) label for display in situations where
     *                space is short.
     */
    function flist($sub = false, $filter = array())
    {
        global $conf, $notification;

        $inbox_entry = array('INBOX' => array('val' => 'INBOX', 'label' => _("Inbox"), 'abbrev' => _("Inbox")));

        if ($_SESSION['imp']['base_protocol'] == 'pop3') {
            return $inbox_entry;
        }

        $list = array();
        $subidx = intval($sub);

        /* Compute values that will uniquely identify this list. */
        $full_signature = md5(serialize(array($subidx, $filter)));

        /* Either get the list from the cache, or go to the IMAP server to
           obtain it. */
        if ($conf['server']['cache_folders']) {
            require_once 'Horde/SessionObjects.php';
            $sessionOb = &Horde_SessionObjects::singleton();
            if (!isset($_SESSION['imp']['cache']['folder_cache'])) {
                $_SESSION['imp']['cache']['folder_cache'] = array();
            }
            $folder_cache = &$_SESSION['imp']['cache']['folder_cache'];
            if (isset($folder_cache[$full_signature])) {
                $data = $sessionOb->query($folder_cache[$full_signature]);
                if ($data) {
                    return $data;
                }
            }
        }

        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imaptree = &IMP_Tree::singleton();

        if (!isset($this->_listCache[$subidx])) {
            $list_mask = IMPTREE_FLIST_CONTAINER | IMPTREE_FLIST_OB;
            if (!$sub) {
                $list_mask |= IMPTREE_FLIST_UNSUB;
            }
            $this->_listCache[$subidx] = $imaptree->folderList($list_mask);
        }

        foreach ($this->_listCache[$subidx] as $ob) {
            if (in_array($ob['v'], $filter)) {
                continue;
            }

            $abbrev = $label = str_repeat(' ', 4 * $ob['c']) . $ob['l'];
            if (strlen($abbrev) > 26) {
                $abbrev = String::substr($abbrev, 0, 10) . '...' . String::substr($abbrev, -13, 13);
            }
            $list[$ob['v']] = array('val' => $imaptree->isContainer($ob) ? '' : $ob['v'], 'label' => $label, 'abbrev' => $abbrev);
        }

        /* Add the INBOX on top of list if not in the filter list. */
        if (!in_array('INBOX', $filter)) {
            $list = $inbox_entry + $list;
        }

        /* Save in cache, if needed. */
        if ($conf['server']['cache_folders']) {
            $folder_cache[$full_signature] = $sessionOb->storeOid($list, false);
        }

        return $list;
    }

    /**
     * Returns an array of folders. This is a wrapper around the flist()
     * function which reduces the number of arguments needed if we can assume
     * that IMP's full environment is present.
     *
     * @param array $filter  An array of mailboxes to ignore.
     * @param boolean $sub   If set, will be used to determine if we should
     *                       list only subscribed folders.
     *
     * @return array  The array of mailboxes returned by flist().
     */
    function flist_IMP($filter = array(), $sub = null)
    {
        return $this->flist(($sub === null) ? $GLOBALS['prefs']->getValue('subscribe') : $sub, $filter);
    }

    /**
     * Clears the flist folder cache.
     *
     * @since IMP 4.2
     */
    function clearFlistCache()
    {
        if (!empty($_SESSION['imp']['cache']['folder_cache'])) {
            require_once 'Horde/SessionObjects.php';
            $sessionOb = &Horde_SessionObjects::singleton();
            foreach ($_SESSION['imp']['cache']['folder_cache'] as $val) {
                $sessionOb->setPruneFlag($val, true);
            }
            $_SESSION['imp']['cache']['folder_cache'] = array();
        }
        $this->_listCache = array();
    }

    /**
     * Deletes one or more folders.
     *
     * @param array $folder_array  An array of full utf encoded folder names
     *                             to be deleted.
     * @param boolean $force       Delete folders even if they are fixed.
     *
     * @return boolean  Whether or not the folders were successfully deleted.
     */
    function delete($folder_array, $force = false)
    {
        global $conf, $notification;

        $server = IMP::serverString();
        $return_value = true;
        $deleted = array();

        $imp_imap = &IMP_IMAP::singleton();

        foreach ($folder_array as $folder) {
            if (!$force &&
                !empty($conf['server']['fixed_folders']) &&
                in_array(IMP::folderPref($folder, false), $conf['server']['fixed_folders'])) {
                $notification->push(sprintf(_("The folder \"%s\" may not be deleted."), IMP::displayFolder($folder)), 'horde.error');
                continue;
            }
            if (!imap_deletemailbox($imp_imap->stream(), $server . $folder)) {
                $notification->push(sprintf(_("The folder \"%s\" was not deleted. This is what the server said"), IMP::displayFolder($folder)) .
                                    ': ' . imap_last_error(), 'horde.error');
                $return_value = false;
            } else {
                imap_unsubscribe($imp_imap->stream(), $server . $folder);
                $notification->push(sprintf(_("The folder \"%s\" was successfully deleted."), IMP::displayFolder($folder)), 'horde.success');
                $deleted[] = $folder;
            }
        }

        if (!empty($deleted)) {
            /* Update the IMAP_Tree cache. */
            require_once IMP_BASE . '/lib/IMAP/Tree.php';
            $imaptree = &IMP_Tree::singleton();
            $imaptree->delete($deleted);

            $this->_onDelete($deleted);
        }

        return $return_value;
    }

    /**
     * Do the necessary cleanup/cache updates when deleting folders.
     *
     * @access private
     *
     * @param array $deleted  The list of deleted folders.
     */
    function _onDelete($deleted)
    {
        /* Update the mailbox cache. */
        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
        $msg_cache = &IMP_MessageCache::singleton();
        $msg_cache->deleteMboxes($deleted);

        /* Update the IMAP caches. */
        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();
        foreach ($deleted as $val) {
            $imap_cache->expireCache($val, 1 | 2 | 4);
        }

        /* Reset the folder cache. */
        unset($_SESSION['imp']['cache']['folder_cache']);

        /* Recreate Virtual Folders. */
        $GLOBALS['imp_search']->sessionSetup(true);

        /* Clear the folder from the sort prefs. */
        foreach ($deleted as $val) {
            IMP::setSort(null, null, $val, true);
        }
    }

    /**
     * Create a new IMAP folder if it does not already exist, and subcribe to
     * it as well if requested.
     *
     * @param string $folder      The full utf encoded folder to be created.
     * @param boolean $subscribe  A boolean describing whether or not to use
     *                            folder subscriptions.
     *
     * @return boolean  Whether or not the folder was successfully created.
     */
    function create($folder, $subscribe)
    {
        global $conf, $notification;

        /* Check permissions. */
        if (!IMP::hasPermission('create_folders')) {
            $message = @htmlspecialchars(_("You are not allowed to create folders."), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('imp:create_folders'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            return false;
        } elseif (!IMP::hasPermission('max_folders')) {
            $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d folders."), IMP::hasPermission('max_folders', true)), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('imp:max_folders'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            return false;
        }

        $display_folder = IMP::displayFolder($folder);

        /* Make sure we are not trying to create a duplicate folder */
        if ($this->exists($folder)) {
            $notification->push(sprintf(_("The folder \"%s\" already exists"), $display_folder), 'horde.warning');
            return false;
        }

        $imp_imap = &IMP_IMAP::singleton();
        $server_folder = IMP::serverString($folder);

        /* Attempt to create the mailbox */
        if (!imap_createmailbox($imp_imap->stream(), $server_folder)) {
            $notification->push(sprintf(_("The folder \"%s\" was not created. This is what the server said"), $display_folder) .
                            ': ' . imap_last_error(), 'horde.error');
            return false;
        }

        /* Reset the folder cache. */
        if ($conf['server']['cache_folders']) {
            unset($_SESSION['imp']['cache']['folder_cache']);
        }

        /* Subscribe to the folder. */
        $res = imap_subscribe($imp_imap->stream(), $server_folder);
        if ($subscribe && !$res) {
            $notification->push(sprintf(_("The folder \"%s\" was created but you were not subscribed to it."), $display_folder), 'horde.warning');
        } else {
            /* The folder creation has been successful */
            $notification->push(sprintf(_("The folder \"%s\" was successfully created."), $display_folder), 'horde.success');
        }

        /* Update the IMAP_Tree object. */
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imaptree = &IMP_Tree::singleton();
        $imaptree->insert($folder);

        /* Recreate Virtual Folders. */
        $GLOBALS['imp_search']->sessionSetup(true);

        return true;
    }

    /**
     * Finds out if a specific folder exists or not.
     *
     * @param string $folder  The full utf encoded folder name to be checked.
     *
     * @return boolean  Whether or not the folder exists.
     */
    function exists($folder)
    {
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imaptree = &IMP_Tree::singleton();
        $elt = $imaptree->get($folder);
        if ($elt && !$imaptree->isContainer($elt)) {
            return true;
        }

        $imp_imap = &IMP_IMAP::singleton();
        $ret = @imap_getmailboxes($imp_imap->stream(), IMP::serverString(), $folder);
        return !empty($ret);
    }

    /**
     * Renames an IMAP folder. The subscription status remains the same.  All
     * subfolders will also be renamed.
     *
     * @param string $old     The old utf encoded folder name.
     * @param string $new     The new utf encoded folder name.
     * @param boolean $force  Rename folders even if they are fixed.
     *
     * @return boolean  Whether or not all folder(s) were successfully renamed.
     */
    function rename($old, $new, $force = false)
    {
        /* Don't try to rename from or to an empty string. */
        if (strlen($old) == 0 || strlen($new) == 0) {
            return false;
        }
        if (!$force &&
            !empty($GLOBALS['conf']['server']['fixed_folders']) &&
            in_array(IMP::folderPref($old, false), $GLOBALS['conf']['server']['fixed_folders'])) {
            $GLOBALS['notification']->push(sprintf(_("The folder \"%s\" may not be renamed."), IMP::displayFolder($old)), 'horde.error');
            return false;
        }

        $server = IMP::serverString();
        $deleted = array($old);
        $inserted = array($new);

        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imaptree = &IMP_Tree::singleton();
        $imp_imap = &IMP_IMAP::singleton();

        /* Get list of any folders that are underneath this one. */
        $all_folders = array_merge(array($old), $imaptree->folderList(IMPTREE_FLIST_UNSUB, $old));
        $sub_folders = $imaptree->folderList();

        if (!imap_renamemailbox($imp_imap->stream(), $server . $old, $server . $new)) {
            $GLOBALS['notification']->push(sprintf(_("Renaming \"%s\" to \"%s\" failed. This is what the server said"), IMP::displayFolder($old), IMP::displayFolder($new)) . ': ' . imap_last_error(), 'horde.error');
            return false;
        }
        $GLOBALS['notification']->push(sprintf(_("The folder \"%s\" was successfully renamed to \"%s\"."), IMP::displayFolder($old), IMP::displayFolder($new)), 'horde.success');

        foreach ($all_folders as $folder_old) {
            $deleted[] = $folder_old;

            /* Get the new folder name. */
            $inserted[] = $folder_new = substr_replace($folder_old, $new, 0, strlen($old));

            /* Correctly set subscriptions on renamed folder. */
            if (in_array($folder_old, $sub_folders)) {
                imap_unsubscribe($imp_imap->stream(), $server . $folder_old);
                imap_subscribe($imp_imap->stream(), $server . $folder_new);
            }
        }

        if (!empty($deleted)) {
            $imaptree->rename($deleted, $inserted);
            $this->_onDelete($deleted);
        }

        return true;
    }

    /**
     * Subscribes to one or more IMAP folders.
     *
     * @param array $folder_array  An array of full utf encoded folder names
     *                             to be subscribed.
     *
     * @return boolean  Whether or not the folders were successfully
     *                  subscribed to.
     */
    function subscribe($folder_array)
    {
        global $notification;

        $return_value = true;
        $subscribed = array();

        if (!is_array($folder_array)) {
            $notification->push(_("No folders were specified"), 'horde.warning');
            return false;
        }

        $imp_imap = &IMP_IMAP::singleton();

        foreach ($folder_array as $folder) {
            if ($folder != ' ') {
                if (!imap_subscribe($imp_imap->stream(), IMP::serverString($folder))) {
                    $notification->push(sprintf(_("You were not subscribed to \"%s\". Here is what the server said"), IMP::displayFolder($folder)) . ': ' . imap_last_error(), 'horde.error');
                    $return_value = false;
                } else {
                    $notification->push(sprintf(_("You were successfully subscribed to \"%s\""), IMP::displayFolder($folder)), 'horde.success');
                    $subscribed[] = $folder;
                }
            }
        }

        if (!empty($subscribed)) {
            /* Initialize the IMAP_Tree object. */
            require_once IMP_BASE . '/lib/IMAP/Tree.php';
            $imaptree = &IMP_Tree::singleton();
            $imaptree->subscribe($subscribed);

            /* Reset the folder cache. */
            unset($_SESSION['imp']['cache']['folder_cache']);
        }

        return $return_value;
    }

    /**
     * Unsubscribes from one or more IMAP folders.
     *
     * @param array $folder_array  An array of full utf encoded folder names
     *                             to be unsubscribed.
     *
     * @return boolean  Whether or not the folders were successfully
     *                  unsubscribed from.
     */
    function unsubscribe($folder_array)
    {
        global $notification;

        $return_value = true;
        $unsubscribed = array();

        if (!is_array($folder_array)) {
            $notification->push(_("No folders were specified"), 'horde.message');
            return false;
        }

        $imp_imap = &IMP_IMAP::singleton();

        foreach ($folder_array as $folder) {
            if ($folder != ' ') {
                if (strcasecmp($folder, 'INBOX') == 0) {
                    $notification->push(sprintf(_("You cannot unsubscribe from \"%s\"."), IMP::displayFolder($folder)), 'horde.error');
                } elseif (!imap_unsubscribe($imp_imap->stream(), IMP::serverString($folder))) {
                    $notification->push(sprintf(_("You were not unsubscribed from \"%s\". Here is what the server said"), IMP::displayFolder($folder)) . ': ' . imap_last_error(), 'horde.error');
                    $return_value = false;
                } else {
                    $notification->push(sprintf(_("You were successfully unsubscribed from \"%s\""), IMP::displayFolder($folder)), 'horde.success');
                    $unsubscribed[] = $folder;
                }
            }
        }

        if (!empty($unsubscribed)) {
            /* Initialize the IMAP_Tree object. */
            require_once IMP_BASE . '/lib/IMAP/Tree.php';
            $imaptree = &IMP_Tree::singleton();
            $imaptree->unsubscribe($unsubscribed);

            /* Reset the folder cache. */
            unset($_SESSION['imp']['cache']['folder_cache']);
        }

        return $return_value;
    }

    /**
     * Generates a string that can be saved out to an mbox format mailbox file
     * for a folder or set of folders, optionally including all subfolders of
     * the selected folders as well. All folders will be put into the same
     * string.
     *
     * @author Didi Rieder <adrieder@sbox.tugraz.at>
     *
     * @param array $folder_list  A list of full utf encoded folder names to
     *                            generate an mbox file for.
     * @param boolean $recursive  Include subfolders?
     *
     * @return string  An mbox format mailbox file.
     */
    function &generateMbox($folder_list, $recursive = false)
    {
        $body = '';

        if (is_array($folder_list)) {
            $imp_imap = &IMP_IMAP::singleton();
            $stream = $imp_imap->stream();
            foreach ($folder_list as $folder) {
                $imp_imap->changeMbox($folder, IMP_IMAP_AUTO);
                $count = imap_num_msg($stream);
                for ($i = 1; $i <= $count; $i++) {
                    $h = imap_header($stream, $i);
                    $from = '<>';
                    if (isset($h->from[0])) {
                        if (isset($h->from[0]->mailbox) && isset($h->from[0]->host)) {
                            $from = $h->from[0]->mailbox . '@' . $h->from[0]->host;
                        }
                    }

                    /* We need this long command since some MUAs (e.g. pine)
                       require a space in front of single digit days. */
                    $date = sprintf('%s %2s %s', date('D M', $h->udate), date('j', $h->udate), date('H:i:s Y', $h->udate));
                    $body .= 'From ' . $from . ' ' . $date . "\n";
                    $body .= str_replace("\r\n", "\n", imap_fetchheader($stream, $i, FT_PREFETCHTEXT));
                    $body .= str_replace("\r\n", "\n", imap_body($stream, $i, FT_PEEK)) . "\n";
                }
            }
        }

        return $body;
    }

    /**
     * Imports messages into a given folder from a mbox format mailbox file.
     *
     * @param string $folder  The folder to put the messages into.
     * @param string $mbox    String containing the mbox filename.
     *
     * @return mixed  False (boolean) on fail or the number of messages
     *                imported (integer) on success.
     */
    function importMbox($folder, $mbox)
    {
        $message = '';
        $msgcount = 0;
        $target = IMP::serverString($folder);

        $imp_imap = &IMP_IMAP::singleton();
        $stream = $imp_imap->stream();

        $fd = fopen($mbox, "r");
        while (!feof($fd)) {
            $line = fgets($fd, 4096);

            if (preg_match('/From (.+@.+|- )/A', $line)) {
                if (!empty($message)) {
                    if (@imap_append($stream, $target, IMP::removeBareNewlines($message))) {
                        $msgcount++;
                    }
                }
                $message = '';
            } else {
                $message .= $line;
            }
        }
        fclose($fd);

        if (!empty($message)) {
            if (@imap_append($stream, $target, IMP::removeBareNewlines($message))) {
                $msgcount++;
            }
        }

        return ($msgcount > 0) ? $msgcount : false;
    }

}
