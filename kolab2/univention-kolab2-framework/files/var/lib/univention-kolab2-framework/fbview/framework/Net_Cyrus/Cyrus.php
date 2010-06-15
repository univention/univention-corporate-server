<?php

require_once('Net/Socket.php');
require_once('Auth/SASL.php');

/**
 * The Net_Cyrus:: class provides an API for the administration of
 * Cyrus IMAP servers.
 *
 * $Horde: framework/Net_Cyrus/Cyrus.php,v 1.1 2004/01/11 10:58:53 jan Exp $
 *
 * Copyright 2001-2004 Gernot Stocker <muecketb@sbox.tu-graz.ac.at>
 * Copyright 2002-2004 Richard Heyes <richard@php.net>
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gernot Stocker <muecketb@sbox.tu-graz.ac.at>
 * @author  Richard Heyes <richard@php.net>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Net_Cyrus
 */

class Net_Cyrus
{

    /**
     * Hostname of server
     * @var string
     */
    var $_host;

    /**
     * Port number of server
     * @var string
     */
    var $_port;

    /**
     * Username used to connect
     * @var string
     */
    var $_user;

    /**
     * Password used to connect
     * @var string
     */
    var $_pass;

    /**
     * Initial mailbox
     * @var string
     */
    var $_mbox;

    /**
     * Timeout for socket connect
     * @var integer
     */
    var $_timeout;

    /**
     * Constructor.
     *
     * @param string  $user     Cyrus admin username
     * @param string  $pass     Cyrus admin password
     * @param string  $host     Server hostname
     * @param integer $port     Server port number
     * @param integer $timeout  Connection timeout value
     */
    function Net_Cyrus($user, $pass, $host = 'localhost', $port = 143, $timeout = 5)
    {
        $this->_sock      = &new Net_Socket();
        $this->_user      = $user;
        $this->_pass      = $pass;
        $this->_host      = $host;
        $this->_port      = $port;
        $this->_mbox      = '';
        $this->_timeout   = $timeout;
        $this->_lastError = '';

        if (is_a($res = $this->connect(), 'PEAR_Error')) {
            $this->_lastError = $res;
        }
    }

    /**
     * Connects and logs into the server. Uses the Auth_SASL
     * library to produce the LOGIN command.
     *
     * @access private
     */
    function connect()
    {
        if (is_a($err = $this->_sock->connect($this->_host, $this->_port, null, $this->_timeout), 'PEAR_Error')) {
            return $err;
        }

        // Read greeting line
        $this->_sock->readLine();

        $sasl = &Auth_SASL::factory('Login');
        $this->_sendCommand($sasl->getResponse($this->_user, $this->_pass));
    }

    /**
     * Ends the session. Issues the LOGOUT command first.
     */
    function disconnect()
    {
        $this->_sendCommand('LOGOUT');
        $this->_sock->disconnect();
    }

    /**
     * Sends a command to the server.
     *
     * @param string $command  The command to send to the server
     *
     * @return array  An array of the lines of the response
     *
     * @access private
     */
    function _sendCommand($command)
    {
        static $imapSequence = 0;
        $imapSequence++;
        $response = array();

        $this->_sock->writeLine($imapSequence . ' ' . $command);

        while ($line = $this->_sock->readLine()) {
            $response[] = $line;
            if (preg_match('/^' . $imapSequence . ' (OK|NO|BAD)/i', $line)) {
                break;
            }
        }

        if (preg_match('/^' . $imapSequence . ' (NO|BAD)/i', $line) &&
            !preg_match('/^' . $imapSequence . ' NO QUOTA/i', $line))  {
            // Set message *without* imap sequence number
            return PEAR::raiseError(preg_replace('/^\d+\s+/', '', $line));
        }

        return $response;
    }

    /**
     * Sets admin privileges on a folder/mailbox.
     *
     * @param string $mailbox  Mailbox
     *
     * @return string  Previous permissions for admin user on this mailbox.
     *
     * @access private
     */
    function _setAdminPriv($mailbox)
    {
        $oldPrivs = $this->getACL($mailbox, $this->_user);
        $this->setACL($mailbox, $this->_user, 'lrswipcda');
        return $oldPrivs;
    }

