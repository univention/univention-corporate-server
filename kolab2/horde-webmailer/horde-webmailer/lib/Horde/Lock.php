<?php
/**
 * The Horde_Lock class provides an API to create, store, check and expire locks
 * based on a given resource URI.
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you did
 * not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * $Horde: framework/Lock/Lock.php,v 1.6.2.5 2009-01-06 15:23:20 jan Exp $
 *
 * @author  Ben Klang <ben@alkaloid.net>
 * @since   Horde 3.2
 * @package Horde_Lock
 */

/**
 * The exclusive lock type
 */
define('HORDE_LOCK_TYPE_EXCLUSIVE', 1);

/**
 * The shared lock type
 */
define('HORDE_LOCK_TYPE_SHARED', 2);

class Horde_Lock
{
    /**
     * Local copy of driver parameters
     * @var $_params
     */
    var $_params;

    /**
     * Horde_Lock constructor
     *
     * @param array $params  Parameters for the specific Horde_Lock driver
     *
     * @return Horde_Lock    Instance of Horde_Lock on success or PEAR_Error
     */
    function Horde_Lock($params)
    {
        $this->_params = $params;
        return $this;
    }

    /**
     * Return an array of information about the requested lock.
     *
     * @param string $lockid   Lock ID to look up
     *
     * @return mixed           Array of lock information on success; PEAR_Error
     *                         on failure.
     */
    function getLockInfo($lockid)
    {
        return PEAR::raiseError(_("No lock driver configured!"));
    }

    /**
     * Return a list of valid locks with the option to limit the results
     * by principal, scope and/or type.
     *
     * @param string $scope      The scope of the lock.  Typically the name of
     *                           the application requesting the lock or some
     *                           other identifier used to group locks together.
     * @param string $principal  Principal for which to check for locks
     * @param int $type          Only return locks of the given type.
     *                           Defaults to null, or all locks
     *
     * @return mixed  Array of locks with the ID as the key and the lock details
     *                as the value. If there are no current locks this will
     *                return an empty array. On failure a PEAR_Error object
     *                will be returned.
     */
    function getLocks($scope = null, $principal = null, $type = null)
    {
        return PEAR::raiseError(_("No lock driver configured!"));
    }

    /**
     * Extend the valid lifetime of a valid lock to now + $extend.
     *
     * @param string $lockid  Lock ID to reset.  Must be a valid, non-expired
     *                        lock.
     * @param int $extend     Extend lock this many seconds from now.
     *
     * @return mixed          True on success; PEAR_Error on failure.
     */
    function resetLock($lockid, $extend)
    {
        return PEAR::raiseError(_("No lock driver configured!"));
    }

    /**
     * Sets a lock on the requested principal and returns the generated lock ID.
     * NOTE: No security checks are done in the Horde_Lock API.  It is expected
     * that the calling application has done all necessary security checks
     * before requesting a lock be granted.
     *
     * @param string $requestor  User ID of the lock requestor.
     * @param string $scope      The scope of the lock.  Typically the name of
     *                           the application requesting the lock or some
     *                           other identifier used to group locks together.
     * @param string $principal  A principal on which a lock should be granted.
     *                           The format can be any string but is suggested 
     *                           to be in URI form.
     * @param int $lifetime      Time (in seconds) for which the lock will be
     *                           considered valid.
     * @param string exclusive   One of HORDE_LOCK_TYPE_SHARED or
     *                           HORDE_LOCK_TYPE_EXCLUSIVE.
     *                           - An exclusive lock will be enforced strictly
     *                             and must be interpreted to mean that the
     *                             resource can not be modified.  Only one
     *                             exclusive lock per principal is allowed.
     *                           - A shared lock is one that notifies other
     *                             potential lock requestors that the resource
     *                             is in use.  This lock can be overridden
     *                             (cleared or replaced with a subsequent
     *                             call to setLock()) by other users.  Multiple
     *                             users may request (and will be granted) a
     *                             shared lock on a given principal.  All locks
     *                             will be considered valid until they are
     *                             cleared or expire.
     *
     * @return mixed   A string lock ID on success; PEAR_Error on failure.
     */
    function setLock($requestor, $scope, $principal,
                     $lifetime = 1, $exclusive = HORDE_LOCK_TYPE_SHARED)
    {
        return PEAR::raiseError(_("No lock driver configured!"));
    }

