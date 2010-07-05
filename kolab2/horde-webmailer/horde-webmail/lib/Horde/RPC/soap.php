<?php
/**
 * The Horde_RPC_soap class provides an SOAP implementation of the
 * Horde RPC system.
 *
 * $Horde: framework/RPC/RPC/soap.php,v 1.13.10.17 2009-01-06 15:23:32 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_soap extends Horde_RPC {

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
     * Hash holding all methods' signatures.
     *
     * @var array
     */
    var $__dispatch_map = array();

    /**
     * SOAP server constructor
     *
     * @access private
     */
    function Horde_RPC_soap($params = null)
    {
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

        require_once 'SOAP/Server.php';
        $this->_server = new SOAP_Server();
        $this->_server->_auto_translation = true;
    }

    /**
     * Fills a hash that is used by the SOAP server with the signatures of
     * all available methods.
     */
    function _setupDispatchMap()
    {
        global $registry;

        $methods = $registry->listMethods();
        foreach ($methods as $method) {
            $signature = $registry->getSignature($method);
            if (!is_array($signature)) {
                continue;
            }
            if (!empty($this->_allowedMethods) &&
                !in_array($method, $this->_allowedMethods)) {
                continue;
            }
            $method = str_replace('/', '.', $method);
            $this->__dispatch_map[$method] = array(
                'in' => $signature[0],
                'out' => array('output' => $signature[1])
            );
        }

        $this->__typedef = array();
        foreach ($registry->listTypes() as $type => $params) {
            if (!empty($this->_allowedTypes) &&
                !in_array($type, $this->_allowedTypes)) {
                continue;
            }

            $this->__typedef[$type] = $params;
        }
    }

    /**
     * Returns the signature of a method.
     * Internally used by the SOAP server.
     *
     * @param string $method  A method name.
     *
     * @return array  An array describing the method's signature.
     */
    function __dispatch($method)
    {
        global $registry;
        $method = str_replace('.', '/', $method);

        $signature = $registry->getSignature($method);
        if (!is_array($signature)) {
            return null;
        }

        return array('in' => $signature[0],
                     'out' => array('output' => $signature[1]));
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
    function _dispatcher($method, $params)
    {
        global $registry;
        $method = str_replace('.', '/', $method);

        if (!empty($this->_params['allowedMethods']) &&
            !in_array($method, $this->_params['allowedMethods'])) {
            return sprintf(_("Method \"%s\" is not defined"), $method);
        }

        $GLOBALS['__horde_rpc_soap']['lastMethodCalled'] = $method;
        $GLOBALS['__horde_rpc_soap']['lastMethodParams'] =
            !empty($params) ? $params : array();

        if (!$registry->hasMethod($method)) {
            return sprintf(_("Method \"%s\" is not defined"), $method);
        }

        $this->_server->bindWSDL(Horde::url($registry->get('webroot', 'horde') . '/rpc.php?wsdl', true, false));
        return $registry->call($method, $params);
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
        $this->_server->addObjectMap($this, 'urn:horde');

        if ($request == 'disco' || $request == 'wsdl') {
            require_once 'SOAP/Disco.php';
            $disco = new SOAP_DISCO_Server($this->_server,
                !empty($this->_serviceName) ? $this->_serviceName : 'horde');
            if ($request == 'wsdl') {
                $this->_setupDispatchMap();
                return $disco->getWSDL();
            } else {
                return $disco->getDISCO();
            }
        }

        $this->_server->setCallHandler(array($this, '_dispatcher'));

        /* We can't use Util::bufferOutput() here for some reason. */
        $beginTime = time();
        ob_start();
        $this->_server->service($request);
        Horde::logMessage(
            sprintf('SOAP call: %s(%s) by %s serviced in %d seconds, sent %d bytes in response',
                    $GLOBALS['__horde_rpc_soap']['lastMethodCalled'],
                    is_array($GLOBALS['__horde_rpc_soap']['lastMethodParams'])
                        ? implode(', ', array_map(create_function('$a', 'return is_array($a) ? "Array" : $a;'),
                                                  $GLOBALS['__horde_rpc_soap']['lastMethodParams']))
                        : '',
                    Auth::getAuth(),
                    time() - $beginTime,
                    ob_get_length()),
            __FILE__, __LINE__, PEAR_LOG_INFO
        );
        return ob_get_clean();
    }

    /**
     * Builds an SOAP request and sends it to the SOAP server.
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
    function request($url, $method, $params = null, $options = array())
    {
        if (!isset($options['timeout'])) {
            $options['timeout'] = 5;
        }
        if (!isset($options['allowRedirects'])) {
            $options['allowRedirects'] = true;
            $options['maxRedirects']   = 3;
        }

        require_once 'SOAP/Client.php';
        $soap = new SOAP_Client($url, false, false, $options);
        return $soap->call($method, $params, $options['namespace']);
    }

}
