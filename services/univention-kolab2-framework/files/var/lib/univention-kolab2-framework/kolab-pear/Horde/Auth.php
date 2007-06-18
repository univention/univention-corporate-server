<?php
/** @const string AUTH_REASON_PARAM  The parameter name for the logout reason. */
define('AUTH_REASON_PARAM', 'logout_reason');

/** @const string AUTH_REASON_PARAM  The parameter name for the logout message used with type AUTH_REASON_MESSAGE. */
define('AUTH_REASON_MSG_PARAM', 'logout_msg');

/*
 * The following 'reasons' for the logout screen are recognized:
 *   'badlogin'   --  Bad username and/or password
 *   'browser'    --  A browser change was detected
 *   'failed'     --  Login failed
 *   'logout'     --  Logout due to user request
 *   'message'    --  Logout with custom message in AUTH_REASON_MSG_PARAM
 *   'session'    --  Logout due to session expiration
 *   'sessionip'  --  Logout due to change of IP address during session
 */
/** @const string AUTH_REASON_BADLOGIN  The 'badlogin' reason. */
define('AUTH_REASON_BADLOGIN', 'badlogin');

/** @const string AUTH_REASON_BROWSER  The 'browser' reason. */
define('AUTH_REASON_BROWSER', 'browser');

/** @const string AUTH_REASON_FAILED  The 'failed' reason. */
define('AUTH_REASON_FAILED', 'failed');

/** @const string AUTH_REASON_LOGOUT  The 'logout' reason. */
define('AUTH_REASON_LOGOUT', 'logout');

/** @const string AUTH_REASON_MESSAGE  The 'message' reason. */
define('AUTH_REASON_MESSAGE', 'message');

/** @const string AUTH_REASON_SESSION  The 'session' reason. */
define('AUTH_REASON_SESSION', 'session');

/** @const string AUTH_REASON_SESSIONIP  The 'sessionip' reason. */
define('AUTH_REASON_SESSIONIP', 'sessionip');

