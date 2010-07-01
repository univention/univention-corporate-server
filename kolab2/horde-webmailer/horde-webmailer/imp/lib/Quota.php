<?php
/**
 * IMP_Quota:: provides an API for retrieving Quota details from a mail
 * server.
 *
 * $Horde: imp/lib/Quota.php,v 1.23.10.15 2009-01-06 15:24:04 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package IMP_Quota
 */
class IMP_Quota {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Constructor.
     *
     * @param array $params  Hash containing connection parameters.
     */
    function IMP_Quota($params = array())
    {
        $this->_params = $params;

        /* If 'password' exists in params, it has been encrypted in the
         * session so we need to decrypt. */
        if (isset($this->_params['password'])) {
            $this->_params['password'] = Secret::read(Secret::getKey('imp'), $this->_params['password']);
        }
    }

    /**
     * Get quota information (used/allocated), in bytes.
     *
     * @return mixed  An associative array.
     *                'limit' = Maximum quota allowed
     *                'usage' = Currently used portion of quota (in bytes)
     *                Returns PEAR_Error on failure.
     */
    function getQuota()
    {
        return array('usage' => 0, 'limit' => 0);
    }

    /**
     * Returns the quota messages variants, including sprintf placeholders.
     *
     * @return array  A hash with quota message templates.
     */
    function getMessages()
    {
        return array(
            'long' => isset($this->_params['format']['long'])
                ? $this->_params['format']['long']
                : _("Quota status: %.2f MB / %.2f MB  (%.2f%%)"),
            'short' => isset($this->_params['format']['short'])
                ? $this->_params['format']['short']
                : _("%.0f%% of %.0f MB"),
            'nolimit_long' => isset($this->_params['format']['nolimit_long'])
                ? $this->_params['format']['nolimit_long']
                : _("Quota status: %.2f MB / NO LIMIT"),
            'nolimit_short' => isset($this->_params['format']['nolimit_short'])
                ? $this->_params['format']['nolimit_short']
                : _("%.0f MB"));
    }

    /**
     * Attempts to return a concrete Quota instance based on $driver.
     *
     * @param string $driver  The type of concrete Quota subclass to return.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return mixed  The newly created concrete Quota instance, or false
     *                on error.
     */
    function &factory($driver, $params = array())
    {
        $driver = basename($driver);
        require_once dirname(__FILE__) . '/Quota/' . $driver . '.php';
        $class = 'IMP_Quota_' . $driver;
        if (class_exists($class)) {
            $quota = new $class($params);
        } else {
            $quota = false;
        }

        return $quota;
    }

    /**
     * Attempts to return a reference to a concrete Quota instance based on
     * $driver.
     *
     * It will only create a new instance if no Quota instance with the same
     * parameters currently exists.
     *
     * This should be used if multiple quota sources are required.
     *
     * This method must be invoked as: $var = &Quota::singleton()
     *
     * @param string $driver  The type of concrete Quota subclass to return.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return mixed  The created concrete Quota instance, or false on error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &IMP_Quota::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
