<?php

require_once 'PEAR.php';

/**
 * Net_SMS Class
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Net_SMS/SMS.php,v 1.10.10.15 2009-01-06 15:23:28 jan Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Net_SMS
 */
class Net_SMS {

    /**
     * A hash containing any parameters for the current gateway driver.
     *
     * @var array
     */
    var $_params = array();

    var $_auth = null;

    /**
     * Constructor
     *
     * @param array $params  Any parameters needed for this gateway driver.
     */
    function Net_SMS($params = null)
    {
        $this->_params = $params;
    }

    /**
     * Returns a list of available gateway drivers.
     *
     * @return array  An array of available drivers.
     */
    function getDrivers()
    {
        static $drivers = array();
        if (!empty($drivers)) {
            return $drivers;
        }

        $drivers = array();

        if ($driver_dir = opendir(dirname(__FILE__) . '/SMS/')) {
            while (false !== ($file = readdir($driver_dir))) {
                /* Hide dot files and non .php files. */
                if (substr($file, 0, 1) != '.' && substr($file, -4) == '.php') {
                    $driver = substr($file, 0, -4);
                    $driver_info = Net_SMS::getGatewayInfo($driver);
                    $drivers[$driver] = $driver_info['name'];
                }
            }
            closedir($driver_dir);
        }

        return $drivers;
    }

    /**
     * Returns information on a gateway, such as name and a brief description,
     * from the driver subclass getInfo() function.
     *
     * @return array  An array of extra information.
     */
    function getGatewayInfo($gateway)
    {
        static $info = array();
        if (isset($info[$gateway])) {
            return $info[$gateway];
        }

        require_once 'Net/SMS/' . $gateway . '.php';
        $class = 'Net_SMS_' . $gateway;
        $info[$gateway] = call_user_func(array($class, 'getInfo'));

        return $info[$gateway];
    }

    /**
     * Returns parameters for a gateway from the driver subclass getParams()
     * function.
     *
     * @param string  The name of the gateway driver for which to return the
     *                parameters.
     *
     * @return array  An array of extra information.
     */
    function getGatewayParams($gateway)
    {
        static $params = array();
        if (isset($params[$gateway])) {
            return $params[$gateway];
        }

        require_once 'Net/SMS/' . $gateway . '.php';
        $class = 'Net_SMS_' . $gateway;
        $params[$gateway] = call_user_func(array($class, 'getParams'));

        return $params[$gateway];
    }

    /**
     * Returns send parameters for a gateway from the driver subclass
     * getDefaultSendParams()function. These are parameters which are available
     * to the user during sending, such as setting a time for delivery, or type
     * of SMS (normal text or flash), or source address, etc.
     *
     * @param string  The name of the gateway driver for which to return the
     *                send parameters.
     *
     * @return array  An array of available send parameters.
     */
    function getDefaultSendParams($gateway)
    {
        static $params = array();
        if (isset($params[$gateway])) {
            return $params[$gateway];
        }

        require_once 'Net/SMS/' . $gateway . '.php';
        $class = 'Net_SMS_' . $gateway;
        $params[$gateway] = call_user_func(array($class, 'getDefaultSendParams'));

        return $params[$gateway];
    }

    /**
     * Query the current Gateway object to find out if it supports the given
     * capability.
     *
     * @param string $capability  The capability to test for.
     *
     * @return mixed  Whether or not the capability is supported or any other
     *                value that the capability wishes to report.
     */
    function hasCapability($capability)
    {
        if (!empty($this->capabilities[$capability])) {
            return $this->capabilities[$capability];
        }
        return false;
    }

