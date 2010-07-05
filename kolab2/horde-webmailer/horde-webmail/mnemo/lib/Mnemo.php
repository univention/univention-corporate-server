<?php
/**
 * $Horde: mnemo/lib/Mnemo.php,v 1.52.2.15 2009-01-13 15:47:33 chuck Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @package Mnemo
 */

/**
 * Sort by memo description.
 */
define('MNEMO_SORT_DESC', 0);

/**
 * Sort by memo category.
 */
define('MNEMO_SORT_CATEGORY', 1);

/**
 * Sort by notepad.
 */
define('MNEMO_SORT_NOTEPAD', 2);

/**
 * Sort in ascending order.
 */
define('MNEMO_SORT_ASCEND', 0);

/**
 * Sort in descending order.
 */
define('MNEMO_SORT_DESCEND', 1);

/**
 * No passphrase provided.
 */
define('MNEMO_ERR_NO_PASSPHRASE', 100);

/**
 * Decrypting failed
 */
define('MNEMO_ERR_DECRYPT', 101);

/**
 * Mnemo Base Class.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Mnemo 1.0
 * @package Mnemo
 */
class Mnemo {

    /**
     * Retrieves the current user's note list from storage. This function will
     * also sort the resulting list, if requested.
     *
     * @param constant $sortby   The field by which to sort. (MNEMO_SORT_DESC,
     *                           MNEMO_SORT_CATEGORY, MNEMO_SORT_NOTEPAD)
     * @param constant $sortdir  The direction by which to sort.
     *                           (MNEMO_SORT_ASC, MNEMO_SORT_DESC)
     *
     * @return array  A list of the requested notes.
     *
     * @see Mnemo_Driver::listMemos()
     */
    function listMemos($sortby = MNEMO_SORT_DESC,
                       $sortdir = MNEMO_SORT_ASCEND)
    {
        global $conf, $display_notepads;
        $memos = array();

        /* Sort the memo list. */
        $sort_functions = array(
            MNEMO_SORT_DESC => 'ByDesc',
            MNEMO_SORT_CATEGORY => 'ByCategory',
            MNEMO_SORT_NOTEPAD => 'ByNotepad',
        );

        foreach ($display_notepads as $notepad) {
            /* Create a Mnemo storage instance. */
            $storage = &Mnemo_Driver::singleton($notepad);
            $storage->retrieve();

            /* Retrieve the memo list from storage. */
            $newmemos = $storage->listMemos();
            $memos = array_merge($memos, $newmemos);
        }

        /* Sort the array if we have a sort function defined for this
         * field. */
        if (isset($sort_functions[$sortby])) {
            $prefix = ($sortdir == MNEMO_SORT_DESCEND) ? '_rsort' : '_sort';
            uasort($memos, array('Mnemo', $prefix . $sort_functions[$sortby]));
        }

        return $memos;
    }

    /**
     * Returns the number of notes in notepads that the current user owns.
     *
     * @return integer  The number of notes that the user owns.
     */
    function countMemos()
    {
        static $count;
        if (isset($count)) {
            return $count;
        }

        $notepads = Mnemo::listNotepads(true, PERMS_ALL);

        $count = 0;
        foreach (array_keys($notepads) as $notepad) {
            /* Create a Mnemo storage instance. */
            $storage = &Mnemo_Driver::singleton($notepad);
            $storage->retrieve();

            /* Retrieve the memo list from storage. */
            $count += count($storage->listMemos());
        }

        return $count;
    }

    /**
     * Retrieves a specific note from storage.
     *
     * @param string $notepad     The notepad to retrieve the note from.
     * @param string $noteId      The Id of the note to retrieve.
     * @param string $passphrase  A passphrase with which this note was
     *                            supposed to be encrypted.
     *
     * @return array  The note.
     */
    function getMemo($notepad, $noteId, $passphrase = null)
    {
        $storage = &Mnemo_Driver::singleton($notepad);
        return $storage->get($noteId, $passphrase);
    }

