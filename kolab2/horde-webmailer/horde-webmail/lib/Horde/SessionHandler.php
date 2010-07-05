<?php
/**
 * SessionHandler:: defines an API for implementing custom PHP session
 * handlers.
 *
 * Optional parameters:<pre>
 *   'memcache' - (boolean) Use memcache to cache session data?
 * </pre>
 *
 * $Horde: framework/SessionHandler/SessionHandler.php,v 1.13.10.20 2009-10-08 22:25:23 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @author  Michael Slusarz <slusarz@curecanti.org>
 * @package Horde_SessionHandler
 */
class SessionHandler {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Initial session data signature.
     *
     * @var string
     */
    var $_sig;

    /**
     * Force saving the session data?
     *
     * @var boolean
     */
    var $_force = false;

    /**
     * Has a connection been made to the backend?
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Constructs a new SessionHandler object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function SessionHandler($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Destructor (PHP 5 only).
     *
     * This is necessary as of PHP 5.0.5 because objects are not available
     * when the write() handler is called at the end of a session access.
     */
    function __destruct()
    {
        session_write_close();
    }

    /**
     * Attempts to return a concrete SessionHandler instance based on
     * $driver.
     *
     * @param string $driver  The type of concrete SessionHandler subclass to
     *                        return.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return mixed  The newly created concrete SessionHandler instance, or
     *                false on an error.
     */
    function &factory($driver, $params = null)
    {
        if (is_array($driver)) {
            $app = $driver[0];
            $driver = $driver[1];
        }

        $driver = basename($driver);
        $persistent_params = array();

        if ($driver == 'memcached') {
            // Trap for old driver name.
            $driver = 'memcache';
        } elseif (($driver != 'memcache') && !empty($params['memcache'])) {
            unset($params['memcache']);
            $persistent_params = array('persistent_driver' => $driver, 'persistent_params' => $params);
            $driver = 'memcache';
            $params = null;
        }

        $class = 'SessionHandler_' . $driver;
        if (!class_exists($class)) {
            if (!empty($app)) {
                include $GLOBALS['registry']->get('fileroot', $app) . '/lib/SessionHandler/' . $driver . '.php';
            } else {
                include 'Horde/SessionHandler/' . $driver . '.php';
            }
        }

        if (class_exists($class)) {
            if (empty($params)) {
                include_once 'Horde.php';
                $params = Horde::getDriverConfig('sessionhandler', $driver);
            }
            $handler = new $class(array_merge($params, $persistent_params));
        } else {
            $handler = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $handler;
    }

    /**
     * Attempts to return a reference to a concrete SessionHandler
     * instance based on $driver. It will only create a new instance
     * if no SessionHandler instance with the same parameters
     * currently exists.
     *
     * This method must be invoked as: $var = &SessionHandler::singleton()
     *
     * @param string $driver  See SessionHandler::factory().
     * @param array $params   See SessionHandler::factory().
     *
     * @return mixed  The created concrete SessionHandler instance, or
     *                PEAR_Error on error.
     */
    function &singleton($driver, $params = null)
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (empty($instances[$signature])) {
            $instances[$signature] = &SessionHandler::factory($driver, $params);
        }

        return $instances[$signature];
    }

