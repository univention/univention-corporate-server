<?php

include_once 'Log.php';

// Constant Definitions
define('IMSP_CRLF', "\r\n");
define('IMSP_DEFAULT_RESPONSE_LENGTH',512);
define('IMSP_OCTET_COUNT', "/({)([0-9]{1,})(\}$)/");
define('IMSP_MUST_USE_LITERAL', "/[^a-z0-9\s\-,]/i");

// These define regExp that should match the respective server
// response strings.
define('IMSP_CONNECTION_OK', "/^\* OK/");
define('IMSP_COMMAND_CONTINUATION_RESPONSE', "/^\+/");
define('IMSP_CAPABILITY_RESPONSE', "/^\* CAPABILITY/");

// Exit code values
define('IMSP_EXIT_LOGIN_FAILED', 'Login to IMSP host failed.');
define('IMSP_CONNECTION_FAILURE', 'Connection to IMSP host failed.');
define('IMSP_UNEXPECTED_RESPONSE', 'Did not receive the expected response from the server.');
define('IMSP_SYNTAX_ERROR', 'The IMSP server did not understand your request.');
define('IMSP_NO', 'IMSP server is unable to perform your request.');
define('IMSP_EXIT_BAD_ARGUMENT', 'The wrong type of arguement was passed to this function');
define('IMSP_NO_CONTINUATION_RESPONSE', 'Did not receive expexted command continuation response from IMSP server.');

/**
 * The Net_IMSP class provides a common interface to an IMSP server .
 *
 * Required parameters:
 * =========================
 * 'server' -- Hostname of IMSP server.
 * 'port'   -- Port of IMSP server.
 *
 * $Horde: framework/Net_IMSP/IMSP.php,v 1.12 2004/04/19 20:27:37 chuck Exp $
 *
 * Copyright 2003-2004 Michael Rubinsky <mike@theupstairsroom.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @version $Revision: 1.1.2.1 $
 * @author  Michael Rubinsky <mike@theupstairsroom.com>
 * @package Net_IMSP
 */
class Net_IMSP {

    /**
     * String containing name/IP address of imsp host.
     * @var string $imsp_server
     */
    var $imsp_server                = 'localhost';

    /**
     * String containing port for imsp server.
     * @var string $imsp_port
     */
    var $imsp_port                  = '406';

    /**
     * Boolean to set if we should write to a log, if one is set up.
     * @var boolean $logEnabled
     */
    var $logEnabled                 = true;

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
     * @access public
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
     * @access public
     * @return mixed  True on success PEAR_Error on connection failure.
     */
    function init()
    {
        $result = $this->imspOpen();

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->writeToLog('Initializing Net_IMSP object.', __FILE__, __LINE__,
                          PEAR_LOG_DEBUG);
        return true;
    }

