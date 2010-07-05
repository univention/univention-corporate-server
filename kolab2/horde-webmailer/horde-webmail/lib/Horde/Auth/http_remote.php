<?php
/**
 * $Horde: framework/Auth/Auth/http_remote.php,v 1.1.2.3 2009-01-06 15:22:49 jan Exp $
 *
 * @package Horde_Auth
 */

/** HTTP_Request */
require_once 'HTTP/Request.php';

/**
 * The Auth_http_remote class authenticates users against a remote
 * HTTP-Auth endpoint.
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Duck <duck@obala.net>
 * @since   Horde 3.2
 * @package Horde_Auth
 */
class Auth_http_remote extends Auth {

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
                              'transparent'   => false);

    /**
     * Constructs a new Remote HTTP authentication object.
     *
     * @param array $params  A hash containing parameters.
     */
    function Auth_http_remote($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId       The userId to check.
     * @param array  $credentials  An array of login credentials.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        $options['method'] = 'GET';
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;
        if (!empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
            $options = array_merge($options, $GLOBALS['conf']['http']['proxy']);
        }

        $request = new HTTP_Request($this->_params['url'], $options);
        $request->setBasicAuth($userId, $credentials['password']);

        $request->sendRequest();
        if ($request->getResponseCode() == 200) {
            return true;
        } else {
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }
    }

}
