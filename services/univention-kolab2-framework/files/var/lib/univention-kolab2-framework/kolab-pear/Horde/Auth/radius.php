<?php
/**
 * The Auth_radius class provides a RADIUS implementation of the Horde
 * authentication system.
 *
 * This class requires the 'radius' PECL extension.
 * RADIUS PECL extension: http://pecl.php.net/package/radius
 *
 * On *nix-y machines, this extension can be installed as follows:
 *   "pear install radius"
 *
 * Then, edit your php.ini file and make sure the following line is present:
 *   For Windows machines:  extension=php_radius.dll
 *   For all others:        extension=radius.so
 *
 * Required parameters:
 * ====================
 *   'host'    --  The RADIUS host to use (IP address or fully qualified
 *                 hostname).
 *   'method'  --  The RADIUS method to use for validating the request.
 *                 Either: 'PAP', 'CHAP_MD5', 'MSCHAPv1', or 'MSCHAPv2'.
 *                 ** CURRENTLY, only 'PAP' is supported. **
 *   'secret'  --  The RADIUS shared secret string for the host.
 *                 The RADIUS protocol ignores all but the leading 128 bytes
 *                 of the shared secret.
 *
 * Optional parameters:
 * ====================
 *   'nas'      --  The RADIUS NAS identifier to use.
 *                  DEFAULT: The value of $_SERVER['HTTP_HOST'] or, if not
 *                           defined, then 'localhost'.
 *   'port'     --  The port to use on the RADIUS server.
 *                  DEFAULT: Whatever the local system identifies as the
 *                           'radius' UDP port
 *   'retries'  --  The maximum number of repeated requests to make before
 *                  giving up.
 *                  DEFAULT: 3
 *   'suffix'   --  The domain name to add to unqualified user names.
 *                  DEFAULT: NONE
 *   'timeout'  --  The timeout for receiving replies from the server (in
 *                  seconds).
 *                  DEFAULT: 3 seconds
 *
 *
 * $Horde: framework/Auth/Auth/radius.php,v 1.23 2004/05/25 08:50:11 mdjukic Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_radius extends Auth {

    /** 
     * An array of capabilities, so that the driver can report which
     * operations it supports and which it doesn't.
     *
     * @var array $capabilities 
     */
    var $capabilities = array('add'           => false,
                              'update'        => false,
                              'resetpassword' => false,
                              'remove'        => false,
                              'list'          => false,
                              'transparent'   => false);

    /**
     * Constructs a new RADIUS authentication object.
     *
     * @access public
     *
     * @param array optional $params  A hash containing connection parameters.
     */
    function Auth_radius($params = array())
    {
        if (!Util::extensionExists('radius')) {
            Horde::fatal(PEAR::raiseError('Auth_radius requires the radius PECL extension to be loaded.'), __FILE__, __LINE__);
        }

        $this->_setParams($params);
    }

    /**
     * Set parameters.
     *
     * @access private
     *
     * @param array $params  The parameter hash.
     */
    function _setParams($params)
    {
        /* A RADIUS host is required. */
        if (empty($params['host'])) {
            Horde::fatal(PEAR::raiseError('Auth_radius requires a RADIUS host to connect to.'), __FILE__, __LINE__);
        }

        /* A RADIUS secret string is required. */
        if (empty($params['secret'])) {
            Horde::fatal(PEAR::raiseError('Auth_radius requires a RADIUS secret string.'), __FILE__, __LINE__);
        }

        /* A RADIUS authentication method is required. */
        if (empty($params['method'])) {
            Horde::fatal(PEAR::raiseError('Auth_radius requires a RADIUS authentication method.'), __FILE__, __LINE__);
        }

        /* RADIUS NAS Identifier. */
        if (empty($params['nas'])) {
            $params['nas'] = isset($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'
] : 'localhost';
        }

        /* Suffix to add to unqualified user names. */
        if (empty($params['suffix'])) {
            $params['suffix'] = '';
        }

        /* The RADIUS port to use. */
        if (empty($params['port'])) {
            $params['port'] = 0;
        }

        /* Maximum number of retries. */
        if (empty($params['retries'])) {
            $params['retries'] = 3;
        }

        /* RADIUS timeout. */
        if (empty($params['timeout'])) {
            $params['timeout'] = 3;
        }

        $this->_params = $params;
    }

    /**
     * Find out if a set of login credentials are valid.
     *
     * @access private
     *
     * @param string $username    The userId to check.
     * @param array $credentials  An array of login credentials.
     *                            For radius, this must contain a password
     *                            entry.
     *
     * @return boolean  Whether or not the credentials are valid.
     */
    function _authenticate($username, $credentials)
    {
        /* Password is required. */
        if (!isset($credentials['password'])) {
            Horde::fatal(PEAR::raiseError(_("Password required for RADIUS authentication.")), __FILE__, __LINE__);
        }

        $res = radius_auth_open();
        radius_add_server($res, $this->_params['host'], $this->_params['port'], $this->_params['secret'], $this->_params['timeout'], $this->_params['retries']);
        radius_create_request($res, RADIUS_ACCESS_REQUEST);
        radius_put_attr($res, RADIUS_NAS_IDENTIFIER, $this->_params['nas']);
        radius_put_attr($res, RADIUS_NAS_PORT_TYPE, RADIUS_VIRTUAL);
        radius_put_attr($res, RADIUS_SERVICE_TYPE, RADIUS_FRAMED);
        radius_put_attr($res, RADIUS_FRAMED_PROTOCOL, RADIUS_PPP);
        radius_put_attr($res, RADIUS_CALLING_STATION_ID, isset($_SERVER['REMOTE_HOST']) ? $_SERVER['REMOTE_HOST'] : '127.0.0.1');

        /* Insert username/password into request. */
        radius_put_attr($res, RADIUS_USER_NAME, $username);
        radius_put_attr($res, RADIUS_USER_PASSWORD, $credentials['password']);

        /* Send request. */
        $success = radius_send_request($res);

        switch ($success) {
        case RADIUS_ACCESS_ACCEPT:
            return true;

        case RADIUS_ACCESS_REJECT:
            $this->_setAuthError(AUTH_REASON_MESSAGE, _("Authentication rejected by RADIUS server."));
            return false;

        default:
            $this->_setAuthError(AUTH_REASON_MESSAGE, radius_strerror($success));
            return false;
        }
    }

}
