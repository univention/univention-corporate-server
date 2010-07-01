<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP/test.php,v 1.1.2.4 2009-03-08 05:30:12 wrobel Exp $
 */

/**
 * Indicate that a mail has been marked as deleted
 */
define('KOLAB_IMAP_FLAG_DELETED', 1);

/**
 * The Horde_Kolab_IMAP_Connection_test class simulates an IMAP server for
 * testing purposes.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP/test.php,v 1.1.2.4 2009-03-08 05:30:12 wrobel Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Storage
 */
class Horde_Kolab_IMAP_test extends Horde_Kolab_IMAP {

    /**
     * If we are supposed to be connected this holds the user
     * credentials and some connection details.
     *
     * @var string
     */
    var $_connected;

    /**
     * Login of the current user
     *
     * @var string
     */
    var $_user;

    /**
     * The data of the mailbox currently opened
     *
     * @var array
     */
    var $_mbox = null;

    /**
     * The name of the mailbox currently opened
     *
     * @var array
     */
    var $_mboxname = null;

    /**
     * Prepare the dummy server.
     *
     * @param string  $login     The user account name.
     * @param string  $password  The user password.
     * @param boolean $tls       Should TLS be used for the connection?
     *
     * @return mixed  True in case the connection was opened successfully, a
     *                PEAR error otherwise.
     */
    function connect($login, $password, $tls = false)
    {
        if (!is_array($GLOBALS['KOLAB_TESTING'])) {
            /* Simulate an empty IMAP server */
            $GLOBALS['KOLAB_TESTING'] = array();
        }

        $tls = ($tls) ? 'tls' : 'notls';
        $this->_connected = $login . ':' . $password . ':' . $tls;
        $this->_user = $login;
        unset($this->_mbox);
        $this->_mboxname = null;
    }

    /**
     * Disconnects from the IMAP server.
     *
     * @return mixed  True in case the connection was closed successfully, a
     *                PEAR error otherwise.
     */
    function disconnect()
    {
        $this->_connected = null;
    }

    function _parseFolder($folder)
    {
        if (substr($folder, 0, 5) == 'INBOX') {
            $user = split('@', $this->_user);
            return 'user/' . $user[0] . substr($folder, 5);
        }
        return $folder;
    }

    /**
     * Opens the given folder.
     *
     * @param string $folder  The folder to open
     *
     * @return mixed  True in case the folder was opened successfully, a PEAR
     *                error otherwise.
     */
    function select($folder)
    {
        $folder = $this->_parseFolder($folder);
        if (!isset($GLOBALS['KOLAB_TESTING'][$folder])) {
            return PEAR::raiseError(sprintf("IMAP folder %s does not exist!", $folder));
        }
        $this->_mbox = &$GLOBALS['KOLAB_TESTING'][$folder];
        $this->_mboxname = $folder;
        return true;
    }

    /**
     * Does the given folder exist?
     *
     * @param string $folder  The folder to check.
     *
     * @return mixed True in case the folder exists, false otherwise
     */
    function exists($folder)
    {
        $folder = $this->_parseFolder($folder);
        if (!isset($GLOBALS['KOLAB_TESTING'][$folder])) {
            return false;
        }
        return true;
    }

    /**
     * Create the specified folder.
     *
     * @param string $folder  The folder to create.
     *
     * @return mixed True in case the operation was successfull, a
     *               PEAR error otherwise.
     */
    function create($folder)
    {
        $folder = $this->_parseFolder($folder);
        if (isset($GLOBALS['KOLAB_TESTING'][$folder])) {
            return PEAR::raiseError(sprintf("IMAP folder %s does already exist!", $folder));
        }
        $GLOBALS['KOLAB_TESTING'][$folder] = array(
            'status' => array(
                'uidvalidity' => time(),
                'uidnext' => 1),
            'mails' => array(),
            'permissions' => array(),
            'annotations' => array(),
        );
        return true;
    }

