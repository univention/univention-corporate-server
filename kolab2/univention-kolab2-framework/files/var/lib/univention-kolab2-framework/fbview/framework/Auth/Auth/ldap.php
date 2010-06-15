<?php
/**
 * The Auth_ldap class provides an LDAP implementation of the Horde
 * authentication system.
 *
 * Required parameters:
 * ====================
 *   'basedn'       --  The base DN for the LDAP server.
 *   'hostspec'     --  The hostname of the LDAP server.
 *   'uid'          --  The username search key.
 *   'filter'       --  The LDAP formatted search filter to search for users.
 *                      This setting overrides the 'objectclass' method below.
 *   'objectclass'  --  The objectclass filter used to search for users. Can
 *                      be a single objectclass or an array.
 *
 * Optional parameters:
 * ====================
 *   'binddn'       --  The DN used to bind to the LDAP server
 *   'password'     --  The password used to bind to the LDAP server
 *   'version'      --  The version of the LDAP protocol to use.
 *                      DEFAULT: NONE (system default will be used)
 *
 *
 * $Horde: framework/Auth/Auth/ldap.php,v 1.45 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_ldap extends Auth {

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
                              'list'          => true,
                              'transparent'   => false);

    /**
     * Constructs a new LDAP authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing connection parameters.
     */
    function Auth_ldap($params = array())
    {
        if (!Util::extensionExists('ldap')) {
            Horde::fatal(PEAR::raiseError(_("Auth_ldap: Required LDAP extension not found."), __FILE__, __LINE__));
        }

        $this->_setParams($params);
    }

    /**
     * Set configuration parameters
     *
     * @access private
     *
     * @param array $params  A hash containing connection parameters.
     */
    function _setParams($params)
    {
        /* Ensure we've been provided with all of the necessary parameters. */
        Horde::assertDriverConfig($params, 'auth',
            array('hostspec', 'basedn', 'uid'),
            'authentication LDAP');

        $this->_params = $params;
    }

    /**
     * Find out if the given set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId       The userId to check.
     * @param array  $credentials  An array of login credentials.
     *
     * @return boolean  True on success or a PEAR_Error object on failure.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password'])) {
            Horde::fatal(PEAR::raiseError(_("No password provided for LDAP authentication.")), __FILE__, __LINE__);
        }

        /* Connect to the LDAP server. */
        $ldap = @ldap_connect($this->_params['hostspec']);
        if (!$ldap) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Failed to connect to LDAP server."));
            return false;
        }

        $this->_setProtocolVersion($ldap);

        if (isset($this->_params['binddn'])) {
            $binddn = $this->_params['binddn'];
            $bind = @ldap_bind($ldap, $binddn, $this->_params['password']);
            if (!$bind) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, _("Could not bind to LDAP server."));
                return false;
            }
        }

        /* Search for the user's full DN. */
        $search = @ldap_search($ldap, $this->_params['basedn'],
                               $this->_params['uid'] . '=' . $userId,
                               array($this->_params['uid']));
        if (!$search) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, _("Could not search the LDAP server."));
                return false;
        }

        $result = @ldap_get_entries($ldap, $search);
        if (is_array($result) && (count($result) > 1)) {
            $dn = $result[0]['dn'];
        } else {
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Empty result."));
            return false;
        }

        /* Attempt to bind to the LDAP server as the user. */
        $bind = @ldap_bind($ldap, $dn, $credentials['password']);
        if ($bind != false) {
            @ldap_close($ldap);
            return true;
        } else {
            @ldap_close($ldap);
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to be set.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        $ldap = @ldap_connect($this->_params['hostspec']);
        $this->_setProtocolVersion($ldap);

        if (isset($this->_params['binddn'])) {
            $binddn = $this->_params['binddn'];
            $bind = @ldap_bind($ldap, $binddn, $this->_params['password']);
        } else {
            $bind = @ldap_bind($ldap);
        }

        global $conf;
        if (!empty($conf['hooks']['authldap'])) {
            @include HORDE_BASE . '/config/hooks.php';
            if (function_exists('_horde_hook_authldap')) {
                $entry = call_user_func('_horde_hook_authldap', $userId, $credentials);
                $dn = $entry['dn'];
                // remove the dn entry from the array
                unset($entry['dn']);
            }
        } else {
            // Try this simple default and hope it works.
            $dn = $this->_params['uid'] . '=' . $userId . ',' . $this->_params['basedn'];
            $entry['cn'] = $userId;
            $entry['sn'] = $userId;
            // password not encrypted?
            $entry['userpassword'] = $credentials['password'];
        }
        $success = @ldap_add($ldap, $dn, $entry);

        if (!$success) {
           return PEAR::raiseError(sprintf(_("Auth_ldap: Unable to add user %s. This is what the server said: "), $userId) . ldap_error($ldap), __FILE__, __LINE__);
        }
        return true;
    }

    /**
     * Remove a set of authentication credentials.
     *
     * @access public
     *
     * @param string $userId      The userId to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($userId)
    {
        $ldap = @ldap_connect($this->_params['hostspec']);
        $this->_setProtocolVersion($ldap);

        if (isset($this->_params['binddn'])) {
            $binddn = $this->_params['binddn'];
            $bind = @ldap_bind($ldap, $binddn, $this->_params['password']);
        } else {
            $bind = @ldap_bind($ldap);
        }

        global $conf;
        if (!empty($conf['hooks']['authldap'])) {
            @include HORDE_BASE . '/config/hooks.php';
            if (function_exists('_horde_hook_authldap')) {
                $entry = call_user_func('_horde_hook_authldap', $userId);
                $dn = $entry['dn'];
            }
        } else {
            // Try this simple default and hope it works
            $dn = $this->_params['uid'] . '=' . $userId . ',' . $this->_params['basedn'];
        }

        $success = @ldap_delete($ldap,$dn);
        if (!$success) {
           return PEAR::raiseError(sprintf(_("Auth_ldap: Unable to remove user %s"), $userId), __FILE__, __LINE__);
        }
        return true;
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
        $ldap = @ldap_connect($this->_params['hostspec']);
        $this->_setProtocolVersion($ldap);

        if (isset($this->_params['binddn'])) {
            $binddn = $this->_params['binddn'];
            $bind = @ldap_bind($ldap, $binddn, $this->_params['password']);
        } else {
            $bind = @ldap_bind($ldap);
        }

        global $conf;
        if (!empty($conf['hooks']['authldap'])) {
            @include HORDE_BASE . '/config/hooks.php';
            if (function_exists('_horde_hook_authldap')) {
                $entry = call_user_func('_horde_hook_authldap', $oldID);
                $olddn = $entry['dn'];
                $entry = call_user_func('_horde_hook_authldap', $newID);
                $newdn = $entry['dn'];
                unset($entry['dn']);
            }
        } else {
            // Try this simple default and hope it works
            $newdn = $this->_params['uid'] . '=' . $newID . ',' . $this->_params['basedn'];
            $olddn = $this->_params['uid'] . '=' . $oldID . ',' . $this->_params['basedn'];
            $entry['userpassword'] = $credentials['user_pass_2'];
        }
        if ($oldID != $newID) {
            if (LDAP_OPT_PROTOCOL_VERSION == 3) {
                ldap_rename($ldap, $olddn, $newdn, $this->_params['basedn'], true);

                $success = ldap_modify($ldap, $newdn, $entry);
            } else {
                $success = $this->addUser($newID, $entry);
                if ($success) {
                    $success = $this->removeUser($oldID);
                }
            }
        } else {
            $success = ldap_modify($ldap, $newdn, $entry);
        }

        if (!$success) {
            return PEAR::raiseError(sprintf(_("Auth_ldap: Unable to update user %s"), $newID), __FILE__, __LINE__);
        }
        return true;
    }

    /**
     * List Users
     *
     * @access public
     *
     * @return array  List of Users
     */
    function listUsers()
    {
        $ldap = @ldap_connect($this->_params['hostspec']);
        $this->_setProtocolVersion($ldap);

        if (isset($this->_params['binddn'])) {
            $dn = $this->_params['binddn'];
            $bind = @ldap_bind($ldap, $dn, $this->_params['password']);
        } else {
            $bind = @ldap_bind($ldap);
        }
        if (!empty($this->_params['filter'])) {
            $filter = $this->_params['filter'];
        } elseif (!is_array($this->_params['objectclass'])) {
            $filter = 'objectclass=' . $this->_params['objectclass'];
        } else {
            $filter = '';
            foreach ($this->_params['objectclass'] as $objectclass) {
                $filter = '(&' . $filter;
                $filter .= '(objectclass=' . $objectclass . '))';
            }
        }

        $search = ldap_search($ldap, $this->_params['basedn'], $filter);
        $entries = ldap_get_entries($ldap, $search);
        $userlist = array();
        for ($i = 0; $i < $entries['count']; $i++) {
            $userlist[$i] = $entries[$i][$this->_params['uid']][0];
        }

        return $userlist;
    }

    /**
     * Set the LDAP protocol version according to the driver
     * parameters.
     *
     * @param resource &$conn  The LDAP connection to modify.
     */
    function _setProtocolVersion(&$conn)
    {
        /* Set the LDAP protocol version. */
        if (isset($this->_params['version'])) {
            if (!ldap_set_option($conn, LDAP_OPT_PROTOCOL_VERSION,
                                 $this->_params['version'])) {
                Horde::logMessage(
                    sprintf('Set LDAP protocol version to %d failed: [%d] %s',
                            $this->_params['version'],
                            ldap_errno($conn),
                            ldap_error($conn),
                            __FILE__, __LINE__));
            }
        }
    }

}
