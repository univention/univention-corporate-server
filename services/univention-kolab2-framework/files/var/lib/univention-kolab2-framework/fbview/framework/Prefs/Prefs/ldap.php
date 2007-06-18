<?php
/**
 * Preferences storage implementation for PHP's LDAP extention.
 *
 * Required parameters:
 * ====================
 *   'basedn'    --  The base DN for the LDAP server.
 *   'hostspec'  --  The hostname of the LDAP server.
 *   'uid'       --  The username search key.
 *
 * Optional parameters:
 * ====================
 *   'password'  --  'rootdn's password for bind authentication.
 *   'port'      --  The port of the LDAP server.
 *                   DEFAULT: 389
 *   'rootdn'    --  The DN of the root (administrative) account to bind for
 *                   write operations.
 *   'username'  --  TODO
 *   'version'   --  The version of the LDAP protocol to use.
 *                   DEFAULT: NONE (system default will be used)
 *
 * NOTE: parameter 'username' for $params has been deprecated. Use 'rootdn'.
 *
 *
 * If setting up as the Horde preference handler in conf.php, the following
 * is an example configuration.
 * The schemas needed for ldap are in horde/scripts/ldap.
 *
 *   $conf['prefs']['driver'] = 'ldap';
 *   $conf['prefs']['params']['hostspec'] = 'localhost';
 *   $conf['prefs']['params']['port'] = '389';
 *   $conf['prefs']['params']['basedn'] = 'dc=example,dc=org';
 *   $conf['prefs']['params']['uid'] = 'mail';
 *
 * The following is valid but would only be necessary if users
 * do NOT have permission to modify their own LDAP accounts.
 *
 *   $conf['prefs']['params']['rootdn'] = 'cn=Manager,dc=example,dc=org';
 *   $conf['prefs']['params']['password'] = 'password';
 *
 *
 * $Horde: framework/Prefs/Prefs/ldap.php,v 1.84 2004/02/21 17:40:32 chuck Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Prefs
 */
class Prefs_ldap extends Prefs {

    /**
     * Hash containing connection parameters.
     *
     * @var array $params
     */
    var $_params = array();

    /**
     * Handle for the current LDAP connection.
     *
     * @var integer $connection
     */
    var $_connection;

    /**
     * Boolean indicating whether or not we're connected to the LDAP server.
     *
     * @var boolean $_connected
     */
    var $_connected = false;

    /**
     * String holding the user's DN.
     *
     * @var string $dn
     */
    var $_dn = '';


    /**
     * Constructs a new LDAP preferences object.
     *
     * @access public
     *
     * @param string $user               The user who owns these preferences.
     * @param string $password           The password associated with $user.
     * @param string $scope              The current application scope.
     * @param array $params              A hash containing connection
     *                                   parameters.
     * @param optional boolean $caching  Should caching be used?
     */
    function Prefs_ldap($user, $password, $scope = '',
                        $params = array(), $caching = false)
    {
        if (!Util::extensionExists('ldap')) {
            Horde::fatal(PEAR::raiseError(_("Prefs_ldap: Required LDAP extension not found."), __FILE__, __LINE__));
        }

        $this->_user = $user;
        $this->_scope = $scope;
        $this->_params = $params;
        $this->_caching = $caching;

        /* If a valid server port has not been specified, set the default. */
        if (!isset($this->_params['port']) || !is_int($this->_params['port'])) {
            $this->_params['port'] = 389;
        }

        /* If $params['rootdn'] is empty, authenticate as the current user.
           Note: This assumes the user is allowed to modify their own LDAP
                 entry. */
        if (empty($this->_params['username']) &&
            empty($this->_params['rootdn'])) {
            $this->_params['username'] = $user;
            $this->_params['password'] = $password;
        }

        parent::Prefs();
    }

    /**
     * Opens a connection to the LDAP server.
     *
     * @access private
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function _connect()
    {
        /* Return if already connected. */
        if ($this->_connected) {
            return true;
        }

        Horde::assertDriverConfig($this->_params, 'prefs',
            array('hostspec', 'basedn', 'uid', 'rootdn', 'password'),
            'preferences LDAP');

        /* Connect to the LDAP server anonymously. */
        $conn = ldap_connect($this->_params['hostspec'], $this->_params['port']);
        if (!$conn) {
            Horde::logMessage(
                sprintf('Failed to open an LDAP connection to %s.',
                        $this->_params['hostspec']),
                __FILE__, __LINE__);
            return false;
        }

        /* Set the LDAP protocol version. */
        if (isset($this->_params['version'])) {
            if (!ldap_set_option($conn, LDAP_OPT_PROTOCOL_VERSION,
                                 $this->_params['version'])) {
                Horde::logMessage(
                    sprintf('Set LDAP protocol version to %d failed: [%d] %s',
                            $this->_params['version'],
                            ldap_errno($this->_connection),
                            ldap_error($this->_connection)),
                            __FILE__, __LINE__);
            }
        }

