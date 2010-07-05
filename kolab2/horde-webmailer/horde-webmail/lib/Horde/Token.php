<?php

require_once 'PEAR.php';
require_once 'Horde/Util.php';

/**
 * The Horde_Token:: class provides a common abstracted interface into the
 * various token generation mediums. It also includes all of the
 * functions for retrieving, storing, and checking tokens.
 *
 * $Horde: framework/Token/Token.php,v 1.33.6.18 2009-01-06 15:23:44 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Max Kalika <max@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 1.3
 * @package Horde_Token
 */
class Horde_Token {

    /**
     * Hash of parameters necessary to use the chosen backend.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Constructor.
     *
     * @param array $params  A hash containing parameters.
     */
    function Horde_Token($params = array())
    {
    }

    /**
     */
    function encodeRemoteAddress()
    {
        if (isset($_SERVER['REMOTE_ADDR'])) {
            return base64_encode($_SERVER['REMOTE_ADDR']);
        } else {
            return '';
        }
    }

    /**
     * Generates a connection id and returns it.
     *
     * @param string $seed  A unique ID to be included in the token.
     *
     * @return string   The generated id string.
     */
    function generateId($seed = '')
    {
        return Util::uriB64Encode(pack('H*', sha1(uniqid(mt_rand(), true) . $seed . (isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : ''))));
    }

    /**
     * Checks if the given token has been previously used. First
     * purges all expired tokens. Then retrieves current tokens for
     * the given ip address. If the specified token was not found,
     * adds it.
     *
     * @param string $token  The value of the token to check.
     *
     * @return boolean       True if the token has not been used,
     *                       false otherwise.
     */
    function verify($token)
    {
        $this->purge();
        $exists = $this->exists($token);
        if (is_a($exists, 'PEAR_Error')) {
            return $exists;
        } elseif ($exists) {
            return false;
        } else {
            return $this->add($token);
        }
    }

    /**
     * This is an abstract method that should be overridden by a
     * subclass implementation. The base implementation allows all
     * token values.
     */
    function exists()
    {
        return false;
    }

    /**
     * This is an abstract method that should be overridden by a
     * subclass implementation. The base implementation allows all
     * token values.
     */
    function add()
    {
        return true;
    }

    /**
     * This is an abstract method that should be overridden by a
     * subclass implementation. The base implementation allows all
     * token values.
     */
    function purge()
    {
        return true;
    }

    /**
     * Attempts to return a concrete Horde_Token instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Token subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Token/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Token  The newly created concrete Horde_Token instance, or
     *                      false an error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        $driver = basename($driver);
        if ($driver == 'none') {
            $class = 'Horde_Token';
        } else {
            $class = 'Horde_Token_' . $driver;
        }
        if (!class_exists($class)) {
            if (!empty($app)) {
                require_once $app . '/lib/Token/' . $driver . '.php';
            } else {
                include_once 'Horde/Token/' . $driver . '.php';
            }
        }

        if (class_exists($class)) {
            $token = new $class($params);
        } else {
            /* If driver class doesn't exist or the driver is not
             * available just default to the parent class, and it is
             * not necessary to warn about degraded service. */
            $token = new Horde_Token($params);
        }

        return $token;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Token instance based
     * on $driver.
     *
     * It will only create a new instance if no Horde_Token instance with the
     * same parameters currently exists.
     *
     * This should be used if multiple types of token generators (and, thus,
     * multiple Horde_Token instances) are required.
     *
     * This method must be invoked as:
     * <code>$var = &Horde_Token::singleton();</code>
     *
     * @param mixed $driver  The type of concrete Horde_Token subclass to
     *                       return. If $driver is an array, then we will look
     *                       in $driver[0]/lib/Token/ for the subclass
     *                       implementation named $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Token  The concrete Horde_Token reference, or false on
     *                      error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Token::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
