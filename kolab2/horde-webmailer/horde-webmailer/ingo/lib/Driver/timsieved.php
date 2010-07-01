<?php

require_once('Net/Sieve.php');

/**
 * Ingo_Driver_timsieved:: Implements the Sieve_Driver api to allow scripts to
 * be installed and set active via a Cyrus timsieved server.
 *
 * $Horde: ingo/lib/Driver/timsieved.php,v 1.15.10.12 2009-11-05 10:29:09 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Jan Schneider <jan@horde.org>
 * @package Ingo
 */
class Ingo_Driver_timsieved extends Ingo_Driver {

    /**
     * Whether this driver allows managing other users' rules.
     *
     * @var boolean
     */
    var $_support_shares = true;

    /**
     * The Net_Sieve object.
     *
     * @var Net_Sieve
     */
    var $_sieve;

    /**
     * Constructor.
     */
    function Ingo_Driver_timsieved($params = array())
    {
        $default_params = array(
            'hostspec'   => 'localhost',
            'logintype'  => 'PLAIN',
            'port'       => 2000,
            'scriptname' => 'ingo',
            'admin'      => '',
            'usetls'     => true
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

        if (empty($this->_params['admin'])) {
            $auth = $this->_params['username'];
        } else {
            $auth = $this->_params['admin'];
        }
        $this->_sieve = &new Net_Sieve($auth,
                                       $this->_params['password'],
                                       $this->_params['hostspec'],
                                       $this->_params['port'],
                                       $this->_params['logintype'],
                                       Ingo::getUser(false),
                                       false,
                                       false,
                                       $this->_params['usetls']);

        $res = $this->_sieve->getError();
        if (is_a($res, 'PEAR_Error')) {
            unset($this->_sieve);
            return $res;
        } else {
            $this->_sieve->setDebug(true, array($this, '_debug'));
            return true;
        }
    }

    /**
     * Routes the Sieve protocol log to the Horde log.
     *
     * @param Net_Sieve $sieve  A Net_Sieve object.
     * @param string $message   The tracked Sieve communication.
     */
    function _debug($sieve, $message)
    {
        Horde::logMessage($message, __FILE__, __LINE__, PEAR_LOG_DEBUG);
    }

    /**
     * Sets a script running on the backend.
     *
     * @param string $script    The sieve script.
     *
     * @return mixed  True on success, PEAR_Error on error.
     */
    function setScriptActive($script)
    {
        $res = $this->_connect();
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }

        if (!strlen($script)) {
            return $this->_sieve->setActive('');
        }

        $res = $this->_sieve->haveSpace($this->_params['scriptname'],
                                        strlen($script));
        if (is_a($res, 'PEAR_ERROR')) {
            return $res;
        }

        return $this->_sieve->installScript($this->_params['scriptname'],
                                            $script, true);
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
        $active = $this->_sieve->getActive();
        if (empty($active)) {
            return '';
        }
        return $this->_sieve->getScript($active);
    }

}
