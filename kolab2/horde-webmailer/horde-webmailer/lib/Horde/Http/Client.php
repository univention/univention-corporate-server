<?php
/**
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Http_Client
 */

/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Http_Client
 */
class Horde_Http_Client
{
    /**
     * URI to make our next request to
     * @var string
     */
    protected $_uri = null;

    /**
     * Request headers
     * @var array
     */
    protected $_headers = array();

    /**
     * Proxy server
     * @var string
     */
    protected $_proxyServer = null;

    /**
     * Proxy username
     * @var string
     */
    protected $_proxyUser = null;

    /**
     * Proxy password
     * @var string
     */
    protected $_proxyPass = null;

    /**
     * The most recent HTTP request
     *
     * An array with these values:
     *   'uri'
     *   'method'
     *   'headers'
     *   'data'
     *
     * @var array
     */
    protected $_lastRequest;

    /**
     * The most recent HTTP response
     * @var Horde_Http_Client_Response
     */
    protected $_lastResponse;

    /**
     * Horde_Http_Client constructor.
     *
     * @param array $args Any Http_Client settings to initialize in the
     * constructor. Available settings are:
     *     uri
     *     headers
     *     proxyServer
     *     proxyUser
     *     proxyPass
     */
    public function __construct($args = array())
    {
        if (!ini_get('allow_url_fopen')) {
            throw new Horde_Http_Client_Exception('allow_url_fopen must be enabled');
        }

        foreach ($args as $key => $val) {
            $this->$key = $val;
        }
    }

    /**
     * Set one or more headers
     *
     * @param mixed $headers A hash of header + value pairs, or a single header name
     * @param string $value  A header value
     */
    public function setHeaders($headers, $value = null)
    {
        if (!is_array($headers)) {
            $headers = array($headers => $value);
        }

        foreach ($headers as $header => $value) {
            $this->_headers[$header] = $value;
        }
    }

    /**
     * Get the current value of $header
     *
     * @param string $header Header name to get
     * @return string $header's current value
     */
    public function getHeader($header)
    {
        return isset($this->_headers[$header]) ? $this->_headers[$header] : null;
    }

    /**
     * Send a GET request
     *
     * @return Horde_Http_Client_Response
     */
    public function get($uri = null, $headers = array())
    {
        return $this->request('GET', $uri, null, $headers);
    }

    /**
     * Send a POST request
     *
     * @return Horde_Http_Client_Response
     */
    public function post($uri = null, $data = null, $headers = array())
    {
        return $this->request('POST', $uri, $data, $headers);
    }

    /**
     * Send a PUT request
     *
     * @return Horde_Http_Client_Response
     */
    public function put($uri = null, $data = null, $headers = array())
    {
        // FIXME: suport method override (X-Method-Override: PUT).
        return $this->request('PUT', $uri, $data, $headers);
    }

    /**
     * Send a DELETE request
     *
     * @return Horde_Http_Client_Response
     */
    public function delete($uri = null, $headers = array())
    {
        // FIXME: suport method override (X-Method-Override: DELETE).
        return $this->request('DELETE', $uri, null, $headers);
    }

    /**
     * Send an HTTP request
     *
     * @param string $method HTTP request method (GET, PUT, etc.)
     * @param string $uri URI to request, if different from $this->uri
     * @param mixed $data Request data. Can be an array of form data that will be
     *                    encoded automatically, or a raw string.
     * @param array $headers Any headers specific to this request. They will
     *                       be combined with $this->_headers, and override
     *                       headers of the same name for this request only.
     *
     * @return Horde_Http_Client_Response
     */
    public function request($method, $uri = null, $data = null, $headers = array())
    {
        if (is_null($uri)) {
            $uri = $this->uri;
        }

        if (is_array($data)) {
            $data = http_build_query($data, '', '&');
        }

        $headers = array_merge($this->_headers, $headers);

        // Store the last request for ease of debugging.
        $this->_lastRequest = array(
            'uri' => $uri,
            'method' => $method,
            'headers' => $headers,
            'data' => $data,
        );

        // Stream context config.
        $opts = array('http' => array(
            'method' => $method,
            'header' => implode("\n", $headers),
            'content' => $data));

        // Proxy settings
        if ($this->proxyServer) {
            $opts['http']['proxy'] = 'tcp://' . $this->proxyServer;
            $opts['http']['request_fulluri'] = true;
            if ($this->proxyUser && $this->proxyPass) {
                $headers['Proxy-Authorization'] = 'Basic ' . base64_encode($this->proxyUser . ':' . $this->proxyPass);
            }
        }

        $context = stream_context_create($opts);
        $stream = @fopen($uri, 'rb', false, $context);
        if (!$stream) {
            throw new Horde_Http_Client_Exception('Problem with ' . $uri . ': ', error_get_last());
        }

        $meta = stream_get_meta_data($stream);
        $headers = isset($meta['wrapper_data']) ? $meta['wrapper_data'] : array();

        $this->_lastResponse = new Horde_Http_Client_Response($uri, $stream, $headers);
        return $this->_lastResponse;
    }

    /**
     * Get a client parameter
     *
     * @param string $name  The parameter to get.
     * @return mixed        Parameter value.
     */
    public function __get($name)
    {
        return isset($this->{'_' . $name}) ? $this->{'_' . $name} : null;
    }

    /**
     * Set a client parameter
     *
     * @param string $name   The parameter to set.
     * @param mixed  $value  Parameter value.
     */
    public function __set($name, $value)
    {
        switch ($name) {
        case 'headers':
            $this->setHeaders($value);
            break;
        }

        $this->{'_' . $name} = $value;
    }

}