    /**
     * Removes admin privileges on a folder/mailbox
     * after the above function has been used. If the
     * ACLs passed in is null, then the privs are deleted.
     *
     * @param string $mailbox  Mailbox
     * @param string $privs    Previous privileges as returned
     *                         by the _setAdminPriv() method
     *
     * @access private
     */
    function _resetAdminPriv($mailbox, $privs = null)
    {
        if (is_null($privs)) {
            $this->deleteACL($mailbox, $this->_user);
        } else {
            $this->setACL($mailbox, $this->_user, $privs);
        }
    }

    /**
     * Returns quota details.
     *
     * @param string $mailbox  Mailbox to get quota info for.
     *
     * @return mixed  Array of current usage and quota limit or
     *                false on failure.
     */
    function getQuota($mailbox)
    {
        $response = $this->_sendCommand(sprintf('GETQUOTA "%s"', $mailbox));

        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        if (preg_match('/NO QUOTA/i', $response[0])) {
            return array('NOT SET', 'NOT SET');

        } else {
            if (preg_match('/\(STORAGE (\d+) (\d+)\)/', $response[0], $matches)) {
                return array($matches[1], $matches[2]);
            } else {
                return  PEAR::raiseError('Invalid format for GETQUOTA response: ' . $response[0]);
            }
        }
    }

    /**
     * Sets a quota.
     *
     * @param string $mailbox  Mailbox to get quota info for
     * @param integer $quota   The quota to set
     *
     * @return mixed  True on success, PEAR_Error otherwise
     */
    function setQuota($mailbox, $quota)
    {
        $response = $this->_sendCommand(sprintf('SETQUOTA "%s" (STORAGE %d)', $mailbox, $quota));

        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        return true;
    }

    /**
     * Copies a quota from one mailbox to another.
     *
     * @param string $from  Mailbox to copy quota from
     * @param string $to    Mailbox to set quota on
     */
    function copyQuota($from, $to)
    {
        $currentQuota = $this->getQuota($from);
        $oldQuotaMax = trim($currentQuota[1]);

        if ($oldQuotaMax != 'NOT-SET') {
            $this->setQuota($to, $oldQuotaMax);
        }
    }

    /**
     * Retrieves details of current ACL.
     *
     * @param string $mailbox  Name of mailbox
     * @param  string $user    Optional user to get ACL for
     *
     * @return string  Access stuff
     */
    function getACL($mailbox, $user = null)
    {
        $return = array();
        $response = $this->_sendCommand(sprintf('GETACL "%s"', $mailbox));

        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        // Check format
        if (preg_match('/^\* ACL ' . preg_quote($mailbox) . '/', $response[0])) {
            $response = preg_replace('/^\* ACL ' . preg_quote($mailbox) . '\s+/i', '', $response[0]);
            $acls     = explode(' ', $response);

            // Check correct number in array (must be even)
            if (count($acls) % 2 == 0) {
                for ($i = 0; $i < count($acls); $i += 2) {
                    $return[$acls[$i]] = $acls[$i + 1];
                }

                if ($user && isset($return[$user])) {
                    return $return[$user];
                } else if ($user) {
                    return null;
                } else {
                    return $return;
                }
            }
        }

        return PEAR::raiseError('Unrecognised response format: ' . $response[0]);
    }

    /**
     * Sets ACL on a mailbox.
     *
     * @param string $mailbox  Name of mailbox
     * @param string $user     Username to apply ACL to
     * @param string $acl      The ACL
     *
     * @return mixed  True on success, PEAR_Error otherwise
     */
    function setACL($mailbox, $user, $acl)
    {
        $response = $this->_sendCommand(sprintf('SETACL "%s" "%s" %s', $mailbox, $user, $acl));

        return is_a($response, 'PEAR_Error') ? $response : true;
    }

    /**
     * Deletes ACL from a mailbox.
     *
     * @param string $mailbox  Name of mailbox
     * @param string $user     Username to remove ACL from
     *
     * @return mixed  True on success, PEAR_Error otherwise
     */
    function deleteACL($mailbox, $user)
    {
        return is_a($response = $this->_sendCommand(sprintf('DELETEACL "%s" "%s"', $mailbox, $user)), 'PEAR_Error') ? $response : true;
    }

    /**
     * Creates a mailbox.
     *
     * @param string $mailbox  Name of mailbox to create
     *
     * @return mixed  True on success, PEAR error otherwise
     */
    function createMailbox($mailbox)
    {
        return is_a($response = $this->_sendCommand(sprintf('CREATE "%s"', $mailbox)), 'PEAR_Error') ? $response : true;
    }

