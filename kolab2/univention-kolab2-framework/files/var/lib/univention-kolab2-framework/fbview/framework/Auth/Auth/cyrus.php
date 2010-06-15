<?php
/**
 * The Auth_cyrus class provides horde with the ability of administrating
 * a Cyrus mail server authentications against another backend that Horde
 * can update (eg SQL or LDAP).
 *
 * Required values for $params:
 *   'cyradmin'      The username of the cyrus administrator
 *   'cyrpass'       The password for the cyrus administrator
 *   'imap_dsn'      The full IMAP DSN (i.e. {localhost:993/imap/ssl/novalidate-cert} )
 *   'backend'       The complete hash for the Auth_* driver that cyrus
 *                   authenticates against (eg SQL, LDAP).
 *   'separator'     Hierarchy separator to use (e.g., is it user/mailbox or user.mailbox)
 *
 * Optional values:
 *   'unixhier'       The value of imapd.conf's unixhierarchysep setting
 *                    (set this to true if the value is true in imapd.conf)
 *   'folders'        An array of folders to create under username.
 *                    Doesn't create subfolders by default
 *   'quota'          The quota (in kilobytes) to grant on the mailbox.
 *                    Does not establish quota by default.
 *
 * Example Usage:
 *   $conf['auth']['driver'] = 'composite';
 *   $conf['auth']['params']['loginscreen_switch'] = '_horde_select_loginscreen';
 *   $conf['auth']['params']['admin_driver'] = 'cyrus';
 *   $conf['auth']['params']['drivers']['imp'] = array('driver' => 'application',
 *                                                     'params' => array('app' => 'imp'));
 *   $conf['auth']['params']['drivers']['cyrus'] = array('driver' => 'cyrus',
 *                                                       'params' => array('cyradmin' => 'cyrus',
 *                                                                         'cyrpass' => 'password',
 *                                                                         'separator' => '.',
 *                                                                         'imap_dsn' => '{maik.example.com/imap}'));
 *    $conf['auth']['params']['drivers']['cyrus']['params']['backend'] = array('driver' => 'sql',
 *                                                                             'params' => array('phptype' => 'mysql',
 *                                                                                           'hostspec' => 'database.example.com',
 *                                                                                           'protocol' => 'tcp',
 *                                                                                           'username' => 'username',
 *                                                                                           'password' => 'password',
 *                                                                                           'database' => 'mail',
 *                                                                                           'table' => 'accountuser',
 *                                                                                           'encryption' => 'md5-hex',
 *                                                                                           'username_field' => 'username',
 *                                                                                           'password_field' => 'password'));
 *
 *   if (!function_exists('_horde_select_loginscreen')) {
 *       function _horde_select_loginscreen() {
 *           return 'imp';
 *       }
 *   }
 *
 * $Horde: framework/Auth/Auth/cyrus.php,v 1.12 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2002-2004 Ilya <mail@krel.org>
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Ilya <mail@krel.org>
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_cyrus extends Auth {

    /**
     * Handle for the current IMAP connection.
     *
     * @var resource $_imapStream
     */
    var $_imapStream;

    /**
     * Flag indicating if the IMAP connection is connected.
     *
     * @var boolean $_connected
     */
    var $_connected;

    /**
     * Pointer to another Auth_ backend that Cyrus
     * authenticates against.
     *
     * @var Auth_*  $_backend
     */
     var $_backend;

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities
     */
    var $capabilities = array('add'           => true,
                              'update'        => true,
                              'resetpassword' => false,
                              'remove'        => true,
                              'list'          => false,
                              'groups'        => false,
                              'transparent'   => false);

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_cyrus($params = array())
    {
        $this->_params = $params;

        if (!isset($this->_params['seperator'])) {
            $this->_params['seperator'] = '.';
        }

        if (isset($this->_params['unixhier']) && $this->_params['unixhier'] == true) {
            $this->_params['seperator'] = '/';
        }

        if (!Util::extensionExists('imap')) {
            Horde::fatal(PEAR::raiseError(_("Auth_cyrus: Required imap extension not found."), __FILE__, __LINE__));
        }

        // Create backend instance.
        $this->_backend = &Auth::singleton($this->_params['backend']['driver'], $this->_params['backend']['params']);
        if (is_a($this->_backend, 'PEAR_Error')) {
            return $this->_backend;
        }

        // Check the capabilities of the backend.
        if (!$this->_backend->hasCapability('add') ||
            !$this->_backend->hasCapability('update') ||
            !$this->_backend->hasCapability('remove')) {
            Horde::fatal(PEAR::raiseError(_("Auth_cyrus: Backend does not have required capabilites."), __FILE__, __LINE__));
        }

        $this->capabilities['list'] = $this->_backend->hasCapability('list');
        $this->capabilities['groups'] = $this->_backend->hasCapability('groups');
        $this->capabilities['transparent'] = $this->_backend->hasCapability('transparent');
    }

    /**
     * Add a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId       The userId to add.
     * @param array  $credentials  The credentials to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        $this->_connect();

        $res = $this->_backend->addUser($userId, $credentials);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        $name = imap_utf7_encode($userId);
        if (@imap_createmailbox($this->_imapStream,
                                imap_utf7_encode($this->_params['imap_dsn'] .
                                'user' . $this->_params['separator'] . $name))) {
            if (isset($this->_params['folders']) && is_array($this->_params['folders'])) {
                foreach ($this->_params['folders'] as $folder) {
                    $this->_createSubFolder($name, $folder);
                }
            }
        } else {
            Horde::logMessage('IMAP mailbox creation for ' . $name . ' failed ',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(sprintf(_("IMAP mailbox creation failed: %s"), imap_last_error()));
        }

        if (isset($this->_params['quota']) && $this->_params['quota'] >= 0) {
            if (!@imap_set_quota($this->_imapStream,
                                 'user' . $this->_separator . $name,
                                 $this->_params['quota'])) {
                return PEAR::raiseError(sprintf(_("IMAP mailbox quota creation failed: %s"), imap_last_error()));
            }
        }

        return true;
    }

    /**
     * Delete a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId  The userId to delete.
     *
     * @return boolean        Success or failure.
     */
    function removeUser($userId)
    {
        $this->_connect();

        $res = $this->_backend->removeUser($userId);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        /* Set ACL for mailbox deletion. */
        list($admin) = explode('@', $this->_params['cyradmin']);
        @imap_setacl($this->_imapStream,
                     'user' . $this->_params['separator'] . $userId,
                     $admin, 'lrswipcda');

        /* Delete IMAP mailbox. */
        $imapresult = @imap_deletemailbox($this->_imapStream,
                                          $this->_params['imap_dsn'] .
                                          'user' . $this->_params['separator'] . $userId);

        if (!$imapresult) {
            return PEAR::raiseError(sprintf(_("IMAP mailbox deletion failed: %s"), imap_last_error()));
        }

        return true;
    }

    /**
     * Attempts to open connections to the SQL and IMAP servers.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        if (!$this->_connected) {

            $this->_imapStream = @imap_open($this->_params['imap_dsn'], $this->_params['cyradmin'],
                                            $this->_params['cyrpass'], OP_HALFOPEN);

            if (!$this->_imapStream) {
                Horde::fatal(new PEAR_Error(sprintf(_("Can't connect to IMAP server: %s"),
                                                    imap_last_error())), __FILE__, __LINE__);
            }

            $this->_connected = true;
        }

        return true;
    }

    /**
     * Disconnect from the IMAP server.
     *
     * @access private
     *
     * @return boolean  True on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            @imap_close($this->_imapStream);
        }

        return true;
    }

    /**
     * Creates a mailboxes supplied in configuration
     *
     * @access private
     */
    function _createSubFolder($userName, $folderName)
    {
         @imap_createmailbox($this->_imapStream,
                            imap_utf7_encode($this->_params['imap_dsn'] .
                            'user' . $this->_params['separator'] . $userName .
                                     $this->_params['separator'] . $folderName));
    }

    /**
     * List all users in the system.
     *
     * @access public
     *
     * @return mixed  The array of userIds, or false on failure/unsupported.
     */
    function listUsers()
    {
        return $this->_backend->listUsers();
    }

    /**
     * Update a set of authentication credentials.
     *
     * @access public
     *
     * @param string $oldID       The old userId.
     * @param string $newID       The new userId.
     * @param array $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        return $this->_backend->updateUser($oldID, $newID, $credentials);
    }

    /**
     * Return the URI of the login screen for this authentication
     * method.
     *
     * @access public
     *
     * @param optional string $app  The application to use.
     * @param optional string $url  The URL to redirect to after login.
     *
     * @return string  The login screen URI.
     */
    function _getLoginScreen($app = 'horde', $url = '')
    {
        return $this->_backend->_getLoginScreen($app, $url);
    }

    /**
     * Checks if a userId exists in the sistem.
     *
     * @access public
     *
     * @return boolean  Whether or not the userId already exists.
     */
    function exists($userId)
    {
        return $this->_backend->exists($userId);
    }

    /**
     * Automatic authentication: Find out if the client matches an
     * allowed IP block.
     *
     * @access public
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        return $this->_backend->transparent();
    }

}
