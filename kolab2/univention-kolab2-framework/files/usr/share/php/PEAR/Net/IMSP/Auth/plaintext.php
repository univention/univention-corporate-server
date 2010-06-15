<?php
/**
 * The Net_IMSP_Auth_plaintext class for IMSP authentication.
 *
 * Required parameters:
 * ====================
 * 'username'       -- Username to logon to IMSP server as.
 * 'password'       -- Password for current user.
 * 'server'         -- The hostname of the IMSP server.
 * 'port'           -- The port of the IMSP server.
 *
 * $Horde: framework/Net_IMSP/IMSP/Auth/plaintext.php,v 1.7 2004/04/19 20:27:37 chuck Exp $
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
class Net_IMSP_Auth_plaintext extends Net_IMSP_Auth {

    /**
     * Private authentication function.  Provides actual
     * authentication code.
     *
     * @access private
     * @param mixed $params Hash of IMSP parameters.
     * @return mixed  Net_IMSP object connected to server if successful,
     *                PEAR_Error on failure.
     */
    function &_authenticate($params)
    {
        $imsp = &Net_IMSP::singleton('none',$params);
        $result = $imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

         $userId = $params['username'];
         $credentials = $params['password'];

        // Start the command.
        $result = $imsp->imspSend('LOGIN ', true, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Username as a {}?
        if (preg_match(IMSP_MUST_USE_LITERAL, $userId)) {
            $biUser = sprintf('{%d}', strlen($userId));

            $result = $imsp->imspSend($biUser, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match(IMSP_COMMAND_CONTINUATION_RESPONSE,
                            $imsp->imspReceive())) {

                return $imsp->imspError(IMSP_NO_CONTINUATION_RESPONSE,
                                        __FILE__,__LINE__);
            }
        }

        $result = $imsp->imspSend($userId . ' ', false, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        //Don't want to log the password!
        $logValue = $imsp->logEnabled;
        $imsp->logEnabled = false;

        // Pass as {}?
        if (preg_match(IMSP_MUST_USE_LITERAL, $credentials)) {
            $biPass = sprintf('{%d}', strlen($credentials));
            $result = $imsp->imspSend($biPass, false, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            if (!preg_match(IMSP_COMMAND_CONTINUATION_RESPONSE,
                            $imsp->imspReceive())) {
                return $imsp->imspError(IMSP_NO_CONTINUATION_RESPONSE,
                                        __FILE__,__LINE__);
            }
        }

        $result = $imsp->imspSend($credentials, false, true);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // Restore the logging boolean.
        $imsp->logEnabled = $logValue;

        $server_response = $imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }

        if ($server_response != 'OK') {
            return $imsp->imspError(IMSP_EXIT_LOGIN_FAILED,__FILE__,__LINE__);
        }

        return $imsp;
    }

}
