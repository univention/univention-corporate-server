<?php
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.02 of the PHP license,      |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Damian Alejandro Fernandez Sosa <damlists@cnba.uba.ar>      |
// |          Chuck Hagenbuch <chuck@horde.org>                           |
// |          Jon Parise <jon@php.net>                                    |
// |                                                                      |
// +----------------------------------------------------------------------+

require_once 'Net/Socket.php';

/**
 * Provides an implementation of the LMTP protocol using PEAR's
 * Net_Socket:: class.
 *
 * @package Net_LMTP
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@php.net>
 * @author  Damian Alejandro Fernandez Sosa <damlists@cnba.uba.ar>
 */
class Net_LMTP {


    /**
     * The server to connect to.
     * @var string
     */
    var $_host;

    /**
     * The port to connect to.
     * @var int
     */
    var $_port;

    /**
     * The value to give when sending LHLO.
     * @var string
     */
    var $_localhost;

    /**
     * Should debugging output be enabled?
     * @var boolean
     * @access private
     */
    var $_debug = false;

    /**
     * The socket resource being used to connect to the LMTP server.
     * @var resource
     * @access private
     */
    var $_socket = null;

    /**
     * The most recent server response code.
     * @var int
     * @access private
     */
    var $_code = -1;

    /**
     * The most recent server response arguments.
     * @var array
     * @access private
     */
    var $_arguments = array();

    /**
     * Stores detected features of the LMTP server.
     * @var array
     * @access private
     */
    var $_esmtp = array();


   /**
    * The auth methods this class support
    * @var array
    */
    var $supportedAuthMethods=array('DIGEST-MD5', 'CRAM-MD5', 'LOGIN');


    /**
    * The auth methods this class support
    * @var array
    */
    var $supportedSASLAuthMethods=array('DIGEST-MD5', 'CRAM-MD5');




    /**
     * Instantiates a new Net_LMTP object, overriding any defaults
     * with parameters that are passed in.
     *
     * @param string The server to connect to.
     * @param int The port to connect to.
     * @param string The value to give when sending LHLO.
     *
     * @access  public
     * @since   1.0
     */
    function Net_LMTP($host = 'localhost', $port = 2003, $localhost = 'localhost')
    {
        $this->_host = $host;
        $this->_port = $port;
        $this->_localhost = $localhost;
        $this->_socket = new Net_Socket();

       if ((@include_once 'Auth/SASL.php') == false) {
            foreach($this->supportedSASLAuthMethods as $SASLMethod){
                $pos = array_search( $SASLMethod , $this->supportedAuthMethods);
                unset($this->supportedAuthMethods[$pos]);
            }
        }


    }

    /**
     * Set the value of the debugging flag.
     *
     * @param   boolean $debug      New value for the debugging flag.
     *
     * @access  public
     * @since   1.0
     */
    function setDebug($debug)
    {
        $this->_debug = $debug;
    }

    /**
     * Send the given string of data to the server.
     *
     * @param   string  $data       The string of data to send.
     *
     * @return  mixed   True on success or a PEAR_Error object on failure.
     *
     * @access  private
     * @since   1.0
     */
    function _send($data)
    {
        if ($this->_debug) {
            echo "DEBUG: Send: $data\n";
        }

        if (PEAR::isError($error = $this->_socket->write($data))) {
            return new PEAR_Error('Failed to write to socket: ' .
                                  $error->getMessage());
        }

        return true;
    }

    /**
     * Send a command to the server with an optional string of arguments.
     * A carriage return / linefeed (CRLF) sequence will be appended to each
     * command string before it is sent to the LMTP server.
     *
     * @param   string  $command    The LMTP command to send to the server.
     * @param   string  $args       A string of optional arguments to append
     *                              to the command.
     *
     * @return  mixed   The result of the _send() call.
     *
     * @access  private
     * @since   1.0
     */
    function _put($command, $args = '')
    {
        if (!empty($args)) {
            return $this->_send($command . ' ' . $args . "\r\n");
        }

        return $this->_send($command . "\r\n");
    }

    /**
     * Read a reply from the LMTP server.  The reply consists of a response
     * code and a response message.
     *
     * @param   mixed   $valid      The set of valid response codes.  These
     *                              may be specified as an array of integer
     *                              values or as a single integer value.
     *
     * @return  mixed   True if the server returned a valid response code or
     *                  a PEAR_Error object is an error condition is reached.
     *
     * @access  private
     * @since   1.0
     *
     * @see     getResponse
     */
    function _parseResponse($valid)
    {
        $this->_code = -1;
        $this->_arguments = array();

        while ($line = $this->_socket->readLine()) {
            if ($this->_debug) {
                echo "DEBUG: Recv: $line\n";
            }

            /* If we receive an empty line, the connection has been closed. */
            if (empty($line)) {
                $this->disconnect();
                return new PEAR_Error("Connection was unexpectedly closed");
            }

            /* Read the code and store the rest in the arguments array. */
            $code = substr($line, 0, 3);
            $this->_arguments[] = trim(substr($line, 4));

            /* Check the syntax of the response code. */
            if (is_numeric($code)) {
                $this->_code = (int)$code;
            } else {
                $this->_code = -1;
                break;
            }

            /* If this is not a multiline response, we're done. */
            if (substr($line, 3, 1) != '-') {
                break;
            }
        }

        /* Compare the server's response code with the valid code. */
        if (is_int($valid) && ($this->_code === $valid)) {
            return true;
        }

        /* If we were given an array of valid response codes, check each one. */
        if (is_array($valid)) {
            foreach ($valid as $valid_code) {
                if ($this->_code === $valid_code) {
                    return true;
                }
            }
        }

        return new PEAR_Error("Invalid response code received from server");
    }

