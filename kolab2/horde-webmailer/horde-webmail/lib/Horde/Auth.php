<?php
/**
 * The parameter name for the logout reason.
 */
define('AUTH_REASON_PARAM', 'logout_reason');

/**
 * The parameter name for the logout message used with type
 * AUTH_REASON_MESSAGE.
 */
define('AUTH_REASON_MSG_PARAM', 'logout_msg');

/**
 * The 'badlogin' reason.
 *
 * The following 'reasons' for the logout screen are recognized:
 * <pre>
 *   'badlogin'   --  Bad username and/or password
 *   'browser'    --  A browser change was detected
 *   'failed'     --  Login failed
 *   'expired'    --  Password has expired
 *   'logout'     --  Logout due to user request
 *   'message'    --  Logout with custom message in AUTH_REASON_MSG_PARAM
 *   'session'    --  Logout due to session expiration
 *   'sessionip'  --  Logout due to change of IP address during session
 * </pre>
 */
define('AUTH_REASON_BADLOGIN', 'badlogin');

/**
 * The 'browser' reason.
 */
define('AUTH_REASON_BROWSER', 'browser');

/**
 * The 'failed' reason.
 */
define('AUTH_REASON_FAILED', 'failed');

/**
 * The 'expired' reason.
 */
define('AUTH_REASON_EXPIRED', 'expired');

/**
 * The 'logout' reason.
 */
define('AUTH_REASON_LOGOUT', 'logout');

/**
 * The 'message' reason.
 */
define('AUTH_REASON_MESSAGE', 'message');

/**
 * The 'session' reason.
 */
define('AUTH_REASON_SESSION', 'session');

/**
 * The 'sessionip' reason.
 */
define('AUTH_REASON_SESSIONIP', 'sessionip');

/**
 * The Auth:: class provides a common abstracted interface into the various
 * backends for the Horde authentication system.
 *
 * $Horde: framework/Auth/Auth.php,v 1.142.10.37 2009-10-26 11:58:58 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 1.3
 * @package Horde_Auth
 */
class Auth {

    /**
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => false,
                              'groups'        => false,
                              'admins'        => false,
                              'transparent'   => false);

    /**
     * Hash containing parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The credentials currently being authenticated.
     *
     * @access protected
     *
     * @var array
     */
    var $_authCredentials = array();

    /**
     * Returns the name of the concrete Auth implementation.
     *
     * @return string  The Auth implementation name.
     */
    function getDriver()
    {
        return str_replace('auth_', '', strtolower(get_class($this)));
    }

    /**
     * Finds out if a set of login credentials are valid, and if requested,
     * mark the user as logged in in the current session.
     *
     * @param string $userId      The userId to check.
     * @param array $credentials  The credentials to check.
     * @param boolean $login      Whether to log the user in. If false, we'll
     *                            only test the credentials and won't modify
     *                            the current session. Defaults to true.
     * @param string $realm       The authentication realm to check.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function authenticate($userId, $credentials, $login = true, $realm = null)
    {
        $auth = false;
        $userId = trim($userId);

        if (!empty($GLOBALS['conf']['hooks']['preauthenticate'])) {
            if (!Horde::callHook('_horde_hook_preauthenticate', array($userId, $credentials, $realm), 'horde', false)) {
                if ($this->_getAuthError() != AUTH_REASON_MESSAGE) {
                    $this->_setAuthError(AUTH_REASON_FAILED);
                }
                return false;
            }
        }

        /* Store the credentials being checked so that subclasses can modify
         * them if necessary (like transparent auth does). */
        $this->_authCredentials = array(
            'userId' => $userId,
            'credentials' => $credentials,
            'realm' => $realm,
            'changeRequested' => false
        );