        /* Register our callback function to handle referrals. */
        if (function_exists('ldap_set_rebind_proc') &&
            !ldap_set_rebind_proc($conn, array($this, '_rebindProc'))) {
            Horde::logMessage(
                sprintf('Set rebind proc failed: [%d] %s',
                        ldap_errno($this->_connection),
                        ldap_error($this->_connection)),
                __FILE__, __LINE__);
            return false;
        }

        /* Define the DN of the current user */
        $this->_dn = sprintf('%s=%s,%s', $this->_params['uid'],
                            $this->_user,
                            $this->_params['basedn']);

        /* And the DN of the authenticating user (may be the same as above) */
        if (!empty($this->_params['rootdn'])) {
            $bind_dn = $this->_params['rootdn'];
        } else {
            $bind_dn = sprintf('%s=%s,%s', $this->_params['uid'],
                               $this->_params['username'],
                               $this->_params['basedn']);
        }

        /* Store the connection handle at the instance level. */
        $this->_connection = $conn;
        $this->_connected = true;

        /* Bind to the LDAP server as the authenticating user. */
        $bind = @ldap_bind($this->_connection, $bind_dn,
                           $this->_params['password']);
        if (!$bind) {
            Horde::logMessage(
                sprintf('Bind to server %s:%d with DN %s failed: [%d] %s',
                        $this->_params['hostspec'],
                        $this->_params['port'],
                        $bind_dn,
                        ldap_errno($this->_connection),
                        ldap_error($this->_connection)),
                __FILE__, __LINE__);
            return false;
        }

        /* Search for the user's full DN. */
        $search = ldap_search($this->_connection, $this->_params['basedn'],
                              $this->_params['uid'] . '=' . $this->_user,
                              array('dn'));
        if ($search) {
            $result = ldap_get_entries($this->_connection, $search);
            if ($result && !empty($result[0]['dn'])) {
                $this->_dn = $result[0]['dn'];
            }
        } else {
            Horde::logMessage(
                sprintf('Failed to retrieve user\'s DN: [%d] %s',
                        ldap_errno($this->_connection),
                        ldap_error($this->_connection)),
                __FILE__, __LINE__);
            return false;
        }