    /**
     * Get preview text for a note (the first 20 lines or so).
     *
     * @param array $note The note array
     *
     * @return string A few lines of the note for previews or
     * tooltips.
     */
    function getNotePreview($note)
    {
        if (is_a($note['body'], 'PEAR_Error')) {
            return $note['body']->getMessage();
        }
        $lines = explode("\n", wordwrap($note['body']));
        return implode("\n", array_splice($lines, 0, 20));
    }

    /**
     * Lists all notepads a user has access to.
     *
     * @param boolean $owneronly   Only return memo lists that this user owns?
     *                             Defaults to false.
     * @param integer $permission  The permission to filter notepads by.
     *
     * @return array  The memo lists.
     */
    function listNotepads($owneronly = false, $permission = PERMS_SHOW)
    {
        // Work around BC break in listShares() parameters (http://bugs.horde.org/ticket/7820)
        include_once $GLOBALS['registry']->get('fileroot', 'horde') . '/lib/version.php';
        if (version_compare(HORDE_VERSION, '3.2', '<')) {
            $notepads = $GLOBALS['mnemo_shares']->listShares(Auth::getAuth(), $permission, $owneronly ? Auth::getAuth() : null, DATATREE_ROOT, true, 0, 0, 'name');
        } else {
            $notepads = $GLOBALS['mnemo_shares']->listShares(Auth::getAuth(), $permission, $owneronly ? Auth::getAuth() : null, 0, 0, 'name');
        }
        if (is_a($notepads, 'PEAR_Error')) {
            Horde::logMessage($notepads, __FILE__, __LINE__, PEAR_LOG_ERR);
            $empty = array();
            return $empty;
        }

        return $notepads;
    }

    /**
     * Returns the default notepad for the current user at the specified
     * permissions level.
     */
    function getDefaultNotepad($permission = PERMS_SHOW)
    {
        global $prefs;

        $default_notepad = $prefs->getValue('default_notepad');
        $notepads = Mnemo::listNotepads(false, $permission);

        if (isset($notepads[$default_notepad])) {
            return $default_notepad;
        } elseif ($prefs->isLocked('default_notepad')) {
            return '';
        } elseif (count($notepads)) {
            return key($notepads);
        }

        return false;
    }

    /**
     * Returns the real name, if available, of a user.
     *
     * @since Mnemo 2.2
     */
    function getUserName($uid)
    {
        static $names = array();

        if (!isset($names[$uid])) {
            require_once 'Horde/Identity.php';
            $ident = &Identity::singleton('none', $uid);
            $ident->setDefault($ident->getDefault());
            $names[$uid] = $ident->getValue('fullname');
            if (empty($names[$uid])) {
                $names[$uid] = $uid;
            }
        }

        return $names[$uid];
    }

    /**
     * Comparison function for sorting notes by description.
     *
     * @param array $a  Note one.
     * @param array $b  Note two.
     *
     * @return integer  1 if memo one is greater, -1 if memo two is greater; 0
     *                  if they are equal.
     */
    function _sortByDesc($a, $b)
    {
        return strcasecmp($a['desc'], $b['desc']);
    }

    /**
     * Comparison function for reverse sorting notes by description.
     *
     * @param array $a  Note one.
     * @param array $b  Note two.
     *
     * @return integer  -1 if note one is greater, 1 if note two is greater; 0
     *                  if they are equal.
     */
    function _rsortByDesc($a, $b)
    {
        return strcasecmp($b['desc'], $a['desc']);
    }

    /**
     * Comparison function for sorting notes by category.
     *
     * @param array $a  Note one.
     * @param array $b  Note two.
     *
     * @return integer  1 if note one is greater, -1 if note two is greater; 0
     *                  if they are equal.
     */
    function _sortByCategory($a, $b)
    {
        return strcasecmp($a['category'] ? $a['category'] : _("Unfiled"),
                          $b['category'] ? $b['category'] : _("Unfiled"));
    }