        if ($authenticated = $this->_authenticate($userId, $credentials)) {
            if (is_a($authenticated, 'PEAR_Error')) {
                return false;
            }

            if ($login) {
                $auth = $this->setAuth(
                    $this->_authCredentials['userId'],
                    $this->_authCredentials['credentials'],
                    $this->_authCredentials['realm'],
                    $this->_authCredentials['changeRequested']);
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

        return $auth;
    }

    /**
     * Formats a password using the current encryption.
     *
     * @param string $plaintext      The plaintext password to encrypt.
     * @param string $salt           The salt to use to encrypt the password.
     *                               If not present, a new salt will be
     *                               generated.
     * @param string $encryption     The kind of pasword encryption to use.
     *                               Defaults to md5-hex.
     * @param boolean $show_encrypt  Some password systems prepend the kind of
     *                               encryption to the crypted password ({SHA},
     *                               etc). Defaults to false.
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
            $encrypted = base64_encode(pack('H*', sha1($plaintext)));
            return ($show_encrypt) ? '{SHA}' . $encrypted : $encrypted;

        case 'crypt':
        case 'crypt-des':
        case 'crypt-md5':
        case 'crypt-blowfish':
            return ($show_encrypt ? '{crypt}' : '') . crypt($plaintext, $salt);

        case 'md5-base64':
            $encrypted = base64_encode(pack('H*', md5($plaintext)));
            return ($show_encrypt) ? '{MD5}' . $encrypted : $encrypted;

        case 'ssha':
            $encrypted = base64_encode(pack('H*', sha1($plaintext . $salt)) . $salt);
            return ($show_encrypt) ? '{SSHA}' . $encrypted : $encrypted;

        case 'smd5':
            $encrypted = base64_encode(pack('H*', md5($plaintext . $salt)) . $salt);
            return ($show_encrypt) ? '{SMD5}' . $encrypted : $encrypted;

        case 'aprmd5':
            $length = strlen($plaintext);
            $context = $plaintext . '$apr1$' . $salt;
            $binary = pack('H*', md5($plaintext . $salt . $plaintext));

            for ($i = $length; $i > 0; $i -= 16) {
                $context .= substr($binary, 0, ($i > 16 ? 16 : $i));
            }
            for ($i = $length; $i > 0; $i >>= 1) {
                $context .= ($i & 1) ? chr(0) : $plaintext[0];
            }

            $binary = pack('H*', md5($context));

            for ($i = 0; $i < 1000; $i++) {
                $new = ($i & 1) ? $plaintext : substr($binary, 0, 16);
                if ($i % 3) {
                    $new .= $salt;
                }
                if ($i % 7) {
                    $new .= $plaintext;
                }
                $new .= ($i & 1) ? substr($binary, 0, 16) : $plaintext;
                $binary = pack('H*', md5($new));
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

            return '$apr1$' . $salt . '$' . implode('', $p) . Auth::_toAPRMD5(ord($binary[11]), 3);

        case 'md5-hex':
        default:
            return ($show_encrypt) ? '{MD5}' . md5($plaintext) : md5($plaintext);
        }
    }

    /**
     * Returns a salt for the appropriate kind of password encryption.
     * Optionally takes a seed and a plaintext password, to extract the seed
     * of an existing password, or for encryption types that use the plaintext
     * in the generation of the salt.
     *
     * @param string $encryption  The kind of pasword encryption to use.
     *                            Defaults to md5-hex.
     * @param string $seed        The seed to get the salt from (probably a
     *                            previously generated password). Defaults to
     *                            generating a new seed.
     * @param string $plaintext   The plaintext password that we're generating
     *                            a salt for. Defaults to none.
     *
     * @return string  The generated or extracted salt.
     */
    function getSalt($encryption = 'md5-hex', $seed = '', $plaintext = '')
    {
        switch ($encryption) {
        case 'crypt':
        case 'crypt-des':
            if ($seed) {
                return substr(preg_replace('|^{crypt}|i', '', $seed), 0, 2);
            } else {
                return substr(md5(mt_rand()), 0, 2);
            }

        case 'crypt-md5':
            if ($seed) {
                return substr(preg_replace('|^{crypt}|i', '', $seed), 0, 12);
            } else {
                return '$1$' . substr(md5(mt_rand()), 0, 8) . '$';
            }

        case 'crypt-blowfish':
            if ($seed) {
                return substr(preg_replace('|^{crypt}|i', '', $seed), 0, 16);
            } else {
                return '$2$' . substr(md5(mt_rand()), 0, 12) . '$';
            }

        case 'ssha':
            if ($seed) {
                return substr(base64_decode(preg_replace('|^{SSHA}|i', '', $seed)), 20);
            } else {
                $salt = substr(pack('h*', md5(mt_rand())), 0, 8);
                return substr(pack('H*', sha1($salt . $plaintext)), 0, 4);
            }

        case 'smd5':
            if ($seed) {
                return substr(base64_decode(preg_replace('|^{SMD5}|i', '', $seed)), 16);
            } else {
                $salt = substr(pack('h*', md5(mt_rand())), 0, 8);
                return substr(pack('H*', md5($salt . $plaintext)), 0, 4);
            }

        case 'aprmd5':
            /* 64 characters that are valid for APRMD5 passwords. */
            $APRMD5 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';

            if ($seed) {
                return substr(preg_replace('/^\$apr1\$(.{8}).*/', '\\1', $seed), 0, 8);
            } else {
                $salt = '';
                for ($i = 0; $i < 8; $i++) {
                    $salt .= $APRMD5[mt_rand(0, 63)];
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
     *
     * @return string A random password
     */
    function genRandomPassword()
    {
        $vowels    = 'aeiouy';
        $constants = 'bcdfghjklmnpqrstvwxz';
        $numbers   = '0123456789';

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
     * Adds a set of authentication credentials.
     *
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
     * Updates a set of authentication credentials.
     *
     * @abstract
     *
     * @param string $oldID        The old userId.
     * @param string $newID        The new userId.
     * @param array $credentials   The new credentials
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function updateUser($oldID, $newID, $credentials)
    {
        return PEAR::raiseError('unsupported');
    }

    /**
     * Deletes a set of authentication credentials.
     *
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
     * Calls all applications' removeUser API methods.
     *
     * @param string $userId  The userId to delete.
     *
     * @return mixed  True on success or a PEAR_Error object on failure.
     */
    function removeUserData($userId)
    {
        global $registry;

        $errApps = array();

        foreach ($registry->listApps(array('notoolbar', 'hidden', 'active', 'admin')) as $app) {
            if ($registry->hasMethod('removeUserData', $app)) {
                if (is_a($result = $registry->callByPackage($app, 'removeUserData', array($userId)), 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    $errApps[] = $app;
                }
            }
        }

        if (count($errApps)) {
            $err = implode(', ', $errApps);
            return PEAR::raiseError(sprintf(_("The following applications encountered errors removing user data: %s"), $err));
        } else {
            return true;
        }
    }

    /**
     * Lists all users in the system.
     *
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
     * @abstract
     *
     * @param string $userId User ID for which to check
     *
     * @return boolean  Whether or not $userId already exists.
     */
    function exists($userId)
    {
        $users = $this->listUsers();
        if (is_a($users, 'PEAR_Error')) {
            return $users;
        }
        return in_array($userId, $users);
    }

    /**
     * Automatic authentication.
     *
     * @abstract
     *
     * @return boolean  Whether or not the user is authenticated automatically.
     */
    function transparent()
    {
        return false;
    }

    /**
     * Checks if there is a session with valid auth information. for the
     * specified user. If there isn't, but the configured Auth driver supports
     * transparent authentication, then we try that.
     *
     * @param string $realm  The authentication realm to check.
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
        if ($auth->hasCapability('transparent') && $auth->transparent()) {
            return Auth::isAuthenticated($realm);
        }

        return false;
    }

    /**
     * Returns the currently logged in user, if there is one.
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
     * Return whether the authentication backend requested a password change.
     *
     * @return boolean Whether the backend requested a password change.
     */
    function isPasswordChangeRequested()
    {
        if (isset($_SESSION['__auth']) &&
            !empty($_SESSION['__auth']['authenticated']) &&
            !empty($_SESSION['__auth']['changeRequested'])) {
            return true;
        }

        return false;
    }

    /**
     * Returns the curently logged-in user without any domain information
     * (e.g., bob@example.com would be returned as 'bob').
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
     * Returns the domain of currently logged-in user (e.g., bob@example.com
     * would be returned as 'example.com').
     *
     * @since Horde 3.0.6
     *
     * @return mixed  The domain suffix of the current user, or false.
     */
    function getAuthDomain()
    {
        if ($user = Auth::getAuth()) {
            $pos = strpos($user, '@');
            if ($pos !== false) {
                return substr($user, $pos + 1);
            }
        }

        return false;
    }

    /**
     * Returns the requested credential for the currently logged in user, if
     * present.
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
            $credentials = Secret::read(Secret::getKey('auth'), $_SESSION['__auth']['credentials']);
            $credentials = @unserialize($credentials);
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
     * Sets the requested credential for the currently logged in user.
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
     * Sets a variable in the session saying that authorization has succeeded,
     * note which userId was authorized, and note when the login took place.
     *
     * If a user name hook was defined in the configuration, it gets applied
     * to the userId at this point.
     *
     * @param string $userId            The userId who has been authorized.
     * @param array $credentials        The credentials of the user.
     * @param string $realm             The authentication realm to use.
     * @param boolean $changeRequested  Whether to request that the user change
     *                                  their password.
     */
    function setAuth($userId, $credentials, $realm = null, $changeRequested = false)
    {
        $userId = trim($userId);
        $userId = Auth::addHook($userId);

        if (!empty($GLOBALS['conf']['hooks']['postauthenticate'])) {
            if (!Horde::callHook('_horde_hook_postauthenticate', array($userId, $credentials, $realm), 'horde', false)) {
                if ($this->_getAuthError() != AUTH_REASON_MESSAGE) {
                    $this->_setAuthError(AUTH_REASON_FAILED);
                }
                return false;
            }
        }

        /* If we're already set with this userId, don't continue. */
        if (isset($_SESSION['__auth']['userId']) &&
            $_SESSION['__auth']['userId'] == $userId) {
            return true;
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
            'remote_addr' => isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : null,
            'browser' => $GLOBALS['browser']->getAgentString(),
            'changeRequested' => $changeRequested
        );

        /* Reload preferences for the new user. */
        $GLOBALS['registry']->loadPrefs();
        NLS::setLang($GLOBALS['prefs']->getValue('language'));

        /* Fetch the user's last login time. */
        $old_login = @unserialize($GLOBALS['prefs']->getValue('last_login'));

        /* Display it, if we have a notification object and the
         * show_last_login preference is active. */
        if (isset($GLOBALS['notification']) && $GLOBALS['prefs']->getValue('show_last_login')) {
            if (empty($old_login['time'])) {
                $GLOBALS['notification']->push(_("Last login: Never"), 'horde.message');
            } else {
                if (empty($old_login['host'])) {
                    $GLOBALS['notification']->push(sprintf(_("Last login: %s"), strftime('%c', $old_login['time'])), 'horde.message');
                } else {
                    $GLOBALS['notification']->push(sprintf(_("Last login: %s from %s"), strftime('%c', $old_login['time']), $old_login['host']), 'horde.message');
                }
            }
        }

        /* Set the user's last_login information. */
        $host = empty($_SERVER['HTTP_X_FORWARDED_FOR'])
            ? $_SERVER['REMOTE_ADDR']
            : $_SERVER['HTTP_X_FORWARDED_FOR'];

	if ((@include_once 'Net/DNS.php')) {
	    $resolver = new Net_DNS_Resolver();
	    $resolver->retry = isset($GLOBALS['conf']['dns']['retry']) ? $GLOBALS['conf']['dns']['retry'] : 1;
	    $resolver->retrans = isset($GLOBALS['conf']['dns']['retrans']) ? $GLOBALS['conf']['dns']['retrans'] : 1;
	    $response = $resolver->query($host, 'PTR');
	    $ptrdname = $response ? $response->answer[0]->ptrdname : $host;
	} else {
	    $ptrdname = @gethostbyaddr($host);
	}

        $last_login = array('time' => time(),
                            'host' => $ptrdname);
        $GLOBALS['prefs']->setValue('last_login', serialize($last_login));

        if ($changeRequested) {
            $GLOBALS['notification']->push(_("Your password has expired."),
                                           'horde.message');
            if ($this->hasCapability('update')) {
                /* A bit of a kludge.  URL is set from the login screen, but
                 * we aren't completely certain we got here from the login
                 * screen.  So any screen which calls setAuth() which has a
                 * url will end up going there.  Should be OK. */
                $url_param = Util::getFormData('url');

                if ($url_param) {
                    $url = Horde::url(Util::removeParameter($url_param,
                                                            session_name()),
                                      true);
                    $return_to = $GLOBALS['registry']->get('webroot', 'horde') .
                                 '/index.php';
                    $return_to = Util::addParameter($return_to, 'url', $url);
                } else {
                    $return_to = Horde::url($GLOBALS['registry']->get('webroot', 'horde')
                                 . '/index.php');
                }

                $url = Horde::applicationUrl('services/changepassword.php');
                $url = Util::addParameter($url,
                                          array('return_to' => $return_to),
                                          null, false);

                header('Location: ' . $url);
                exit;
            }
        }

        return true;
    }

    /**
     * Clears any authentication tokens in the current session.
     *
     * @param string $realm  The authentication realm to clear.
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

        /* Remove the user's cached preferences if they are present. */
        if (isset($GLOBALS['registry'])) {
            $GLOBALS['registry']->unloadPrefs();
        }
    }

    /**
     * Is the current user an administrator?
     *
     * @param string $permission  Allow users with this permission admin access
     *                            in the current context.
     * @param integer $permlevel  The level of permissions to check for
     *                            (PERMS_EDIT, PERMS_DELETE, etc). Defaults
     *                            to PERMS_EDIT.
     * @param string $user        The user to check. Defaults to Auth::getAuth().
     *
     * @return boolean  Whether or not this is an admin user.
     */
    function isAdmin($permission = null, $permlevel = null, $user = null)
    {
        if (is_null($user)) {
            $user = Auth::getAuth();
        }

        if ($user
            && @is_array($GLOBALS['conf']['auth']['admins'])
            && in_array($user, $GLOBALS['conf']['auth']['admins'])) {
            return true;
        }

        if ($user) {
            $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
            if ($auth->hasCapability('admins')
                && $auth->_isAdmin($permission, $permlevel, $user)) {
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
     * Applies a hook defined by the function _username_hook_frombackend() to
     * the given user name if this function exists and user hooks are enabled.
     *
     * This method should be called if a authentication backend's user name
     * needs to be converted to a (unique) Horde user name. The backend's user
     * name is what the user sees and uses, but internally we use the Horde
     * user name.
     *
     * @param string $userId  The authentication backend's user name.
     *
     * @return string  The internal Horde user name.
     */
    function addHook($userId)
    {
        if (!empty($GLOBALS['conf']['hooks']['username'])) {
            $newId = Horde::callHook('_username_hook_frombackend', array($userId));
            if (!is_a($newId, 'PEAR_Error')) {
                return $newId;
            }
        }

        return $userId;
    }

    /**
     * Applies a hook defined by the function _username_hook_tobackend() to
     * the given user name if this function exists and user hooks are enabled.
     *
     * This method should be called if a Horde user name needs to be converted
     * to an authentication backend's user name or displayed to the user. The
     * backend's user name is what the user sees and uses, but internally we
     * use the Horde user name.
     *
     * @param string $userId  The internal Horde user name.
     *
     * @return string  The authentication backend's user name.
     */
    function removeHook($userId)
    {
        if (!empty($GLOBALS['conf']['hooks']['username'])) {
            $newId = Horde::callHook('_username_hook_tobackend', array($userId));
            if (!is_a($newId, 'PEAR_Error')) {
                return $newId;
            }
        }

        return $userId;
    }

    /**
     * Queries the current Auth object to find out if it supports the given
     * capability.
     *
     * @param string $capability  The capability to test for.
     *
     * @return boolean  Whether or not the capability is supported.
     */
    function hasCapability($capability)
    {
        return !empty($this->capabilities[$capability]);
    }

    /**
     * Returns the URI of the login screen for the current authentication
     * method.
     *
     * @param string $app  The application to use.
     * @param string $url  The URL to redirect to after login.
     *
     * @return string  The login screen URI.
     */
    function getLoginScreen($app = 'horde', $url = '')
    {
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        return $auth->_getLoginScreen($app, $url);
    }

    /**
     * Returns the named parameter for the current auth driver.
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
     * Returns the name of the authentication provider.
     *
     * @param string $driver  Used by recursive calls when untangling composite
     *                        auth.
     * @param array  $params  Used by recursive calls when untangling composite
     *                        auth.
     *
     * @return string  The name of the driver currently providing
     *                 authentication.
     */
    function getProvider($driver = null, $params = null)
    {
        if (is_null($driver)) {
            $driver = $GLOBALS['conf']['auth']['driver'];
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
     * Returns the logout reason.
     *
     * @return string One of the logout reasons (see the AUTH_LOGOUT_*
     *                constants for the valid reasons).  Returns null if there
     *                is no logout reason present.
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
     * Returns the status string to use for logout messages.
     *
     * @return string  The logout reason string.
     */
    function getLogoutReasonString()
    {
        switch (Auth::getLogoutReason()) {
        case AUTH_REASON_SESSION:
            $text = sprintf(_("Your %s session has expired. Please login again."), $GLOBALS['registry']->get('name'));
            break;

        case AUTH_REASON_SESSIONIP:
            $text = sprintf(_("Your Internet Address has changed since the beginning of your %s session. To protect your security, you must login again."), $GLOBALS['registry']->get('name'));
            break;

        case AUTH_REASON_BROWSER:
            $text = sprintf(_("Your browser appears to have changed since the beginning of your %s session. To protect your security, you must login again."), $GLOBALS['registry']->get('name'));
            break;

        case AUTH_REASON_LOGOUT:
            $text = _("You have been logged out.");
            break;

        case AUTH_REASON_FAILED:
            $text = _("Login failed.");
            break;

        case AUTH_REASON_BADLOGIN:
            $text = _("Login failed because your username or password was entered incorrectly.");
            break;

        case AUTH_REASON_EXPIRED:
            $text = _("Your login has expired.");
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
     * Generates the correct parameters to pass to the given logout URL.
     *
     * If no reason/msg is passed in, use the current global authentication
     * error message.
     *
     * @param string $url     The URL to redirect to.
     * @param string $reason  The reason for logout.
     * @param string $msg     If reason is AUTH_REASON_MESSAGE, the message to
     *                        display to the user.
     * @return string The formatted URL
     */
    function addLogoutParameters($url, $reason = null, $msg = null)
    {
        $params = array('horde_logout_token' => Horde::getRequestToken('horde.logout'));

        if (isset($GLOBALS['registry'])) {
            $params['app'] = $GLOBALS['registry']->getApp();
        }

        if (is_null($reason)) {
            $reason = Auth::getLogoutReason();
        }

        if ($reason) {
            $params[AUTH_REASON_PARAM] = $reason;
            if ($reason == AUTH_REASON_MESSAGE) {
                if (is_null($msg)) {
                    $msg = Auth::getLogoutReasonString();
                }
                $params[AUTH_REASON_MSG_PARAM] = $msg;
            }
        }

        return Util::addParameter($url, $params, null, false);
    }

    /**
     * Reads session data to determine if it contains Horde authentication
     * credentials.
     *
     * @since Horde 3.2
     *
     * @param string $session_data  The session data.
     * @param boolean $info         Return session information.  The following
     *                              information is returned: userid, realm,
     *                              timestamp, remote_addr, browser.
     *
     * @return array  An array of the user's sesion information if
     *                authenticated or false.  The following information is
     *                returned: userid, realm, timestamp, remote_addr, browser.
     */
    function readSessionData($session_data)
    {
        if (empty($session_data)) {
            return false;
        }

        $pos = strpos($session_data, '__auth|');
        if ($pos === false) {
            return false;
        }

        $endpos = $pos + 7;
        $old_error = error_reporting(0);

        while ($endpos !== false) {
            $endpos = strpos($session_data, '|', $endpos);
            $data = unserialize(substr($session_data, $pos + 7, $endpos));
            if (is_array($data)) {
                error_reporting($old_error);
                if (empty($data['authenticated'])) {
                    return false;
                }
                return array(
                    'userid' => $data['userId'],
                    'realm' => $data['realm'],
                    'timestamp' => $data['timestamp'],
                    'remote_addr' => $data['remote_addr'],
                    'browser' => $data['browser']
                );
            }
            ++$endpos;
        }

        return false;
    }

    /**
     * Returns the URI of the login screen for this authentication object.
     *
     * @access private
     *
     * @param string $app  The application to use.
     * @param string $url  The URL to redirect to after login.
     *
     * @return string  The login screen URI.
     */
    function _getLoginScreen($app = 'horde', $url = '')
    {
        $login = Horde::url($GLOBALS['registry']->get('webroot', $app) . '/login.php', true);
        if (!empty($url)) {
            $login = Util::addParameter($login, 'url', $url);
        }
        return $login;
    }

    /**
     * Authentication stub.
     *
     * @abstract
     * @access protected
     *
     * @return boolean  False.
     */
    function _authenticate()
    {
        return false;
    }

    /**
     * Driver-level admin check stub.
     *
     * @abstract
     * @access protected
     *
     * @return boolean  False.
     */
    function _isAdmin($permission = null, $permlevel = null, $user = null)
    {
        return false;
    }

    /**
     * Sets the error message for an invalid authentication.
     *
     * @access private
     *
     * @param string $type  The type of error (AUTH_REASON constant).
     * @param string $msg   The error message/reason for invalid
     *                      authentication.
     */
    function _setAuthError($type, $msg = null)
    {
        $GLOBALS['__autherror'] = array();
        $GLOBALS['__autherror']['type'] = $type;
        $GLOBALS['__autherror']['msg'] = $msg;
    }

    /**
     * Returns the error type for an invalid authentication or false on error.
     *
     * @access private
     *
     * @return mixed Error type or false on error
     */
    function _getAuthError()
    {
        if (isset($GLOBALS['__autherror']['type'])) {
            return $GLOBALS['__autherror']['type'];
        }

        return false;
    }

    /**
     * Returns the appropriate authentication driver, if any, selecting by the
     * specified parameter.
     *
     * @access private
     *
     * @param string $name          The parameter name.
     * @param array $params         The parameter list.
     * @param string $driverparams  A list of parameters to pass to the driver.
     *
     * @return mixed Return value or called user func or null if unavailable
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
     * Performs check on session to see if IP Address has changed since the
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
     * Performs check on session to see if browser string has changed since
     * the last access.
     *
     * @access private
     *
     * @return boolean  True if browser string is the same, false if the
     *                  string has changed.
     */
    function _checkBrowserString()
    {
        return (empty($GLOBALS['conf']['auth']['checkbrowser']) ||
                $_SESSION['__auth']['browser'] == $GLOBALS['browser']->getAgentString());
    }

    /**
     * Converts to allowed 64 characters for APRMD5 passwords.
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
        /* 64 characters that are valid for APRMD5 passwords. */
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
     * Attempts to return a concrete Auth instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Auth subclass to return. This
     *                       is based on the storage driver ($driver). The code
     *                       is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/Auth/ for the
     *                       subclass implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Auth  The newly created concrete Auth instance, or false on an
     *               error.
     */
    function factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        if (empty($driver) || ($driver == 'none')) {
            return new Auth();
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('auth', $driver);
        }

        $class = 'Auth_' . $driver;
        $include_error = '';
        if (!class_exists($class)) {
            $oldTrackErrors = ini_set('track_errors', 1);
            if (!empty($app)) {
                include $GLOBALS['registry']->get('fileroot', $app) . '/lib/Auth/' . $driver . '.php';
            } else {
                include 'Horde/Auth/' . $driver . '.php';
            }
            if (isset($php_errormsg)) {
                $include_error = $php_errormsg;
            }
            ini_set('track_errors', $oldTrackErrors);
        }

        if (class_exists($class)) {
            $auth = new $class($params);
        } else {
            $auth = PEAR::raiseError('Auth Driver (' . $class . ') not found' . ($include_error ? ': ' . $include_error : '') . '.');
        }

        return $auth;
    }

    /**
     * Attempts to return a reference to a concrete Auth instance based on
     * $driver. It will only create a new instance if no Auth instance with
     * the same parameters currently exists.
     *
     * This should be used if multiple authentication sources (and, thus,
     * multiple Auth instances) are required.
     *
     * This method must be invoked as: $var = &Auth::singleton()
     *
     * @param string $driver  The type of concrete Auth subclass to return.
     *                        This is based on the storage driver ($driver).
     *                        The code is dynamically included.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return Auth  The concrete Auth reference, or false on an error.
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
            $instances[$signature] = Auth::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