        return true;
    }

    /**
     * Disconnect from the LDAP server and clean up the connection.
     *
     * @access private
     *
     * @return boolean  True on success, false on failure.
     */
    function _disconnect()
    {
        if ($this->_connected) {
            $this->_dn = '';
            $this->_connected = false;
            return ldap_close($this->_connection);
        } else {
            return true;
        }
    }

    /**
     * Callback function for LDAP referrals.  This function is called when an
     * LDAP operation returns a referral to an alternate server.
     *
     * @access private
     *
     * @return integer  1 on error, 0 on success.
     *
     * @since Horde 2.1
     */
    function _rebindProc($conn, $who)
    {
        /* Strip out the hostname we're being redirected to. */
        $who = preg_replace(array('|^.*://|', '|:\d*$|'), '', $who);

        /* Figure out the DN of the authenticating user. */
        if (!empty($this->_params['rootdn'])) {
            $bind_dn = $this->_params['rootdn'];
        } else {
            $bind_dn = sprintf('%s=%s,%s', $this->_params['uid'],
                               $this->_params['username'],
                               $this->_params['basedn']);
        }

        /* Make sure the server we're being redirected to is in our list of
           valid servers. */
        if (!strstr($this->_params['hostspec'], $who)) {
            Horde::logMessage(
                sprintf('Referral target %s for DN %s is not in the authorized server list!', $who, $bind_dn),
                __FILE__, __LINE__);
            return 1;
        }

        /* Bind to the new server. */
        $bind = @ldap_bind($conn, $bind_dn, $this->_params['password']);
        if (!$bind) {
            Horde::logMessage(
                sprintf('Rebind to server %s:%d with DN %s failed: [%d] %s',
                        $this->_params['hostspec'],
                        $this->_params['port'],
                        $bind_dn,
                        ldap_errno($this->_connection),
                        ldap_error($this->_connection)),
                __FILE__, __LINE__);
        }

        return 0;
    }

    /**
     * Retrieves the requested set of preferences from the user's LDAP
     * entry.
     *
     * @access public
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function retrieve()
    {
        /* Attempt to pull the values from the session cache first. */
        if ($this->cacheLookup()) {
            return true;
        }

        /* Load defaults to make sure we have all preferences. */
        parent::retrieve();

        /* Make sure we are connected. */
        $this->_connect();

        /* Only fetch the fields for the attributes we need. */
        $attrs = array('hordePrefs');
        if (strcmp($this->_scope, 'horde') != 0) {
            array_push($attrs, $this->_scope . 'Prefs');
        }

        /* Search for the multi-valued field containing the array of
           preferences. */
        $search = ldap_search($this->_connection, $this->_params['basedn'],
                              $this->_params['uid'] . '=' . $this->_user, $attrs);
        if ($search) {
            $result = ldap_get_entries($this->_connection, $search);
        } else {
            Horde::logMessage('Failed to connect to LDAP preferences server.', __FILE__, __LINE__);
        }

        /* ldap_get_entries() converts attribute indexes to lowercase. */
        $field = String::lower($this->_scope . 'prefs');

        if (isset($result)) {
            /* Set the requested values in the $this->_prefs hash based on
               the contents of the LDAP result.

               Preferences are stored as colon-separated name:value pairs.
               Each pair is stored as its own attribute off of the multi-
               value attribute named in: $this->_scope . 'Prefs'

               Note that Prefs::setValue() can't be used here because of the
               check for the "changeable" bit.  We want to override that
               check when populating the $this->_prefs hash from the LDAP
               server.
             */

            $prefs = array();

            /* If hordePrefs exists, merge them as the base of the prefs. */
            if (isset($result[0]['hordeprefs'])) {
                $prefs = array_merge($prefs, $result[0]['hordeprefs']);
            }

            /* If this scope's prefs are available, merge them as will.  Give
             * them a higher precedence than hordePrefs. */
            if (strcmp($this->_scope, 'horde') != 0) {
                if (isset($result[0][$field])) {
                    $prefs = array_merge($prefs, $result[0][$field]);
                }
            }

            foreach ($prefs as $prefstr) {
                /* If the string doesn't contain a colon delimiter, skip it. */
                if (substr_count($prefstr, ':') == 0) {
                    continue;
                }

                /* Split the string into its name:value components. */
                list($pref, $val) = split(':', $prefstr, 2);

                /* Retrieve this preference. */
                if (isset($this->_prefs[$pref])) {
                    $this->_setValue($pref, base64_decode($val), false);
                    $this->setDefault($pref, false);
                } else {
                    $this->add($pref, base64_decode($val), _PREF_SHARED);
                }
            }

            /* Make sure we know that we've loaded these
             * preferences. */
            $_SESSION['prefs_cache']['_filled']['horde'] = true;
            $_SESSION['prefs_cache']['_filled'][$this->_scope] = true;

            /* Call hooks. */
            $this->_callHooks();
        } else {
            Horde::logMessage('No preferences were retrieved.', __FILE__, __LINE__);
            return;
        }

        /* Update the session cache. */
        $this->cacheUpdate();

        return true;
    }

    /**
     * Stores preferences to the LDAP server.
     *
     * @access public
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function store()
    {
        $updated = true;

        /* Check for any "dirty" preferences. If no "dirty"
         * preferences are found, there's no need to update the LDAP
         * server. Exit successfully. */
        $dirty_prefs = $this->_dirtyPrefs();
        if (!count($dirty_prefs)) {
            return true;
        }

        /* Make sure we are connected. */
        $this->_connect();

        /* Build a hash of the preferences and their values that need
         * to be stored in the LDAP server. Because we have to update
         * all of the values of a multi-value entry wholesale, we
         * can't just pick out the dirty preferences; we must update
         * everything. */
        $new_values = array();
        foreach (array_keys($this->_prefs) as $pref) {
            // Don't store locked preferences.
            if (!$this->isLocked($pref)) {
                $entry = $pref . ':' . base64_encode($this->getValue($pref));
                $field = $this->getScope($pref) . 'Prefs';
                $new_values[$field][] = $entry;
            }
        }

        /* Entries must have the objectclasses 'top' and 'hordeperson'
         * to successfully store LDAP prefs. Check for both of them,
         * and add them if necessary. */
        $search = ldap_search($this->_connection, $this->_params['basedn'],
                              $this->_params['uid'] . '=' . $this->_user,
                              array('objectclass'));
        if ($search) {
            $result = ldap_get_entries($this->_connection, $search);
            if ($result) {
                $top = false;
                $hordeperson = false;

                for ($i = 0; $i < $result[0]['objectclass']['count']; $i++) {
                    if ($result[0]['objectclass'][$i] == 'top') {
                        $top = true;
                    } elseif ($result[0]['objectclass'][$i] == 'hordePerson') {
                        $hordeperson = true;
                    }
                }

                /* Add any missing objectclasses. */
                if (!$top) {
                    ldap_mod_add($this->_connection, $this->_dn, array('objectclass' => 'top'));
                }

                if (!$hordeperson) {
                    ldap_mod_add($this->_connection, $this->_dn, array('objectclass' => 'hordePerson'));
                }
            }
        }

        /* Send the hash to the LDAP server. */
        if (ldap_mod_replace($this->_connection, $this->_dn, $new_values)) {
            foreach ($dirty_prefs as $pref) {
                $this->setDirty($pref, false);
            }
        } else {
            Horde::logMessage(
               sprintf('Unable to modify preferences: [%d] %s',
                        ldap_errno($this->_connection),
                        ldap_error($this->_connection)),
                __FILE__, __LINE__);
            $updated = false;
        }

        /* Attempt to cache the preferences in the session. */
        $this->cacheUpdate();

        return $updated;
    }

    /**
     * Perform cleanup operations.
     *
     * @access public
     *
     * @param optional boolean $all  Cleanup all Horde preferences.
     */
    function cleanup($all = false)
    {
        /* Close the LDAP connection. */
        $this->_disconnect();

        parent::cleanup($all);
    }

}
