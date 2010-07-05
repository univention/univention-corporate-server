<?php
/**
 * Mnemo external API interface.
 *
 * This file defines Mnemo's external API interface.  Other applications can
 * interact with Mnemo through this API.
 *
 * $Horde: mnemo/lib/api.php,v 1.53.2.35 2009-09-04 10:38:37 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @since   Mnemo 1.0
 * @package Mnemo
 */

$_services['perms'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray'
);

$_services['removeUserData'] = array(
    'args' => array('user' => 'string'),
    'type' => 'boolean'
);

$_services['show'] = array(
    'link' => '%application%/view.php?memolist=|notepad|&memo=|note|&uid=|uid|',
);

$_services['listNotepads'] = array(
    'args' => array('owneronly' => 'boolean', 'permission' => 'int'),
    'type' => '{urn:horde}stringArray',
);

$_services['list'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray'
);

$_services['listBy'] = array(
    'args' => array('action' => 'string', 'timestamp' => 'int', 'notepad' => 'string'),
    'type' => '{urn:horde}stringArray'
);

$_services['getActionTimestamp'] = array(
    'args' => array('uid' => 'string', 'action' => 'string', 'notepad' => 'string'),
    'type' => 'int',
);

$_services['import'] = array(
    'args' => array('content' => 'string', 'contentType' => 'string'),
    'type' => 'string'
);

$_services['export'] = array(
    'args' => array('uid' => 'string', 'contentType' => 'string'),
    'type' => 'string'
);

$_services['delete'] = array(
    'args' => array('uid' => 'string'),
    'type' => 'boolean'
);

$_services['replace'] = array(
    'args' => array('uid' => 'string', 'content' => 'string', 'contentType' => 'string'),
    'type' => 'boolean'
);

$_services['synchronize'] = array(
    'args' => array(),
    'type' => 'boolean'
);

/**
 * Returns a list of available permissions.
 *
 * @return array  An array describing all available permissions.
 */
function _mnemo_perms()
{
    $perms = array();
    $perms['tree']['mnemo']['max_notes'] = false;
    $perms['title']['mnemo:max_notes'] = _("Maximum Number of Notes");
    $perms['type']['mnemo:max_notes'] = 'int';

    return $perms;
}

/**
 * Removes user data.
 *
 * @param string $user  Name of user to remove data for.
 *
 * @return mixed  true on success | PEAR_Error on failure
 */