    /**
     * Delete the specified folder.
     *
     * @param string $folder  The folder to delete.
     *
     * @return mixed True in case the operation was successfull, a
     *               PEAR error otherwise.
     */
    function delete($folder)
    {
        $folder = $this->_parseFolder($folder);
        if (!isset($GLOBALS['KOLAB_TESTING'][$folder])) {
            return PEAR::raiseError(sprintf("IMAP folder %s does not exist!", $folder));
        }
        unset($GLOBALS['KOLAB_TESTING'][$folder]);
        return true;
    }

    /**
     * Rename the specified folder.
     *
     * @param string $old  The folder to rename.
     * @param string $new  The new name of the folder.
     *
     * @return mixed True in case the operation was successfull, a
     *               PEAR error otherwise.
     */
    function rename($old, $new)
    {
        $old = $this->_parseFolder($old);
        $new = $this->_parseFolder($new);

        if (!isset($GLOBALS['KOLAB_TESTING'][$old])) {
            return PEAR::raiseError(sprintf("IMAP folder %s does not exist!", $old));
        }
        if (isset($GLOBALS['KOLAB_TESTING'][$new])) {
            return PEAR::raiseError(sprintf("IMAP folder %s does already exist!", $new));
        }
        $GLOBALS['KOLAB_TESTING'][$new] = $GLOBALS['KOLAB_TESTING'][$old];
        unset($GLOBALS['KOLAB_TESTING'][$old]);
        return true;
    }

