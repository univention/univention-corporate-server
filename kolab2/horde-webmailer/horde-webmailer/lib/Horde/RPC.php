<?php
/**
 * The Horde_RPC:: class provides a set of server and client methods for
 * RPC communication.
 *
 * TODO:
 * - Introspection documentation and method signatures.
 *
 * EXAMPLE:
 * <code>
 * $response = Horde_RPC::request('xmlrpc',
 *                                'http://localhost:80/horde/rpc.php',
 *                                'contacts.search',
 *                                array(array('jan'), array('localsql'),
 *                                      array('name', 'email')),
 *                                array('user' => Auth::getAuth(),
 *                                      'pass' => Auth::getCredential('password')));
 * </code>
 *
 * $Horde: framework/RPC/RPC.php,v 1.7.10.18 2009-06-16 15:28:04 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC {

    /**
     * All driver-specific parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Do we need an authenticated user?
     *
     * @var boolean
     */
    var $_requireAuthorization = true;

    /**
     * Whether we should exit if auth fails instead of requesting
     * authorization credentials.
     *
     * @var boolean
     */
    var $_requestMissingAuthorization = true;

    /**
     * RPC server constructor.
     *
     * @param array $config  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_RPC  An RPC server instance.
     */
    function Horde_RPC($params = array())
    {
        $this->_params = $params;

        if (isset($params['requireAuthorization'])) {
            $this->_requireAuthorization = $params['requireAuthorization'];
        }
        if (isset($params['requestMissingAuthorization'])) {
            $this->_requestMissingAuthorization = $params['requestMissingAuthorization'];
        }
    }

    /**
     * Check authentication. Different backends may handle
     * authentication in different ways. The base class implementation
     * checks for HTTP Authentication against the Horde auth setup.
     *
     * @return boolean  Returns true if authentication is successful.
     *                  Should send appropriate "not authorized" headers
     *                  or other response codes/body if auth fails,
     *                  and take care of exiting.
     */
    function authorize()
    {
        if (!$this->_requireAuthorization) {
            return true;
        }

        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);

        if (isset($_SERVER['PHP_AUTH_USER'])) {
            $user = $_SERVER['PHP_AUTH_USER'];
            $pass = $_SERVER['PHP_AUTH_PW'];
        } elseif (isset($_SERVER['Authorization'])) {
            $hash = str_replace('Basic ', '', $_SERVER['Authorization']);
            $hash = base64_decode($hash);
            if (strpos($hash, ':') !== false) {
                list($user, $pass) = explode(':', $hash, 2);
            }
        }

        if (!isset($user)
            || !$auth->authenticate($user, array('password' => $pass))) {
            if ($this->_requestMissingAuthorization) {
                header('WWW-Authenticate: Basic realm="Horde RPC"');
            }
            header('HTTP/1.0 401 Unauthorized');
            echo '401 Unauthorized';
            exit;
        }

        return true;
    }

    /**
     * Get the request body input. Different RPC backends can override
     * this to return an open stream to php://stdin, for instance -
     * whatever is easiest to handle in the getResponse() method.
     *
     * The base class implementation looks for $HTTP_RAW_POST_DATA and
     * returns that if it's available; otherwise, it returns the
     * contents of php://stdin.
     *
     * @return mixed  The input - a string (default), a filehandle, etc.
     */
    function getInput()
    {
        if (isset($GLOBALS['HTTP_RAW_POST_DATA'])) {
            return $GLOBALS['HTTP_RAW_POST_DATA'];
        } else {
            return implode("\r\n", file('php://input'));
        }
    }

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string  The raw request string.
     *
     * @return string  The XML encoded response from the server.
     */
    function getResponse($request)
    {
        return 'not implemented';
    }

    /**
     * Returns the Content-Type of the response.
     *
     * @return string  The MIME Content-Type of the RPC response.
     */
    function getResponseContentType()
    {
        return 'text/xml';
    }

    /**
     * Builds an RPC request and sends it to the RPC server.
     *
     * This statically called method is actually the RPC client.
     *
     * @param string $driver    The protocol driver to use. Currently 'soap',
     *                          'xmlrpc' and 'jsonrpc' are available.
     * @param string $url       The path to the RPC server on the called host.
     * @param string $method    The method to call.
     * @param array $params     A hash containing any necessary parameters for
     *                          the method call.
     * @param $options          Associative array of parameters depending on
     *                          the selected protocol driver.
     *
     * @return mixed            The returned result from the method or a PEAR
     *                          error object on failure.
     */
    function request($driver, $url, $method, $params = null, $options = array())
    {
        $driver = basename($driver);
        $class = 'Horde_RPC_' . $driver;
        if (!class_exists($class)) {
            include 'Horde/RPC/' . $driver . '.php';
        }

        if (class_exists($class)) {
            return call_user_func(array($class, 'request'), $url, $method, $params, $options);
        } else {
            include_once 'PEAR.php';
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a concrete RPC server instance based on
     * $driver.
     *
     * @param mixed $driver  The type of concrete RPC subclass to return. If
     *                       $driver is an array, then we will look in
     *                       $driver[0]/lib/RPC/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_RPC  The newly created concrete Horde_RPC server instance,
     *                    or PEAR_Error on error.
     */
    function factory($driver, $params = null)
    {
        $driver = basename($driver);
        $class = 'Horde_RPC_' . $driver;
        if (!class_exists($class)) {
            include 'Horde/RPC/' . $driver . '.php';
        }

        if (class_exists($class)) {
            return new $class($params);
        } else {
            include_once 'PEAR.php';
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

}
