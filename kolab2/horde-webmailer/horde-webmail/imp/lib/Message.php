<?php

/* Constants used in copy(). */
define('IMP_MESSAGE_MOVE', 1);
define('IMP_MESSAGE_COPY', 2);

/**
 * The IMP_Message:: class contains all functions related to handling messages
 * within IMP. Actions such as moving, copying, and deleting messages are
 * handled in here so that code need not be repeated between mailbox, message,
 * and other pages.
 *
 * Indices format:
 * ===============
 * For any function below that requires an $indices parameter, see
 * IMP::parseIndicesList() for the list of allowable inputs.
 *
 * $Horde: imp/lib/Message.php,v 1.164.8.63 2009-01-06 15:24:04 jan Exp $
 *
 * Copyright 2000-2001 Chris Hyde <chris@jeks.net>
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chris Hyde <chris@jeks.net>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_Message {

    /**
     * Using POP to access mailboxes?
     *
     * @var boolean
     */
    var $_usepop = false;

    /**
     * The active IMP_Mailbox object to update on certain actions
     *
     * @var IMP_Mailbox
     */
    var $_mboxOb;

    /**
     * Recursion count used to determine when $_mboxOb should be unset.
     *
     * @var integer
     */
    var $_mboxObCount = 0;

    /**
     * Returns a reference to the global IMP_Message object, only creating it
     * if it doesn't already exist. This ensures that only one IMP_Message
     * instance is instantiated for any given session.
     *
     * This method must be invoked as:<code>
     *   $imp_message = &IMP_Message::singleton();
     * </code>
     *
     * @return IMP_Message  The IMP_Message instance.
     */
    function &singleton()
    {
        static $message;

        if (!isset($message)) {
            $message = new IMP_Message();
        }

        return $message;
    }

    /**
     * Constructor.
     */
    function IMP_Message()
    {
        if ($_SESSION['imp']['base_protocol'] == 'pop3') {
            $this->_usepop = true;
        }
    }

    /**
     * Copies or moves a list of messages to a new folder.
     * Handles use of the IMP_SEARCH_MBOX mailbox and the Trash folder.
     *
     * @param string $targetMbox  The mailbox to move/copy messages to.
     * @param integer $action     Either IMP_MESSAGE_MOVE or IMP_MESSAGE_COPY.
     * @param mixed &$indices     See above.
     * @param boolean $new        Whether the target mailbox has to be created.
     *
     * @return boolean  True if successful, false if not.
     */
    function copy($targetMbox, $action, &$indices, $new = false)
    {
        global $conf, $notification, $prefs;

        if ($conf['tasklist']['use_tasklist'] &&
            (strpos($targetMbox, '_tasklist_') === 0)) {
            /* If the target is a tasklist, handle the move/copy specially. */
            $tasklist = str_replace('_tasklist_', '', $targetMbox);
            return $this->createTasksOrNotes($tasklist, $action, $indices, 'task');
        }
        if ($conf['notepad']['use_notepad'] &&
            (strpos($targetMbox, '_notepad_') === 0)) {
            /* If the target is a notepad, handle the move/copy specially. */
            $notepad = str_replace('_notepad_', '', $targetMbox);
            return $this->createTasksOrNotes($notepad, $action, $indices, 'note');
        }

        if (!($msgList = IMP::parseIndicesList($indices))) {
            return false;
        }
        $this->_mboxOb = &$indices;
        ++$this->_mboxObCount;

        if ($new) {
            require_once IMP_BASE . '/lib/Folder.php';
            $imp_folder = &IMP_Folder::singleton();
            if (!$imp_folder->exists($targetMbox) &&
                !$imp_folder->create($targetMbox, $prefs->getValue('subscribe'))) {
                return false;
            }
        }

        $expunge_list = array();
        $imap_flags = CP_UID;
        $return_value = true;

        switch ($action) {
        case IMP_MESSAGE_MOVE:
            $imap_flags |= CP_MOVE;
            $message = _("There was an error moving messages from \"%s\" to \"%s\". This is what the server said");
            break;

        case IMP_MESSAGE_COPY:
            $message = _("There was an error copying messages from \"%s\" to \"%s\". This is what the server said");
            break;
        }

        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();
        $imp_imap = &IMP_IMAP::singleton();

        foreach ($msgList as $folder => $msgIndices) {
            $msgIdxString = implode(',', $msgIndices);

            /* Switch folders. */
            $imp_imap->changeMbox($folder, ($action == IMP_MESSAGE_MOVE) ? IMP_IMAP_READWRITE : IMP_IMAP_AUTO);

            /* Attempt to copy/move messages to new mailbox. */
            if (!@imap_mail_copy($imp_imap->stream(), $msgIdxString, $targetMbox, $imap_flags)) {
                $notification->push(sprintf($message, IMP::displayFolder($folder), IMP::displayFolder($targetMbox)) . ': ' . imap_last_error(), 'horde.error');
                $return_value = false;
            } elseif ($action == IMP_MESSAGE_MOVE) {
                $imap_cache->expireCache($folder, 2 | 4);
                $expunge_list[$folder] = $msgIndices;
            }
        }

        $imap_cache->expireCache($targetMbox, 2 | 4);
        $this->expungeMailbox($expunge_list);
        if (!(--$this->_mboxObCount)) {
            unset($this->_mboxOb);
        }

        return $return_value;
    }

    /**
     * Deletes a list of messages taking into account whether or not a
     * Trash folder is being used.
     * Handles use of the IMP_SEARCH_MBOX mailbox and the Trash folder.
     *
     * @param mixed &$indices   See above.
     * @param boolean $nuke     Override user preferences and nuke (i.e.
     *                          permanently delete) the messages instead?
     * @param boolean $keeplog  Should any history information of the
     *                          message be kept?
     *
     * @return integer|boolean  The number of messages deleted if successful,
     *                          false if not.
     */
    function delete(&$indices, $nuke = false, $keeplog = false)
    {
        global $conf, $notification, $prefs;

        if (!($msgList = IMP::parseIndicesList($indices))) {
            return false;
        }

        $trash = IMP::folderPref($prefs->getValue('trash_folder'), true);
        $use_trash = $prefs->getValue('use_trash');
        $use_vtrash = $prefs->getValue('use_vtrash');
        if ($use_trash && !$use_vtrash && empty($trash)) {
            $notification->push(_("Cannot move messages to Trash - no Trash mailbox set in preferences."), 'horde.error');
            return false;
        }

        $return_value = 0;
        $maillog_update = (!$keeplog && !empty($conf['maillog']['use_maillog']));

        $imp_imap = &IMP_IMAP::singleton();
        $stream = $imp_imap->stream();

        $this->_mboxOb = &$indices;
        ++$this->_mboxObCount;

        foreach ($msgList as $folder => $msgIndices) {
            $indices_array = array($folder => $msgIndices);
            $sequence = implode(',', $msgIndices);
            $return_value += count($msgIndices);

            /* Switch folders, if necessary. */
            $imp_imap->changeMbox($folder);

            /* Trash is only valid for IMAP mailboxes. */
            if (!$this->_usepop &&
                !$nuke &&
                !$use_vtrash &&
                $use_trash &&
                ($folder != $trash)) {
                if (!isset($imp_folder)) {
                    include_once IMP_BASE . '/lib/Folder.php';
                    $imp_folder = &IMP_Folder::singleton();
                }

                if (!$imp_folder->exists($trash)) {
                    if (!$imp_folder->create($trash, $prefs->getValue('subscribe'))) {
                        if (!(--$this->_mboxObCount)) {
                            unset($this->_mboxOb);
                        }
                        return false;
                    }
                }

                if (!@imap_mail_move($stream, $sequence, $trash, CP_UID)) {
                    $error_msg = imap_last_error();
                    $error = true;

                    /* Handle the case when the mailbox is overquota (moving
                     * message to trash would fail) by first deleting then
                     * copying message to Trash. */
                    if ((stristr($error_msg, 'over quota') !== false) ||
                        (stristr($error_msg, 'quota exceeded') !== false) ||
                        (stristr($error_msg, 'exceeded your mail quota') !== false)) {
                        $error = false;
                        $msg_text = array();

                        /* Get text of deleted messages. */
                        foreach ($msgIndices as $val) {
                            $msg_text[] = imap_fetchheader($stream, $val, FT_UID | FT_PREFETCHTEXT) . imap_body($stream, $val, FT_UID);
                        }
                        @imap_delete($stream, $sequence, FT_UID);
                        $this->expungeMailbox($indices_array);

                        /* Save messages in Trash folder. */
                        foreach ($msg_text as $val) {
                            if (!@imap_append($stream, IMP::serverString($trash), $val)) {
                                $error = true;
                                break;
                            }
                        }
                    }

                    if ($error) {
                        $notification->push(sprintf(_("There was an error deleting messages from the folder \"%s\". This is what the server said"), IMP::displayFolder($folder)) . ': ' . $error_msg, 'horde.error');
                        $return_value = false;
                    }
                } else {
                    $this->expungeMailbox($indices_array);
                }
            } else {
                /* Get the list of Message-IDs for the deleted messages if
                 * using maillogging. */
                if ($maillog_update) {
                    if (!isset($msg_cache)) {
                        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
                        $msg_cache = &IMP_MessageCache::singleton();
                    }
                    $overview = $msg_cache->retrieve($folder, $msgIndices, 1);
                }

                /* Delete the messages. */
                if ($this->_usepop ||
                    $nuke ||
                    ($use_trash && ($folder == $trash)) ||
                    ($use_vtrash && ($GLOBALS['imp_search']->isVTrashFolder()))) {
                    /* Purge messages immediately. */
                    @imap_delete($stream, $sequence, FT_UID);
                    $this->expungeMailbox($indices_array);
                } else {
                    /* If we are using virtual trash, we must mark the message
                     * as seen or else it will appear as an 'unseen' message
                     * for purposes of new message counts. */
                    $del_flags = array('deleted');
                    if ($use_vtrash) {
                        $del_flags[] = 'seen';
                    }
                    $this->flag($del_flags, $indices_array);
                }

                /* Get the list of Message-IDs deleted, and remove
                 * the information from the mail log. */
                if ($maillog_update) {
                    $msg_ids = array();
                    foreach ($overview as $val) {
                        if (!empty($val->message_id)) {
                            $msg_ids[] = $val->message_id;
                        }
                    }
                    require_once IMP_BASE . '/lib/Maillog.php';
                    IMP_Maillog::deleteLog($msg_ids);
                }
            }
        }

        if (!(--$this->_mboxObCount)) {
            unset($this->_mboxOb);
        }

        return $return_value;
    }

    /**
     * Undeletes a list of messages.
     * Handles the IMP_SEARCH_MBOX mailbox.
     * This function works with IMAP only, not POP3.
     *
     * @param mixed &$indices  See above.
     *
     * @return boolean  True if successful, false if not.
     */
    function undelete(&$indices)
    {
        return $this->flag(array('deleted'), $indices, false);
    }

    /**
     * Copies or moves a list of messages to a tasklist or notepad.
     * Handles use of the IMP_SEARCH_MBOX mailbox and the Trash folder.
     *
     * @param string $list      The list in which the task or note will be
     *                          created.
     * @param integer $action   Either IMP_MESSAGE_MOVE or IMP_MESSAGE_COPY.
     * @param mixed $indices    See above.
     * @param string $type      The object type to create, defaults to task.
     *
     * @return boolean  True if successful, false if not.
     */
    function createTasksOrNotes($list, $action, &$indices, $type = 'task')
    {
        global $registry, $notification, $prefs;

        if (!($msgList = IMP::parseIndicesList($indices))) {
            return false;
        }

        require_once IMP_BASE . '/lib/Compose.php';
        require_once IMP_BASE . '/lib/MIME/Contents.php';
        require_once 'Text/Flowed.php';
        require_once 'Horde/iCalendar.php';

        foreach ($msgList as $folder => $msgIndices) {
            foreach ($msgIndices as $index) {
                /* Fetch the message contents. */
                $imp_contents = &IMP_Contents::singleton($index . IMP_IDX_SEP . $folder);
                $imp_contents->buildMessage();

                /* Fetch the message headers. */
                $imp_headers = &$imp_contents->getHeaderOb();
                $subject = $imp_headers->getValue('subject');

                /* Extract the message body. */
                $imp_compose = &IMP_Compose::singleton();
                $mime_message = $imp_contents->getMIMEMessage();
                $body_id = $imp_compose->getBodyId($imp_contents);
                $body = $imp_compose->findBody($imp_contents);

                /* Re-flow the message for prettier formatting. */
                $flowed = new Text_Flowed($mime_message->replaceEOL($body, "\n"));
                if (($mime_message->getContentTypeParameter('delsp') == 'yes') &&
                    method_exists($flowed, 'setDelSp')) {
                    $flowed->setDelSp(true);
                }
                $body = $flowed->toFlowed(false);

                /* Convert to current charset */
                /* TODO: When Horde_iCalendar supports setting of charsets
                 * we need to set it there instead of relying on the fact
                 * that both Nag and IMP use the same charset. */
                $body_part = $mime_message->getPart($body_id);
                $body = String::convertCharset($body, $body_part->getCharset(), NLS::getCharset());

                /* Create a new iCalendar. */
                $vCal = new Horde_iCalendar();
                $vCal->setAttribute('PRODID', '-//The Horde Project//IMP ' . IMP_VERSION . '//EN');
                $vCal->setAttribute('METHOD', 'PUBLISH');

                switch ($type) {
                case 'task':
                    /* Create a new vTodo object using this message's
                     * contents. */
                    $vTodo = &Horde_iCalendar::newComponent('vtodo', $vCal);
                    $vTodo->setAttribute('SUMMARY', $subject);
                    $vTodo->setAttribute('DESCRIPTION', $body);
                    $vTodo->setAttribute('PRIORITY', '3');

                    /* Get the list of editable tasklists. */
                    $lists = $registry->call('tasks/listTasklists',
                                             array(false, PERMS_EDIT));

                    /* Attempt to add the new vTodo item to the requested
                     * tasklist. */
                    $res = $registry->call('tasks/import',
                                           array($vTodo, 'text/calendar', $list));
                    break;

                case 'note':
                    /* Create a new vNote object using this message's
                     * contents. */
                    $vNote = &Horde_iCalendar::newComponent('vnote', $vCal);
                    $vNote->setAttribute('BODY', $subject . "\n". $body);

                    /* Get the list of editable notepads. */
                    $lists = $registry->call('notes/listNotepads',
                                             array(false, PERMS_EDIT));

                    /* Attempt to add the new vNote item to the requested
                     * notepad. */
                    $res = $registry->call('notes/import',
                                           array($vNote, 'text/x-vnote', $list));
                    break;
                }

                if (is_a($res, 'PEAR_Error')) {
                    $notification->push($res, $res->getCode());
                } elseif (!$res) {
                    switch ($type) {
                    case 'task': $notification->push(_("An unknown error occured while creating the new task."), 'horde.error'); break;
                    case 'note': $notification->push(_("An unknown error occured while creating the new note."), 'horde.error'); break;
                    }
                } else {
                    $name = '"' . htmlspecialchars($subject) . '"';

                    /* Attempt to convert the object name into a hyperlink. */
                    switch ($type) {
                    case 'task':
                        $link = $registry->link('tasks/show',
                                                array('uid' => $res));
                        break;
                    case 'note':
                        if ($registry->hasMethod('notes/show')) {
                            $link = $registry->link('notes/show',
                                                    array('uid' => $res));
                        } else {
                            $link = false;
                        }
                        break;
                    }
                    if ($link && !is_a($link, 'PEAR_Error')) {
                        $name = sprintf('<a href="%s">%s</a>',
                                        Horde::url($link),
                                        $name);
                    }

                    $notification->push(sprintf(_("%s was successfully added to \"%s\"."), $name, htmlspecialchars($lists[$list]->get('name'))), 'horde.success', array('content.raw'));
                }
            }
        }

        /* Delete the original messages if this is a "move" operation. */
        if ($action == IMP_MESSAGE_MOVE) {
            $this->delete($indices);
        }

        return true;
    }

    /**
     * Strips one or all MIME parts out of a message.
     *
     * Handles the IMP_SEARCH_MBOX mailbox.
     *
     * @param IMP_Mailbox $imp_mailbox  The IMP_Mailbox object with the
     *                                  current index set to the message to be
     *                                  processed.
     * @param string $partid            The MIME ID of the part to strip. All
     *                                  parts are stripped if null.
     *
     * @return boolean  Returns true on success, or PEAR_Error on error.
     */
    function stripPart(&$imp_mailbox, $partid = null)
    {
        /* Return error if no index was provided. */
        if (!($msgList = IMP::parseIndicesList($imp_mailbox))) {
            return PEAR::raiseError('No index provided to IMP_Message::stripPart().');
        }

        /* If more than one index provided, return error. */
        reset($msgList);
        list($folder, $index) = each($msgList);
        if (each($msgList) || (count($index) > 1)) {
            return PEAR::raiseError('More than 1 index provided to IMP_Message::stripPart().');
        }
        $index = implode('', $index);

        require_once 'Horde/MIME/Part.php';
        require_once IMP_BASE . '/lib/MIME/Contents.php';
        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';

        /* Get a local copy of the message. */
        $contents = &IMP_Contents::singleton($index . IMP_IDX_SEP . $folder);
        $contents->rebuildMessage();
        $message = $contents->getMIMEMessage();

        /* Loop through all to-be-stripped mime parts. */
        if (is_null($partid)) {
            $partids = $contents->getDownloadAllList();
        } else {
            $partids = array($partid);
        }
        foreach ($partids as $partid) {
            $oldPart = $message->getPart($partid);
            if (!is_a($oldPart, 'MIME_Part')) {
                continue;
            }
            $newPart = new MIME_Part('text/plain');

            /* We need to make sure all text is in the correct charset. */
            $newPart->setCharset(NLS::getCharset());
            $newPart->setContents(sprintf(_("[Attachment stripped: Original attachment type: %s, name: %s]"), $oldPart->getType(), $oldPart->getName(true, true)), '8bit');
            $newPart->setDisposition('attachment');
            $message->alterPart($partid, $newPart);
        }

        /* We need to make sure we add "\r\n" after every line for
         * imap_append() - some servers require it (e.g. Cyrus). */
        $message->setEOL(MIME_PART_RFC_EOL);

        /* Get the headers for the message. */
        $msg_cache = &IMP_MessageCache::singleton();
        $cache_ob = $msg_cache->retrieve($folder, array($index), 1 | 32);
        $ob = reset($cache_ob);
        $flags = array();
        /* If in Virtual Inbox, we need to reset flag to unseen so that it
         * appears again in the mailbox list. */
        $vinbox = $GLOBALS['imp_search']->isVINBOXFolder($imp_mailbox->getMailboxName());
        foreach (array('answered', 'deleted', 'draft', 'flagged', 'seen') as $flag) {
            if ($ob->$flag && (!$vinbox || ($flag != 'seen'))) {
                $flags[] = '\\' . $flag;
            }
        }
        $flags = implode(' ', $flags);

        $imp_imap = &IMP_IMAP::singleton();
        $imp_imap->changeMbox($folder);
        $folder = IMP::serverString($folder);
        if (@imap_append($imp_imap->stream(), $folder, $ob->header->getHeaderText() . $contents->toString($message, true), $flags)) {
            $this->delete($imp_mailbox, true, true);
            $imp_mailbox->updateMailbox(IMP_MAILBOX_UPDATE);

            /* Search for the most recent message in the current mailbox with
             * the old Message-ID - this is the IMAP UID of the saved
             * message. */
            require_once IMP_BASE . '/lib/IMAP/Search.php';
            $query = new IMP_IMAP_Search_Query();
            $query->header('Message-ID', $ob->header->getValue('message-id'));
            $ids = $GLOBALS['imp_search']->runSearchQuery($query, $folder, SORTARRIVAL, 1);
            $imp_mailbox->setIndex($ids[0]);

            /* We need to replace the old index in the query string with the
               new index. */
            $_SERVER['QUERY_STRING'] = preg_replace('/' . $index . '/', $ids[0], $_SERVER['QUERY_STRING']);

            return true;
        } else {
            return PEAR::raiseError(_("An error occured while attempting to strip the attachment. The IMAP server said: ") . imap_last_error());
        }
    }

    /**
     * Sets or clears a given flag for a list of messages.
     * Handles use of the IMP_SEARCH_MBOX mailbox.
     * This function works with IMAP only, not POP3.
     *
     * Valid flags are:
     *   'seen', 'flagged', 'answered', 'deleted', 'draft'
     *
     * @param array $flag      The IMAP flag(s) to set or clear.
     * @param mixed &$indices  See above.
     * @param boolean $action  If true, set the flag(s), otherwise clear the
     *                         flag(s).
     *
     * @return boolean  True if successful, false if not.
     */
    function flag($flag, &$indices, $action = true)
    {
        if (!($msgList = IMP::parseIndicesList($indices))) {
            return false;
        }
        $this->_mboxOb = &$indices;
        ++$this->_mboxObCount;

        $function = ($action) ? 'imap_setflag_full' : 'imap_clearflag_full';
        $update_list = array();

        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
        $msg_cache = &IMP_MessageCache::singleton();

        $imp_imap = &IMP_IMAP::singleton();

        foreach ($msgList as $folder => $msgIndices) {
            $msgIdxString = implode(',', $msgIndices);

            /* Switch folders, if necessary. */
            $imp_imap->changeMbox($folder);

            $del_flag = false;
            $flag_str = '';
            foreach ($flag as $val) {
                $flag_val = String::upper($val);
                $flag_str .= " \\" . $flag_val;
                if ($flag_val == 'DELETED') {
                    $del_flag = true;
                }
            }

            /* Flag/unflag the messages now. */
            if (!call_user_func($function, $imp_imap->stream(), $msgIdxString, ltrim($flag_str), ST_UID)) {
                $GLOBALS['notification']->push(sprintf(_("There was an error flagging messages in the folder \"%s\". This is what the server said"), IMP::displayFolder($folder)) . ': ' . imap_last_error(), 'horde.error');
            } else {
                if ($action && $del_flag) {
                    $this->_updateMailbox(array($folder => $msgIndices), 'delete');
                }
                $msg_cache->updateFlags($folder, $msgIndices, $flag, $action);
                $update_list[$folder] = $msgIndices;
            }
        }

        /* Update the mailbox. */
        $this->_updateMailbox($update_list, 'flag');
        if (!(--$this->_mboxObCount)) {
            unset($this->_mboxOb);
        }

        return (!empty($update_list));
    }

    /**
     * Sets or clears a given flag(s) for all messages in a list of mailboxes.
     * This function works with IMAP only, not POP3.
     *
     * See flag() for the list of valid flags.
     *
     * @param array $flag      The IMAP flag(s) to set or clear.
     * @param array $mboxes    The list of mailboxes to flag.
     * @param boolean $action  If true, set the flag(s), otherwise, clear the
     *                         flag(s).
     *
     * @return boolean  True if successful, false if not.
     */
    function flagAllInMailbox($flag, $mboxes, $action = true)
    {
        if (empty($mboxes) || !is_array($mboxes)) {
            return false;
        }

        $return_value = true;

        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();

        foreach ($mboxes as $val) {
            if ($uids = $imap_cache->getMailboxArrival($val)) {
                $indices = array($val => $uids);
                if (!$this->flag($flag, $indices, $action)) {
                    $return_value = false;
                }
            } else {
                $return_value = false;
            }
        }

        return $return_value;
    }

    /**
     * Expunges all deleted messages from the list of mailboxes.
     *
     * @param array $mbox_list  The list of mailboxes to empty as keys; an
     *                          optional array of indices to delete as values.
     *                          If the value is not an array, all messages
     *                          flagged as deleted in the mailbox will be
     *                          deleted.
     *
     * @return array  An array of mailbox names as keys and UIDS as values
     *                that were expunged.
     */
    function expungeMailbox($mbox_list)
    {
        if (empty($mbox_list)) {
            return array();
        }

        $process_list = $update_list = array();

        if (!$this->_usepop) {
            require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
            $msg_cache = &IMP_MessageCache::singleton();
        }

        $imp_imap = &IMP_IMAP::singleton();
        $stream = $imp_imap->stream();

        foreach (array_keys($mbox_list) as $key) {
            if ($GLOBALS['imp_search']->isSearchMbox($key)) {
                foreach ($GLOBALS['imp_search']->getSearchFolders($key) as $skey) {
                    $process_list[$skey] = $mbox_list[$key];
                }
            } else {
                $process_list[$key] = $mbox_list[$key];
            }
        }

        foreach ($process_list as $key => $val) {
            $unflag = false;
            $imp_imap->changeMbox($key);
            if ($this->_usepop) {
                $update_list[$key] = $val;
            } else {
                $ids = @imap_search($stream, 'DELETED', SE_UID);
                if (!empty($ids)) {
                    if (is_array($val) && !empty($val)) {
                        $unflag = array_diff($ids, $val);
                        if (!empty($unflag)) {
                            $unflag = implode(',', $unflag);
                            @imap_clearflag_full($stream, $unflag, '\\DELETED', ST_UID);
                        }
                        $ids = $val;
                    }
                    $msg_cache->deleteMsgs($key, $ids);
                    $update_list[$key] = $ids;
                }
            }
            // Need to make sure we have a read-write mailbox since
            // deleteMsgs() may switch to read-only access.
            $imp_imap->changeMbox($key);
            @imap_expunge($stream);
            if ($unflag) {
                @imap_setflag_full($stream, $unflag, '\\DELETED', ST_UID);
            }
        }

        $this->_updateMailbox($update_list, 'expunge');

        return $update_list;
    }

    /**
     * Empties an entire mailbox.
     *
     * @param array $mbox_list  The list of mailboxes to empty.
     */
    function emptyMailbox($mbox_list)
    {
        global $notification;

        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();
        $msg_cache = &IMP_MessageCache::singleton();

        $imp_imap = &IMP_IMAP::singleton();
        $stream = $imp_imap->stream();

        foreach ($mbox_list as $mbox) {
            if ($GLOBALS['imp_search']->isVTrashFolder($mbox)) {
                $this->expungeMailbox(array_flip($GLOBALS['imp_search']->getSearchFolders($mbox)));
                $notification->push(_("Emptied all messages from Virtual Trash Folder."), 'horde.success');
                continue;
            }

            $display_mbox = IMP::displayFolder($mbox);

            if (!$imp_imap->changeMbox($mbox)) {
                $notification->push(sprintf(_("Could not delete messages from %s. The server said: %s"), $display_mbox, imap_last_error()), 'horde.error');
                continue;
            }

            /* Make sure there is at least 1 message before attempting to
               delete. */
            if (!@imap_num_msg($stream)) {
                $notification->push(sprintf(_("The mailbox %s is already empty."), $display_mbox), 'horde.message');
            } else {
                $trash_folder = ($GLOBALS['prefs']->getValue('use_trash')) ? IMP::folderPref($GLOBALS['prefs']->getValue('trash_folder'), true) : null;
                if (empty($trash_folder) || ($trash_folder == $mbox)) {
                    @imap_setflag_full($stream, '1:*', '\\DELETED');
                    $this->expungeMailbox(array($mbox => 1));
                } else {
                    $indices = array($mbox => $imap_cache->getMailboxArrival($mbox, false));
                    $this->delete($indices);
                }
                $notification->push(sprintf(_("Emptied all messages from %s."), $display_mbox), 'horde.success');
            }
        }
    }

    /**
     * Update the IMP_Mailbox object with mailbox changes.
     *
     * @access private
     *
     * @param array $msgList  The list of mailboxes/indices to update.
     * @param string $action  The update action.
     */
    function _updateMailbox($msgList, $action)
    {
        require_once IMP_BASE . '/lib/Mailbox.php';

        $mbox = false;
        $mbox_actions = array(
            'delete' => IMP_MAILBOX_DELETE,
            'expunge' => IMP_MAILBOX_EXPUNGE,
            'flag' => IMP_MAILBOX_FLAG
        );

        /* The IMP_Mailbox object, if it exists, can be either a regular or
         * search mailbox. */
        if (is_a($this->_mboxOb, 'IMP_Mailbox')) {
            $this->_mboxOb->updateMailbox($mbox_actions[$action], $msgList);
            $mbox = $this->_mboxOb->getMailboxName();
        }

        /* We already know that there are no search mailboxes in $msgList,
         * only regular mailboxes. */
        foreach ($msgList as $key => $val) {
            if (!$mbox || ($mbox != $key)) {
                $mbox_ob = &IMP_Mailbox::singleton($key);
                $mbox_ob->updateMailbox($mbox_actions[$action], array($key => $val));
            }
        }
    }

    /**
     * Obtains the size of a mailbox.
     *
     * @since IMP 4.2
     *
     * @param string $mbox_list   The mailbox to obtain the size of.
     * @param boolean $formatted  Whether to return a human readable value.
     */
    function sizeMailbox($mbox, $formatted = true)
    {
        $imp_imap = &IMP_IMAP::singleton();
        $imp_imap->changeMbox($mbox);
        $info = @imap_mailboxmsginfo($imp_imap->stream());
        if ($info) {
            return ($formatted)
                ? sprintf(_("%.2fMB"), $info->Size / (1024 * 1024))
                : $info->Size;
        } else {
            return 0;
        }
    }

}
