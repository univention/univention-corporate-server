<?php

include_once 'Log.php';

// Constant Definitions
define('IMSP_OCTET_COUNT', "/({)([0-9]{1,})(\}$)/");
define('IMSP_MUST_USE_LITERAL', "/[\x80-\xFF\\r\\n\"\\\\]/");
define('IMSP_MUST_USE_QUOTE', "/[\W]/i");

/**
 * The Net_IMSP class provides a common interface to an IMSP server .
 *
 * Required parameters:<pre>
 *   'server'  Hostname of IMSP server.
 *   'port'    Port of IMSP server.</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP.php,v 1.13.10.27 2009-10-02 00:03:01 mrubinsk Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP {

    /**
     * String containing name/IP address of IMSP host.
     *
     * @var string
     */
    var $imsp_server                = 'localhost';

    /**
     * String containing port for IMSP server.
     *
     * @var string
     */
    var $imsp_port                  = '406';

    /**
     * Boolean to set if we should write to a log, if one is set up.
     *
     * @var boolean
     */
    var $logEnabled                 = true;

    /**
     * String buffer containing the last raw NO or BAD response from the
     * server.
     *
     * @var string
     */
    var $lastRawError              = '';

    // Private Declarations
    var $_commandPrefix             = 'A';
    var $_commandCount              = 1;
    var $_tag                       = '';
    var $_stream                    = null;
    var $_lastCommandTag            = 'undefined';
    var $_logger                    = null;
    var $_logSet                    = null;
    var $_logLevel                  = PEAR_LOG_INFO;
    var $_logBuffer                  = array();

    /**
     * Constructor function.
     *
     * @param array $params Hash containing server parameters.
     */
    function Net_IMSP($params)
    {
        if (is_array($params) && !empty($params['server'])) {
            $this->imsp_server = $params['server'];
        }

        if (is_array($params) && !empty($params['port'])) {
            $this->imsp_port = $params['port'];
        }

    }

    /**
     * Initialization function to be called after object is returned.  This
     * allows errors to occur and not break the script.
     *
     * @return mixed  True on success PEAR_Error on connection failure.
     */
    function init()
    {
        $result = $this->imspOpen();

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->writeToLog('Initializing Net_IMSP object.', __FILE__, __LINE__,
                          PEAR_LOG_INFO);
        return true;
    }

    /**
     * Logs out of the server and closes the IMSP stream
     */
    function logout()
    {
        $this->writeToLog('Closing IMSP Connection.', __FILE__, __LINE__,
                          PEAR_LOG_INFO);
        $command_string = 'LOGOUT';
        $result = $this->imspSend($command_string);
        if (is_a($result, 'PEAR_Error')) {
            fclose($this->_stream);
            return $result;
        } else {
            fclose($this->_stream);
            return true;
        }
    }

    /**
     * Returns the raw capability response from the server.
     *
     * @return string  The raw capability response.
     */
    function capability()
    {
        $command_string = 'CAPABILITY';
        $result = $this->imspSend($command_string);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        } else {
            $server_response = $this->imspReceive();
            if (preg_match("/^\* CAPABILITY/", $server_response)) {
                $capability = preg_replace("/^\* CAPABILITY/",
                                           '', $server_response);

                $server_response = $this->imspReceive(); //OK

                if (!$server_response == 'OK') {
                    return $this->imspError('Did not receive the expected response from the server.',
                                            __FILE__, __LINE__);
                } else {
                    $this->writeToLog('CAPABILITY completed OK', __FILE__,
                                      __LINE__, PEAR_LOG_INFO);
                    return $capability;
                }
            }
        }
    }

    /**
     * Attempts to open an IMSP socket with the server.
     *
     * @return mixed  True on success PEAR_Error on failure.
     */
    function imspOpen()
    {
        $fp = @fsockopen($this->imsp_server, $this->imsp_port);
        if (!$fp) {
            return $this->imspError('Connection to IMSP host failed.', __FILE__,
                                    __LINE__);
        }
        $this->_stream = $fp;
        $server_response = $this->imspReceive();
        if (!preg_match("/^\* OK/", $server_response)) {
            fclose($fp);
            return $this->imspError('Did not receive the expected response from the server.', __FILE__, __LINE__);
        }
        return true;
    }

    /**
     * Attempts to send a command to the server.
     *
     * @param string  $commandText Text to send to the server.
     * @param boolean $includeTag  Determines if command tag is prepended.
     * @param boolean  $sendCRLF   Determines if CRLF is appended.
     * @return mixed   True on success PEAR_Error on failure.
     */
    function imspSend($commandText, $includeTag=true, $sendCRLF=true)
    {
        $command_text = '';

        if (!$this->_stream) {
            return $this->imspError('Connection to IMSP host failed.', __FILE__, __LINE__);
        }

        if ($includeTag) {
            $this->_tag = $this->_getNextCommandTag();
            $command_text = "$this->_tag ";
        }

        $command_text .= $commandText;

        if ($sendCRLF) {
            $command_text .= "\r\n";
        }

        $this->writeToLog('To: ' . $command_text, __FILE__,
                          __LINE__, PEAR_LOG_DEBUG);

        if (!fputs($this->_stream, $command_text)) {
            return $this->imspError('Connection to IMSP host failed.', __FILE__, __LINE__);
        } else {
            return true;
        }
    }

    /**
     * Receives a single CRLF terminated server response string
     *
     * @return mixed 'NO', 'BAD', 'OK', raw response or PEAR_Error.
     */
    function imspReceive()
    {
        if (!$this->_stream) {
            return $this->imspError('Connection to IMSP host failed.', __FILE__, __LINE__);
        }
        $result = fgets($this->_stream, 512);
        if (!$result) {
            return $this->imspError('Did not receive the expected response from the server.',
                                    __FILE__, __LINE__);
        }
        $meta = stream_get_meta_data($this->_stream);
        if ($meta['timed_out']) {
            return $this->imspError('Connection to IMSP host failed.' . ': Connection timed out!',
                                    __FILE__, __LINE__);
        }

        $server_response = trim($result);
        $this->writeToLog('From: ' . $server_response, __FILE__,
                          __LINE__, PEAR_LOG_DEBUG);

        /* Parse out the response:
         * First make sure that this is not for a previous command.
         * If it is, it means we did not read all the server responses from
         * the last command...read them now, but throw an error. */
        while (preg_match("/^" . $this->_lastCommandTag
                          ."/", $server_response)) {
            $server_response =
                trim(fgets($this->_stream, 512));
            $this->imspError('Did not receive the expected response from the server.' . ": $server_response",
                             __FILE__, __LINE__);
        }

        $currentTag = $this->_tag;
        if (preg_match("/^" . $currentTag . " NO/", $server_response)) {
            $this->lastRawError = $server_response;
            return 'NO';
        }

        if (preg_match("/^" . $currentTag . " BAD/", $server_response)) {
            $this->imspError('The IMSP server did not understand your request.', __FILE__, __LINE__);
            $this->lastRawError = $server_response;
            return 'BAD';
        }

        if (preg_match("/^" . $currentTag . " OK/", $server_response)) {
            return 'OK';
        }

        /* If it was not a 'NO', 'BAD' or 'OK' response,
         * then it's up to the calling function to decide
         * what to do with it. */
        return $server_response;
    }

    /**
     * Retrieves CRLF terminated response from server and splits it into
     * an array delimited by a <space>.
     *
     * @return array result from explode().
     */
    function getServerResponseChunks()
    {
        $server_response =
            trim(fgets($this->_stream, 512));
        $chunks = explode(' ', $server_response);
        return $chunks;
    }

    /*
     * Receives fixed number of bytes from IMSP socket. Used when
     * server returns a string literal.
     *
     * @param integer $length  Number of bytes to read from socket.
     *
     * @return string  Text of string literal.
     */
    function receiveStringLiteral($length)
    {
        $literal = '';
        do {
            $temp = fread($this->_stream, $length);
            $length -= strlen($temp);
            $literal .= $temp;
        } while ($length > 0 && strlen($temp));
        $this->writeToLog('From{}: ' . $literal, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $literal;
    }

    /**
     * Increments the IMSP command tag token.
     *
     * @access private
     * @return string Next command tag.
     */
    function _getNextCommandTag()
    {
        $this->_lastCommandTag = $this->_tag ? $this->_tag : 'undefined';
        return $this->_commandPrefix . sprintf('%04d', $this->_commandCount++);
    }

    /**
     * Determines if a string needs to be quoted before sending to the server.
     *
     * @param string $string  String to be tested.
     * @return string Original string quoted if needed.
     */
    function quoteSpacedString($string)
    {
        if (strpos($string, ' ') !== false ||
            preg_match(IMSP_MUST_USE_QUOTE, $string)) {
            return '"' . $string . '"';
        } else {
            return $string;
        }
    }

    /**
     * Raises an IMSP error.  Basically, only writes
     * error out to the horde logfile and returns PEAR_Error
     *
     * @param string $err    Either PEAR_Error object or text to write to log.
     * @param string $file   File name where error occured.
     * @param integer $line  Line number where error occured.
     */
    function imspError($err = '', $file=__FILE__, $line=__LINE__)
    {
        if (is_a($err, 'PEAR_Error')) {
            $log_text = $err->getMessage();
        } else {
            $log_text = $err;
        }

        $this->writeToLog($log_text, $file, $line, PEAR_LOG_ERR);
        if (is_a($err, 'PEAR_Error')) {
            return $err;
        } else {
            return PEAR::raiseError($err);
        }
    }

    /**
     * Writes a message to the IMSP logfile.
     *
     * @param string $message  Text to write.
     */
    function writeToLog($message, $file = __FILE__,
                        $line = __LINE__, $priority = PEAR_LOG_INFO)
    {
        if (($this->logEnabled) && ($this->_logSet)) {
            if ($priority > $this->_logLevel) {
                return;
            }

            $logMessage = '[imsp] ' . $message . ' [on line ' . $line . ' of "' . $file . '"]';
            $this->_logger->log($logMessage, $priority);
        } elseif ((!$this->_logSet) && ($this->logEnabled)) {
            $this->_logBuffer[] = array('message'  => $message,
                                        'priority' => $priority,
                                        'file'     => $file,
                                        'line'     => $line
                                        );
        }
    }

    /**
     * Creates a new Log object based on $params
     *
     * @param  array  $params Log object parameters.
     * @return mixed  True on success or PEAR_Error on failure.
     */
    function setLogger($params)
    {
        if (!empty($params['enabled'])) {
            $this->_logLevel = $params['priority'];
            $logger = &Log::singleton($params['type'], $params['name'],
                                      $params['ident'], $params['params']);

            if (is_a($logger, 'PEAR_Error')) {
                $this->logEnabled = false;
                $this->_logSet = false;
                return $logger;
            } else {
                $this->_logSet = true;
                $this->_logger = &$logger;
                $this->logEnabled = true;
                $this->_writeLogBuffer();
                return true;
            }
        } else {
            $this->logEnabled = false;
        }
    }

    /**
     * Writes out contents of $_logBuffer to log file.  Allows messages
     * to be logged during initialization of object before Log object is
     * instantiated.
     *
     * @access private
     */
    function _writeLogBuffer()
    {
        for ($i = 0; $i < count($this->_logBuffer); $i++) {
            $this->writeToLog($this->_logBuffer[$i]['message'],
                              $this->_logBuffer[$i]['file'],
                              $this->_logBuffer[$i]['line'],
                              $this->_logBuffer[$i]['priority']);
        }
    }

    /**
     * Attempts to create a Net_IMSP object based on $driver.
     * Must be called as $imsp = &Net_IMSP::factory($driver, $params);
     *
     * @param  string $driver Type of Net_IMSP object to return.
     * @param  mixed  $params  Any parameters needed by the Net_IMSP object.
     * @return mixed  The requested Net_IMSP object or PEAR_Error on failure.
     */
    function factory($driver, $params)
    {
        $driver = basename($driver);
        if (empty($driver) || $driver == 'none') {
            return new Net_IMSP($params);
        }

        include_once dirname(__FILE__) . '/IMSP/' . $driver . '.php';
        $class = 'Net_IMSP_' . $driver;
        if (class_exists($class)) {
            return new $class($params);
        } else {
            Horde::fatal(PEAR::raiseError(sprintf(_("Unable to load the definition of %s."), $class)), __FILE__, __LINE__);
        }
    }

    /**
     * Attempts to return a Net_IMSP object based on $driver.  Only
     * creates a new object if one with the same parameters already
     * doesn't exist.
     * Must be called as $imsp = &Net_IMSP::singleton($driver, $params);
     *
     * @param  string $driver Type of Net_IMSP object to return.
     * @param  mixed  $params Any parameters needed by the Net_IMSP object.
     * @return mixed  Reference to the Net_IMSP object or PEAR_Error on failure.
     */
    function &singleton($driver, $params)
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = Net_IMSP::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