    /**
     * Returns the status of the current folder.
     *
     * @return array  An array that contains 'uidvalidity' and 'uidnext'.
     */
    function status()
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        return $this->_mbox['status'];
    }

    /**
     * Returns the message ids of the messages in this folder.
     *
     * @return array  The message ids.
     */
    function getUids()
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        $uids = array();
        foreach ($this->_mbox['mails'] as $uid => $mail) {
            if (!($mail['flags'] & KOLAB_IMAP_FLAG_DELETED)) {
                $uids[] = $uid;
            }
        }
        return $uids;
    }

    /**
     * Searches the current folder using the given list of search criteria.
     *
     * @param string $search_list  A list of search criteria.
     *
     * @return mixed  The list of matching message ids or a PEAR error in case
     *                of an error.
     */
    function search($search_list, $uidSearch = true)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        $uids = array();
        if (substr($search_list, 0, 7) == 'SUBJECT') {
            $needle = '^Subject: ' . substr($search_list, 8);
            foreach ($this->_mbox['mails'] as $uid => $mail) {
                if (preg_match($needle, $mail['header'])) {
                    $uids[] = $uid;
                }
            }
        } else if (substr($search_list, 0, 6) == 'HEADER') {
            preg_match('([^ ]*) ([^ ]*)', substr($search_list, 7), $matches);
            $needle = '^' . $matches[0] . ': ' . $matches[1];
            foreach ($this->_mbox['mails'] as $uid => $mail) {
                if (preg_match($needle, $mail['header'])) {
                    $uids[] = $uid;
                }
            }

        }
        return $uids;
    }

    /**
     * Searches the headers of the messages.
     *
     * @param string $field  The name of the header field.
     * @param string $value  The value that field should match.
     *
     * @return mixed  The list of matching message ids or a PEAR error in case
     *                of an error.
     */
    function searchHeaders($field, $value)
    {
        return $this->search('HEADER "' . $field . '" "' . $value . '"', true);
    }

    /**
     * Retrieves the message headers for a given message id.
     *
     * @param int $uid                The message id.
     * @param boolean $peek_for_body  Prefetch the body.
     *
     * @return mixed  The message header or a PEAR error in case of an error.
     */
    function getMessageHeader($uid, $peek_for_body = true)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        if (!isset($this->_mbox['mails'][$uid])) {
            return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
        }
        return $this->_mbox['mails'][$uid]['header'];
    }

    /**
     * Retrieves the message body for a given message id.
     *
     * @param integet $uid  The message id.
     *
     * @return mixed  The message body or a PEAR error in case of an error.
     */
    function getMessageBody($uid)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        if (!isset($this->_mbox['mails'][$uid])) {
            return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
        }
        return $this->_mbox['mails'][$uid]['body'];
    }

    /**
     * Retrieves the full message text for a given message id.
     *
     * @param integer $uid  The message id.
     *
     * @return mixed  The message text or a PEAR error in case of an error.
     */
    function getMessage($uid)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        if (!isset($this->_mbox['mails'][$uid])) {
            return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
        }
        return $this->_mbox['mails'][$uid]['header'] . $this->_mbox['mails'][$uid]['body'];
    }

    /**
     * Retrieves a list of mailboxes on the server.
     *
     * @return mixed  The list of mailboxes or a PEAR error in case of an
     *                error.
     */
    function getMailboxes()
    {
        $mboxes = array_keys($GLOBALS['KOLAB_TESTING']);
        $user = split('@', $this->_user);
        $pattern = '#^user/' . $user[0] . '#';
        $result = array();
        foreach ($mboxes as $mbox) {
            $result[] = preg_replace($pattern, 'INBOX', $mbox);
        }
        return $result;
    }

    /**
     * Fetches the annotation on a folder.
     *
     * @param string $entries       The entry to fetch.
     * @param string $value         The specific value to fetch.
     * @param string $mailbox_name  The name of the folder.
     *
     * @return mixed  The annotation value or a PEAR error in case of an error.
     */
    function getAnnotation($entries, $value, $mailbox_name)
    {
        $mailbox_name = $this->_parseFolder($mailbox_name);
        $old_mbox = null;
        if ($mailbox_name != $this->_mboxname) {
            $old_mbox = $this->_mboxname;
            $result = $this->select($mailbox_name);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        if (!isset($this->_mbox['annotations'][$entries])
            || !isset($this->_mbox['annotations'][$entries][$value])) {
            return false;
        }
        $annotation = $this->_mbox['annotations'][$entries][$value];
        if ($old_mbox) {
            $this->select($old_mbox);
        }
        return $annotation;
    }

    /**
     * Sets the annotation on a folder.
     *
     * @param string $entries        The entry to set.
     * @param array  $values         The values to set
     * @param string $mailbox_name   The name of the folder.
     *
     * @return mixed  True if successfull, a PEAR error otherwise.
     */
    function setAnnotation($entries, $values, $mailbox_name)
    {
        $mailbox_name = $this->_parseFolder($mailbox_name);
        $old_mbox = null;
        if ($mailbox_name != $this->_mboxname) {
            $old_mbox = $this->_mboxname;
            $result = $this->select($mailbox_name);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        if (!isset($this->_mbox['annotations'][$entries])) {
            $this->_mbox['annotations'][$entries] = array();
        }
        foreach ($values as $key => $value) {
            $this->_mbox['annotations'][$entries][$key] = $value;
        }
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return true;
    }

    /**
     * Retrieve the access rights from a folder
     *
     * @param string $folder  The folder to retrieve the ACLs from.
     *
     * @return mixed An array of rights if successfull, a PEAR error
     * otherwise.
     */
    function getACL($folder)
    {
        $folder = $this->_parseFolder($folder);
        $old_mbox = null;
        if ($folder != $this->_mboxname) {
            $old_mbox = $this->_mboxname;
            $result = $this->select($folder);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        $acl = $this->_mbox['permissions'];
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return $acl;
    }

    /**
     * Retrieve the access rights on a folder not owned by the current user
     *
     * @param string $folder  The folder to retrieve the ACLs from.
     *
     * @return mixed An array of rights if successfull, a PEAR error
     * otherwise.
     */
    function getMyRights($folder)
    {
        $folder = $this->_parseFolder($folder);
        $old_mbox = null;
        if ($folder != $this->_mboxname) {
            $old_mbox = $this->_mboxname;
            $result = $this->select($folder);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        $acl = '';
        if (isset($this->_mbox['permissions'][$this->_user])) {
            $acl = $this->_mbox['permissions'][$this->_user];
        }
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return $acl;
    }

    /**
     * Set the access rights for a folder
     *
     * @param string $folder  The folder to retrieve the ACLs from.
     * @param string $user    The user to set the ACLs for
     * @param string $acl     The ACLs
     *
     * @return mixed True if successfull, a PEAR error otherwise.
     */
    function setACL($folder, $user, $acl)
    {
        $folder = $this->_parseFolder($folder);
        $old_mbox = null;
        if ($folder != $this->_mboxname) {
            $old_mbox = $this->_mboxname;
            $result = $this->select($folder);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        $this->_mbox['permissions'][$user] = $acl;
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return true;
    }

    /**
     * Delete the access rights for a user.
     *
     * @param string $folder  The folder that should be modified.
     * @param string $user    The user that should get the ACLs removed
     *
     * @return mixed True if successfull, a PEAR error otherwise.
     */
    function deleteACL($folder, $user)
    {
        $folder = $this->_parseFolder($folder);
        $old_mbox = null;
        if ($folder != $this->_mboxname) {
            $old_mbox = $this->_mboxname;
            $result = $this->select($folder);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        unset($this->_mbox['permissions'][$user]);
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return true;
    }

    /**
     * Appends a message to the current folder.
     *
     * @param string $msg  The message to append.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function appendMessage($msg)
    {
        $split = strpos($msg, "\r\n\r\n");
        $mail = array('header' => substr($msg, 0, $split + 2),
                      'body' => substr($msg, $split + 3));
        return $this->_appendMessage($mail);
    }

    /**
     * Appends a message to the current folder.
     *
     * @param array $msg  The message to append.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function _appendMessage($msg)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        $mail = array();
        $mail['flags'] = 0;
        $mail['header'] = $msg['header'];
        $mail['body'] = $msg['body'];


        $this->_mbox['mails'][$this->_mbox['status']['uidnext']] = $mail;
        $this->_mbox['status']['uidnext']++;
        return true;
    }

    /**
     * Copies a message to a new folder.
     *
     * @param integer $uid        IMAP message id.
     * @param string $new_folder  Target folder.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function copyMessage($uid, $new_folder)
    {
        $new_folder = $this->_parseFolder($new_folder);
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        if (!isset($this->_mbox['mails'][$uid])) {
            return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
        }
        $mail = $this->_mbox['mails'][$uid];

        $old_mbox = null;
        $result = $this->select($new_folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->_appendMessage($mail);
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return true;
    }

    /**
     * Moves a message to a new folder.
     *
     * @param integer $uid        IMAP message id.
     * @param string $new_folder  Target folder.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function moveMessage($uid, $new_folder)
    {
        $new_folder = $this->_parseFolder($new_folder);
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }
        if (!isset($this->_mbox['mails'][$uid])) {
            return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
        }
        $mail = $this->_mbox['mails'][$uid];
        unset($this->_mbox['mails'][$uid]);

        $old_mbox = null;
        $result = $this->select($new_folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->_appendMessage($mail);
        if ($old_mbox) {
            $result = $this->select($old_mbox);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return true;
    }

    /**
     * Deletes messages from the current folder.
     *
     * @param integer $uids  IMAP message ids.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function deleteMessages($uids)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }

        if (!is_array($uids)) {
            $uids = array($uids);
        }

        foreach ($uids as $uid) {

            if (!isset($this->_mbox['mails'][$uid])) {
                return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
            }
            $this->_mbox['mails'][$uid]['flags'] |= KOLAB_IMAP_FLAG_DELETED;
        }
        return true;
    }

    /**
     * Undeletes a message in the current folder.
     *
     * @param integer $uid  IMAP message id.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function undeleteMessages($uid)
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }

        if (!isset($this->_mbox['mails'][$uid])) {
            return PEAR::raiseError(sprintf("No IMAP message %s!", $uid));
        }
        $this->_mbox['mails'][$uid]['flags'] &= ~KOLAB_IMAP_FLAG_DELETED;
        return true;
    }

    /**
     * Expunges messages in the current folder.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function expunge()
    {
        if (!$this->_mbox) {
            return PEAR::raiseError("No IMAP folder selected!");
        }

        $remaining = array();
        foreach ($this->_mbox['mails'] as $uid => $mail) {
            if (!($mail['flags'] & KOLAB_IMAP_FLAG_DELETED)) {
                $remaining[$uid] = $mail;
            }
        }
        $this->_mbox['mails'] = $remaining;
        return true;
    }

    /**
     * Return the currently selected mailbox
     *
     * @return string  The mailbox currently selected
     */
    function current()
    {
        return $this->_mboxname;
    }
}
