<?php

require_once 'Net/Sieve.php';

/**
 * Ingo_Driver_sivtest:: Implements the Sieve_Driver api to allow scripts to
 * be installed and set active via the Cyrus sivtest command line utility.
 *
 * $Horde: ingo/lib/Driver/sivtest.php,v 1.6.2.3 2009-01-06 15:24:35 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 * Copyright 2004-2007 Liam Hoekenga <liamr@umich.edu>
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Liam Hoekenga <liamr@umich.edu>
 * @package Ingo
 */
class Ingo_Driver_sivtest extends Ingo_Driver {

    /**
     * Whether this driver allows managing other users' rules.
     *
     * @var boolean
     */
    var $_support_shares = false;

    /**
     * The Net_Sieve object.
     *
     * @var Net_Sieve
     */
    var $_sieve;

    /**
     * Constructor.
     */
    function Ingo_Driver_sivtest($params = array())
    {
        $default_params = array(
            'hostspec'   => 'localhost',
            'logintype'  => '',
            'port'       => 2000,
            'scriptname' => 'ingo',
            'admin'      => '',
            'usetls'     => true,
            'command'    => '',
            'socket'     => '',
        );
        $this->_params = array_merge($this->_params, $default_params, $params);
    }

    /**
     * Connect to the sieve server.
     *
     * @return mixed  True on success, PEAR_Error on false.
     */
    function _connect()
    {
        if (!empty($this->_sieve)) {
            return true;
        }

        $this->sivtestSocket($this->_params['username'],
        $this->_params['password'], $this->_params['hostspec']);
        if (substr(PHP_VERSION, 0, 1) == '5') {
            $domain_socket = 'unix://' . $this->_params['socket'];
        } else {
            $domain_socket = $this->_params['socket'];
        }

        $this->_sieve = new Net_Sieve($this->_params['username'],
                                      $this->_params['password'],
                                      $domain_socket,
                                      0,
                                      null,
                                      null,
                                      false,
                                      true,
                                      $this->_params['usetls']);

        $res = $this->_sieve->getError();
        if (is_a($res, 'PEAR_Error')) {
            unset($this->_sieve);
            return $res;
        } else {
            return true;
        }
    }

    /**
     * Sets a script running on the backend.
     *
     * @param string $script    The sieve script.
     *
     * @return mixed  True on success.
     *                Returns PEAR_Error on error.
     */
    function setScriptActive($script)
    {
        $res = $this->_connect();
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        $res = $this->_sieve->haveSpace($this->_params['scriptname'], strlen($script));
        if (is_a($res, 'PEAR_ERROR')) {
            return $res;
        }

        return $this->_sieve->installScript($this->_params['scriptname'], $script, true);
    }

    /**
     * Returns the content of the currently active script.
     *
     * @return string  The complete ruleset of the specified user.
     */
    function getScript()
    {
        $res = $this->_connect();
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }
        return $this->_sieve->getScript($this->_sieve->getActive());
    }

    /**
     * Used to figure out which Sieve server the script will be run
     * on, and then open a GSSAPI authenticated socket to said server.
     *
     * @param
     *
     * @return
     */
    function sivtestSocket($username, $password, $hostspec)
    {
        $command = '';
        $error_return = '';

        if (strtolower($this->_params['logintype']) == 'gssapi'
            && isset($_SERVER['KRB5CCNAME'])) {
            $command .= 'KRB5CCNAME=' . $_SERVER['KRB5CCNAME'];
        }

        if (substr(PHP_VERSION, 0, 1) == '5') {
            $domain_socket = 'unix://' . $this->_params['socket'];
        } else {
            $domain_socket = $this->_params['socket'];
        }

        $command .= ' ' . $this->_params['command']
            . ' -m ' . $this->_params['logintype']
            . ' -u ' . $username
            . ' -a ' . $username
            . ' -w ' . $password
            . ' -p ' . $this->_params['port']
            . ' -X ' . $this->_params['socket']
            . ' ' . $hostspec;

        $conn_attempts = 0;
        while ($conn_attempts++ < 4) {
            $attempts = 0;
            if (!file_exists($this->_params['socket'])) {
                exec($command . ' > /dev/null 2>&1');
                sleep(1);
                while (!file_exists($this->_params['socket'])) {
                    usleep(200000);
                    if ($attempts++ > 5) {
                        $error_return = ': No socket after 10 seconds of trying!';
                        continue 2;
                    }
                }
            }
            $socket = new Net_Socket();
            $error = $socket->connect($domain_socket, 0, true, 30);
            if (!is_a($error, 'PEAR_Error')) {
                break;
            }

            // We failed, break this connection.
            unlink($this->_params['socket']);
        }

        if (!empty($error_return)) {
            return PEAR::raiseError(_($error_return));
        }

        $status = $socket->getStatus();
        if (is_a($status, 'PEAR_Error') || $status['eof']) {
            return PEAR::raiseError(_('Failed to write to socket: (connection lost!)'));
        }

        $error = $socket->writeLine("CAPABILITY");
        if (is_a($error, 'PEAR_Error')) {
            return PEAR::raiseError(_('Failed to write to socket: ' . $error->getMessage()));
        }

        $result = $socket->readLine();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(_('Failed to read from socket: ' . $error->getMessage()));
        }

        if (preg_match('|^bye \(referral "(sieve://)?([^"]+)|i',
                       $result, $matches)) {
            $socket->disconnect();

            $this->sivtestSocket($username, $password, $matches[2]);
        } else {
            $socket->disconnect();
            exec($command . ' > /dev/null 2>&1');
            sleep(1);
        }
    }

}