    /**
     * Open the SessionHandler backend.
     *
     * @param string $save_path     The path to the session object.
     * @param string $session_name  The name of the session.
     *
     * @return boolean  True on success, false otherwise.
     */
    function open($save_path = null, $session_name = null)
    {
        if ($this->_connected) {
            return true;
        }

        $res = $this->_open($save_path, $session_name);
        if (is_a($res, 'PEAR_Error')) {
            Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        register_shutdown_function(array(&$this, '_shutdown'));
        $this->_connected = true;
        return true;
    }

    /**
     * Open the SessionHandler backend.
     *
     * @abstract
     * @access private
     *
     * @param string $save_path     The path to the session object.
     * @param string $session_name  The name of the session.
     *
     * @return boolean  True on success, PEAR_Error on error.
     */
    function _open($save_path = null, $session_name = null)
    {
        return true;
    }

    /**
     * Close the SessionHandler backend.
     *
     * @return boolean  True on success, false otherwise.
     */
    function close()
    {
        $res = $this->_close();
        $this->_connected = false;
        return $res;
    }

    /**
     * Close the SessionHandler backend.
     *
     * @abstract
     * @access private
     *
     * @return boolean  True on success, false otherwise.
     */
    function _close()
    {
        return true;
    }

    /**
     * Read the data for a particular session identifier from the
     * SessionHandler backend.
     * This method should only be called internally by PHP via
     * session_set_save_handler().
     *
     * @param string $id  The session identifier.
     *
     * @return string  The session data.
     */
    function read($id)
    {
        $result = $this->_read($id);
        $this->_sig = md5($result);
        return $result;
    }

    /**
     * Read the data for a particular session identifier from the
     * SessionHandler backend.
     *
     * @abstract
     * @access private
     *
     * @param string $id  The session identifier.
     *
     * @return string  The session data.
     */
    function _read($id)
    {
        return '';
    }

    /**
     * Write session data to the SessionHandler backend.
     * This method should only be called internally by PHP via
     * session_set_save_handler().
     *
     * @param string $id            The session identifier.
     * @param string $session_data  The session data.
     *
     * @return boolean  True on success, false otherwise.
     */
    function write($id, $session_data)
    {
        if (!$this->_force && ($this->_sig == md5($session_data))) {
            Horde::logMessage('Session data unchanged (id = ' . $id . ')', __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return true;
        }

        return $this->_write($id, $session_data);
    }

    /**
     * Write session data to the SessionHandler backend.
     *
     * @abstract
     * @access private
     *
     * @param string $id            The session identifier.
     * @param string $session_data  The session data.
     *
     * @return boolean  True on success, false otherwise.
     */
    function _write($id, $session_data)
    {
        return false;
    }

    /**
     * Destroy the data for a particular session identifier in the
     * SessionHandler backend.
     * This method should only be called internally by PHP via
     * session_set_save_handler().
     *
     * @abstract
     *
     * @param string $id  The session identifier.
     *
     * @return boolean  True on success, false otherwise.
     */
    function destroy($id)
    {
        return false;
    }

    /**
     * Garbage collect stale sessions from the SessionHandler backend.
     * This method should only be called internally by PHP via
     * session_set_save_handler().
     *
     * @abstract
     *
     * @param integer $maxlifetime  The maximum age of a session.
     *
     * @return boolean  True on success, false otherwise.
     */
    function gc($maxlifetime = 300)
    {
        return false;
    }

    /**
     * Get session data read-only.
     *
     * @access private
     *
     * @param string $id  The session identifier.
     *
     * @return string  The session data.
     */
    function _readOnly($id)
    {
        return $this->read($id);
    }

    /**
     * Get a list of the valid session identifiers.
     *
     * @abstract
     *
     * @return array  A list of valid session identifiers.
     *                Returns PEAR_Error on error.
     */
    function getSessionIDs()
    {
        return PEAR::raiseError(_("Not supported."));
    }

    /**
     * Determine the number of currently logged in users.
     * getSessionsInfo() should be called instead.
     *
     * @deprecated
     *
     * @return integer  A count of logged in users or PEAR_Error on error.
     */
    function countAuthenticatedUsers()
    {
        $sessions = $this->getSessionsInfo();
        if (is_a($sessions, 'PEAR_Error')) {
            return $sessions;
        }
        return count($sessions);
    }

    /**
     * Returns a list of currently logged in users.
     * getSessionsInfo() should be called instead.
     *
     * @deprecated
     *
     * @param boolean $date  Prefix the timestamp to the username?
     *
     * @return array  A list of logged in users or PEAR_Error on error.
     */
    function listAuthenticatedUsers($date = false)
    {
        $sessions = $this->getSessionsInfo();
        if (is_a($sessions, 'PEAR_Error')) {
            return $sessions;
        }

        $users = array();

        reset($users);
        while (list($key, $val) = each($users)) {
            $users[] = (($date) ? date('r', $data['timestamp']) . '  ' : '') . $data['userid'];
        }

        return $users;
    }

    /**
     * Returns a list of authenticated users and data about their session.
     *
     * @since Horde 3.2
     *
     * @return array  For authenticated users, the sessionid as a key and the
     *                information returned from Auth::readSessionData() as
     *                values.
     *                Returns PEAR_Error on error.
     */
    function getSessionsInfo()
    {
        $sessions = $this->getSessionIDs();
        if (is_a($sessions, 'PEAR_Error')) {
            return $sessions;
        }

        $info = array();

        foreach ($sessions as $id) {
            $data = $this->_readOnly($id);
            if (is_a($data, 'PEAR_Error')) {
                continue;
            }
            $data = Auth::readSessionData($data, true);
            if ($data !== false) {
                $info[$id] = $data;
            }
        }

        return $info;
    }

    /**
     * Shutdown function.  Used to determine if we need to write the session
     * to avoid a session timeout, even though the session is unchanged.
     * Theory: On initial login, set the current time plus half of the max
     * lifetime in the session.  Then check this timestamp before saving.
     * If we exceed, force a write of the session and set a new timestamp.
     * Why half the maxlifetime?  It guarantees that if we are accessing the
     * server via a periodic mechanism (think folder refreshing in IMP) that
     * we will catch this refresh.
     *
     * @access private
     */
    function _shutdown()
    {
        $curr_time = time();

        if (!isset($_SESSION['__sessionhandler']) ||
            ($curr_time >= $_SESSION['__sessionhandler'])) {

            $_SESSION['__sessionhandler'] = $curr_time + (ini_get('session.gc_maxlifetime') / 2);
            $this->_force = true;
        }
    }

}
