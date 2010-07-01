<?php
/**
 * $Horde: framework/Auth/Auth/msad.php,v 1.7.2.4 2009-10-26 11:58:59 jan Exp $
 *
 * @package Horde_Auth
 */

/** Auth_ldap */
require_once dirname(__FILE__) . '/ldap.php';

/**
 * The Auth_msad class provides an experimental MSAD extension of the LDAP
 * implementation of the Horde authentication system.
 *
 * Required parameters:<pre>
 *   'basedn'       The base DN for the AD server.
 *   'hostspec'     The hostname of the AD server.
 *   'uid'          The username search key.
 *   'filter'       The LDAP formatted search filter to search for users. This
 *                  setting overrides the 'objectclass' method below.
 *   'objectclass'  The objectclass filter used to search for users. Can be a
 *                  single objectclass or an array.
 * </pre>
 *
 * Optional parameters:<pre>
 *   'binddn'       The DN used to bind to the MSAD server
 *   'password'     The password used to bind to the MSAD server
 * </pre>
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Francois Helly <fhelly@bebop-design.net>
 * @since   Horde 3.2
 * @package Horde_Auth
 */
class Auth_msad extends Auth_ldap {

    /**
     * Constructs a new MSAD authentication object.
     *
     * @access public
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_msad($params = array())
    {
        Horde::assertDriverConfig($params, 'auth',
            array('hostspec', 'basedn', ), 'authentication MSAD');

        /* Assumes Horde framework 3 compatibilities */
        if (!isset($params['encryption'])) {
            $params['encryption'] = 'msad';
        }
        if (!isset($params['newuser_objectclass'])) {
            $params['newuser_objectclass'] = 'user';
        }
        if (!isset($params['password_expiration'])) {
            $params['password_expiration'] = 'no';
        }
        if (!isset($params['port'])) {
            $params['port'] = 389;
        }
        if (!isset($params['ssl'])) {
            $params['ssl'] = false;
        }
        if (!isset($params['adduser'])) {
            $params['adduser'] = true;
        }

        /* Define the UID used for horde authentication */
        if (!isset($params['authId'])) {
            $params['authId'] = 'initials';
        }

        /* Define the list of uids used for ldap authentication */
        if (!isset($params['uid'])) {
            $params['uid'] = array('samaccountname');
        }
        if (!is_array($params['uid'])) {
            $params['uid'] = array($params['uid']);
        }

        /* Adjust capabilities: depending on if SSL encryption is
         * enabled or not */
        $this->capabilities = array(
            'add'           => ($params['ssl'] || $params['adduser']),
            'update'        => $params['ssl'],
            'resetpassword' => $params['ssl'],
            'remove'        => true,
            'list'          => true,
            'groups'        => false,
            'transparent'   => false
        );