    /**
     * Renames a mailbox.
     *
     * @param string $mailbox  Name of mailbox to rename
     * @param string $newname  New name of mailbox
     *
     * @return mixed  True on success, PEAR error otherwise
     */
    function renameMailbox($mailbox, $newname)
    {
        $oldPrivs = $this->_setAdminPriv($mailbox);
        $response = $this->_sendCommand(sprintf('RENAME "%s" "%s"', $mailbox, $newname));
        $this->_resetAdminPriv($mailbox, $oldPrivs);

        return is_a($response, 'PEAR_Error') ? $response : true;
    }

    /**
     * Deletes a mailbox.
     *
     * @param string $mailbox  Name of mailbox to delete
     *
     * @return mixed  True on success, PEAR error otherwise
     */
    function deleteMailbox($mailbox)
    {
        $oldPrivs = $this->_setAdminPriv($mailbox);
        $response = $this->_sendcommand(sprintf('DELETE "%s"', $mailbox));
        $this->_resetAdminPriv($mailbox, $oldPrivs);

        return is_a($response, 'PEAR_Error') ? $response : true;
    }

    /**
     * Returns a list of folders for a particular user.
     *
     * @param string $prepend  Optional string to prepend
     *
     * @return array  Array of folders matched
     */
    function getFolderList($prepend = 'user.*')
    {
        $folders  = array();
        $response = $this->_sendCommand(sprintf('LIST "" %s', $prepend));

        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        // Lose last line of response
        array_pop($response);

        foreach ($response as $value) {
            $parts = explode('"', $value);
            $folders[] = $parts[3];
        }

        return $folders;
    }

    /**
     * Returns a list of users.
     *
     * @return array  Array of users found
     */
    function getUserList()
    {
        $users = array();
        $response = $this->getFolderList('user.%');

        if (is_a($response, 'PEAR_Error')) {
            return $response;
        }

        foreach ($response as $value) {
            if (preg_match('/^user\.(.*)$/', $value, $matches)) {
                $users[] = $matches[1];
            }
        }

        return $users;
    }

    /**
     * Renames a user. This is here since the RENAME command
     * is not allowed on a user's INBOX (ie. the user.<username>
     * mailbox). Supplied args can be either with or without
     * the "user." at the beginning.
     *
     * @param string $oldUser  Name of user to rename
     * @param string $newUser  New name of user
     */
    function renameUser($oldUser, $newUser)
    {
        if (!preg_match('/^user\./', $oldUser)) {
            $oldUser = 'user.' . $oldUser;
        }

        if (!preg_match('/^user\./', $newUser)) {
            $newUser = 'user.' . $newUser;
        }

        list($oldUsername, $newUsername) = preg_replace('/^user\./', '', array($oldUser, $newUser));

        // Check new user doesn't already exist and old user exists
        if (!in_array($oldUsername, $this->getUserList())) {
            return PEAR::raiseError(sprintf('User "%s" doesn\'t exist', $oldUsername));

        } elseif (in_array($newUsername, $this->getUserList())) {
            return PEAR::raiseError(sprintf('User "%s" already exists', $newUsername));
        }

        // Create the new mailbox
        $this->createMailbox($newUser);
        $oldAdminPrivs = $this->_setAdminPriv($newUser);

        // Copy Mail and quotas
        $this->copyMail($oldUser, $newUser);
        $this->copyQuota($oldUser, $newUser);

        // Copy the folders
        $folderList = $this->getFolderList($oldUser . '.*');

        if (!empty($folderList)) {
            foreach ($folderList as $folder) {
                $newFolderName = str_replace($oldUser, $newUser, $folder);
                $this->renameMailbox($folder, $newFolderName);
                $this->setACL($newFolderName, $newUsername, 'lrswipcd');
                $this->deleteACL($newFolderName, $oldUsername);
            }
        }

        $this->_resetAdminPriv($newUser, $oldAdminPrivs);
        $this->deleteMailbox($oldUser);
    }

    /**
     * Copies mail from one folder to another.
     *
     * @param string $from  From mailbox name
     * @param string $to    To mailbox name
     */
    function copyMail($from, $to)
    {
        $oldFromPrivs = $this->_setAdminPriv($from);
        $oldToPrivs   = $this->_setAdminPriv($to);

        $this->_sendCommand('SELECT ' . $from);
        $this->_sendCommand('COPY 1:* ' . $to);

        $this->_resetAdminPriv($from, $oldFromPrivs);
        $this->_resetAdminPriv($to, $oldToPrivs);
    }

}