    /**
     * Comparison function for reverse sorting notes by category.
     *
     * @param array $a  Note one.
     * @param array $b  Note two.
     *
     * @return integer  -1 if note one is greater, 1 if note two is greater; 0
     *                  if they are equal.
     */
    function _rsortByCategory($a, $b)
    {
        return strcasecmp($b['category'] ? $b['category'] : _("Unfiled"),
                          $a['category'] ? $a['category'] : _("Unfiled"));
    }

    /**
     * Comparison function for sorting notes by notepad name.
     *
     * @param array $a  Note one.
     * @param array $b  Note two.
     *
     * @return integer  1 if note one is greater, -1 if note two is greater;
     *                  0 if they are equal.
     */
    function _sortByNotepad($a, $b)
    {
        $aowner = $a['memolist_id'];
        $bowner = $b['memolist_id'];

        $ashare = $GLOBALS['mnemo_shares']->getShare($aowner);
        $bshare = $GLOBALS['mnemo_shares']->getShare($bowner);

        if (!is_a($ashare, 'PEAR_Error') && $aowner != $ashare->get('owner')) {
            $aowner = $ashare->get('name');
        }
        if (!is_a($bshare, 'PEAR_Error') && $bowner != $bshare->get('owner')) {
            $bowner = $bshare->get('name');
        }

        return strcasecmp($aowner, $bowner);
    }

    /**
     * Comparison function for reverse sorting notes by notepad name.
     *
     * @param array $a  Note one.
     * @param array $b  Note two.
     *
     * @return integer  -1 if note one is greater, 1 if note two is greater;
     *                  0 if they are equal.
     */
    function _rsortByNotepad($a, $b)
    {
        $aowner = $a['memolist_id'];
        $bowner = $b['memolist_id'];

        $ashare = $GLOBALS['mnemo_shares']->getShare($aowner);
        $bshare = $GLOBALS['mnemo_shares']->getShare($bowner);

        if (!is_a($ashare, 'PEAR_Error') && $aowner != $ashare->get('owner')) {
            $aowner = $ashare->get('name');
        }
        if (!is_a($bshare, 'PEAR_Error') && $bowner != $bshare->get('owner')) {
            $bowner = $bshare->get('name');
        }

        return strcasecmp($bowner, $aowner);
    }

    /**
     * Returns the specified permission for the current user.
     *
     * @since Mnemo 2.1
     *
     * @param string $permission  A permission, currently only 'max_notes'.
     *
     * @return mixed  The value of the specified permission.
     */
    function hasPermission($permission)
    {
        global $perms;

        if (!$perms->exists('mnemo:' . $permission)) {
            return true;
        }

        $allowed = $perms->getPermissions('mnemo:' . $permission);
        if (is_array($allowed)) {
            switch ($permission) {
            case 'max_notes':
                $allowed = max($allowed);
                break;
            }
        }

        return $allowed;
    }

    /**
     * Returns a note's passphrase for symmetric encryption from the session
     * cache.
     *
     * @param string $id  A note id.
     *
     * @return string  The passphrase, if set.
     */
    function getPassphrase($id)
    {
        if (isset($_SESSION['mnemo'][$id]['passphrase'])) {
            return Secret::read(Secret::getKey('mnemo'), $_SESSION['mnemo'][$id]['passphrase']);
        }
    }

    /**
     * Stores a note's passphrase for symmetric encryption in the session
     * cache.
     *
     * @param string $id          A note id.
     * @param string $passphrase  The note's passphrase.
     *
     * @return boolean  True
     */
    function storePassphrase($id, $passphrase)
    {
        $_SESSION['mnemo'][$id]['passphrase'] = Secret::write(Secret::getKey('mnemo'), $passphrase);
    }

