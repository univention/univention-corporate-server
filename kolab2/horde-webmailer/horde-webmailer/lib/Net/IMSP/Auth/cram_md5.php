<?php
/**
 * The Net_IMSP_Auth_cram_md5 class for IMSP authentication.
 *
 * Required parameters:<pre>
 *   'username'  Username to logon to IMSP server as.
 *   'password'  Password for current user.
 *   'server'    The hostname of the IMSP server.
 *   'port'      The port of the IMSP server.</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP/Auth/cram_md5.php,v 1.6.10.13 2009-01-06 15:23:27 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Auth_cram_md5 extends Net_IMSP_Auth {

    /**
     * Private authentication function.  Provides actual
     * authentication code.
     *
     * @access private
     * @param  mixed $params Hash of IMSP parameters.
     *
     * @return mixed Net_IMSP object connected to server if successful,
     *               PEAR_Error on failure.
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
        $result = $imsp->imspSend('AUTHENTICATE CRAM-MD5');
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Get response and decode it. Note that we remove the 1st 2
         * characters from the response to get rid of the '+'
         * continuation character and the space that is sent as part
         * of the CRAM-MD5 response (at least on cyrus-imspd). */
        $server_response = $imsp->imspReceive();
        if (is_a($server_response, 'PEAR_Error')) {
            return $server_response;
        }

        $server_response = base64_decode(trim(substr($server_response, 2)));

        /* Build and base64 encode the response to the challange. */
        $response_to_send = $userId . ' ' . $this->_hmac($credentials, $server_response);
        $command_string = base64_encode($response_to_send);

        /* Send the response. */
        $result = $imsp->imspSend($command_string, false);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $imsp->imspReceive();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($result != 'OK') {
            $result = $imsp->imspError('Login to IMSP host failed.', __FILE__, __LINE__);
            return $result;
        } else {
            return $imsp;
        }
    }

    /**
     * RFC 2104 HMAC implementation.
     *
     * @access private
     * @param  string  $key    The HMAC key.
     * @param  string  $data   The data to hash with the key.
     *
     * @return string  The MD5 HMAC.
     */
    function _hmac($key, $data)
    {
        if (function_exists(hash_hmac)) {
            return hash_hmac('md5', $data, $key);
        }

        /* Byte length for md5. */
        $b = 64;

        if (strlen($key) > $b) {
            $key = pack('H*', md5($key));
        }

        $key = str_pad($key, $b, chr(0x00));
        $ipad = str_pad('', $b, chr(0x36));
        $opad = str_pad('', $b, chr(0x5c));
        $k_ipad = $key ^ $ipad;
        $k_opad = $key ^ $opad;
        return md5($k_opad . pack('H*', md5($k_ipad . $data)));
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
         return 'cram_md5';
     }

}