    /**
     * Return a 2-tuple containing the last response from the LMTP server.
     *
     * @return  array   A two-element array: the first element contains the
     *                  response code as an integer and the second element
     *                  contains the response's arguments as a string.
     *
     * @access  public
     * @since   1.0
     */
    function getResponse()
    {
        return array($this->_code, join("\n", $this->_arguments));
    }

    /**
     * Attempt to connect to the LMTP server.
     *
     * @param   int     $timeout    The timeout value (in seconds) for the
     *                              socket connection.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function connect($timeout = null)
    {
        $result = $this->_socket->connect($this->_host, $this->_port,
                                          false, $timeout);
        if (PEAR::isError($result)) {
            return new PEAR_Error('Failed to connect socket: ' .
                                  $result->getMessage());
        }

        if (PEAR::isError($error = $this->_parseResponse(220))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_negotiate())) {
            return $error;
        }

        return true;
    }

    /**
     * Attempt to disconnect from the LMTP server.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function disconnect()
    {
        if (PEAR::isError($error = $this->_put('QUIT'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(221))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_socket->disconnect())) {
            return new PEAR_Error('Failed to disconnect socket: ' .
                                  $error->getMessage());
        }

        return true;
    }

    /**
     * Attempt to send the LHLO command and obtain a list of ESMTP
     * extensions available
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     *
     * @access private
     * @since  1.0
     */
    function _negotiate()
    {
        if (PEAR::isError($error = $this->_put('LHLO', $this->_localhost))) {
            return $error;
        }

        if (PEAR::isError($this->_parseResponse(250))) {
            return new PEAR_Error('LHLO was not accepted: ', $this->_code);
            return true;
        }

        foreach ($this->_arguments as $argument) {
            $verb = strtok($argument, ' ');
            $arguments = substr($argument, strlen($verb) + 1,
                                strlen($argument) - strlen($verb) - 1);
            $this->_esmtp[$verb] = $arguments;
        }

        return true;
    }

    /**
     * Returns the name of the best authentication method that the server
     * has advertised.
     *
     * @return mixed    Returns a string containing the name of the best
     *                  supported authentication method or a PEAR_Error object
     *                  if a failure condition is encountered.
     * @access private
     * @since  1.0
     */
    function _getBestAuthMethod()
    {
        $available_methods = explode(' ', $this->_esmtp['AUTH']);

        foreach ($this->supportedAuthMethods as $method) {
            if (in_array($method, $available_methods)) {
                return $method;
            }
        }

        return new PEAR_Error('No supported authentication methods');
    }

    /**
     * Attempt to do LMTP authentication.
     *
     * @param string The userid to authenticate as.
     * @param string The password to authenticate with.
     * @param string The requested authentication method.  If none is
     *               specified, the best supported method will be used.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function auth($uid, $pwd , $method = '')
    {
        if (!array_key_exists('AUTH', $this->_esmtp)) {
            return new PEAR_Error('LMTP server does no support authentication');
        }

        /*
         * If no method has been specified, get the name of the best supported
         * method advertised by the LMTP server.
         */
        if (empty($method) || $method === true ) {
            if (PEAR::isError($method = $this->_getBestAuthMethod())) {
                /* Return the PEAR_Error object from _getBestAuthMethod(). */
                return $method;
            } 
        } else {
            $method = strtoupper($method);
        }

        switch ($method) {
            case 'DIGEST-MD5':
                $result = $this->_authDigest_MD5($uid, $pwd);
                break;
            case 'CRAM-MD5':
                $result = $this->_authCRAM_MD5($uid, $pwd);
                break;
            case 'LOGIN':
                $result = $this->_authLogin($uid, $pwd);
                break;
            case 'PLAIN':
                $result = $this->_authPlain($uid, $pwd);
                break;
            default : 
                $result = new PEAR_Error("$method is not a supported authentication method");
                break;
        }

        /* If an error was encountered, return the PEAR_Error object. */
        if (PEAR::isError($result)) {
            return $result;
        }

        /* RFC-2554 requires us to re-negotiate ESMTP after an AUTH. */
        if (PEAR::isError($error = $this->_negotiate())) {
            return $error;
        }

