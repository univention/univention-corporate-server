<?php
/**
 * The Net_IMSP_Auth_plaintext class for IMSP authentication.
 *
 * Required parameters:<pre>
 *   'username'  Username to logon to IMSP server as.
 *   'password'  Password for current user.
 *   'server'    The hostname of the IMSP server.
 *   'port'      The port of the IMSP server.</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP/Auth/plaintext.php,v 1.7.10.15 2009-01-06 15:23:27 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Auth_plaintext extends Net_IMSP_Auth {

    /**
     * Private authentication function.  Provides actual
     * authentication code.
     *
     * @access private
     * @param  mixed  $params Hash of IMSP parameters.
     *
     * @return mixed  Net_IMSP object connected to server if successful,
     *                PEAR_Error on failure.
     */
    function &_authenticate($params)
    {
        $imsp = &Net_IMSP::singleton('none', $params);
        $result = $imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

         $userId = $params['username'];
         $credentials = $params['password'];

        /* Start the command. */
        $result = $imsp->imspSend('LOGIN ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Username as a {}? */
        if (preg_match(IMSP_MUST_USE_LITERAL, $userId)) {
            $biUser = sprintf('{%d}', strlen($userId));
            $result = $imsp->imspSend($biUser, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $imsp->imspReceive())) {

                $result = $imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                        __FILE__, __LINE__);
                return $result;
           }
        }

        $result = $imsp->imspSend($userId . ' ', false, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Don't want to log the password! */
        $logValue = $imsp->logEnabled;
        $imsp->logEnabled = false;

        /* Pass as {}? */
        if (preg_match(IMSP_MUST_USE_LITERAL, $credentials)) {
            $biPass = sprintf('{%d}', strlen($credentials));
            $result = $imsp->imspSend($biPass, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match("/^\+/",
                            $imsp->imspReceive())) {
                $result = $imsp->imspError('Did not receive expected command continuation response from IMSP server.',
                                        __FILE__, __LINE__);
                return $result;
            }
        }

        $result = $imsp->imspSend($credentials, false, true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Restore the logging boolean. */
        $imsp->logEnabled = $logValue;

        $server_response = $imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }

        if ($server_response != 'OK') {
            $result = $imsp->imspError('Login to IMSP host failed.', __FILE__, __LINE__);
            return $result;
        }

        return $imsp;
    }

    /**
     * Force a logout command to the imsp stream.
     *
     */
    function logout()
    {
        $this->_imsp->logout();
    }

    /**
     * Return the driver type
     *
     * @return string the type of this IMSP_Auth driver
     */
     function getDriverType()
     {
         return 'plaintext';
     }

}
