<?php

require_once 'Horde/IMAP/ACL.php';

/**
 * The IMP_IMAP_ACL:: class extends the IMAP_ACL class in order to
 * ensure backwards compatibility with Horde 3.0.
 *
 * $Horde: imp/lib/IMAP/ACL.php,v 1.4.2.4 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Eric Garrido <ekg2002@columbia.edu>
 * @since   IMP 4.2
 * @package Horde_IMAP
 */
class IMP_IMAP_ACL extends IMAP_ACL {

    /**
     * Hash containing the list of possible rights and a human
     * readable, short title of each
     *
     * Array (
     *     right-id => right-title
     * )
     *
     * @var array
     */
    var $_rightsListTitles = array();

    function getRightsTitles()
    {
        return $this->_rightsListTitles;
    }

    /**
     * Attempts to return an ACL instance based on $driver.
     *
     * @param string $driver  The type of concrete ACL subclass to return.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return mixed  The newly created concrete ACL instance, or false
     *                on error.
     */
    function &factory($driver, $params = array())
    {
        $driver = basename($driver);
        require_once dirname(__FILE__) . '/ACL/' . $driver . '.php';
        $class = 'IMP_IMAP_ACL_' . $driver;
        if (class_exists($class)) {
            $acl = &new $class($params);
        } else {
            $acl = false;
        }

        return $acl;
    }

    /**
     * Attempts to return a reference to a concrete ACL instance
     * based on $driver.  It will only create a new instance if no
     * ACL instance with the same parameters currently exists.
     *
     * This method must be invoked as: $var = &IMP_IMAP_ACL::singleton()
     *
     * @param string $driver  The type of concrete ACL subclass to return.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return mixed  The created concrete ACL instance, or false on error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &IMP_IMAP_ACL::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
