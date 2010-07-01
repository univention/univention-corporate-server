<?php
/**
 * The Auth_http class transparently logs users in to Horde using
 * already present HTTP authentication headers.
 *
 * The 'encryption' parameter specifies what kind of passwords are in
 * the .htpasswd file. The supported options are 'crypt-des' (standard
 * crypted htpasswd entries) and 'aprmd5'. This information is used if
 * you want to directly authenticate users with this driver, instead
 * of relying on transparent auth.
 *
 * $Horde: framework/Auth/Auth/http.php,v 1.21.10.14 2009-01-06 15:22:49 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_http extends Auth {

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
                              'transparent'   => true);

    /**
     * Array of usernames and hashed passwords.
     *
     * @var array
     */
    var $_users = array();

    /**
     * Constructs a new HTTP authentication object.
     *
     * @param array $params  A hash containing parameters.
     */
    function Auth_http($params = array())
    {
        $this->_params = $params;

        // Default to DES passwords.
        if (empty($this->_params['encryption'])) {
            $this->_params['encryption'] = 'crypt-des';
        }

        if (!empty($this->_params['htpasswd_file'])) {
            $users = file($this->_params['htpasswd_file']);
            if (is_array($users)) {
                // Enable the list users capability.
                $this->capabilities['list'] = true;

                // Put users into alphabetical order.
                sort($users);

                foreach ($users as $line) {
                    list($user, $pass) = explode(':', $line, 2);
                    $this->_users[trim($user)] = trim($pass);
                }
            }
        }
    }

    /**
     * Find out if a set of login credentials are valid. Only supports
     * htpasswd files with DES passwords right now.
     *
     * @access private
     *
     * @param string $userId       The userId to check.
     * @param array  $credentials  An array of login credentials. For IMAP,
     *                             this must contain a password entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        if (empty($credentials['password']) ||
            empty($this->_users[$userId])) {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }

        $hash = $this->getCryptedPassword($credentials['password'], $this->_users[$userId], $this->_params['encryption'], !empty($this->_params['show_encryption']));
        if ($hash == $this->_users[$userId]) {
            return true;
        } else {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }
    }

    /**
     * Return the URI of the login screen for this authentication object.
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
        if (!empty($this->_params['loginScreen'])) {
            if ($url) {
                return Util::addParameter($this->_params['loginScreen'], 'url', $url);
            } else {
                return $this->_params['loginScreen'];
            }
        } else {
            return parent::_getLoginScreen($app, $url);
        }
    }

    /**
     * List all users in the system.
     *
     * @return mixed  The array of userIds, or a PEAR_Error object on failure.
     */
    function listUsers()
    {
        return array_keys($this->_users);
    }

    /**
     * Automatic authentication: Find out if the client has HTTP
     * authentication info present.
     *
     * @return boolean  Whether or not the client is allowed.
     */
    function transparent()
    {
        if (!empty($_SERVER['PHP_AUTH_USER']) &&
            !empty($_SERVER['PHP_AUTH_PW'])) {
            return $this->setAuth(Util::dispelMagicQuotes($_SERVER['PHP_AUTH_USER']),
                                  array('password' => Util::dispelMagicQuotes($_SERVER['PHP_AUTH_PW']),
                                        'transparent' => 1));
        }

        $this->_setAuthError(AUTH_REASON_MESSAGE, _("HTTP Authentication not found."));
        return false;
    }

}
