<?php
/**
 * The Auth_ldap class provides an LDAP implementation of the Horde
 * authentication system.
 *
 * Required parameters:<pre>
 *   'basedn'       The base DN for the LDAP server.
 *   'hostspec'     The hostname of the LDAP server.
 *   'uid'          The username search key.
 *   'filter'       The LDAP formatted search filter to search for users. This
 *                  setting overrides the 'objectclass' method below.
 *   'objectclass'  The objectclass filter used to search for users. Can be a
 *                  single objectclass or an array.</pre>
 *
 * Optional parameters:<pre>
 *   'binddn'       The DN used to bind to the LDAP server
 *   'password'     The password used to bind to the LDAP server
 *   'version'      The version of the LDAP protocol to use.
 *                  DEFAULT: NONE (system default will be used)</pre>
 *
 *
 * $Horde: framework/Auth/Auth/ldap.php,v 1.47.10.33 2009-10-26 11:58:59 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you did
 * not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth_ldap extends Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array
     */
    var $capabilities = array('add'           => true,
                              'update'        => true,
                              'resetpassword' => false,
                              'remove'        => true,
                              'list'          => true,
                              'transparent'   => false);

    /**
     * LDAP connection handle
     *
     * @var resource
     */
    var $_ds;

    /**
     * Constructs a new LDAP authentication object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Auth_ldap($params = array())
    {
        /* Ensure we've been provided with all of the necessary parameters. */
        Horde::assertDriverConfig($params, 'auth',
                                  array('hostspec', 'basedn', 'uid'),
                                  'authentication LDAP');

        $this->_params = $params;
    }

    /**
     * Does an ldap connect and binds as the guest user or as the optional dn.
     *
     * @access private
     *
     * @return boolean  True or False based on success of connect and bind.
     */
    function _connect()
    {
        if (!Util::extensionExists('ldap')) {
            return PEAR::raiseError(_("Auth_ldap: Required LDAP extension not found."));
        }

        /* Connect to the LDAP server. */
        $this->_ds = @ldap_connect($this->_params['hostspec']);
        if (!$this->_ds) {
            return PEAR::raiseError(_("Failed to connect to LDAP server."));
        }

        if (isset($this->_params['version'])) {
            if (!ldap_set_option($this->_ds, LDAP_OPT_PROTOCOL_VERSION,
                                 $this->_params['version'])) {
                Horde::logMessage(
                    sprintf('Set LDAP protocol version to %d failed: [%d] %s',
                            $this->_params['version'],
                            @ldap_errno($this->_ds),
                            @ldap_error($this->_ds)),
                    __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        /* Start TLS if we're using it. */
        if (!empty($this->_params['tls'])) {
            if (!@ldap_start_tls($this->_ds)) {
                Horde::logMessage(
                    sprintf('STARTTLS failed: [%d] %s',
                            @ldap_errno($this->_ds),
                            @ldap_error($this->_ds)),
                    __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        /* Work around Active Directory quirk. */
        if (!empty($this->_params['ad'])) {
            if (!ldap_set_option($this->_ds, LDAP_OPT_REFERRALS, false)) {
                Horde::logMessage(
                    sprintf('Unable to disable directory referrals on this connection to Active Directory: [%d] %s',
                            @ldap_errno($this->_ds),
                            @ldap_error($this->_ds)),
                    __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        if (isset($this->_params['binddn'])) {
            $bind = @ldap_bind($this->_ds, $this->_params['binddn'],
                               $this->_params['password']);
        } else {
            $bind = @ldap_bind($this->_ds);
        }

        if (!$bind) {
            return PEAR::raiseError(_("Could not bind to LDAP server."));
        }

        return true;
    }

    /**
     * Find the user dn
     *
     * @access private
     *
     * @param string $userId       The userId to find.
     *
     * @return string  The users full DN
     */
    function _findDN($userId)
    {
        /* Search for the user's full DN. */
        $filter = $this->_getParamFilter();
        $filter = '(&(' . $this->_params['uid'] . '=' . $userId . ')' .
                  $filter . ')';

        if ($this->_params['scope'] == 'one') {
            $func = 'ldap_list';
        } else {
            $func = 'ldap_search';
        }

        $search = @$func($this->_ds, $this->_params['basedn'], $filter,
                         array($this->_params['uid']));
        if (!$search) {
            Horde::logMessage(ldap_error($this->_ds), __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(_("Could not search the LDAP server."));
        }

        $result = @ldap_get_entries($this->_ds, $search);
        if (is_array($result) && (count($result) > 1)) {
            $dn = $result[0]['dn'];
        } else {
            return PEAR::raiseError(_("Empty result."));
        }

        return $dn;
    }

    /**
     * Checks for shadowLastChange and shadowMin/Max support and returns their
     * values.  We will also check for pwdLastSet if Active Directory is
     * support is requested.  For this check to succeed we need to be bound
     * to the directory
     *
     * @access private
     *
     * @param string $dn     The dn of the user
     *
     * @return array  Array with keys being "shadowlastchange", "shadowmin"
     *                "shadowmax", "shadowwarning" and containing their
     *                respective values or false for no support.
     */
    function _lookupShadow($dn)
    {
        /* Init the return array. */
        $lookupshadow = array('shadowlastchange' => false,
                              'shadowmin' => false,
                              'shadowmax' => false,
                              'shadowwarning' => false);

        /* According to LDAP standard, to read operational attributes, you
         * must request them explicitly. Attributes involved in password
         * expiration policy:
         *    pwdlastset: Active Directory
         *    shadow*: shadowUser schema
         *    passwordexpirationtime: Sun and Fedora Directory Server */
        $result = @ldap_read($this->_ds, $dn, '(objectClass=*)',
                             array('pwdlastset', 'shadowmax', 'shadowmin',
                                   'shadowlastchange', 'shadowwarning',
                                   'passwordexpirationtime'));
        if ($result) {
            $information = @ldap_get_entries($this->_ds, $result);

            if ($this->_params['ad']) {
                if (isset($information[0]['pwdlastset'][0])) {
                    /* Active Directory handles timestamps a bit differently.
                     * Convert the timestamp to a UNIX timestamp. */
                    $lookupshadow['shadowlastchange'] = floor((($information[0]['pwdlastset'][0] / 10000000) - 11644406783) / 86400) - 1;

                    /* Password expiry attributes are in a policy. We cannot
                     * read them so use the Horde config. */
                    $lookupshadow['shadowwarning'] = $this->_params['warnage'];
                    $lookupshadow['shadowmin'] = $this->_params['minage'];
                    $lookupshadow['shadowmax'] = $this->_params['maxage'];
                }
            } elseif (isset($information[0]['passwordexpirationtime'][0])) {
                /* Sun/Fedora Directory Server uses a special attribute
                 * passwordexpirationtime.  It has precedence over shadow*
                 * because it actually locks the expired password at the LDAP
                 * server level.  The correct way to check expiration should
                 * be using LDAP controls, unfortunately PHP doesn't support
                 * controls on bind() responses. */
                $ldaptimepattern = "/([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})Z/";
                if (preg_match($ldaptimepattern, $information[0]['passwordexpirationtime'][0], $regs)) {
                    /* Sun/Fedora Directory Server return expiration time, not
                     * last change time. We emulate the behaviour taking it
                     * back to maxage. */
                    $lookupshadow['shadowlastchange'] = floor(mktime($regs[4], $regs[5], $regs[6], $regs[2], $regs[3], $regs[1]) / 86400) - $this->_params['maxage'];

                    /* Password expiry attributes are in not accessible policy
                     * entry. */
                    $lookupshadow['shadowwarning'] = $this->_params['warnage'];
                    $lookupshadow['shadowmin']     = $this->_params['minage'];
                    $lookupshadow['shadowmax']     = $this->_params['maxage'];
                } else {
                    Horde::logMessage('Wrong time format: ' . $information[0]['passwordexpirationtime'][0], __FILE__, __LINE__, PEAR_LOG_ERR);
                }
            } else {
                if (isset($information[0]['shadowmax'][0])) {
                    $lookupshadow['shadowmax'] =
                        $information[0]['shadowmax'][0];
                }
                if (isset($information[0]['shadowmin'][0])) {
                    $lookupshadow['shadowmin'] =
                        $information[0]['shadowmin'][0];
                }
                if (isset($information[0]['shadowlastchange'][0])) {
                    $lookupshadow['shadowlastchange'] =
                        $information[0]['shadowlastchange'][0];
                }
                if (isset($information[0]['shadowwarning'][0])) {
                    $lookupshadow['shadowwarning'] =
                        $information[0]['shadowwarning'][0];
                }
            }
        }

        return $lookupshadow;
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
        /* Connect to the LDAP server. */
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, $result->getMessage());
            return false;
        }

        /* Search for the user's full DN. */
        $dn = $this->_findDN($userId);
        if (is_a($dn, 'PEAR_Error')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, $dn->getMessage());
            return false;
        }

        /* Attempt to bind to the LDAP server as the user. */
        $bind = @ldap_bind($this->_ds, $dn, $credentials['password']);
        if ($bind != false) {
            if ($this->_params['password_expiration'] == 'yes') {
                $shadow = $this->_lookupShadow($dn);
                if ($shadow['shadowmax'] && $shadow['shadowlastchange'] &&
                    $shadow['shadowwarning']) {
                    $today = floor(time() / 86400);
                    $warnday = $shadow['shadowlastchange'] +
                               $shadow['shadowmax'] - $shadow['shadowwarning'];
                    $toexpire = $shadow['shadowlastchange'] +
                                $shadow['shadowmax'] - $today;

                    if ($today >= $warnday) {
                        $GLOBALS['notification']->push(sprintf(ngettext("%d day until your password expires.", "%d days until your password expires.", $toexpire), $toexpire), 'horde.warning');
                    }
                    if ($toexpire == 0) {
                        $this->_authCredentials['changeRequested'] = true;
                    }
                    if ($toexpire < 0) {
                        $this->_setAuthError(AUTH_REASON_EXPIRED);
                        return false;
                    }
                }
            }

            @ldap_close($this->_ds);
            return true;
        } else {
            @ldap_close($this->_ds);
            $this->_setAuthError(AUTH_REASON_FAILED);
            return false;
        }
    }

    /**
     * Add a set of authentication credentials.
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to be set.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        if ($this->_params['ad']) {
           return PEAR::raiseError(_("Auth_ldap: Adding users is not supported for Active Directory"));
        }

        /* Connect to the LDAP server. */
        $result = $this->_connect();

        global $conf;
        if (!empty($conf['hooks']['authldap'])) {
            $entry = Horde::callHook('_horde_hook_authldap',
                                     array($userId, $credentials));
            if (is_a($entry, 'PEAR_Error')) {
                return $entry;
            }
            $dn = $entry['dn'];
            /* Remove the dn entry from the array. */
            unset($entry['dn']);
        } else {
            /* Try this simple default and hope it works. */
            $dn = $this->_params['uid'] . '=' . $userId . ','
                . $this->_params['basedn'];
            $entry['cn'] = $userId;
            $entry['sn'] = $userId;
            $entry[$this->_params['uid']] = $userId;
            $entry['objectclass'] = array_merge(
                array('top'),
                $this->_params['newuser_objectclass']);
            $entry['userPassword'] = $this->getCryptedPassword(
                $credentials['password'], '',
                $this->_params['encryption'],
                'true');

            if ($this->_params['password_expiration'] == 'yes') {
                $entry['shadowMin'] = $this->_params['minage'];
                $entry['shadowMax'] = $this->_params['maxage'];
                $entry['shadowWarning'] = $this->_params['warnage'];
                $entry['shadowLastChange'] = floor(time() / 86400);
            }
        }
        $result = @ldap_add($this->_ds, $dn, $entry);

        if (!$result) {
           return PEAR::raiseError(sprintf(_("Auth_ldap: Unable to add user \"%s\". This is what the server said: "), $userId) . @ldap_error($this->_ds));
        }

        @ldap_close($this->_ds);

        return true;
    }

    /**
     * Remove a set of authentication credentials.
     *
     * @param string $userId      The userId to add.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($userId)
    {
        if ($this->_params['ad']) {
           return PEAR::raiseError(_("Auth_ldap: Removing users is not supported for Active Directory"));
        }

        /* Connect to the LDAP server. */
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            $this->_setAuthError(AUTH_REASON_MESSAGE, $result->getMessage());
            return false;
        }

        if (!empty($GLOBALS['conf']['hooks']['authldap'])) {
            $entry = Horde::callHook('_horde_hook_authldap', array($userId));
            if (is_a($entry, 'PEAR_Error')) {
                return $entry;
            }
            $dn = $entry['dn'];
        } else {
            /* Search for the user's full DN. */
            $dn = $this->_findDN($userId);
            if (is_a($dn, 'PEAR_Error')) {
                $this->_setAuthError(AUTH_REASON_MESSAGE, $dn->getMessage());
                return false;
            }
        }

        $result = @ldap_delete($this->_ds, $dn);
        if (!$result) {
           return PEAR::raiseError(sprintf(_("Auth_ldap: Unable to remove user \"%s\""), $userId));
        }

        @ldap_close($this->_ds);

        return $this->removeUserData($userId);
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
    function updateUser($oldID, $newID, $credentials)
    {
        if ($this->_params['ad']) {
           return PEAR::raiseError(_("Auth_ldap: Updating users is not supported for Active Directory."));
        }

        /* Connect to the LDAP server. */
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (!empty($GLOBLS['conf']['hooks']['authldap'])) {
            $entry = Horde::callHook('_horde_hook_authldap',
                                     array($oldID, $credentials));
            if (is_a($entry, 'PEAR_Error')) {
                return $entry;
            }
            $olddn = $entry['dn'];
            $entry = Horde::callHook('_horde_hook_authldap',
                                     array($newID, $credentials));
            $newdn = $entry['dn'];
            unset($entry['dn']);
        } else {
            /* Search for the user's full DN. */
            $dn = $this->_findDN($oldID);

            if (is_a($dn, 'PEAR_Error')) {
                return $dn;
            } else {
                $olddn = $dn;
                $newdn = preg_replace('/uid=.*?,/', 'uid=' . $newID . ',', $dn, 1);
                $shadow = $this->_lookupShadow($dn);

                /* if shadowmin hasn't yet expired only change when we are
                   administrator */
                if ($shadow['shadowlastchange'] && $shadow['shadowmin']) {
                    if ($shadow['shadowlastchange'] + $shadow['shadowmin'] > (time() / 86400)) {
                        return PEAR::raiseError(_("Minimum password age has not yet expired"));
                    }
                }

                /* Set the lastchange field */
                if ($shadow['shadowlastchange']) {
                    $entry['shadowlastchange'] =  floor(time() / 86400);
                }

                /* Encrypt the new password */
                $entry['userpassword'] = $this->getCryptedPassword(
                    $credentials['password'], '',
                    $this->_params['encryption'],
                    'true');
            }
        }

        if ($oldID != $newID) {
            if (LDAP_OPT_PROTOCOL_VERSION == 3) {
                ldap_rename($this->_ds, $olddn, $newdn,
                            $this->_params['basedn'], true);

                $result = ldap_modify($this->_ds, $newdn, $entry);
            } else {
                /* Get the complete old record first */
                $result = @ldap_read($this->_ds, $olddn, 'objectClass=*');

                if ($result) {
                    $information = @ldap_get_entries($this->_ds, $result);

                    /* Remove the count elements from the array */
                    $counter = 0;
                    $newrecord = array();
                    while (isset($information[0][$counter])) {
                        if ($information[0][$information[0][$counter]]['count'] == 1) {
                            $newrecord[$information[0][$counter]] = $information[0][$information[0][$counter]][0];
                        } else {
                            $newrecord[$information[0][$counter]] = $information[0][$information[0][$counter]];
                            unset($newrecord[$information[0][$counter]]['count']);
                        }
                        $counter++;
                    }

                    /* Adjust the changed parameters */
                    unset($newrecord['dn']);
                    $newrecord[$this->_params['uid']] = $newID;
                    $newrecord['userpassword'] = $entry['userpassword'];
                    if (isset($entry['shadowlastchange'])) {
                        $newrecord['shadowlastchange'] = $entry['shadowlastchange'];
                    }

                    $result = ldap_add($this->_ds, $newdn, $newrecord);
                    if ($result) {
                        $result = @ldap_delete($this->_ds, $olddn);
                    }
                }
            }
        } else {
            $result = @ldap_modify($this->_ds, $olddn, $entry);
        }

        if (!$result) {
            return PEAR::raiseError(sprintf(_("Auth_ldap: Unable to update user \"%s\""), $newID));
        }

        @ldap_close($this->_ds);

        return true;
    }

    /**
     * List Users
     *
     * @return array  List of Users
     */
    function listUsers()
    {
        /* Connect to the LDAP server. */
        $result = $this->_connect();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $filter = $this->_getParamFilter();

        if ($this->_params['scope'] == 'one') {
            $func = 'ldap_list';
        } else {
            $func = 'ldap_search';
        }

        /* Add a sizelimit, if specified. Default is 0, which means no limit.
         * Note: You cannot override a server-side limit with this. */
        $sizelimit = isset($this->_params['sizelimit']) ? $this->_params['sizelimit'] : 0;
        $search = @$func($this->_ds, $this->_params['basedn'], $filter,
                         array($this->_params['uid']), 0, $sizelimit);

        $entries = @ldap_get_entries($this->_ds, $search);
        $userlist = array();
        $uid = String::lower($this->_params['uid']);
        for ($i = 0; $i < $entries['count']; $i++) {
            $userlist[$i] = $entries[$i][$uid][0];
        }

        return $userlist;
    }

    /**
     * Return a formatted LDAP filter as configured within the parameters.
     *
     * @return string LDAP search filter
     * @access private
     */
    function _getParamFilter()
    {
        if (!empty($this->_params['filter'])) {
            $filter = $this->_params['filter'];
        } elseif (!is_array($this->_params['objectclass'])) {
            $filter = 'objectclass=' . $this->_params['objectclass'];
        } else {
            $filter = '';
            if (count($this->_params['objectclass']) > 1) {
                $filter = '(&' . $filter;
                foreach ($this->_params['objectclass'] as $objectclass) {
                    $filter .= '(objectclass=' . $objectclass . ')';
                }
                $filter .= ')';
            } elseif (count($this->_params['objectclass']) == 1) {
                $filter = '(objectClass=' . $this->_params['objectclass'][0] . ')';
            }
        }
        return $filter;
    }
}
