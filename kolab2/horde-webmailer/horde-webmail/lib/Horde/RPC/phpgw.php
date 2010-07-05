<?php
/**
 * The Horde_RPC_phpgw class provides an XMLRPC implementation of the
 * Horde RPC system compatible with phpgw. It is based on the
 * xmlrpc.php implementation by Jan Schneider.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Braun <mi.braun@onlinehome.de>
 * @since   Horde 3.2
 * @package Horde_RPC
 */
class Horde_RPC_phpgw extends Horde_RPC {

    /**
     * Resource handler for the XML-RPC server.
     *
     * @var resource
     */
    var $_server;

    /**
     * XMLRPC server constructor.
     */
    function Horde_RPC_phpgw()
    {
        parent::Horde_RPC();

        $this->_server = xmlrpc_server_create();

        // Register only phpgw services.
        foreach ($GLOBALS['registry']->listMethods('phpgw') as $method) {
            $methods = explode('/', $method);
            array_shift($methods);
            $method = implode('.', $methods);
            xmlrpc_server_register_method($this->_server, $method, array('Horde_RPC_phpgw', '_dispatcher'));
        }
    }

    /**
     * Authorization is done by xmlrpc method system.login.
     */
    function authorize()
    {
        return true;
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
        $response = null;
        return xmlrpc_server_call_method($this->_server, $request, $response);
    }

    /**
     * Will be registered as the handler for all available methods
     * and will call the appropriate function through the registry.
     *
     * @access private
     *
     * @param string $method  The name of the method called by the RPC request.
     * @param array $params   The passed parameters.
     * @param mixed $data     Unknown.
     *
     * @return mixed  The result of the called registry method.
     */
    function _dispatcher($method, $params, $data)
    {
        global $registry;
        $method = str_replace('.', '/', 'phpgw.' . $method);

        if (!$registry->hasMethod($method)) {
            Horde::logMessage(sprintf(_("Method \"%s\" is not defined"), $method), __FILE__, __LINE__, PEAR_LOG_NOTICE);
            return sprintf(_("Method \"%s\" is not defined"), $method);
        }

        // Try to resume a session
        if (isset($params[0]['kp3']) && $params[0]["kp3"] == session_name() && session_id() != $params[0]["sessionid"]) {
            Horde::logMessage("manually reload session ".$params[0]["sessionid"], __FILE__, __LINE__, PEAR_LOG_NOTICE);
            // Make sure to force a completely new session ID and clear
            // all session data.
            if (version_compare(PHP_VERSION, '4.3.3') !== -1) {
                session_regenerate_id();
                session_unset();
                session_id($params[0]["sessionid"]);
            } else {
                @session_destroy();
                session_id($params[0]["sessionid"]);
                Horde::setupSessionHandler();
                session_start();
            }
        }

        // Be authenticated or call system.login.
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        $authenticated = $auth->isAuthenticated() || $method== "phpgw/system/login";

        if ($authenticated) {
            Horde::logMessage("rpc call $method allowed", __FILE__, __LINE__, PEAR_LOG_NOTICE);
            return $registry->call($method, $params);
        } else {
            return PEAR::raiseError(_("You did not authenticate."), 'horde.error');
            // return parent::authorize();
            // error 9 "access denied"
        }
    }

    /**
     * Builds an XMLRPC request and sends it to the XMLRPC server.
     *
     * This statically called method is actually the XMLRPC client.
     *
     * @param string $url     The path to the XMLRPC server on the called host.
     * @param string $method  The method to call.
     * @param array $params   A hash containing any necessary parameters for
     *                        the method call.
     * @param $options  Optional associative array of parameters which can be:
     *                  user           - Basic Auth username
     *                  pass           - Basic Auth password
     *                  proxy_host     - Proxy server host
     *                  proxy_port     - Proxy server port
     *                  proxy_user     - Proxy auth username
     *                  proxy_pass     - Proxy auth password
     *                  timeout        - Connection timeout in seconds.
     *                  allowRedirects - Whether to follow redirects or not
     *                  maxRedirects   - Max number of redirects to follow
     *
     * @return mixed            The returned result from the method or a PEAR
     *                          error object on failure.
     */
    function request($url, $method, $params = null, $options = array())
    {
        $options['method'] = 'POST';
        $language = isset($GLOBALS['language']) ? $GLOBALS['language'] :
            (isset($_SERVER['LANG']) ? $_SERVER['LANG'] : '');

        if (!isset($options['timeout'])) {
            $options['timeout'] = 5;
        }
        if (!isset($options['allowRedirects'])) {
            $options['allowRedirects'] = true;
            $options['maxRedirects'] = 3;
        }
        if (!isset($options['proxy_host']) && !empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
            $options = array_merge($options, $GLOBALS['conf']['http']['proxy']);
        }

        require_once 'HTTP/Request.php';
        $http = new HTTP_Request($url, $options);
        if (!empty($language)) {
            $http->addHeader('Accept-Language', $language);
        }
        $http->addHeader('User-Agent', 'Horde RPC client');
        $http->addHeader('Content-Type', 'text/xml');
        $http->addRawPostData(xmlrpc_encode_request($method, $params));

        $result = $http->sendRequest();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        } elseif ($http->getResponseCode() != 200) {
            return PEAR::raiseError(_("Request couldn't be answered. Returned errorcode: ") . $http->getResponseCode(), 'horde.error');
        } elseif (strpos($http->getResponseBody(), '<?xml') === false) {
            return PEAR::raiseError(_("No valid XML data returned"), 'horde.error', null, null, $http->getResponseBody());
        } else {
            $response = @xmlrpc_decode(substr($http->getResponseBody(), strpos($http->getResponseBody(), '<?xml')));
            if (is_array($response) && isset($response['faultString'])) {
                return PEAR::raiseError($response['faultString'], 'horde.error');
            } elseif (is_array($response) && isset($response[0]) &&
                      is_array($response[0]) && isset($response[0]['faultString'])) {
                return PEAR::raiseError($response[0]['faultString'], 'horde.error');
            }
            return $response;
        }
    }

}
