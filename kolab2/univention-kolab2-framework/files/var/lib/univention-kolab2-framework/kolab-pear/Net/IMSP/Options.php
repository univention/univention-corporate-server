<?php

require_once 'Net/IMSP/Auth.php';

// Constants
define('IMSP_GETOPTION_RESPONSE', "/^\* OPTION/");

/**
 * Net_IMSP_Options Class - provides an interface to IMSP server-based
 * options storage.
 *
 * Required parameters:
 * ====================
 * 'username'       -- Username to logon to IMSP server as.
 * 'password'       -- Password for current user.
 * 'auth_method'    -- The authentication method to use to login.
 * 'server'         -- The hostname of the IMSP server.
 * 'port'           -- The port of the IMSP server.
 *
 * $Horde: framework/Net_IMSP/IMSP/Options.php,v 1.2 2004/04/19 20:27:37 chuck Exp $
 *
 * Copyright 2004 Michael Rubinsky <mike@theupstairsroom.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @version $Revision: 1.1.2.1 $
 * @author  Michael Rubinsky <mike@theupstairsroom.com>
 * @package Net_IMSP
 */
class Net_IMSP_Options {

    var $_imsp;
    var $user = '';
    var $pass = '';
    var $auth_method = '';
    var $server = '';
    var $port = '';
    var $params;

    /**
     * Constructor function.
     *
     * @access public
     * @param array $params Hash containing IMSP parameters.
     */
    function Net_IMSP_Options($params)
    {
        $this->params = $params;
    }

    /**
     * Initialization function to be called after object is returned.
     * This allows errors to occur and not break the script.
     *
     * @access public
     * @return mixed True on success PEAR_Error on failure.
     */
    function init()
    {
        if (!isset($this->_imsp)) {
            $auth = &Net_IMSP_Auth::singleton($this->params['auth_method']);
            $this->_imsp = $auth->authenticate($this->params);
        }

        if (is_a($this->_imsp, 'PEAR_Error')) {
            return $this->_imsp;
        }
        $this->_imsp->writeToLog('Net_IMSP_Options initialized.', __FILE__,
                                 __LINE__, PEAR_LOG_DEBUG);
        return true;
    }

    /**
     * Function sends a GET command to IMSP server and retrieves values.
     *
     * @access public
     * @param string $optionName Name of option to retrieve. Accepts '*'
     *                           as wild card.
     * @return mixed  Associative array containing option=>value pairs or
     *                PEAR_Error.
     */
    function get($optionName)
    {
        $options = array();
        $result = $this->_imsp->imspSend("GET $optionName", true, true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $server_response = $this->_imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }

        while (preg_match(IMSP_GETOPTION_RESPONSE,$server_response)){
            /* First, check for a {}. */
            if (preg_match(IMSP_OCTET_COUNT, $server_response, $tempArray)){
                $temp = split(' ', $server_response);
                $options[$temp[2]] = $this->_imsp->receiveStringLiteral($tempArray[2]);
                $this->_imsp->imspReceive(); // [READ WRITE]
            } else {
                $temp = split(' ', $server_response);
                $options[$temp[2]] = trim($temp[3]);
                $i = 3;
                $lastChar = "";
                $nextElement = trim($temp[3]);
                // Was the value quoted and spaced?
                if ((substr($nextElement,0,1) == '"') &&
                    (substr($nextElement,strlen($nextElement)-1,1) != '"')) {

                    do {
                        $nextElement = $temp[$i+1];
                        $lastChar = substr($nextElement,
                                           strlen($nextElement)-1,1);
                        $options[$temp[2]] .= ' ' . $nextElement;
                        if ($lastChar == '"') {
                            $done = true;
                        } else {
                            $done = false;
                            $lastChar = substr($temp[$i+2],
                                               strlen($temp[$i+2])-1,1);
                            $i++;
                        }

                    } while ($lastChar != '"');

                    if (!$done) {
                        $nextElement = $temp[$i+1];
                        $options[$temp[2]] .= ' ' . $nextElement;
                    }
                }
            }
            $server_response = $this->_imsp->imspReceive();
            if (is_a($server_response, 'PEAR_Error')){
                return $server_response;
            }
        }

        if ($server_response != 'OK') {
            return $this->_imsp->imspError(IMSP_UNEXPECTED_RESPONSE,
                                           __FILE__,__LINE__);
        }

        $this->_imsp->writeToLog('GET command OK.', '', '', PEAR_LOG_DEBUG);
        return $options;
    }

    /**
     * Function sets an option value on the IMSP server.
     *
     * @access public
     * @param string $optionName Name of option to set.
     * @param string $optionValue Value to assign.
     * @return mixed True or PEAR_Error.
     */
    function set($optionName, $optionValue)
    {
        // Send the beginning of the command.
        $result = $this->_imsp->imspSend("SET $optionName ", true, false);

        // Send $optionValue as a literal {}?
        if (preg_match(IMSP_MUST_USE_LITERAL, $optionValue)) {
            $biValue = sprintf("{%d}",strlen($optionValue));
            $result = $this->_imsp->imspSend($biValue,false,true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match(IMSP_COMMAND_CONTINUATION_RESPONSE,
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError(IMSP_NO_CONTINUATION_RESPONSE,
                                               __FILE__,__LINE__);
            }
        }

        // Now send the rest of the command.
        $result = $this->_imsp->imspSend($optionValue, false, true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $server_response = $this->_imsp->imspReceive();

        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        } elseif ($server_response != 'OK') {
            return $this->_imsp->imspError('The option could not be set on the IMSP server.',__FILE__, __LINE__);
        }

        $this->_imsp->writeToLog('SET command OK.', '', '', PEAR_LOG_DEBUG);
        return true;
    }

    /**
     * Sets the log information in the Net_IMSP object.
     *
     * @access public
     * @param array The log parameters.
     * @return mixed  True on success PEAR_Error on failure.
     */
    function setLogger($params)
    {
        if (isset($this->_imsp)) {
            return $this->_imsp->setLogger($params);
        } else {
            return $this->_imsp->imspError('The IMSP log could not be initialized.');
        }
    }

}