    /**
     * Removes a lock given the lock ID.
     * NOTE: No security checks are done in the Horde_Lock API.  It is expected
     * that the calling application has done all necessary security checks
     * before requesting a lock be cleared.
     *
     * @param string $lockid  The lock ID as generated by a previous call
     *                        to setLock()
     *
     * @return mixed   True on success; PEAR_Error on failure.
     */
    function clearLock($lockid)
    {
        return PEAR::raiseError(_("No lock driver configured!"));
    }

    /**
     * Generate a new Universally Unique Identifier for use as lock token
     *
     * Borrowed from HTTP_WebDAV_Server::_new_uuid()
     *
     * @param  void
     * @return string  UUID string
     */
    function _uuidgen()
    {
        // See if PECL extension exists; if so, use it.
        if (function_exists('uuid_create')) {
            return uuid_create();
        }

        $uuid = md5(uniqid(rand(), true));

        // set variant and version fields for 'true' DCE1.1 compliant uuid
        $uuid{12} = "4";
        $n = 8 + (ord($uuid{16}) & 3);
        $hex = "0123456789abcdef";
        $uuid{16} = $hex{$n};

        return substr($uuid,  0, 8) . "-" . substr($uuid,  8, 4) . "-" .
               substr($uuid, 12, 4) . "-" . substr($uuid, 16, 4) . "-" .
               substr($uuid, 20);
    }

    /**
     * Attempts to return a concrete Horde_Lock instance based on $driver.
     *
     * @param mixed $driver  The type of concrete Horde_Lock subclass to return.
     *                       This is based on the storage driver ($driver).
     *                       The code is dynamically included. If $driver is an
     *                       array, then we will look in $driver[0]/lib/Lock/
     *                       for the subclass implementation named
     *                       $driver[1].php.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return Horde_Lock    The newly created concrete Lock instance, or a
     *                       PEAR_Error object on error.
     */
    function factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        if (empty($driver) || ($driver == 'none')) {
            return new Horde_Lock();
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('lock', $driver);
        }

        $class = 'Horde_Lock_' . $driver;
        $include_error = '';
        if (!class_exists($class)) {
            $oldTrackErrors = ini_set('track_errors', 1);
            if (!empty($app)) {
                include $GLOBALS['registry']->get('fileroot', $app) . '/lib/Horde_Lock/' . $driver . '.php';
            } else {
                include 'Horde/Lock/' . $driver . '.php';
            }
            if (isset($php_errormsg)) {
                $include_error = $php_errormsg;
            }
            ini_set('track_errors', $oldTrackErrors);
        }

        if (class_exists($class)) {
            $lock = new $class($params);
        } else {
            $lock = PEAR::raiseError('Horde_Lock Driver (' . $class . ') not found' . ($include_error ? ': ' . $include_error : '') . '.');
        }

        return $lock;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Lock instance based on
     * $driver. It will only create a new instance if no Horde_Lock instance
     * with the same parameters currently exists.
     *
     * This should be used if multiple authentication sources (and, thus,
     * multiple Horde_Lock instances) are required.
     *
     * This method must be invoked as: $var = &Horde_Lock::singleton()
     *
     * @param string $driver  The type of concrete Horde_Lock subclass to
     *                        return.
     *                        This is based on the storage driver ($driver).
     *                        The code is dynamically included.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return Horde_Lock     The concrete Horde_Lock reference or PEAR_Error
     *                        on failure.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

        if (is_null($params)) {
            $params = Horde::getDriverConfig('lock',
                is_array($driver) ? $driver[1] : $driver);
        }

        $signature = serialize(array($driver, $params));
        if (empty($instances[$signature])) {
            $instances[$signature] = Horde_Lock::factory($driver, $params);
        }

        return $instances[$signature];
    }

}
