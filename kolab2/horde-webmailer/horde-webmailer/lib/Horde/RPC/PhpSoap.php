<?php
/**
 * The Horde_RPC_PhpSoap class provides a PHP 5 Soap implementation
 * of the Horde RPC system.
 *
 * $Horde: framework/RPC/RPC/PhpSoap.php,v 1.1.2.6 2009-11-06 14:35:37 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.2
 * @package Horde_RPC
 */
class Horde_RPC_PhpSoap extends Horde_RPC {

    /**
     * Resource handler for the RPC server.
     *
     * @var object
     */
    var $_server;

    /**
     * List of types to emit in the WSDL.
     *
     * @var array
     */
    var $_allowedTypes = array();

    /**
     * List of method names to allow.
     *
     * @var array
     */
    var $_allowedMethods = array();

    /**
     * Name of the SOAP service to use in the WSDL.
     *
     * @var string
     */
    var $_serviceName = null;

    /**
     * SOAP server constructor
     *
     * @access private
     */
    public function __construct($params = array())
    {
        NLS::setCharset('UTF-8');

        parent::Horde_RPC($params);

        if (!empty($params['allowedTypes'])) {
            $this->_allowedTypes = $params['allowedTypes'];
        }
        if (!empty($params['allowedMethods'])) {
            $this->_allowedMethods = $params['allowedMethods'];
        }
        if (!empty($params['serviceName'])) {
            $this->_serviceName = $params['serviceName'];
        }

        $this->_server = new SoapServer(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/rpc.php?wsdl', true, -1));
        $this->_server->addFunction(SOAP_FUNCTIONS_ALL);
        $this->_server->setClass('Horde_RPC_PhpSoap_Caller', $params);
    }

    /**
     * Takes an RPC request and returns the result.
     *
     * @param string  The raw request string.
     *
     * @return string  The XML encoded response from the server.
     */
    function getResponse($request)
    {
        /* We can't use Util::bufferOutput() here for some reason. */
        $beginTime = time();
        ob_start();
        $this->_server->handle($request);
        Horde::logMessage(
            sprintf('SOAP call: %s(%s) by %s serviced in %d seconds, sent %d bytes in response',
                    $GLOBALS['__horde_rpc_PhpSoap']['lastMethodCalled'],
                    implode(', ', array_map(create_function('$a', 'return is_array($a) ? "Array" : $a;'),
                                            $GLOBALS['__horde_rpc_PhpSoap']['lastMethodParams'])),
                    Auth::getAuth(),
                    time() - $beginTime,
                    ob_get_length()),
            __FILE__, __LINE__, PEAR_LOG_INFO
        );
        return ob_get_clean();
    }

    /**
     * Builds a SOAP request and sends it to the SOAP server.
     *
     * This statically called method is actually the SOAP client.
     *
     * @param string $url     The path to the SOAP server on the called host.
     * @param string $method  The method to call.
     * @param array $params   A hash containing any necessary parameters for
     *                        the method call.
     * @param $options  Optional associative array of parameters which can be:
     *                  user                - Basic Auth username
     *                  pass                - Basic Auth password
     *                  proxy_host          - Proxy server host
     *                  proxy_port          - Proxy server port
     *                  proxy_user          - Proxy auth username
     *                  proxy_pass          - Proxy auth password
     *                  timeout             - Connection timeout in seconds.
     *                  allowRedirects      - Whether to follow redirects or not
     *                  maxRedirects        - Max number of redirects to follow
     *                  namespace
     *                  soapaction
     *                  from                - SMTP, from address
     *                  transfer-encoding   - SMTP, sets the
     *                                        Content-Transfer-Encoding header
     *                  subject             - SMTP, subject header
     *                  headers             - SMTP, array-hash of extra smtp
     *                                        headers
     *
     * @return mixed            The returned result from the method or a PEAR
     *                          error object on failure.
     */
    public function request($url, $method, $params = null, $options = array())
    {
        if (!isset($options['timeout'])) {
            $options['timeout'] = 5;
        }
        if (!isset($options['allowRedirects'])) {
            $options['allowRedirects'] = true;
            $options['maxRedirects']   = 3;
        }
        if (isset($options['user'])) {
            $options['login'] = $options['user'];
            unset($options['user']);
        }
        if (isset($options['pass'])) {
            $options['password'] = $options['pass'];
            unset($options['pass']);
        }
        $options['location'] = $url;
        $options['uri'] = $options['namespace'];

        $soap = new SoapClient(null, $options);
        return $soap->__soapCall($method, $params);
    }

}

class Horde_RPC_PhpSoap_Caller {

    /**
     * List of method names to allow.
     *
     * @var array
     */
    protected $_allowedMethods = array();

    /**
     */
    public function __construct($params = array())
    {
        if (!empty($params['allowedMethods'])) {
            $this->_allowedMethods = $params['allowedMethods'];
        }
    }

    /**
     * Will be registered as the handler for all methods called in the
     * SOAP server and will call the appropriate function through the registry.
     *
     * @todo  PEAR SOAP operates on a copy of this object at some unknown
     *        point and therefore doesn't have access to instance
     *        variables if they're set here. Instead, globals are used
     *        to track the method name and args for the logging code.
     *        Once this is PHP 5-only, the globals can go in favor of
     *        instance variables.
     *
     * @access private
     *
     * @param string $method    The name of the method called by the RPC request.
     * @param array $params     The passed parameters.
     * @param mixed $data       Unknown.
     *
     * @return mixed            The result of the called registry method.
     */
    public function __call($method, $params)
    {
        $method = str_replace('.', '/', $method);

        if (!empty($this->_params['allowedMethods']) &&
            !in_array($method, $this->_params['allowedMethods'])) {
            return sprintf(_("Method \"%s\" is not defined"), $method);
        }

        $GLOBALS['__horde_rpc_PhpSoap']['lastMethodCalled'] = $method;
        $GLOBALS['__horde_rpc_PhpSoap']['lastMethodParams'] =
            !empty($params) ? $params : array();

        if (!$GLOBALS['registry']->hasMethod($method)) {
            return sprintf(_("Method \"%s\" is not defined"), $method);
        }

        return $GLOBALS['registry']->call($method, $params);
    }

}