/**
 * The Auth:: class provides a common abstracted interface into the
 * various backends for the Horde authentication system.
 *
 * $Horde: framework/Auth/Auth.php,v 1.129 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     * @var array $capabilities
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => false,
                              'groups'        => false,
                              'transparent'   => false);

   /**
    * Hash containing parameters.
    *
    * @var array $_params
    */
    var $_params = array();

    /**
     * The credentials currently being authenticated.
     *
     * @access protected
     *
     * @var array $_authCredentials
     */
    var $_authCredentials = array();

    /**
     * Returns the name of the concrete Auth implementation.
     *
     * @return string  The Auth implementation name.
     */
    function getDriver()
    {
        return str_replace('auth_', '', get_class($this));
    }

    /**
     * Find out if a set of login credentials are valid, and if
     * requested, mark the user as logged in in the current session.
     *
     * @access public
     *
     * @param string $userId           The userId to check.
     * @param array $credentials       The credentials to check.
     * @param optional boolean $login  Whether to log the user in. If false,
     *                                 we'll only test the credentials and
     *                                 won't modify the current session.
     *                                 Defaults to true.
     * @param optional string $realm   The authentication realm to check.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function authenticate($userId, $credentials, $login = true, $realm = null)
    {
        global $conf;

        $auth = false;
        $userId = trim($userId);

        if (!empty($conf['hooks']['preauthenticate'])) {
            include_once HORDE_BASE . '/config/hooks.php';
            if (function_exists('_horde_hook_preauthenticate')) {
                if (!call_user_func('_horde_hook_preauthenticate', $userId, $credentials, $realm)) {
                    $this->_setAuthError(AUTH_REASON_FAILED);
                    return false;
                }
            }
        }

        /* Store the credentials being checked so that subclasses can
         * modify them if necessary (like transparent auth does). */
        $this->_authCredentials = array(
            'userId' => $userId,
            'credentials' => $credentials,
            'realm' => $realm
        );

        if ($this->_authenticate($userId, $credentials)) {
            if ($login) {
                $this->setAuth($this->_authCredentials['userId'],
                               $this->_authCredentials['credentials'],
                               $this->_authCredentials['realm']);
                $auth = true;
            } else {
                if (!$this->_checkSessionIP()) {
                    $this->_setAuthError(AUTH_REASON_SESSIONIP);
                    return false;
                } elseif (!$this->_checkBrowserString()) {
                    $this->_setAuthError(AUTH_REASON_BROWSER);
                    return false;
                }
                $auth = true;
            }
        }

        if (!empty($conf['hooks']['postauthenticate'])) {
            include_once HORDE_BASE . '/config/hooks.php';
            if (function_exists('_horde_hook_postauthenticate')) {
                if (!call_user_func('_horde_hook_postauthenticate', $userId, $credentials, $realm)) {
                    $this->_setAuthError(AUTH_REASON_FAILED);
                    return false;
                }
            }
        }

        return $auth;
    }

    /**
     * Format a password using the current encryption.
     *
     * @access public
     *
     * @param string $plaintext               The plaintext password to
     *                                        encrypt.
     * @param optional string $salt           The salt to use to encrypt the
     *                                        password. If not present, a new
     *                                        salt will be generated.
     * @param optional string $encryption     The kind of pasword encryption
     *                                        to use. Defaults to md5-hex.
     * @param optional boolean $show_encrypt  Some password systems prepend
     *                                        the kind of encryption to the
     *                                        crypted password ({SHA}, etc).
     *                                        Defaults to false.
     *
     * @return string  The encrypted password.
     */
    function getCryptedPassword($plaintext, $salt = '',
                                $encryption = 'md5-hex', $show_encrypt = false)
    {
        /* Get the salt to use. */
        $salt = Auth::getSalt($encryption, $salt, $plaintext);

        /* Encrypt the password. */
        switch ($encryption) {
        case 'plain':
            return $plaintext;

        case 'msad':
            return String::convertCharset('"' . $plaintext . '"', 'ISO-8859-1', 'UTF-16LE');

        case 'sha':
            $encrypted = base64_encode(mhash(MHASH_SHA1, $plaintext));
            return ($show_encrypt) ? '{SHA}' . $encrypted : $encrypted;

        case 'crypt':
        case 'crypt-des':
        case 'crypt-md5':
        case 'crypt-blowfish':
            return (($show_encrypt) ? '{crypt}' : '') . crypt($plaintext, $salt);

        case 'md5-base64':
            $encrypted = base64_encode(mhash(MHASH_MD5, $plaintext));
            return ($show_encrypt) ? '{MD5}' . $encrypted : $encrypted;

        case 'ssha':
            $encrypted = base64_encode(mhash(MHASH_SHA1, $plaintext . $salt) . $salt);
            return ($show_encrypt) ? '{SSHA}' . $encrypted : $encrypted;

        case 'smd5':
            $encrypted = base64_encode(mhash(MHASH_SMD5, $plaintext . $salt) . $salt);
            return ($show_encrypt) ? '{SMD5}' . $encrypted : $encrypted;

        case 'aprmd5':
            $length = strlen($plaintext);
            $context = $plaintext . '$apr1$' . $salt;
            $binary = Auth::_bin(md5($plaintext . $salt . $plaintext));

            for ($i = $length; $i > 0; $i -= 16) {
                $context .= substr($binary, 0, ($i > 16 ? 16 : $i));
            }
            for ($i = $length; $i > 0; $i >>= 1) {
                $context .= ($i & 1) ? chr(0) : $plaintext{0};
            }

            $binary = Auth::_bin(md5($context));

            for ($i = 0; $i < 1000; $i++) {
                $new = ($i & 1) ? $plaintext : substr($binary, 0,16);
                if ($i % 3) {
                    $new .= $salt;
                }
                if ($i % 7) {
                    $new .= $plaintext;
                }
                $new .= ($i & 1) ? substr($binary, 0, 16) : $plaintext;
                $binary = Auth::_bin(md5($new));
            }

            $p = array();
            for ($i = 0; $i < 5; $i++) {
                $k = $i + 6;
                $j = $i + 12;
                if ($j == 16) {
                    $j = 5;
                }
                $p[] = Auth::_toAPRMD5((ord($binary[$i]) << 16) |
                                       (ord($binary[$k]) << 8) |
                                       (ord($binary[$j])),
                                       5);
            }

            return '$apr1$' . $salt . '$' . implode($p) . Auth::_toAPRMD5(ord($binary[11]), 3);

        case 'md5-hex':
        default:
            return ($show_encrypt) ? '{MD5}' . md5($plaintext) : md5($plaintext);
        }
    }

    /**
     * Get a salt for the appropriate kind of password
     * encryption. Optionally takes a seed and a plaintext password,
     * to extract the seed of an existing password, or for encryption
     * types that use the plaintext in the generation of the salt.
     *
     * @access public
     *
     * @param optional string $encryption  The kind of pasword encryption to
     *                                     use. Defaults to md5-hex.
     * @param optional string $seed        The seed to get the salt from
     *                                     (probably a previously generated
     *                                     password). Defaults to generating
     *                                     a new seed.
     * @param optional string $plaintext   The plaintext password that we're
     *                                     generating a salt for. Defaults to
     *                                     none.
     *
     * @return string  The generated or extracted salt.
     */
    function getSalt($encryption = 'md5-hex', $seed = '', $plaintext = '')
    {
        // Encrypt the password.
        switch ($encryption) {
        case 'crypt':
        case 'crypt-des':
            if ($seed) {
                return substr(preg_replace('|^{crypt}|', '', $seed), 0, 2);
            } else {
                return substr(md5(mt_rand()), 0, 2);
            }

        case 'crypt-md5':
            if ($seed) {
                return substr(preg_replace('|^{crypt}|', '', $seed), 0, 12);
            } else {
                return '$1$' . substr(md5(mt_rand()), 0, 8) . '$';
            }

        case 'crypt-blowfish':
            if ($seed) {
                return substr(preg_replace('|^{crypt}|', '', $seed), 0, 16);
            } else {
                return '$2$' . substr(md5(mt_rand()), 0, 12) . '$';
            }

        case 'ssha':
            if ($seed) {
                return substr(preg_replace('|^{SSHA}|', '', $seed), -20);
            } else {
                return mhash_keygen_s2k(MHASH_SHA1, $plaintext, substr(pack('h*', md5(mt_rand())), 0, 8), 4);
            }

        case 'smd5':
            if ($seed) {
                return substr(preg_replace('|^{SMD5}|', '', $seed), -16);
            } else {
                return mhash_keygen_s2k(MHASH_MD5, $plaintext, substr(pack('h*', md5(mt_rand())), 0, 8), 4);
            }

        case 'aprmd5':
            /**
             * 64 characters that are valid for APRMD5 passwords.
             * @var string $_APRMD5
             */
            $APRMD5 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';

            if ($seed) {
                return substr(preg_replace('/^\$apr1\$(.{8}).*/', '\\1', $seed), 0, 8);
            } else {
                $salt = '';
                for ($i = 0; $i < 8; $i++) {
                    $salt .= $APRMD5{rand(0, 63)};
                }
                return $salt;
            }

        default:
            return '';
        }
    }

    /**
     * Generates a random, hopefully pronounceable, password. This can be used
     * when resetting automatically a user's password.
     */
    function genRandomPassword()
    {
        $vowels     ='aeiouy';
        $constants  ='bcdfghjklmnpqrstvwxz';
        $numbers    ='0123456789';

        /* Alternate constant and vowel random chars with two random numbers
         * at the end. This should produce a fairly pronounceable password. */
        $chars[0] = substr($constants, mt_rand(0, strlen($constants) - 1), 1);
        $chars[1] = substr($vowels, mt_rand(0, strlen($vowels) - 1), 1);
        $chars[2] = substr($constants, mt_rand(0, strlen($constants) - 1), 1);
        $chars[3] = substr($vowels, mt_rand(0, strlen($vowels) - 1), 1);
        $chars[4] = substr($constants, mt_rand(0, strlen($constants) - 1), 1);
        $chars[5] = substr($numbers, mt_rand(0, strlen($numbers) - 1), 1);
        $chars[6] = substr($numbers, mt_rand(0, strlen($numbers) - 1), 1);

        return implode('', $chars);
    }

    /**
     * Add a set of authentication credentials.
     *
     * @access public
     * @abstract
     *
     * @param string $userId      The userId to add.
     * @param array $credentials  The credentials to use.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function addUser($userId, $credentials)
    {
        return PEAR::raiseError('unsupported');
    }

    /**
     * Update a set of authentication credentials.
     *
     * @access public
     * @abstract
     *
     * @param string $oldID        The old userId.
     * @param string $newID        The new userId.
     * @param array  $credentials  The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        return PEAR::raiseError('unsupported');
    }

    /**
     * Delete a set of authentication credentials.
     *
     * @access public
     * @abstract
     *
     * @param string $userId  The userId to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUser($userId)
    {
        return PEAR::raiseError('unsupported');
    }

    /**
     * List all users in the system.
     *
     * @access public
     * @abstract
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        return PEAR::raiseError('unsupported');
    }

    /**
     * Checks if $userId exists in the system.
     *
     * @access public
     * @abstract
     *
     * @return boolean  Whether or not $userId already exists.
     */
    function exists($userId)
    {
        return in_array($userId, $this->listUsers());
    }

    /**
     * Automatic authentication: Find out if the client matches an
     * allowed IP block.
     *
     * @access public
     * @abstract
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        return false;
    }

    /**
     * Checks if there is a session with valid auth information. for
     * the specified user. If there isn't, but the configured Auth
     * driver supports transparent authentication, then we try that.
     *
     * @access public
     *
     * @param optional string $realm   The authentication realm to check.
     *
     * @return boolean  Whether or not the user is authenticated.
     */
    function isAuthenticated($realm = null)
    {
        if (isset($_SESSION['__auth'])) {
            if (!empty($_SESSION['__auth']['authenticated']) &&
                !empty($_SESSION['__auth']['userId']) &&
                ($_SESSION['__auth']['realm'] == $realm)) {
                if (!Auth::_checkSessionIP()) {
                    Auth::_setAuthError(AUTH_REASON_SESSIONIP);
                    return false;
                } elseif (!Auth::_checkBrowserString()) {
                    Auth::_setAuthError(AUTH_REASON_BROWSER);
                    return false;
                } else {
                    return true;
                }
            }
        }

        // Try transparent authentication now.
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        if ($auth->hasCapability('transparent') &&
            $auth->transparent()) {
            return Auth::isAuthenticated($realm);
        }

        return false;
    }

    /**
     * Return the currently logged in user, if there is one.
     *
     * @access public
     *
     * @return mixed  The userId of the current user, or false if no user is
     *                logged in.
     */
    function getAuth()
    {
        if (isset($_SESSION['__auth'])) {
            if (!empty($_SESSION['__auth']['authenticated']) &&
                !empty($_SESSION['__auth']['userId'])) {
                return $_SESSION['__auth']['userId'];
            }
        }

        return false;
    }

    /**
     * Return the curently logged-in user without any domain
     * information (e.g., bob@example.com would be returned as 'bob').
     *
     * @access public
     *
     * @return mixed  The user ID of the current user, or false if no user
     *                is logged in.
     */
    function getBareAuth()
    {
        $user = Auth::getAuth();
        if ($user) {
            $pos = strpos($user, '@');
            if ($pos !== false) {
                $user = substr($user, 0, $pos);
            }
        }

        return $user;
    }

    /**
     * Return the requested credential for the currently logged in
     * user, if present.
     *
     * @access public
     *
     * @param string $credential  The credential to retrieve.
     *
     * @return mixed  The requested credential, or false if no user is
     *                logged in.
     */
    function getCredential($credential)
    {
        if (!empty($_SESSION['__auth']) &&
            !empty($_SESSION['__auth']['authenticated'])) {
            require_once 'Horde/Secret.php';
            $credentials = @unserialize(Secret::read(Secret::getKey('auth'), $_SESSION['__auth']['credentials']));
        } else {
            return false;
        }

        if (is_array($credentials) &&
            isset($credentials[$credential])) {
            return $credentials[$credential];
        } else {
            return false;
        }
    }

    /**
     * Set the requested credential for the currently logged in user.
     *
     * @access public
     *
     * @param string $credential  The credential to set.
     * @param string $value       The value to set the credential to.
     */
    function setCredential($credential, $value)
    {
        if (!empty($_SESSION['__auth']) &&
            !empty($_SESSION['__auth']['authenticated'])) {
            require_once 'Horde/Secret.php';
            $credentials = @unserialize(Secret::read(Secret::getKey('auth'), $_SESSION['__auth']['credentials']));
            if (is_array($credentials)) {
                $credentials[$credential] = $value;
            } else {
                $credentials = array($credential => $value);
            }
            $_SESSION['__auth']['credentials'] = Secret::write(Secret::getKey('auth'), serialize($credentials));
        }
    }

    /**
     * Set a variable in the session saying that authorization has
     * succeeded, note which userId was authorized, and note when the
     * login took place.
     *
     * If a user name hook was defined in the configuration, it gets
     * applied to the userId at this point.
     *
     * @access public
     *
     * @param          string $userId       The userId who has been authorized.
     * @param          array  $credentials  The credentials of the user.
     * @param optional string $realm        The authentication realm to use.
     */
    function setAuth($userId, $credentials, $realm = null)
    {
        $userId = trim($userId);
        $userId = Auth::addHook($userId);

        /* If we're already set with this userId, don't continue. */
        if (isset($_SESSION['__auth']['userId']) &&
            $_SESSION['__auth']['userId'] == $userId) {
            return;
        }

        /* Clear any existing info. */
        $this->clearAuth($realm);

        require_once 'Horde/Secret.php';
        $credentials = Secret::write(Secret::getKey('auth'), serialize($credentials));

        if (!empty($realm)) {
            $userId .= '@' . $realm;
        }

        $_SESSION['__auth'] = array(
            'authenticated' => true,
            'userId' => $userId,
            'credentials' => $credentials,
            'realm' => $realm,
            'timestamp' => time(),
            'remote_addr' => $_SERVER['REMOTE_ADDR'],
            'browser' => $GLOBALS['browser']->getAgentString()
        );

        /* Reload preferences for the new user. */
        $GLOBALS['registry']->loadPrefs();
        global $prefs;

        /* Display user's last login time if requested. */
        $old_login = @unserialize($prefs->getValue('last_login'));
        if ($prefs->getValue('show_last_login')) {
            global $notification;
            if (empty($old_login['time'])) {
                $notification->push(_("Last login: Never"), 'horde.message');
            } else {
                if (empty($old_login['host'])) {
                    $notification->push(sprintf(_("Last login: %s"), strftime('%c', $old_login['time'])), 'horde.message');
                } else {
                    $notification->push(sprintf(_("Last login: %s from %s"), strftime('%c', $old_login['time']), $old_login['host']), 'horde.message');
                }
            }
        }
        if (!empty($old_login['time'])) {
            $_SESSION['__auth']['last_login'] = $old_login['time'];
        }

        // Set the user's last_login information.
        $last_login['time'] = time();
        $last_login['host'] = @gethostbyaddr($_SERVER['REMOTE_ADDR']);
        $prefs->setValue('last_login', serialize($last_login));
    }

    /**
     * Clear any authentication tokens in the current session.
     *
     * @access public
     *
     * @param optional string $realm  The authentication realm to clear.
     */
    function clearAuth($realm = null)
    {
        if (!empty($realm) && isset($_SESSION['__auth'][$realm])) {
            $_SESSION['__auth'][$realm] = array();
            $_SESSION['__auth'][$realm]['authenticated'] = false;
        } elseif (isset($_SESSION['__auth'])) {
            $_SESSION['__auth'] = array();
            $_SESSION['__auth']['authenticated'] = false;
        }
    }

    /**
     * Is the current user an administrator?
     *
     * @access public
     *
     * @param string $permission  (optional) Allow users with this permission
     *                            admin access in the current context.
     * @param integer $permlevel  (optional) The level of permissions to check for
     *                            (PERMS_EDIT, PERMS_DELETE, etc). Defaults
     *                            to PERMS_EDIT.
     * @param string $user        The user to check. Defaults to Auth::getAuth().
     *
     * @return boolean  Whether or not this is an admin user.
     *
     * @since Horde 2.2
     */
    function isAdmin($permission = null, $permlevel = null, $user = null)
    {
        global $conf;

        if ($user === null) {
            $user = Auth::getAuth();
        }

        if (@is_array($conf['auth']['admins'])) {
            if ($user && in_array($user, $conf['auth']['admins'])) {
                return true;
            }
        }

        if (!is_null($permission)) {
            if (is_null($permlevel)) {
                $permlevel = PERMS_EDIT;
            }
            return $GLOBALS['perms']->hasPermission($permission, $user, $permlevel);
        }

        return false;
    }

    /**
     * Applies a hook defined by the function
     * _username_hook_frombackend() to the given user name if this
     * function exists and user hooks are enabled.
     *
     * This method should be called if a backend's user name needs to
     * be converted to a (unique) Horde user name.
     *
     * @param string $userId  The original user name.
     *
     * @return string  The user name with the hook applied to it.
     */
    function addHook($userId)
    {
        global $conf;

        if (!empty($conf['hooks']['username'])) {
            require_once HORDE_BASE . '/config/hooks.php';
            if (function_exists('_username_hook_frombackend')) {
                $userId = call_user_func('_username_hook_frombackend', $userId);
            }
        }

        return $userId;
    }

    /**
     * Applies a hook defined by the function
     * _username_hook_tobackend() to the given user name if this
     * function exists and user hooks are enabled.
     *
     * This method should be called if a Horde user name needs to be
     * converted to a backend's user name or displayed to the user.
     *
     * @param string $userId  The Horde user name.
     *
     * @return string  The user name with the hook applied to it.
     */
    function removeHook($userId)
    {
        global $conf;

        if (!empty($conf['hooks']['username'])) {
            require_once HORDE_BASE . '/config/hooks.php';
            if (function_exists('_username_hook_tobackend')) {
                $userId = call_user_func('_username_hook_tobackend', $userId);
            }
        }

        return $userId;
    }

    /**
     * Query the current Auth object to find out if it supports the
     * given capability.
     *
     * @access public
     *
     * @param string $capability  The capability to test for.
     * @return boolean            Whether or not the capability is supported.
     */
    function hasCapability($capability)
    {
        return !empty($this->capabilities[$capability]);
    }

    /**
     * Return the URI of the login screen for the current
     * authentication method.
     *
     * @access public
     *
     * @param optional string $app  The application to use.
     * @param optional string $url  The URL to redirect to after login.
     *
     * @return string  The login screen URI.
     */
    function getLoginScreen($app = 'horde', $url = '')
    {
        global $conf;
        $auth = &Auth::singleton($conf['auth']['driver']);
        return $auth->_getLoginScreen($app, $url);
    }

    /**
     * Return the named parameter for the current auth driver.
     *
     * @access public
     *
     * @param string $param  The parameter to fetch.
     *
     * @return string  The parameter's value.
     */
    function getParam($param)
    {
        return isset($this->_params[$param]) ? $this->_params[$param] : null;
    }

    /**
     * Return the name of the authentication provider.
     *
     * @access public
     *
     * @param optional string $driver  Used by recursive calls when untangling composite auth.
     * @param optional array  $params  Used by recursive calls when untangling composite auth.
     *
     * @return string  The name of the driver currently providing authentication.
     */
    function getProvider($driver = null, $params = null)
    {
        global $conf;

        if (is_null($driver)) {
            $driver = $conf['auth']['driver'];
        }
        if (is_null($params)) {
            $params = Horde::getDriverConfig('auth',
                is_array($driver) ? $driver[1] : $driver);
        }

        if ($driver == 'application') {
            return isset($params['app']) ? $params['app'] : 'application';
        } elseif ($driver == 'composite') {
            if (($login_driver = Auth::_getDriverByParam('loginscreen_switch', $params)) &&
                !empty($params['drivers'][$login_driver])) {
                return Auth::getProvider($params['drivers'][$login_driver]['driver'],
                                         isset($params['drivers'][$login_driver]['params']) ? $params['drivers'][$login_driver]['params'] : null);
            }
            return 'composite';
        } else {
            return $driver;
        }
    }

    /**
     * Get the logout reason.
     *
     * @access public
     *
     * @return string  One of the logout reasons (see the AUTH_LOGOUT_*
     *                 constants for the valid reasons).  Returns null if
     *                 there is no logout reason present.
     */
    function getLogoutReason()
    {
        if (isset($GLOBALS['__autherror']['type'])) {
            return $GLOBALS['__autherror']['type'];
        } else {
            return Util::getFormData(AUTH_REASON_PARAM);
        }
    }

    /**
     * Get the status string to use for logout messages.
     *
     * @access public
     *
     * @return string  The logout reason string.
     */
    function getLogoutReasonString()
    {
        switch (Auth::getLogoutReason()) {
        case AUTH_REASON_SESSION:
            $text = sprintf(_("Your %s session has expired. Please login again."), $GLOBALS['registry']->getParam('name'));
            break;

        case AUTH_REASON_SESSIONIP:
            $text = sprintf(_("Your Internet Address has changed since the beginning of your %s session. To protect your security, you must login again."), $GLOBALS['registry']->getParam('name'));
            break;

        case AUTH_REASON_BROWSER:
            $text = sprintf(_("Your browser appears to have changed since the beginning of your %s session. To protect your security, you must login again."), $GLOBALS['registry']->getParam('name'));
            break;

        case AUTH_REASON_LOGOUT:
            $text = _("You have been logged out.") . '<br />' . _("Thank you for using the system.");
            break;

        case AUTH_REASON_FAILED:
            $text = _("Login failed.");
            break;

        case AUTH_REASON_BADLOGIN:
            $text = _("Login failed because your username or password was entered incorrectly.");
            break;

        case AUTH_REASON_MESSAGE:
            if (isset($GLOBALS['__autherror']['msg'])) {
                $text = $GLOBALS['__autherror']['msg'];
            } else {
                $text = Util::getFormData(AUTH_REASON_MSG_PARAM);
            }
            break;

        default:
            $text = '';
            break;
        }

        return $text;
    }

    /**
     * Generate the correct parameters to pass to the given logout URL.
     * If no reason/msg is passed in, use the current global authentication
     * error message.
     *
     * @access public
     *
     * @param string $url              The URL to redirect to.
     * @param optional string $reason  The reason for logout.
     * @param optional string $msg     If reason is AUTH_REASON_MESSAGE, the
     *                                 message to display to the user.
     */
    function addLogoutParameters($url, $reason = null, $msg = null)
    {
        if (is_null($reason)) {
            $reason = Auth::getLogoutReason();
        }

        if ($reason) {
            $url = Util::addParameter($url, AUTH_REASON_PARAM, $reason);
            if ($reason == AUTH_REASON_MESSAGE) {
                if (is_null($msg)) {
                    $msg = Auth::getLogoutReasonString();
                }
                $url = Util::addParameter($url, AUTH_REASON_MSG_PARAM, $msg);
            }
        }

        return $url;
    }

    /**
     * Return the URI of the login screen for this authentication
     * object.
     *
     * @access private
     *
     * @param optional string $app  The application to use.
     * @param optional string $url  The URL to redirect to after login.
     *
     * @return string  The login screen URI.
     */
    function _getLoginScreen($app = 'horde', $url = '')
    {
        $login = Horde::url($GLOBALS['registry']->getParam('webroot', $app) . '/login.php', true);
        if (!empty($url)) {
            $login = Util::addParameter($login, 'url', $url);
        }
        return $login;
    }

    /**
     * Authentication stub.
     *
     * @access private
     * @abstract
     *
     * @return boolean  False.
     */
    function _authenticate()
    {
        return false;
    }

    /**
     * Sets the error message for an invalid authentication.
     *
     * @access private
     *
     * @param string $type          The type of error (AUTH_REASON constant).
     * @param optional string $msg  The error message/reason for invalid
     *                              authentication.
     */
    function _setAuthError($type, $msg = null)
    {
        $GLOBALS['__autherror'] = array();
        $GLOBALS['__autherror']['type'] = $type;
        $GLOBALS['__autherror']['msg'] = $msg;
    }

    /**
     * Return the appropriate authentication driver, if any, selecting
     * by the specified parameter.
     *
     * @access private
     *
     * @param string $name                   The parameter name.
     * @param array $params                  The parameter list.
     * @param optional string $driverparams  A list of parameters to pass to
     *                                       the driver.
     */
    function _getDriverByParam($name, $params, $driverparams = array())
    {
        if (isset($params[$name]) &&
            function_exists($params[$name])) {
            return call_user_func_array($params[$name], $driverparams);
        }

        return null;
    }

    /**
     * Perform check on session to see if IP Address has changed since the
     * last access.
     *
     * @access private
     *
     * @return boolean  True if IP Address is the same (or the check is
     *                  disabled), false if the address has changed.
     */
    function _checkSessionIP()
    {
        return (empty($GLOBALS['conf']['auth']['checkip']) ||
                (isset($_SESSION['__auth']['remote_addr']) && $_SESSION['__auth']['remote_addr'] == $_SERVER['REMOTE_ADDR']));
    }

    /**
     * Perform check on session to see if browser string has changed since
     * the last access.
     *
     * @access private
     *
     * @return boolean  True if browser string is the same, false if the
     *                  string has changed.
     */
    function _checkBrowserString()
    {
        return ($_SESSION['__auth']['browser'] == $GLOBALS['browser']->getAgentString());
    }

    /**
     * Convert to allowed 64 characters for APRMD5 passwords.
     *
     * @access private
     *
     * @param string  $value
     * @param integer $count
     *
     * @return string  $value converted to the 64 MD5 characters.
     */
    function _toAPRMD5($value, $count)
    {
        /**
         * 64 characters that are valid for APRMD5 passwords.
         * @var string $_APRMD5
         */
        $APRMD5 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';

        $aprmd5 = '';
        $count = abs($count);
        while (--$count) {
            $aprmd5 .= $APRMD5[$value & 0x3f];
            $value >>= 6;
        }
        return $aprmd5;
    }

    /**
     * Convert hexadecimal string to binary data.
     * @access private
     *
     * @param string $hex  Hex data.
     *
     * @return string  Binary data.
     */
    function _bin($hex)
    {
        $bin = '';
        $length = strlen($hex);
        for ($i = 0; $i < $length; $i += 2) {
            $bin .= chr(array_shift(sscanf(substr($hex, $i, 2), '%x')));
        }
        return $bin;
    }

    /**
     * Attempts to return a concrete Auth instance based on $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Auth subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is dynamically
     *                                included. If $driver is an array, then we
     *                                will look in $driver[0]/lib/Auth/ for
     *                                the subclass implementation named
     *                                $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Auth   The newly created concrete Auth instance, or false
     *                       on an error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);

        if (empty($driver) || ($driver == 'none')) {
            return $auth = &new Auth();
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('auth', $driver);
        }

        ini_set('track_errors', 1);
        $include_error = '';
        if (!empty($app)) {
            @include_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Auth/' . $driver . '.php';
        } else {
            @include_once 'Horde/Auth/' . $driver . '.php';
        }
        if (isset($php_errormsg)) {
            $include_error = $php_errormsg;
        }
        ini_restore('track_errors');

        $class = 'Auth_' . $driver;
        if (class_exists($class)) {
            return $auth = &new $class($params);
        } else {
            return PEAR::raiseError('Auth Driver (' . $class . ') not found' . ($include_error ? ': ' . $include_error : '') . '.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Auth instance
     * based on $driver. It will only create a new instance if no Auth
     * instance with the same parameters currently exists.
     *
     * This should be used if multiple authentication sources (and,
     * thus, multiple Auth instances) are required.
     *
     * This method must be invoked as: $var = &Auth::singleton()
     *
     * @access public
     *
     * @param string $driver          The type of concrete Auth subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is dynamically
     *                                included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Auth  The concrete Auth reference, or false on an error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

        if (is_null($params)) {
            $params = Horde::getDriverConfig('auth',
                is_array($driver) ? $driver[1] : $driver);
        }

        $signature = serialize(array($driver, $params));
        if (empty($instances[$signature])) {
            $instances[$signature] = &Auth::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
