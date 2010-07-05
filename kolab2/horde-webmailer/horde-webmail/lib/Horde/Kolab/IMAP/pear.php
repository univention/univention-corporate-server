<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP/pear.php,v 1.1.2.2 2009-01-06 15:23:15 jan Exp $
 */

/**
 * The Horde_Kolab library requires version >= 1.0.3 of Net_IMAP (i.e. a
 * version that includes support for the ANNOTATEMORE IMAP extension). The
 * latest version of Net_IMAP can be obtained from
 * http://pear.php.net/get/Net_IMAP
 */
require_once 'Net/IMAP.php';

/**
 * The Horde_Kolab_IMAP_Connection_pear class connects to an IMAP server using the
 * Net_IMAP PEAR package.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP/pear.php,v 1.1.2.2 2009-01-06 15:23:15 jan Exp $
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
class Horde_Kolab_IMAP_pear extends Horde_Kolab_IMAP {

    /**
     * The signature of the current connection
     *
     * @var string
     */
    var $_signature;

    /**
     * Connects to the IMAP server.
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
        $this->_signature = $this->_server . '|' . $this->_port . "|$login|$password|$tls";

        // Reuse existing connection?
        if ($this->_signature == $this->_reuse_detection) {
            return true;
        }

        $this->_imap = &new Net_IMAP($this->_server, $this->_port);
        $result = $this->_imap->login($login, $password, true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_reuse_detection = $this->_signature;

        return true;
    }

    /**
     * Disconnects from the IMAP server.
     *
     * @return mixed  True in case the connection was closed successfully, a
     *                PEAR error otherwise.
     */
    function disconnect()
    {
        $this->_reuse_detection = null;
        return $this->_imap->disconnect();
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
        return $this->_imap->selectMailbox($folder);
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
        return $this->_imap->mailboxExist($folder);
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
        return $this->_imap->createMailbox($folder);
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
        return $this->_imap->deleteMailbox($folder);
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
        return $this->_imap->renameMailbox($old, $new);
    }

    /**
     * Returns the status of the current folder.
     *
     * @return array  An array that contains 'uidvalidity' and 'uidnext'.
     */
    function status()
    {
        $result = array();

        $mailbox = $this->_imap->getCurrentMailbox();

        // Net_IMAP is not very efficent here
        $ret = $this->_imap->cmdStatus($mailbox, 'UIDVALIDITY');
        $result['uidvalidity'] = $ret['PARSED']['STATUS']['ATTRIBUTES']['UIDVALIDITY'];

        $ret = $this->_imap->cmdStatus($mailbox, 'UIDNEXT');
        $result['uidnext'] = $ret['PARSED']['STATUS']['ATTRIBUTES']['UIDNEXT'];

        return $result;
    }

    /**
     * Returns the message ids of the messages in this folder.
     *
     * @return array  The message ids.
     */
    function getUids()
    {
        $uids = $this->_imap->search('UNDELETED', true);
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
    function search($search_list, $uidSearch = true)
    {
        return $this->_imap->search($search_list, $uidSearch);
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
        return $this->_imap->search('HEADER "' . $field . '" "' . $value . '"', true);
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
        $ret = $this->_imap->cmdUidFetch($uid, 'BODY[HEADER]');
        if (String::upper($ret['RESPONSE']['CODE']) != 'OK') {
            return PEAR::raiseError(sprintf(_("Failed fetching headers of IMAP message %s. Error was %s"),
                                            $uid,
                                            $ret['RESPONSE']['CODE'] . ', ' . $ret['RESPONSE']['STR_CODE']));
        }

        if (isset($ret['PARSED'])) {
            foreach ($ret['PARSED'] as $msg) {
                if (isset($msg['EXT']['BODY[HEADER]']['CONTENT'])) {
                    return $msg['EXT']['BODY[HEADER]']['CONTENT'];
                }
            }
        }

        return '';
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
        $ret = $this->_imap->cmdUidFetch($uid, 'BODY[TEXT]');
        if (String::upper($ret['RESPONSE']['CODE']) != 'OK') {
            return PEAR::raiseError(sprintf(_("Failed fetching body of IMAP message %s. Error was %s"),
                                            $uid,
                                            $ret['RESPONSE']['CODE'] . ', ' . $ret['RESPONSE']['STR_CODE']));
        }

        if (isset($ret['PARSED'])) {
            foreach ($ret['PARSED'] as $msg) {
                if (isset($msg['EXT']['BODY[TEXT]']['CONTENT'])) {
                    return $msg['EXT']['BODY[TEXT]']['CONTENT'];
                }
            }
        }

        return '';
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
        $ret = $this->_imap->cmdUidFetch($uid, 'RFC822');
        if (String::upper($ret['RESPONSE']['CODE']) != 'OK') {
            return PEAR::raiseError(sprintf(_("Failed fetching IMAP message %s. Error was %s"),
                                            $uid,
                                            $ret['RESPONSE']['CODE'] . ', ' . $ret['RESPONSE']['STR_CODE']));
        }

        if (isset($ret['PARSED'])) {
            foreach ($ret['PARSED'] as $msg) {
                if (isset($msg['EXT']['RFC822']['CONTENT'])) {
                    return $msg['EXT']['RFC822']['CONTENT'];
                }
            }
        }

        return '';
    }

    /**
     * Retrieves a list of mailboxes on the server.
     *
     * @return mixed  The list of mailboxes or a PEAR error in case of an
     *                error.
     */
    function getMailboxes()
    {
        return $this->_imap->getMailboxes();
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
        static $annotations = array();

        $signature = "$this->_signature|$entries|$value|$mailbox_name";

        if (!isset($annotations[$signature])) {
            $annotations[$signature] = $this->_imap->getAnnotation($entries, $value, $mailbox_name);
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
        return $this->_imap->setAnnotation($entries, $values, $mailbox_name);
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
        $result = $this->_imap->getACL($folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $acl = array();
        foreach ($result as $user) {
            $acl[$user['USER']] = $user['RIGHTS'];
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
        $result = $this->_imap->getMyRights($folder);
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
        return $this->_imap->setACL($folder, $user, $acl);
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
        return $this->_imap->deleteACL($folder, $user);
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
        return $this->_imap->appendMessage($msg);
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
        $ret = $this->_imap->cmdUidCopy($uid, $new_folder);
        if (String::upper($ret['RESPONSE']['CODE']) != 'OK') {
            return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"),
                                            $uid,
                                            $ret['RESPONSE']['CODE'] . ', ' . $ret['RESPONSE']['STR_CODE']));
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
        $result = $this->copyMessage($uid, $new_folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->deleteMessages($uid);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->expunge();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
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
        if (!is_array($uids)) {
            $uids = array($uids);
        }

        foreach ($uids as $uid) {
            $ret = $this->_imap->cmdUidStore($uid, '+FLAGS.SILENT', '\Deleted');
            if (String::upper($ret['RESPONSE']['CODE']) != 'OK') {
                return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"),
                                                $uid,
                                                $ret['RESPONSE']['CODE'] . ', ' . $ret['RESPONSE']['STR_CODE']));
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
        $ret = $this->_imap->cmdUidStore($uid, '-FLAGS.SILENT', '\Deleted');
        if (String::upper($ret['RESPONSE']['CODE']) != 'OK') {
            return PEAR::raiseError(sprintf(_("IMAP error. Message: %s. Error: %s"),
                                            $uid,
                                            $ret['RESPONSE']['CODE'] . ', ' . $ret['RESPONSE']['STR_CODE']));
        }
        return true;
    }

    /**
     * Expunges messages in the current folder.
     *
     * @return mixed  True or a PEAR error in case of an error.
     */
    function expunge()
    {
        return $this->_imap->expunge();
    }

    /**
     * Return the currently selected mailbox
     *
     * @return string  The mailbox currently selected
     */
    function current()
    {
        return $this->_imap->getCurrentMailbox();
    }
}
