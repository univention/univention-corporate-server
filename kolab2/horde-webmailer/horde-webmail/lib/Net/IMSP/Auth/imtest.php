<?php
/**
 * The Net_IMSP_Auth_imtest class for IMSP authentication.
 *
 * Required parameters:<pre>
 *   'username'        Username to logon to IMSP server as.
 *   'password'        Password for current user.
 *   'server'          The hostname of the IMSP server.
 *   'port'            The port of the IMSP server.
 *   'socket'          The named socket to use for connection
 *   'command'         Path to the imtest command on localhost
 *   'auth_mechanism'  Authentication method to use with imtest</pre>
 *
 * $Horde: framework/Net_IMSP/IMSP/Auth/imtest.php,v 1.12.2.8 2009-01-06 15:23:27 jan Exp $
 *
 * Copyright 2005-2007      Liam Hoekenga <liamr@umich.edu>
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Liam Hoekenga <liamr@umich.edu>
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Auth_imtest extends Net_IMSP_Auth {

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
        $command = '';
        $error_return = '';

        if (strtolower($params['auth_mechanism']) == 'gssapi' &&
            isset($_SERVER['KRB5CCNAME'])) {
                $command .= 'KRB5CCNAME=' . $_SERVER['KRB5CCNAME'];
        }

        $command .= ' '    . $params['command'].
                    ' -m ' . $params['auth_mechanism'] .
                    ' -u ' . escapeshellarg($params['username']) .
                    ' -a ' . escapeshellarg($params['username']) .
                    ' -w ' . escapeshellarg($params['password']).
                    ' -p ' . $params['port'] .
                    ' -X ' . $params['socket'] .
                    ' '    . $params['server'];

        $conn_attempts = 0;
        while ($conn_attempts++ < 4) {
            $attempts = 0;
            if (!file_exists($params['socket'])) {
                exec($command . ' > /dev/null 2>&1');
                sleep(1);
                while (!file_exists($params['socket'])) {
                    usleep(200000);
                    if ($attempts++ > 5) {
                        $error_return = ': No socket after 10 seconds of trying!';
                        continue 2;
                    }
                }
            }
            $fp = @fsockopen($params['socket'], 0, $error_number, $error_string, 30);
            $error_return = $error_string;
            if ($fp) break;
            unlink($params['socket']);

        }
        //Failure?
        if (!empty($error_return)) {
            return $imsp->imspError('Connection to IMSP host failed.' . ': ' . $error_return, __FILE__, __LINE__);
        }
        //Success
        $imsp->_stream = $fp;
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
     * Returns the driver type.
     *
     * @return string  The type of this IMSP_Auth driver.
     */
    function getDriverType()
    {
        return 'imtest';
    }
}
