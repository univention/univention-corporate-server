<?php
/**
 * The Auth_yahoo:: class checks login credentials against Yahoo! mail
 * accounts.
 *
 * $Horde: framework/Auth/Auth/yahoo.php,v 1.13 2004/01/28 00:34:00 slusarz Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see yahoo://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_yahoo extends Auth {

    var $_http;

    /**
     * Constructs a new Yahoo authentication object.
     *
     * @access public
     *
     * @param optional array $params  A hash containing parameters.
     */
    function Auth_yahoo($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $userId       The userId to check.
     * @param array  $credentials  The credentials to use.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($userId, $credentials)
    {
        require_once 'HTTP/Request.php';

        // Make sure that we have a bare username - strip off anything
        // after (and including) the first @, if there is one.
        $pos = strpos($userId, '@');
        if ($pos !== false) {
            $userId = substr($userId, 0, $pos);
        }

        $options['method'] = HTTP_REQUEST_METHOD_POST;
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;

        $this->_http = &new HTTP_Request('http://login.yahoo.com/config/login', $options);
        $this->_http->addPostData('login', $userId);
        $this->_http->addPostData('passwd', $credentials['password']);

        $result = $this->_http->sendRequest();
        if (is_a($result, 'PEAR_Error')) {
            $result = $result->getMessage();
        } else {
            $result = $this->_http->getResponseBody();
            $cookies = $this->_http->getResponseCookies();
            if (is_array($cookies)) {
                foreach ($cookies as $cookie) {
                    $this->_http->addCookie($cookie['name'], $cookie['value']);
                }
            }
        }

        // This is _such_ a hack, but it works.
        if (!preg_match('|invalid password|i', $result)) {
            return true;
        } else {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_setAuthError(AUTH_REASON_BADLOGIN);
            return false;
        }
    }

}