        $this->_params = $params;
    }

    /**
     * Add a set of authentication credentials.
     *
     * @access public
     *
     * @param string $accountName  The user sAMAccountName to find.
     * @param array $credentials   The credentials to be set.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($accountName, $credentials)
    {
        /* Connect to the MSAD server. */
        $success = $this->_connect();

        $entry = Horde::callHook('_horde_hook_authmsad', array($accountName, $credentials), 'horde', null);
        if (!is_null($entry)) {
            $dn = $entry['dn'];
            unset($entry['dn']);
        } else {
            $basedn = (isset($credentials['basedn'])) ?
                $credentials['basedn'] : $this->_params['basedn'];

            /* Set a default CN */
            $dn = 'cn=' . $accountName . ',' . $basedn;

            $entry['cn'] = $accountName;
            $entry['samaccountname'] = $accountName;

            $entry['objectclass'][0] = "top";
            $entry['objectclass'][1] = "person";
            $entry['objectclass'][2] = "organizationalPerson";
            $entry['objectclass'][3] = "user";

            $entry['description'] = (isset($credentials['description'])) ?
                $credentials['description'] : 'New horde user';

            if ($this->_params['ssl']) {
                $entry["AccountDisabled"] = false;
            }
            $entry['userPassword'] = $this->getCryptedPassword($credentials['password'],'',
                                                               $this->_params['encryption'],
                                                               false);

            if (isset($this->_params['binddn'])) {
                $entry['manager'] = $this->_params['binddn'];
            }

        }

        $success = @ldap_add($this->_ds, $dn, $entry);

        if (!$success) {
           return PEAR::raiseError(sprintf(_("Auth_msad: Unable to add user \"%s\". This is what the server said: "), $accountName) . ldap_error($this->_ds));
        }

        @ldap_close($this->_ds);
        return true;
    }

    /**
     * Remove a set of authentication credentials.
     *
     * @access public
     *
     * @param string $accountName  The user sAMAccountName to remove.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($accountName)
    {
        /* Connect to the MSAD server. */
        $success = $this->_connect();
        if (is_a($success, 'PEAR_Error')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, $success->getMessage());
            return $success;
        }

        $entry = Horde::callHook('_horde_hook_authmsad', array($accountName), 'horde', null);
        if (!is_null($entry)) {
            $dn = $entry['dn'];
        } else {
            /* Search for the user's full DN. */
            $dn = $this->_findDN($accountName);
            if (is_a($dn, 'PEAR_Error')) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, $dn->getMessage());
                return false;
            }
        }

        $success = @ldap_delete($this->_ds, $dn);
        if (!$success) {
            return PEAR::raiseError(sprintf(_("Auth_msad: Unable to remove user \"%s\""), $accountName));
        }
        @ldap_close($this->_ds);

        /* Remove user data */
        return $this->removeUserData($accountName);
    }

    /**
     * Update a set of authentication credentials.
     *
     * @param string $oldID       The old userId.
     * @param string $newID       The new userId.
     * @param array $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldId, $newId, $credentials)
    {
        /* Connect to the MSAD server. */
        $success = $this->_connect();
        if (is_a($success, 'PEAR_Error')) {
            return PEAR::raiseError($success->getMessage(), __FILE__, __LINE__);
        }

        $entry = Horde::callHook('_horde_hook_authmsad', array($oldId, $credentials), 'horde', null);
        if (!is_null($entry)) {
            $olddn = $entry['dn'];
            unset($entry['dn']);
        } else {
            /* Search for the user's full DN. */
            $dn = $this->_findDN($oldId);
            if (is_a($dn, 'PEAR_Error')) {
                return PEAR::raiseError($success->getMessage(), __FILE__, __LINE__);
            } else {
                /* Encrypt the new password */
                if (isset($credentials['password'])) {
                    $entry['userpassword'] = $this->getCryptedPassword($credentials['password'],'',
                                                                       $this->_params['encryption'],
                                                                       true);
                }
            }
        }

        if ($oldID != $newID) {
            $newdn = str_replace($oldId, $newID, $dn);
            ldap_rename($this->_ds, $olddn, $newdn, $this->_params['basedn'], true);
            $success = @ldap_modify($this->_ds, $newdn, $entry);
        } else {
            $success = @ldap_modify($this->_ds, $olddn, $entry);
        }
        if (!$success) {
            return PEAR::raiseError(sprintf(_("Auth_msad: Unable to update user \"%s\""), $newID), __FILE__, __LINE__);
        }

        @ldap_close($this->_ds);

        return true;
    }

    /**
     * Reset a user's password. Used for example when the user does not
     * remember the existing password.
     *
     * @param string $user_id  The user id for which to reset the password.
     *
     * @return mixed  The new password on success or a PEAR_Error object on
     *                failure.
     */
    function resetPassword($user_id)
    {
        /* Connect to the MSAD server. */
        $success = $this->_connect();
        if (is_a($success, 'PEAR_Error')) {
            return PEAR::raiseError($success->getMessage(), __FILE__, __LINE__);
        }

        /* Get a new random password. */
        $password = Auth::genRandomPassword() . '/';
        $success = $this->updateUser($user_id, $user_id, array('userPassword' => $password));
        return is_a($success, 'PEAR_Error') ? $success : $password;
    }

    /**
     * Does an ldap connect and binds
     * as the guest user or as the optional dn.
     *
     * @access private
     *
     * @return boolean  True or False based on success of connect and bind.
     */
    function _connect($dn = null, $pwd = null)
    {
        if (!Util::extensionExists('ldap')) {
            return PEAR::raiseError(_("Auth_ldap: Required LDAP extension not found."));
        }

        /* Connect to the MSAD server. */
        $ssl = ($this->_params['ssl']) ? 'ldaps://' : '';
        $this->_ds = ldap_connect($ssl . $this->_params['hostspec'], $this->_params['port']);
        if (!$this->_ds) {
            return PEAR::raiseError(_("Failed to connect to MSAD server."));
        }

        if (!ldap_set_option($this->_ds, LDAP_OPT_PROTOCOL_VERSION, 3)) {
            Horde::logMessage(
            sprintf('Set MSAD protocol version to %d failed: [%d] %s',
            3,
            ldap_errno($conn),
            ldap_error($conn),
            __FILE__, __LINE__));
        }
        if (!ldap_set_option($this->_ds, LDAP_OPT_REFERRALS, 0)) {
            Horde::logMessage(
            sprintf('Set MSAD referrals option to %d failed: [%d] %s',
            0,
            ldap_errno($conn),
            ldap_error($conn),
            __FILE__, __LINE__));
        }

        if (isset($dn) && isset($pwd)) {
            $bind = @ldap_bind($this->_ds, $dn, $pwd);
        } elseif (isset($this->_params['binddn'])) {
            $bind = ldap_bind($this->_ds,
                              $this->_params['binddn'],
                              $this->_params['password']);
        } else {
            $bind = ldap_bind($this->_ds);
        }

        if (!$bind) {
            return PEAR::raiseError(_("Could not bind to MSAD server."));
        }

        return true;
    }

    /**
     * Find the user dn
     *
     * @access private
     *
     * @param string $userId  The user UID to find.
     *
     * @return string  The user's full DN
     */
    function _findDN($userId)
    {
        /* Search for the user's full DN. */
        foreach ($this->_params['uid'] as $uid) {
            $entries = array($uid);
            if ($uid != $this->_params['authId']) {
                array_push($entries, $this->_params['authId']);
            }
            $search = @ldap_search($this->_ds, $this->_params['basedn'],
                               $uid . '=' . $userId,
                               $entries
                               );
            /* Searching the tree is not successful */
            if (!$search) {
                return PEAR::raiseError(_("Could not search the MSAD server."));
            }

            /* Fetch the search result */
            $result = @ldap_get_entries($this->_ds, $search);
            /* The result isn't empty: the DN was found */
            if (is_array($result) && (count($result) > 1)) {
                break;
            }
        }

        if (is_array($result) && (count($result) > 1)) {
            $dn = $result[0]['dn'];
        } else {
            return PEAR::raiseError(_("Empty result."));
        }
        /* Be sure the horde userId is the configured one */
        $this->_authCredentials['userId'] = $result[0][$this->_params['authId']][0];
        return $dn;
    }

}
