<?php
/**
 * The Horde_Token:: class provides a common abstracted interface into the
 * various token generation mediums. It also includes all of the
 * functions for retrieving, storing, and checking tokens.
 *
 * $Horde: framework/Token/Token.php,v 1.27 2004/03/30 20:54:03 chuck Exp $
 *
 * Copyright 1999-2004 Max Kalika <max@horde.org>
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Max Kalika <max@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Token
 */
class Horde_Token {

    /**
     * Hash of parameters necessary to use the chosen backend.
     * @var array $_params
     */
    var $_params = array();

    function hexRemoteAddr()
    {
        $addr = explode('.', $_SERVER['REMOTE_ADDR']);
        return sprintf('%02x%02x%02x%02x', $addr[0], $addr[1], $addr[2], $addr[3]);
    }

    /**
     * Generates a connection id and returns it.
     *
     * @param string $seed  A unique ID to be included in the token,
     *                      if it needs to be more unique than time (in seconds)
     *                      and the remote IP.
     *
     * @return string   The generated id string.
     */
    function generateId($seed = '')
    {
        return md5(time() . '][' . $seed . '][' . Horde_Token::hexRemoteAddr());
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
        if ($this->exists($token)) {
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
     * Attempts to return a concrete Horde_Token instance based on
     * $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Token subclass to return.
     *                       This is based on the storage driver ($driver). The
     *                       code is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/Token/ for
     *                       the subclass implementation named $driver[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration or connection parameters a subclass
     *                       might need.
     *
     * @return object Horde_Token  The newly created concrete Horde_Token instance, or
     *                             false an error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        $driver = basename($driver);

        if (!empty($app)) {
            require_once $app . '/lib/Token/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Token/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Token/' . $driver . '.php';
        } else {
            @include_once 'Horde/Token/' . $driver . '.php';
        }
        $class = 'Horde_Token_' . $driver;
        if (class_exists($class)) {
            return new $class($params);
        } else {
            return new Horde_Token($params);
        }
    }

    /**
     * Attempts to return a reference to a concrete Horde_Token
     * instance based on $driver. It will only create a new instance
     * if no Horde_Token instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple types of token generators (and,
     * thus, multiple Horde_Token instances) are required.
     *
     * This method must be invoked as: $var = &Horde_Token::singleton()
     *
     * @param mixed $driver  The type of concrete Horde_Token subclass to return.
     *                       This is based on the storage driver ($driver). The
     *                       code is dynamically included. If $driver is an array,
     *                       then we will look in $driver[0]/lib/Token/ for
     *                       the subclass implementation named $driver[1].php.
     * @param array $params  (optional) A hash containing any additional
     *                       configuration or connection parameters a subclass
     *                       might need.
     *
     * @return object Horde_Token  The concrete Horde_Token reference, or false on an
     *                             error.
     *
     * @since Horde 2.2
     */
    function &singleton($driver, $params = array())
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Token::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