    /**
     * Initial app setup code.
     */
    function initialize()
    {
        // Update the preference for which notepads to display. If the
        // user doesn't have any selected notepads for view then fall
        // back to some available notepad.
        $GLOBALS['display_notepads'] = unserialize($GLOBALS['prefs']->getValue('display_notepads'));
        if (($notepadId = Util::getFormData('display_notepad')) !== null) {
            if (is_array($notepadId)) {
                $GLOBALS['display_notepads'] = $notepadId;
            } else {
                if (in_array($notepadId, $GLOBALS['display_notepads'])) {
                    $key = array_search($notepadId, $GLOBALS['display_notepads']);
                    unset($GLOBALS['display_notepads'][$key]);
                } else {
                    $GLOBALS['display_notepads'][] = $notepadId;
                }
            }
        }

        // Make sure all notepads exist now, to save on checking later.
        $_temp = $GLOBALS['display_notepads'];
        $_all = Mnemo::listNotepads();
        $GLOBALS['display_notepads'] = array();
        foreach ($_temp as $id) {
            if (isset($_all[$id])) {
                $GLOBALS['display_notepads'][] = $id;
            }
        }

        if (count($GLOBALS['display_notepads']) == 0) {
            $lists = Mnemo::listNotepads(true);
            if (!Auth::getAuth()) {
                /* All notepads for guests. */
                $GLOBALS['display_notepads'] = array_keys($lists);
            } else {
                /* Make sure at least the default notepad is visible. */
                $default_notepad = Mnemo::getDefaultNotepad(PERMS_READ);
                if ($default_notepad) {
                    $GLOBALS['display_notepads'] = array($default_notepad);
                }

                /* If the user's personal notepad doesn't exist, then create it. */
                if (!$GLOBALS['mnemo_shares']->exists(Auth::getAuth())) {
                    require_once 'Horde/Identity.php';
                    $identity = &Identity::singleton();
                    $name = $identity->getValue('fullname');
                    if (trim($name) == '') {
                        $name = Auth::removeHook(Auth::getAuth());
                    }
                    $share = &$GLOBALS['mnemo_shares']->newShare(Auth::getAuth());
                    $share->set('name', sprintf(_("%s's Notepad"), $name));
                    $GLOBALS['mnemo_shares']->addShare($share);

                    /* Make sure the personal notepad is displayed by default. */
                    if (!in_array(Auth::getAuth(), $GLOBALS['display_notepads'])) {
                        $GLOBALS['display_notepads'][] = Auth::getAuth();
                    }
                }
            }
        }

        $GLOBALS['prefs']->setValue('display_notepads', serialize($GLOBALS['display_notepads']));
    }

    /**
     * Builds Mnemo's list of menu items.
     */
    function getMenu($returnType = 'object')
    {
        global $conf, $registry, $print_link;

        require_once 'Horde/Menu.php';

        $menu = new Menu();
        $menu->add(Horde::applicationUrl('list.php'), _("_List Notes"), 'mnemo.png', null, null, null, basename($_SERVER['PHP_SELF']) == 'index.php' ? 'current' : null);
        if (Mnemo::getDefaultNotepad(PERMS_EDIT) &&
            (!empty($conf['hooks']['permsdenied']) ||
             Mnemo::hasPermission('max_notes') === true ||
             Mnemo::hasPermission('max_notes') > Mnemo::countMemos())) {
            $menu->add(Horde::applicationUrl('memo.php?actionID=add_memo'), _("_New Note"), 'add.png', null, null, null, Util::getFormData('memo') ? '__noselection' : null);
        }

        /* Search. */
        $menu->add(Horde::applicationUrl('search.php'), _("_Search"), 'search.png', $registry->getImageDir('horde'));

        /* Import/Export */
        if ($conf['menu']['import_export']) {
            $menu->add(Horde::applicationUrl('data.php'), _("_Import/Export"), 'data.png', $registry->getImageDir('horde'));
        }

        /* Print */
        if ($conf['menu']['print'] && isset($print_link)) {
            $menu->add($print_link, _("_Print"), 'print.png', $registry->getImageDir('horde'), '_blank', 'popup(this.href); return false;');
        }

        if ($returnType == 'object') {
            return $menu;
        } else {
            return $menu->render();
        }
    }

}
