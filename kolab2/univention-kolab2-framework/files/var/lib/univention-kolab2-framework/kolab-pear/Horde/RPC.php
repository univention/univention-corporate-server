<?php
/**
 * The Horde_RPC:: class provides a set of server and client methods for
 * RPC communication.
 *
 * TODO:
 * - Introspection documentation and method signatures.
 *
 * EXAMPLE:
 * $response = Horde_RPC::request('xmlrpc',
 *                                '/horde/rpc.php', 'www.example.com', 80,
 *                                'contacts.search',
 *                                array(array('jan'), array('localsql'),
 *                                      array('name', 'email')),
 *                                Auth::getAuth(), Auth::getCredential('password'));
 *
 * $Horde: framework/RPC/RPC.php,v 1.6 2004/02/09 22:42:52 jan Exp $
 *
 * Copyright 2002-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC {

    /**
     * RPC server constructor
     *
     * @access private
     * @return object   An RPC server instance.
     */
    function Horde_RPC()
    {
        register_shutdown_function(array($this, 'shutdown'));
    }

    /**
     * Cleans up the RPC server.
     *
     * @abstract
     */
    function shutdown()
    {
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
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);

        if (isset($_SERVER['PHP_AUTH_USER'])) {
            $user = $_SERVER['PHP_AUTH_USER'];
            $pass = $_SERVER['PHP_AUTH_PW'];
        }

        if (!isset($user)
            || !$auth->authenticate($user, array('password' => $pass))) {
            header('WWW-Authenticate: Basic realm="Horde RPC"');
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
     * @param string    The raw request string.
     *
     * @return string   The XML encoded response from the server.
     */
    function getResponse($request)
    {
        return _("not implemented");
    }

    /**
     * Get the Content-Type of the response.
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
     * @param string $driver    The protocol driver to use. Currently 'soap' and
     *                          'xmlrpc' are available.
     * @param string $url       The path to the RPC server on the called host.
     * @param string $method    The method to call.
     * @param array $params     (optional) A hash containing any necessary
     *                          parameters for the method call.
     * @param $options  Optional associative array of parameters depending on
     *                  the selected protocol driver.
     *
     * @return mixed            The returned result from the method or a PEAR
     *                          error object on failure.
     */
    function request($driver, $url, $method, $params = null, $options = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        $driver = basename($driver);

        if (!empty($app)) {
            require_once $app . '/lib/RPC/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/RPC/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/RPC/' . $driver . '.php';
        } else {
            @include_once 'Horde/RPC/' . $driver . '.php';
        }
        $class = 'Horde_RPC_' . $driver;
        if (class_exists($class)) {
            return call_user_func(array($class, 'request'), $url, $method, $params, $options);
        } else {
            require_once 'PEAR.php';
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a concrete RPC server instance based on
     * $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete RPC subclass to
     *                                return. This is based on the protocol
     *                                driver ($driver). The code is dynamically
     *                                included. If $driver is an array, then
     *                                we will look in $driver[0]/lib/RPC/
     *                                for the subclass implementation named
     *                                $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters
     *                                a subclass might need.
     *
     * @return object Horde_RPC  The newly created concrete Horde_RPC server
     *                           instance, or a PEAR_Error on an error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        $driver = basename($driver);

        if (!empty($app)) {
            require_once $app . '/lib/RPC/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/RPC/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/RPC/' . $driver . '.php';
        } else {
            @include_once 'Horde/RPC/' . $driver . '.php';
        }
        $class = 'Horde_RPC_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            require_once 'PEAR.php';
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete RPC server
     * instance based on $driver. It will only create a new instance
     * if no RPC server instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple RPC servers (and thus, multiple RPC
     * server instances) are required.
     *
     * This method must be invoked as: $var = &Horde_RPC::singleton()
     *
     * @access public
     *
     * @param string $driver          The type of concrete RPC subclass to
     *                                return. This is based on the protocol
     *                                driver ($driver). The code is dynamically
     *                                included.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Horde_RPC   The concrete Horde_RPC server reference, or a
     *                             PEAR_Error
     *                      on an error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!array_key_exists($signature, $instances)) {
            $instances[$signature] = &Horde_RPC::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
