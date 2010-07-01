<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP/cclient.php,v 1.1.2.2 2009-01-06 15:23:15 jan Exp $
 */

/**
 * The Horde_Kolab_IMAP_Connection_cclient class connects to an IMAP server using
 * the IMAP functionality within PHP.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP/cclient.php,v 1.1.2.2 2009-01-06 15:23:15 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Kolab_Storage
 */
class Horde_Kolab_IMAP_cclient extends Horde_Kolab_IMAP {

    /**
     * Basic IMAP connection string.
     *
     * @var string
     */
    var $_base_mbox;

    /**
     * IMAP connection string that includes the folder.
     *
     * @var string
     */
    var $_mbox;

    /**
     * The signature of the current connection.
     *
     * @var string
     */
    var $_signature;

    /**
     * IMAP user name.
     *
     * @var string
     */
    var $_login;

    /**
     * IMAP password.
     *
     * @var string
     */
    var $_password;

    /**
     * Connects to the IMAP server.
     *
     * @param string $login     The user account name.
     * @param string $password  The user password.
     * @param boolean $tls      Should TLS be used for the connection?
     *
     * @return boolean|PEAR_Error  True in case the connection was opened
     *                             successfully.
     */
    function connect($login, $password, $tls = false)
    {
        $options = '';
        if (!$tls) {
            $options = '/notls';
        }

        $mbox = '{' . $this->_server . ':' . $this->_port
            . $options . '}';

        $this->_signature = "$mbox|$login|$password";
        if ($this->_signature == $this->_reuse_detection) {
            return true;
        }

        $this->_mbox = $this->_base_mbox = $mbox;
        $this->_login = $login;
        $this->_password = $password;
        $this->_imap = null;

        $this->_reuse_detection = $this->_signature;

        return true;
    }

