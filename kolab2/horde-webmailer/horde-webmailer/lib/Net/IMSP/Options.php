<?php

require_once 'Net/IMSP/Auth.php';

/**
 * Net_IMSP_Options Class - provides an interface to IMSP server-based
 * options storage.
 *
 * Required parameters:<pre>
 *   'username'     Username to logon to IMSP server as.
 *   'password'     Password for current user.
 *   'auth_method'  The authentication method to use to login.
 *   'server'       The hostname of the IMSP server.
 *   'port'         The port of the IMSP server.</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP/Options.php,v 1.3.2.20 2009-01-06 15:23:27 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Options {

    /**
     * Net_IMSP object.
     *
     * @var Net_IMSP
     */
    var $_imsp;

    /**
     * Parameter list.
     *
     * @var array
     */
    var $_params;

    /**
     * Constructor function.
     *
     * @param array $params  Hash containing IMSP parameters.
     */
    function Net_IMSP_Options($params)
    {
        $this->_params = $params;
    }

    /**
     * Initialization function to be called after object is returned.
     * This allows errors to occur and not break the script.
     *
     * @return mixed  True on success PEAR_Error on failure.
     */
    function init()
    {
        if (!isset($this->_imsp)) {
            $auth = &Net_IMSP_Auth::singleton($this->_params['auth_method']);
            $this->_imsp = $auth->authenticate($this->_params);
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
     * @param  string $optionName Name of option to retrieve. Accepts '*'
     *                            as wild card.
     *
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

        while (preg_match("/^\* OPTION/", $server_response)) {
            /* First, check for a {}. */
            if (preg_match(IMSP_OCTET_COUNT, $server_response, $tempArray)) {
                $temp = explode(' ', $server_response);
                $options[$temp[2]] = $this->_imsp->receiveStringLiteral($tempArray[2]);
                $this->_imsp->imspReceive();
            } else {
                $temp = explode(' ', $server_response);
                $options[$temp[2]] = trim($temp[3]);
                $i = 3;
                $lastChar = "";
                $nextElement = trim($temp[3]);

                /* Was the value quoted and spaced? */
                if ((substr($nextElement,0,1) == '"') &&
                    (substr($nextElement,strlen($nextElement) - 1, 1) != '"')) {
                    do {
                        $nextElement = $temp[$i+1];
                        $lastChar = substr($nextElement,
                                           strlen($nextElement) - 1, 1);
                        $options[$temp[2]] .= ' ' . $nextElement;
                        if ($lastChar == '"') {
                            $done = true;
                        } else {
                            $done = false;
                            $lastChar = substr($temp[$i+2],
                                               strlen($temp[$i+2]) - 1, 1);
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
            if (is_a($server_response, 'PEAR_Error')) {
                return $server_response;
            }
        }

        if ($server_response != 'OK') {
            return $this->_imsp->imspError('Did not receive the expected response from the server.',
                                           __FILE__, __LINE__);
        }

        $this->_imsp->writeToLog('GET command OK.', __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return $options;
    }

    /**
     * Function sets an option value on the IMSP server.
     *
     * @param string $optionName  Name of option to set.
     * @param string $optionValue Value to assign.
     *
     * @return mixed True or PEAR_Error.
     */
    function set($optionName, $optionValue)
    {
        /* Send the beginning of the command. */
        $result = $this->_imsp->imspSend("SET $optionName ", true, false);

        /* Send $optionValue as a literal {}? */
        if (preg_match(IMSP_MUST_USE_LITERAL, $optionValue)) {
            $biValue = sprintf("{%d}", strlen($optionValue));
            $result = $this->_imsp->imspSend($biValue, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $this->_imsp->imspReceive())) {
                return $this->_imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                               __FILE__, __LINE__);
            }
        }

        /* Now send the rest of the command. */
        $result = $this->_imsp->imspSend($optionValue, false, true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $server_response = $this->_imsp->imspReceive();

        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        } elseif ($server_response != 'OK') {
            return $this->_imsp->imspError('The option could not be set on the IMSP server.', __FILE__, __LINE__);
        }

        $this->_imsp->writeToLog('SET command OK.', __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return true;
    }

    /**
     * Sets the log information in the Net_IMSP object.
     *
     * @param array $params  The log parameters.
     *
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

    function logout()
    {
        $this->_imsp->logout();
    }

}
