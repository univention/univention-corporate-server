<?php
/**
 * The Horde_RPC_soap class provides an SOAP implementation of the
 * Horde RPC system.
 *
 * $Horde: framework/RPC/RPC/soap.php,v 1.10 2004/05/24 16:08:32 jwm Exp $
 *
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_soap extends Horde_RPC {

    /**
     * Resource handler for the RPC server.
     * @var object $_server
     */
    var $_server;

    /**
     * Hash holding all methods' signatures.
     * @var array $__dispatch_map
     */
    var $__dispatch_map = array();

    /**
     * SOAP server constructor
     *
     * @access private
     * @return object   An RPC server instance
     */
    function Horde_RPC_soap()
    {
        parent::Horde_RPC();

        global $registry;

        require_once 'SOAP/Server.php';
        $this->_server = &new SOAP_Server();
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
            $method = str_replace('/', '.', $method);
            $this->__dispatch_map[$method] = array(
                'in' => $signature[0],
                'out' => array('output' => $signature[1])
            );
        }

        $this->__typedef = $registry->listTypes();
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

        if (!$registry->hasMethod($method)) {
            return sprintf(_("Method '%s' is not defined"), $method);
        }

        return $registry->call($method, $params);
    }

    /**
     * Takes an RPC request and returns the result.
     *
     * @param string  The raw request string.
     * @param string  (optional) String specifying what kind of data to
     *                return. Defaults to SOAP request. Possible other values:
     *                "wdsl" and "disco".
     *
     * @return string  The XML encoded response from the server.
     */
    function getResponse($request, $params = null)
    {
        $this->_server->addObjectMap($this, 'urn:horde');

        if (!$params) {
            $this->_server->setCallHandler(array($this, '_dispatcher'));
            /* We can't use Util::bufferOutput() here for some reason. */
            ob_start();
            $this->_server->service($request);
            $output = ob_get_contents();
            ob_end_clean();
        } else {
            require_once 'SOAP/Disco.php';
            $disco = new SOAP_DISCO_Server($this->_server, 'horde');
            if ($params == 'wsdl') {
                $this->_setupDispatchMap();
                $output = $disco->getWSDL();
            } else {
                $output = $disco->getDISCO();
            }
        }

        return $output;
    }

    /**
     * Builds an SOAP request and sends it to the SOAP server.
     *
     * This statically called method is actually the SOAP client.
     *
     * @param string $url       The path to the SOAP server on the called host.
     * @param string $method    The method to call.
     * @param array $params     (optional) A hash containing any necessary
     *                          parameters for the method call.
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
        $soap = &new SOAP_Client($url, false, false, $options);
        return $soap->call($method, $params, $options['namespace']);
    }

}