    /**
     * Lazy connect to the IMAP server.
     *
     * @return mixed  True in case the connection was opened successfully, a
     *                PEAR error otherwise.
     */
    function _connect()
    {
        $result = @imap_open($this->_base_mbox, $this->_login, $this->_password, OP_HALFOPEN);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Server: %s. Error: %s"), $this->_server, @imap_last_error()));
        }
        $this->_imap = $result;
        return true;
    }

    /**
     * Disconnects from the IMAP server. If not really necessary this
     * should not be called. Once the page got served the connections
     * should be closed anyhow and if there is a chance to reuse the
     * connection it should be used.
     *
     * @return mixed  True in case the connection was closed successfully, a
     *                PEAR error otherwise.
     */
    function disconnect()
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $this->_reuse_detection = null;

        $result = @imap_close($this->_imap);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Server: %s. Error: %s"), $this->_server, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Opens the given folder.
     *
     * @param string $folder  The folder to open.
     *
     * @return mixed  True in case the folder was opened successfully, a PEAR
     *                error otherwise.
     */
    function select($folder)
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $this->_mbox = $this->_base_mbox . $folder;

        $result = @imap_reopen($this->_imap, $this->_mbox);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $folder, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Does the given folder exist?
     *
     * @param string $folder  The folder to check.
     *
     * @return mixed  True in case the folder exists, false otherwise
     */
    function exists($folder)
    {
        $folders = $this->getMailboxes();
        if (is_a($folders, 'PEAR_Error')) {
            return $folders;
        }
        return in_array($folder, $folders);
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $mbox = $this->_base_mbox . $folder;
        $result = @imap_createmailbox($this->_imap, $mbox);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $folder, @imap_last_error()));
        }
        return $result;
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $mbox = $this->_base_mbox . $folder;
        $result = @imap_deletemailbox($this->_imap, $mbox);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $folder, @imap_last_error()));
        }
        return $result;
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_renamemailbox($this->_imap,
                                      $this->_base_mbox . $old,
                                      $this->_base_mbox . $new);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $old, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Returns the status of the current folder.
     *
     * @return array  An array that contains 'uidvalidity' and 'uidnext'.
     */
    function status()
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $status = @imap_status_current($this->_imap, SA_MESSAGES | SA_UIDVALIDITY | SA_UIDNEXT);
        if (!$status) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $this->_mbox, @imap_last_error()));
        }

        return array('uidvalidity' => $status->uidvalidity,
                     'uidnext' => $status->uidnext);
    }

    /**
     * Returns the uids of the messages in this folder.
     *
     * @return mixed  The message ids or a PEAR error in case of an error.
     */
    function getUids()
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $uids = @imap_search($this->_imap, 'UNDELETED', SE_UID);
        if (!is_array($uids)) {
            $uids = array();
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
    function search($search_list)
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_search($this->_imap, $search_list, SE_UID);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $this->_mbox, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Searches the headers of the messages. c-client does not allow using
     * "HEADER" as it is possible with Net/IMAP, so we need a workaround.
     *
     * @param string $field  The name of the header field.
     * @param string $value  The value that field should match.
     *
     * @return mixed  The list of matching message ids or a PEAR error in case
     *                of an error.
     */
    function searchHeaders($field, $value)
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $uids = $this->getUids();
        if (is_a($uids, 'PEAR_Error')) {
            return $uids;
        }

        $result = array();
        foreach ($uids as $uid) {
            $header = $this->getMessageHeader($uid, false);
            if (is_a($header, 'PEAR_Error')) {
                return $header;
            }
            $header_array = MIME_Headers::parseMIMEHeaders($header);
            if (isset($header_array[$field]) && $header_array[$field] == $value) {
                $result[] = $uid;
            }
        }

        return $result;
    }

    /**
     * Retrieves the message headers for a given message id.
     *
     * @param integer $uid            The message id.
     * @param boolean $peek_for_body  Prefetch the body.
     *
     * @return mixed  The message header or a PEAR error in case of an error.
     */
    function getMessageHeader($uid, $peek_for_body = true)
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $flags = FT_UID;
        if ($peek_for_body) {
            $flags |= FT_PREFETCHTEXT;
        }

        $result = @imap_fetchheader($this->_imap, $uid, $flags);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"), $uid, @imap_last_error()));
        }

        return $result;
    }

    /**
     * Retrieves the message body for a given message id.
     *
     * @param integer $uid  The message id.
     *
     * @return mixed  The message body or a PEAR error in case of an error.
     */
    function getMessageBody($uid)
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_body($this->_imap, $uid, FT_UID);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"), $uid, @imap_last_error()));
        }

        return $result;
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
        $header = $this->getMessageHeader($uid);
        if (is_a($header, 'PEAR_Error')) {
            return $header;
        }

        $body = $this->getMessageBody($uid);
        if (is_a($body, 'PEAR_Error')) {
            return $body;
        }

        return $header . $body;
    }

    /**
     * Retrieves a list of mailboxes on the server.
     *
     * @return mixed  The list of mailboxes or a PEAR error in case of an
     *                error.
     */
    function getMailboxes()
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $folders = array();

        $result = @imap_list($this->_imap, $this->_base_mbox, '*');
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $this->_base_mbox, @imap_last_error()));
        }

        $server_len = strlen($this->_base_mbox);
        foreach ($result as $folder) {
            if (substr($folder, 0, $server_len) == $this->_base_mbox) {
                $folders[] = substr($folder, $server_len);
            }
        }

        return $folders;
    }

    /**
     * Fetches the annotation on a folder.
     *
     * @param string $entries        The entry to fetch.
     * @param string $value          The specific value to fetch.
     * @param string $mailbox_name   The name of the folder.
     *
     * @return mixed  The annotation value or a PEAR error in case of an error.
     */
    function getAnnotation($entries, $value, $mailbox_name)
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        static $annotations = array();

        $signature = "$this->_signature|$entries|$value|$mailbox_name";

        if (!isset($annotations[$signature])) {
            $result = @imap_getannotation($this->_imap, $mailbox_name, $entries, $value);
            if (isset($result[$value])) {
                $annotations[$signature] = $result[$value];
            } else {
                $annotations[$signature] = '';
            }
        }

        return $annotations[$signature];
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        foreach ($values as $key => $value) {
            $result = @imap_setannotation($this->_imap, $mailbox_name, $entries, $key, $value);
            if (!$result) {
                return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $mailbox_name, @imap_last_error()));
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_getacl($this->_imap, $folder);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $folder, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Retrieve the access rights from a folder not owned by the current user
     *
     * @param string $folder  The folder to retrieve the ACLs from.
     *
     * @return mixed An array of rights if successfull, a PEAR error
     * otherwise.
     */
    function getMyRights($folder)
    {
        if (!function_exists('imap_myrights')) {
            return PEAR::raiseError(sprintf(_("PHP does not support imap_myrights."), $folder, @imap_last_error()));
        }

        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_myrights($this->_imap, $folder);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $folder, @imap_last_error()));
        }
        return $result;

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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_setacl($this->_imap, $folder, $user, $acl);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $folder, @imap_last_error()));
        }
        return $result;
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
        return $this->setACL($folder, $user, '');
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_append($this->_imap, $this->_mbox, $msg);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $this->_mbox, @imap_last_error()));
        }
        return $result;
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_mail_copy($this->_imap, $uid, $new_folder, CP_UID);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $new_folder, @imap_last_error()));
        }
        return $result;
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_mail_move($this->_imap, $uid, $new_folder, CP_UID);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Folder: %s. Error: %s"), $new_folder, @imap_last_error()));
        }
        return $result;
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        if (!is_array($uids)) {
            $uids = array($uids);
        }

        foreach($uids as $uid) {
            $result = @imap_delete($this->_imap, $uid, FT_UID);
            if (!$result) {
                return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"), $uid, @imap_last_error()));
            }
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
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_undelete($this->_imap, $uid, FT_UID);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"), $uid, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Expunges messages in the current folder.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function expunge()
    {
        if (!isset($this->_imap)) {
            $result = $this->_connect();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = @imap_expunge($this->_imap);
        if (!$result) {
            return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"), $this->_mbox, @imap_last_error()));
        }
        return $result;
    }

    /**
     * Return the currently selected mailbox
     *
     * @return string  The mailbox currently selected
     */
    function current()
    {
        return $this->_mbox;
    }
}