    /**
     * Logs out of the server and closes the IMSP stream
     *
     *@access public
     */
    function logout()
    {
        $this->writeToLog('Closing Connection.');
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
     * @access public
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

            if (preg_match(IMSP_CAPABILITY_RESPONSE, $server_response)) {
                $capability = preg_replace(IMSP_CAPABILITY_RESPONSE,
                                           '', $server_response);
                $server_response = $this->imspReceive(); //OK

                if (!$server_response == 'OK') {
                    return $this->imspError(IMSP_UNEXPECTED_RESPONSE,
                                            __FILE__,__LINE__);
                } else {
                    $this->writeToLog('CAPABILITY completed OK');
                    return $capability;
                }
            }
        }
    }

    /**
     * Attempts to open an IMSP socket with the server.
     *
     * @access public
     * @return mixed  True on success PEAR_Error on failure.
     */
    function imspOpen()
    {
        $fp = @fsockopen($this->imsp_server, $this->imsp_port);

        // Check for failure
        if (!$fp) {
            return $this->imspError(IMSP_CONNECTION_FAILURE, __FILE__,
                                    __LINE__);
        }

        $this->_stream = $fp;
        $server_response = $this->imspReceive();

        if (!preg_match(IMSP_CONNECTION_OK, $server_response)) {
            fclose($fp);
            return $this->imspError(IMSP_UNEXPECTED_RESPONSE,__FILE__,__LINE__);
        }

        return true;
    }

    /**
     * Attempts to send a command to the server.
     *
     * @access public
     * @param string  $commandText Text to send to the server.
     * @param boolean $includeTag  Determines if command tag is prepended.
     * @param boolean  $sendCRLF   Determines if CRLF is appended.
     * @return mixed   True on success PEAR_Error on failure.
     */
    function imspSend($commandText, $includeTag=true, $sendCRLF=true)
    {
        $command_text = '';

        if (!$this->_stream){
            return $this->imspError(IMSP_CONNECTION_FAILURE,__FILE__,__LINE__);
        }

        if ($includeTag) {
            $this->_tag = $this->_getNextCommandTag();
            $command_text = "$this->_tag ";
        }

        $command_text .= $commandText;

        if ($sendCRLF) {
            $command_text .= IMSP_CRLF;
        }

        $this->writeToLog('To: ' . $command_text, __FILE__,
                          __LINE__,PEAR_LOG_DEBUG);

        if (!fputs($this->_stream, $command_text)) {
            return $this->imspError(IMSP_CONNECTION_FAILURE,__FILE__,__LINE__);
        } else {
            return true;
        }
    }

    /**
     * Receives a single CRLF terminated server response string
     *
     * @access public
     * @return mixed 'NO', 'BAD', 'OK', raw response or PEAR_Error.
     */
    function imspReceive()
    {
        if (!$this->_stream){
            return $this->imspError(IMSP_CONNECTION_FAILURE,__FILE__,__LINE__);
        }

        $result = fgets($this->_stream, IMSP_DEFAULT_RESPONSE_LENGTH);

        if (!$result) {
            return $this->imspError(IMSP_UNEXPECTED_RESPONSE,
                                    __FILE__,__LINE__);
        }

        $server_response = trim($result);
        $this->writeToLog('From: ' . $server_response, __FILE__,
                          __LINE__, PEAR_LOG_DEBUG);

        /**
         * Parse out the response:
         * First make sure that this is not for a previous command.
         * If it is, it means we did not read all the server responses from
         * the last command...read them now, but throw an error.
         */
        while (preg_match("/^" . $this->_lastCommandTag
                          ."/", $server_response)) {
            $server_response =
                trim(fgets($this->_stream,IMSP_DEFAULT_RESPONSE_LENGTH));
            $this->imspError(IMSP_UNEXPECTED_RESPONSE . ": $server_response",
                             __FILE__,__LINE__);
        }

        $currentTag = $this->_tag;

        if (preg_match("/^" . $currentTag . " NO/", $server_response)) {
            return 'NO';
        }

        if (preg_match("/^" . $currentTag . " BAD/", $server_response)) {
            $this->imspError(IMSP_SYNTAX_ERROR,__FILE__,__LINE__);
            return 'BAD';
        }

        if (preg_match("/^" . $currentTag . " OK/", $server_response)) {
            return 'OK';
        }

        /**
         * If it was not a 'NO', 'BAD' or 'OK' response,
         * then it's up to the calling function to decide
         * what to do with it.
         */
        return $server_response;
    }

    /**
     * Retrieves CRLF terminated response from server and splits it into
     * an array delimited by a <space>.
     *
     * @access public
     * @return array result from split().
     */
    function getServerResponseChunks()
    {
        $server_response =
            trim(fgets($this->_stream,IMSP_DEFAULT_RESPONSE_LENGTH));
        $chunks = split(' ', $server_response);
        return $chunks;
    }

    /*
     * Receives fixed number of bytes from imsp socket. Used when
     * server returns a string literal.
     *
     * @access public
     * @param int $length Number of bytes to read from socket.
     * @return string Text of string literal.
     */
    function receiveStringLiteral($length)
    {
        $temp = trim(fread($this->_stream, $length));
        $this->writeToLog('From{}: ' . $temp, __FILE__,
                          __LINE__, PEAR_LOG_DEBUG);
        return $temp;
    }

    /**
     * Increments the imsp command tag token.
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
     * Determines if a string needs to be quoted before sending to the
     * server.
     *
     * @access public
     * @param string $string  String to be tested.
     * @return string Original string quoted if needed.
     */
    function quoteSpacedString($string)
    {
        if (strstr($string, ' ')) {
            return '"' . $string . '"';
        } else {
            return $string;
        }
    }

    /**
     * Raises an 'imsp' error.  Basically, only writes
     * error out to the horde logfile and returns PEAR_Error
     *
     *
     * @param string $err  Either a PEAR_Error object or
     *                     text to write to log.
     * @param string $file File name where error occured.
     * @param int $line Line number where error occured.
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
     * Writes a message to the imsp logfile.
     *
     * @access public
     * @param string $message Text to write.
     */
    function writeToLog($message, $file=__FILE__,
                        $line=__LINE__, $priority=PEAR_LOG_INFO)
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
     * @access public
     * @param array $params Log object parameters.
     * @return mixed  True on success or PEAR_Error on failure.
     */
    function setLogger($params)
    {
        $this->_logLevel = $params['priority'];
        $logger = &Log::singleton($params['type'], $params['name'],
                                  $params['ident'], $params['params']);
        $this->_logSet = true;

        if (is_a($logger, 'PEAR_Error')) {
            $this->logEnabled = false;
            return $logger;
        } else {
            $this->_logger = &$logger;
            $this->logEnabled = true;
            $this->_writeLogBuffer();

            return true;
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
     * @access public
     * @param string $driver Type of Net_IMSP object to return.
     * @param mixed $params  Any parameters needed by the Net_IMSP object.
     * @return mixed  The requested Net_IMSP object or PEAR_Error on failure.
     */
    function &factory($driver, $params)
    {
        $driver = basename($driver);

        if (empty($driver) || $driver == 'none') {
            return $dvr = &new Net_IMSP($params);
        }

        include_once dirname(__FILE__) . '/IMSP/' . $driver . '.php';
        $class = 'Net_IMSP_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
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
     * @param string $driver Type of Net_IMSP object to return.
     * @params mixed $params Any parameters needed by the Net_IMSP object.
     * @return mixed Reference to the Net_IMSP object or PEAR_Error on failure.
     */
    function &singleton($driver, $params)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Net_IMSP::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