        return true;
    }

    /* Authenticates the user using the DIGEST-MD5 method.
     *
     * @param string The userid to authenticate as.
     * @param string The password to authenticate with.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access private
     * @since  1.0
     */
    function _authDigest_MD5($uid, $pwd)
    {


        if (PEAR::isError($error = $this->_put('AUTH', 'DIGEST-MD5'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(334))) {
            return $error;
        }

        $challenge = base64_decode($this->_arguments[0]);
        $digest = &Auth_SASL::factory('digestmd5');
        $auth_str = base64_encode($digest->getResponse($uid, $pwd, $challenge,
                                                       $this->_host, "smtp"));

        if (PEAR::isError($error = $this->_put($auth_str ))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(334))) {
            return $error;
        }

        /*
         * We don't use the protocol's third step because LMTP doesn't allow
         * subsequent authentication, so we just silently ignore it.
         */
        if (PEAR::isError($error = $this->_put(' '))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(235))) {
            return $error;
        }
    }

    /* Authenticates the user using the CRAM-MD5 method.
     *
     * @param string The userid to authenticate as.
     * @param string The password to authenticate with.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access private
     * @since  1.0
     */
    function _authCRAM_MD5($uid, $pwd)
    {


        if (PEAR::isError($error = $this->_put('AUTH', 'CRAM-MD5'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(334))) {
            return $error;
        }

        $challenge = base64_decode($this->_arguments[0]);
        $cram = &Auth_SASL::factory('crammd5');
        $auth_str = base64_encode($cram->getResponse($uid, $pwd, $challenge));

        if (PEAR::isError($error = $this->_put($auth_str))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(235))) {
            return $error;
        }
    }

    /**
     * Authenticates the user using the LOGIN method.
     *
     * @param string The userid to authenticate as.
     * @param string The password to authenticate with.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access private 
     * @since  1.0
     */
    function _authLogin($uid, $pwd)
    {
        if (PEAR::isError($error = $this->_put('AUTH', 'LOGIN'))) { 
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(334))) {
            return $error;
        }

        if (PEAR::isError($error = $this->_put(base64_encode($uid)))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(334))) {
            return $error;
        }

        if (PEAR::isError($error = $this->_put(base64_encode($pwd)))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(235))) {
            return $error;
        }

        return true;
    }

    /**
     * Authenticates the user using the PLAIN method.
     *
     * @param string The userid to authenticate as.
     * @param string The password to authenticate with.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access private 
     * @since  1.0
     */
    function _authPlain($uid, $pwd)
    {
        if (PEAR::isError($error = $this->_put('AUTH', 'PLAIN'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(334))) {
            return $error;
        }

        $auth_str = base64_encode(chr(0) . $uid . chr(0) . $pwd);

        if (PEAR::isError($error = $this->_put($auth_str))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(235))) {
            return $error;
        }

        return true;
    }

    /**
     * Send the MAIL FROM: command.
     *
     * @param string The sender (reverse path) to set.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function mailFrom($sender)
    {
        if (PEAR::isError($error = $this->_put('MAIL', "FROM:<$sender>"))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(250))) {
            return $error;
        }

        return true;
    }

    /**
     * Send the RCPT TO: command.
     *
     * @param string The recipient (forward path) to add.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function rcptTo($recipient)
    {
        if (PEAR::isError($error = $this->_put('RCPT', "TO:<$recipient>"))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(array(250, 251)))) {
            return $error;
        }

        return true;
    }

    /**
     * Send the DATA command.
     *
     * @param string The message body to send.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function data($data)
    {

        if (isset($this->_esmtp['SIZE']) && ($this->_esmtp['SIZE'] > 0)) {
            if (strlen($data) >= $this->_esmtp['SIZE']) {
                $this->disconnect();
                return new PEAR_Error('Message size excedes the server limit');
            }
        }
    

        /*
         * Change Unix (\n) and Mac (\r) linefeeds into Internet-standard CRLF
         * (\r\n) linefeeds.
         */
        $data = preg_replace("/([^\r]{1})\n/", "\\1\r\n", $data);
        $data = preg_replace("/\n\n/", "\n\r\n", $data);

        /*
         * Because a single leading period (.) signifies an end to the data,
         * legitimate leading periods need to be "doubled" (e.g. '..').
         */
        $data = preg_replace("/\n\./", "\n..", $data);

        if (PEAR::isError($error = $this->_put('DATA'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(354))) {
            return $error;
        }

        if (PEAR::isError($this->_send($data . "\r\n.\r\n"))) {
            return new PEAR_Error('write to socket failed');
        }
        if (PEAR::isError($error = $this->_parseResponse(250))) {
            return $error;
        }

        return true;
    }

    /**
     * Send the RSET command.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function rset()
    {
        if (PEAR::isError($error = $this->_put('RSET'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(250))) {
            return $error;
        }

        return true;
    }
    /**
     * Send the NOOP command.
     *
     * @return mixed Returns a PEAR_Error with an error message on any
     *               kind of failure, or true on success.
     * @access public
     * @since  1.0
     */
    function noop()
    {
        if (PEAR::isError($error = $this->_put('NOOP'))) {
            return $error;
        }
        if (PEAR::isError($error = $this->_parseResponse(250))) {
            return $error;
        }

        return true;
    }
}

?>
