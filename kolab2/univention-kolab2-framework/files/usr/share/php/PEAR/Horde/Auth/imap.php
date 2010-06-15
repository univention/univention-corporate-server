<?php
/**
 * The Auth_imap:: class provides an IMAP implementation of the Horde
 * authentication system.
 *
 * Optional parameters:
 * ====================
 *  'folder'         --  The initial folder / mailbox to open.
 *                       Should be null for 'imap' and 'nntp' protocols.
 *                       DEFAULT: null
 *  'hostspec'       --  The hostname or IP address of the server.
 *                       DEFAULT: 'localhost'
 *  'port'           --  The server port to which we will connect.
 *                       IMAP is generally 143, while IMAP-SSL is generally 993.
 *                       DEFAULT: 143
 *  'protocol'       --  The connection protocol (e.g. 'imap', 'pop3', 'nntp').
 *                       Protocol is one of 'imap/notls' (or only 'imap' if you
 *                       have a c-client version 2000c or older), 'imap/ssl',
 *                       or 'imap/ssl/novalidate-cert' (for a self-signed
 *                       certificate).
 *                       DEFAULT: 'imap'
 *  'admin_user'     --  The name of a user with admin privileges.
 *                       DEFAULT: null
 *  'admin_password' --  The password of the adminstrator.
 *                       DEFAULT: null
 *  'userhierarchy'  --  The hierarchy where user mailboxes are stored.
 *                       DEFAULT: 'user.'
 *  'dsn'            --  The full IMAP connection string.
 *                       If not present, this is built from 'hostspec', 'port'
 *                       and 'protocol' parameters.
 *
 *
 * If setting up as Horde auth handler in conf.php, this is a sample entry:
 *   $conf['auth']['params']['folder'] = 'INBOX';
 *   $conf['auth']['params']['hostspec'] = 'imap.example.com';
 *   $conf['auth']['params']['port'] = 143;
 *   $conf['auth']['params']['protocol'] = 'imap/notls/novalidate-cert';
 *
 * 
 * $Horde: framework/Auth/Auth/imap.php,v 1.26 2004/04/13 23:16:47 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Gaudenz Steinlin <gaudenz.steinlin@id.unibe.ch>
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Gaudenz Steinlin <gaudenz.steinlin@id.unibe.ch>
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_imap extends Auth {

    /**
     * Constructs a new IMAP authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_imap($params = array())
    {
        if (!Util::extensionExists('imap')) {
            Horde::fatal(PEAR::raiseError(_("Auth_imap: Required IMAP extension not found."), __FILE__, __LINE__));
        }

        $default_params = array(
            'folder' => null,
            'hostspec' => 'localhost',
            'port' => '143',
            'protocol' => 'imap',
            'userhierarchy' => 'user.'
        );
        $this->_params = array_merge($default_params, $params);

        if (!empty($this->_params['admin_user'])) {
            $this->capabilities['add'] = true;
            $this->capabilities['remove'] = true;
            $this->capabilities['list'] = true;
        }

        /* Create DSN string. */
        if (!isset($this->_params['dsn'])) {
            $this->_params['dsn'] = sprintf('{%s:%d/%s}', 
                                            $this->_params['hostspec'],
                                            $this->_params['port'],
                                            $this->_params['protocol']);
            if (!empty($this->_params['folder'])) {
                $this->_params['dsn'] .= $this->_params['folder'];
            }
        }
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  An array of login credentials. For IMAP,
     *                            this must contain a password entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            Horde::fatal(PEAR::raiseError(_("No password provided for IMAP authentication.")), __FILE__, __LINE__);
        }

        $imap = @imap_open($this->_params['dsn'], $userId,
                           $credentials['password'], OP_HALFOPEN);

        if ($imap) {
            @imap_close($imap);
            return true;
        } else {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId       The userId to add.
     * @param array  $credentials  The credentials to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        require_once 'Horde/IMAP/Admin.php';
        $imap = &new IMAP_Admin($this->_params);
        return $imap->addMailbox(String::convertCharset($userId, NLS::getCharset(), 'utf7-imap'));
    }

    /**
     * Delete a set of authentication credentials.
     *
     * @param string $userId  The userId to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($userId)
    {
        require_once 'Horde/IMAP/Admin.php';
        $imap = &new IMAP_Admin($this->_params);
        return $imap->removeMailbox(String::convertCharset($userId, NLS::getCharset(), 'utf7-imap'));
    }

    /**
     * List all users in the system.
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        require_once 'Horde/IMAP/Admin.php';
        $imap = &new IMAP_Admin($this->_params);
        return $imap->listMailboxes();
    }

}