function _mnemo_removeUserData($user)
{
    require_once dirname(__FILE__) . '/base.php';

    if (!Auth::isAdmin() && $user != Auth::getAuth()) {
        return PEAR::raiseError(_("You are not allowed to remove user data."));
    }

    /* Error flag */
    $hasError = false;

    /* Get the share object for later deletion */
    $share = $GLOBALS['mnemo_shares']->getShare($user);
    if (is_a($share, 'PEAR_Error')) {
        Horde::logMessage($share->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
        unset($share);
    } else {
        $GLOBALS['display_notepads'] = array($user);
        $memos = Mnemo::listMemos();
        if (is_a($memos, 'PEAR_Error')) {
            $hasError = true;
            Horde::logMessage($mnemos->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            $uids = array();
            foreach ($memos as $memo) {
                $uids[] = $memo['uid'];
            }

            /* ... and delete them. */
            foreach ($uids as $uid) {
                _mnemo_delete($uid);
            }
        }

        /* Now delete history as well. */
        $history = &Horde_History::singleton();
        if (method_exists($history, 'removeByParent')) {
            $histories = $history->removeByParent('mnemo:' . $user);
        } else {
            /* Remove entries 100 at a time. */
            $all = $history->getByTimestamp('>', 0, array(), 'mnemo:' . $user);
            if (is_a($all, 'PEAR_Error')) {
                Horde::logMessage($all, __FILE__, __LINE__, PEAR_LOG_ERR);
            } else {
                $all = array_keys($all);
                while (count($d = array_splice($all, 0, 100)) > 0) {
                    $history->removebyNames($d);
                }
            }
        }

        /* Remove the share itself */
        if (!empty($share)) {
            $result = $GLOBALS['mnemo_shares']->removeShare($share);
            if (is_a($result, 'PEAR_Error')) {
                $hasError = true;
                Horde::logMessage($result->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        /* Get a list of all shares this user has perms to and remove the perms */
        $shares = $GLOBALS['mnemo_shares']->listShares($user);
        if (is_a($shares, 'PEAR_Error')) {
            $hasError = true;
            Horde::logMessage($shares, __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            foreach ($shares as $share) {
                $share->removeUser($user);
            }
        }
    }

    if ($hasError) {
        return PEAR::raiseError(sprintf(_("There was an error removing notes for %s. Details have been logged."), $user));
    } else {
        return true;
    }
}

/**
 * @param boolean $owneronly   Only return notepads that this user owns?
 *                             Defaults to false.
 * @param integer $permission  The permission to filter notepads by.
 *
 * @return array  The notepads.
 */
function _mnemo_listNotepads($owneronly, $permission)
{
    require_once dirname(__FILE__) . '/base.php';

    return Mnemo::listNotepads($owneronly, $permission);
}

/**
 * Returns an array of UIDs for all notes that the current user is authorized
 * to see.
 *
 * @param string $notepad  The notepad to list notes from.
 *
 * @return array  An array of UIDs for all notes the user can access.
 */
function _mnemo_list($notepad = null)
{
    require_once dirname(__FILE__) . '/base.php';
    global $conf;

    if (!isset($conf['storage']['driver'])) {
        return PEAR::raiseError('Not configured');
    }

    /* Make sure we have a valid notepad. */
    if (empty($notepad)) {
        $notepad = Mnemo::getDefaultNotepad();
    }

    if (!array_key_exists($notepad,
                          Mnemo::listNotepads(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    /* Set notepad for listMemos. */
    $GLOBALS['display_notepads'] = array($notepad);

    $memos = Mnemo::listMemos();
    if (is_a($memos, 'PEAR_Error')) {
        return $memos;
    }

    $uids = array();
    foreach ($memos as $memo) {
        $uids[] = $memo['uid'];
    }

    return $uids;
}

/**
 * Returns an array of UIDs for notes that have had $action happen since
 * $timestamp.
 *
 * @param string  $action     The action to check for - add, modify, or delete.
 * @param integer $timestamp  The time to start the search.
 * @param string  $notepad    The notepad to search in.
 *
 * @return array  An array of UIDs matching the action and time criteria.
 */
function _mnemo_listBy($action, $timestamp, $notepad = null)
{
    require_once dirname(__FILE__) . '/base.php';

    /* Make sure we have a valid notepad. */
    if (empty($notepad)) {
        $notepad = Mnemo::getDefaultNotepad();
    }

    if (!array_key_exists($notepad,
                          Mnemo::listNotepads(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $history = &Horde_History::singleton();
    $histories = $history->getByTimestamp('>', $timestamp, array(array('op' => '=', 'field' => 'action', 'value' => $action)), 'mnemo:' . $notepad);
    if (is_a($histories, 'PEAR_Error')) {
        return $histories;
    }

    // Strip leading mnemo:username:.
    return preg_replace('/^([^:]*:){2}/', '', array_keys($histories));
}

/**
 * Returns the timestamp of an operation for a given uid an action.
 *
 * @param string $uid     The uid to look for.
 * @param string $action  The action to check for - add, modify, or delete.
 * @param string $notepad The notepad to search in.
 *
 * @return integer  The timestamp for this action.
 */
function _mnemo_getActionTimestamp($uid, $action, $notepad = null)
{
    require_once dirname(__FILE__) . '/base.php';

    /* Make sure we have a valid notepad. */
    if (empty($notepad)) {
        $notepad = Mnemo::getDefaultNotepad();
    }

    if (!array_key_exists($notepad,
                          Mnemo::listNotepads(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $history = &Horde_History::singleton();
    return $history->getActionTimestamp('mnemo:' . $notepad . ':' . $uid, $action);
}

/**
 * Import a memo represented in the specified contentType.
 *
 * @param string $content      The content of the memo.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             text/plain
 *                             text/x-vnote
 * @param string $notepad      (optional) The notepad to save the memo on.
 *
 * @return string  The new UID, or false on failure.
 */
function _mnemo_import($content, $contentType, $notepad = null)
{
    global $prefs;
    require_once dirname(__FILE__) . '/base.php';

    /* Make sure we have a valid notepad and permissions to edit
     * it. */
    if (empty($notepad)) {
        $notepad = Mnemo::getDefaultNotepad(PERMS_EDIT);
    }

    if (!array_key_exists($notepad, Mnemo::listNotepads(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    /* Create a Mnemo_Driver instance. */
    $storage = &Mnemo_Driver::singleton($notepad);

    switch ($contentType) {
    case 'text/plain':
        $noteId = $storage->add($storage->getMemoDescription($content), $content);
        break;

    case 'text/x-vnote':
        if (!is_a($content, 'Horde_iCalendar_vnote')) {
            require_once 'Horde/iCalendar.php';
            $iCal = &new Horde_iCalendar();
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }

            $components = $iCal->getComponents();
            switch (count($components)) {
            case 0:
                return PEAR::raiseError(_("No iCalendar data was found."));

            case 1:
                $content = $components[0];
                break;

            default:
                $ids = array();
                foreach ($components as $content) {
                    if (is_a($content, 'Horde_iCalendar_vnote')) {
                        $note = $storage->fromiCalendar($content);
                        $noteId = $storage->add($note['desc'],
                                                $note['body'],
                                                !empty($note['category']) ? $note['category'] : '');
                        if (is_a($noteId, 'PEAR_Error')) {
                            return $noteId;
                        }
                        $ids[] = $noteId;
                    }
                }
                return $ids;
            }
        }

        $note = $storage->fromiCalendar($content);
        $noteId = $storage->add($note['desc'],
                                $note['body'], !empty($note['category']) ? $note['category'] : '');
        break;

    default:
        return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"),$contentType));
    }

    if (is_a($noteId, 'PEAR_Error')) {
        return $noteId;
    }

    $note = $storage->get($noteId);
    return $note['uid'];
}

/**
 * Export a memo, identified by UID, in the requested contentType.
 *
 * @param string $uid          Identify the memo to export.
 * @param string $contentType  What format should the data be in?
 *                             A string with one of:
 *                             <pre>
 *                               'text/plain'
 *                               'text/x-vnote'
 *                             </pre>
 *
 * @return string  The requested data or PEAR_Error.
 */
function _mnemo_export($uid, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';

    $storage = &Mnemo_Driver::singleton();
    $memo = $storage->getByUID($uid);
    if (is_a($memo, 'PEAR_Error')) {
        return $memo;
    }

    if (!array_key_exists($memo['memolist_id'], Mnemo::listNotepads(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    if (is_a($memo['body'], 'PEAR_Error')) {
        if ($memo['body']->getCode() == MNEMO_ERR_NO_PASSPHRASE ||
            $memo['body']->getCode() == MNEMO_ERR_DECRYPT) {
            $memo['body'] = _("This note has been encrypted.");
        } else {
            return $memo['body'];
        }
    }

    switch ($contentType) {
    case 'text/plain':
        return $memo['body'];

    case 'text/x-vnote':
        require_once dirname(__FILE__) . '/version.php';
        require_once 'Horde/iCalendar.php';

        // Create the new iCalendar container.
        $iCal = &new Horde_iCalendar('1.1');
        $iCal->setAttribute('VERSION', '1.1');
        $iCal->setAttribute('PRODID', '-//The Horde Project//Mnemo ' . MNEMO_VERSION . '//EN');
        $iCal->setAttribute('METHOD', 'PUBLISH');

        // Create a new vNote.
        $vNote = $storage->toiCalendar($memo, $iCal);
        return $vNote->exportvCalendar();
    }

    return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"),$contentType));
}

/**
 * Delete a memo identified by UID.
 *
 * @param string | array $uid  Identify the note to delete, either a
 *                             single UID or an array.
 *
 * @return boolean  Success or failure.
 */
function _mnemo_delete($uid)
{
    // Handle an arrray of UIDs for convenience of deleting multiple
    // notes at once.
    if (is_array($uid)) {
        foreach ($uid as $u) {
            $result = _mnemo_delete($u);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return true;
    }

    require_once dirname(__FILE__) . '/base.php';

    $storage = &Mnemo_Driver::singleton();
    $memo = $storage->getByUID($uid);
    if (is_a($memo, 'PEAR_Error')) {
        return $memo;
    }

    if (!Auth::isAdmin() &&
        !array_key_exists($memo['memolist_id'],
                          Mnemo::listNotepads(false, PERMS_DELETE))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    return $storage->delete($memo['memo_id']);
}

/**
 * Replace the memo identified by UID with the content represented in
 * the specified contentType.
 *
 * @param string $uid         Idenfity the memo to replace.
 * @param string $content      The content of the memo.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             text/plain
 *                             text/x-vnote
 *
 * @return boolean  Success or failure.
 */
function _mnemo_replace($uid, $content, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';

    $storage = &Mnemo_Driver::singleton();
    $memo = $storage->getByUID($uid);
    if (is_a($memo, 'PEAR_Error')) {
        return $memo;
    }

    if (!array_key_exists($memo['memolist_id'], Mnemo::listNotepads(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    switch ($contentType) {
    case 'text/plain':
        return $storage->modify($memo['memo_id'], $storage->getMemoDescription($content), $content, null);

    case 'text/x-vnote':
        if (!is_a($content, 'Horde_iCalendar_vnote')) {
            require_once 'Horde/iCalendar.php';
            $iCal = new Horde_iCalendar();
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }

            $components = $iCal->getComponents();
            switch (count($components)) {
            case 0:
                return PEAR::raiseError(_("No iCalendar data was found."));

            case 1:
                $content = $components[0];
                break;

            default:
                return PEAR::raiseError(_("Multiple iCalendar components found; only one vNote is supported."));
            }
        }
        $note = $storage->fromiCalendar($content);

        return $storage->modify($memo['memo_id'], $note['desc'],
                                $note['body'],!empty($note['category']) ? $note['category'] : '');

    default:
        return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"),$contentType));
    }
}

/**
 * Synchronizes mnemo with the IMAP backend
 *
 * @return boolean  False if something went wrong
 */
function _mnemo_synchronize()
{
    require_once dirname(__FILE__) . '/base.php';

    /* Make sure we have a valid notepad. */
    if (empty($notepad)) {
        $notepad = Mnemo::getDefaultNotepad();
    }

    if (!array_key_exists($notepad,
                          Mnemo::listNotepads(false, PERMS_READ))) {
        return False;
    }

    $storage = &Mnemo_Driver::singleton($notepad);
    if (get_class ($storage) == 'Mnemo_Driver_kolab' &&
        get_class ($storage->_wrapper) == 'Mnemo_Driver_kolab_wrapper_new') {

        $storage->_wrapper->connect ();
        if (get_class ($storage->_wrapper->_store) == 'Kolab_IMAP') {
            $storage->_wrapper->_store->_synchronize ();
        }
    }

    return True;
}