    /**
     * Authenticates against the gateway if required.
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function authenticate()
    {
        /* Do authentication for this gateway if driver requires it. */
        if ($this->hasCapability('auth')) {
            $this->_auth = $this->_authenticate();
            return $this->_auth;
        }
        return true;
    }

    /**
     * Sends a message to one or more recipients. Hands off the actual sending
     * to the gateway driver.
     *
     * @param array $message  The message to be sent, which is composed of:
     *                        <pre>
     *                          id   - A unique ID for the message;
     *                          to   - An array of recipients;
     *                          text - The text of the message;
     *                        </pre>
     *
     *
     * @return mixed  True on success or PEAR Error on failure.
     */
    function send($message)
    {
        /* Authenticate. */
        if (is_a($this->authenticate(), 'PEAR_Error')) {
            return $this->_auth;
        }

        /* Make sure the recipients are in an array. */
        if (!is_array($message['to'])) {
            $message['to'] = array($message['to']);
        }

        /* Array to store each send. */
        $sends = array();

        /* If gateway supports batch sending, preference is given to this
         * method. */
        if ($max_per_batch = $this->hasCapability('batch')) {
            /* Split up the recipients in the max recipients per batch as
             * supported by gateway. */
            $iMax = count($message['to']);
            $batches = ceil($iMax / $max_per_batch);

            /* Loop through the batches and compose messages to be sent. */
            for ($b = 0; $b < $batches; $b++) {
                $recipients = array_slice($message['to'], ($b * $max_per_batch), $max_per_batch);
                $response = $this->_send($message, $recipients);
                foreach ($recipients as $recipient) {
                    if ($response[$recipient][0] == 1) {
                        /* Message was sent, store remote id. */
                        $remote_id = $response[$recipient][1];
                        $error = null;
                    } else {
                        /* Message failed, store error code. */
                        $remote_id = null;
                        $error = $response[$recipient][1];
                    }

                    /* Store the sends. */
                    $sends[] = array('message_id' => $message['id'],
                                     'remote_id'  => $remote_id,
                                     'recipient'  => $recipient,
                                     'error'      => $error);
                }
            }
        } else {
            /* No batch sending available, just loop through all recipients
             * and send a message for each one. */
            foreach ($message['to'] as $recipient) {
                $response = $this->_send($message, $recipient);
                if ($response[0] == 1) {
                    /* Message was sent, store remote id if any. */
                    $remote_id = (isset($response[1]) ? $response[1] : null);
                    $error = null;
                } else {
                    /* Message failed, store error code. */
                    $remote_id = null;
                    $error = $response[1];
                }

                /* Store the sends. */
                $sends[] = array('message_id' => $message['id'],
                                 'remote_id'  => $remote_id,
                                 'recipient'  => $recipient,
                                 'error'      => $error);
            }
        }

        return $sends;
    }

    /**
     * If the current driver has a credit capability, queries the gateway for
     * a credit balance and returns the value.
     *
     * @return integer  Value indicating available credit or null if not
     *                  supported.
     */
    function getBalance()
    {
        /* Authenticate. */
        if (is_a($this->authenticate(), 'PEAR_Error')) {
            return $this->_auth;
        }

        /* Check balance. */
        if ($this->hasCapability('credit')) {
            return $this->_getBalance();
        } else {
            return null;
        }
    }

    /**
     * Attempts to return a concrete Gateway instance based on $driver.
     *
     * @param string $driver  The type of concrete Gateway subclass to return.
     *                        This is based on the gateway driver ($driver).
     *                        The code is dynamically included.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return Net_SMS  The newly created concrete Gateway instance or false on
     *                  an error.
     */
    function &factory($driver, $params = array())
    {
        include_once 'Net/SMS/' . $driver . '.php';
        $class = 'Net_SMS_' . $driver;
        if (class_exists($class)) {
            $sms = &new $class($params);
        } else {
            $sms = PEAR::raiseError(sprintf(_("Class definition of %s not found."), $driver));
        }

        return $sms;
    }

    /**
     * Attempts to return a reference to a concrete Net_SMS instance based on
     * $driver.
     *
     * It will only create a new instance if no Net_SMS instance with the same
     * parameters currently exists.
     *
     * This method must be invoked as: $var = &Net_SMS::singleton()
     *
     * @param string $driver  The type of concrete Net_SMS subclass to return.
     *                        The is based on the gateway driver ($driver).
     *                        The code is dynamically included.
     *
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return mixed  The created concrete Net_SMS instance, or false on error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Net_SMS::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
