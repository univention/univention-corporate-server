<?php
/**
 * @package Horde_Alarm
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Alarm/Alarm/sql.php,v 1.11.2.11 2009-12-10 13:30:48 jan Exp $
 */

/**
 * The Horde_Alarm_sql:: class is a Horde_Alarm storage implementation using
 * the PEAR DB package.
 *
 * Required values for $params:<pre>
 *      'phptype'       The database type (e.g. 'pgsql', 'mysql', etc.).
 *      'charset'       The database's internal charset.</pre>
 *
 * Optional values for $params:<pre>
 *      'table'         The name of the foo table in 'database'.
 *
 * Required by some database implementations:<pre>
 *      'database'      The name of the database.
 *      'hostspec'      The hostname of the database server.
 *      'protocol'      The communication protocol ('tcp', 'unix', etc.).
 *      'username'      The username with which to connect to the database.
 *      'password'      The password associated with 'username'.
 *      'options'       Additional options to pass to the database.
 *      'tty'           The TTY on which to connect to the database.
 *      'port'          The port on which to connect to the database.</pre>
 *
 * The table structure can be created by the scripts/sql/horde_alarm.sql
 * script.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2
 * @package Horde_Alarm
 */
class Horde_Alarm_sql extends Horde_Alarm {

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $_db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Constructs a new SQL storage object.
     *
     * @param array $params  A hash containing connection parameters.
     */
    function Horde_Alarm_sql($params = array())
    {
        $this->_params = array_merge($this->_params, $params);
    }

    /**
     * Converts a value from the driver's charset.
     *
     * @param mixed $value  Value to convert.
     *
     * @return mixed  Converted value.
     */
    function _fromDriver($value)
    {
        return String::convertCharset($value, $this->_params['charset']);
    }

    /**
     * Converts a value to the driver's charset.
     *
     * @param mixed $value  Value to convert.
     *
     * @return mixed  Converted value.
     */
    function _toDriver($value)
    {
        return String::convertCharset($value, NLS::getCharset(), $this->_params['charset']);
    }

    /**
     * Returns an alarm hash from the backend.
     *
     * @param string $id    The alarm's unique id.
     * @param string $user  The alarm's user
     *
     * @return array  An alarm hash.
     */
    function _get($id, $user)
    {
        $query = sprintf('SELECT alarm_id, alarm_uid, alarm_start, alarm_end, alarm_methods, alarm_params, alarm_title, alarm_text, alarm_snooze, alarm_internal FROM %s WHERE alarm_id = ? AND %s',
                         $this->_params['table'],
                         !empty($user) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        Horde::logMessage('SQL query by Horde_Alarm_sql::_get(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $alarm = $this->_db->getRow($query, array($id, $user), DB_FETCHMODE_ASSOC);
        if (is_a($alarm, 'PEAR_Error')) {
            Horde::logMessage($alarm, __FILE__, __LINE__);
            return $alarm;
        }
        if (empty($alarm)) {
            return PEAR::raiseError(_("Alarm not found"));
        }
        $alarm = array(
            'id' => $alarm['alarm_id'],
            'user' => $alarm['alarm_uid'],
            'start' => new Horde_Date($alarm['alarm_start']),
            'end' => empty($alarm['alarm_end']) ? null : new Horde_Date($alarm['alarm_end']),
            'methods' => @unserialize($alarm['alarm_methods']),
            'params' => @unserialize($alarm['alarm_params']),
            'title' => $this->_fromDriver($alarm['alarm_title']),
            'text' => $this->_fromDriver($alarm['alarm_text']),
            'snooze' => empty($alarm['alarm_snooze']) ? null : new Horde_Date($alarm['alarm_snooze']),
            'internal' => empty($alarm['alarm_internal']) ? null : @unserialize($alarm['alarm_internal']));
        return $alarm;
    }

    /**
     * Returns a list of alarms from the backend.
     *
     * @param Horde_Date $time  The time when the alarms should be active.
     * @param string $user      Return alarms for this user, all users if
     *                          null, or global alarms if empty.
     *
     * @return array  A list of alarm hashes.
     */
    function _list($user, $time)
    {
        $query = sprintf('SELECT alarm_id, alarm_uid, alarm_start, alarm_end, alarm_methods, alarm_params, alarm_title, alarm_text, alarm_snooze, alarm_internal FROM %s WHERE alarm_dismissed = 0 AND ((alarm_snooze IS NULL AND alarm_start <= ?) OR alarm_snooze <= ?) AND (alarm_end IS NULL OR alarm_end >= ?)%s ORDER BY alarm_start, alarm_end',
                         $this->_params['table'],
                         is_null($user) ? '' : ' AND (alarm_uid IS NULL OR alarm_uid = ? OR alarm_uid = ?)');
        $values = array($time->sqlDateTime(),
                        $time->sqlDateTime(),
                        $time->sqlDateTime());
        if (!is_null($user)) {
            $values[] = '';
            $values[] = (string)$user;
        }
        Horde::logMessage('SQL query by Horde_Alarm_sql::_list(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $alarms = array();
        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
            return $result;
        }
        while ($alarm = $result->fetchRow(DB_FETCHMODE_ASSOC)) {
            if (is_a($alarm, 'PEAR_Error')) {
                Horde::logMessage($alarm, __FILE__, __LINE__);
                return $alarm;
            }
            $alarms[$alarm['alarm_id']] = array(
                'id' => $alarm['alarm_id'],
                'user' => $alarm['alarm_uid'],
                'start' => new Horde_Date($alarm['alarm_start']),
                'end' => empty($alarm['alarm_end']) ? null : new Horde_Date($alarm['alarm_end']),
                'methods' => @unserialize($alarm['alarm_methods']),
                'params' => @unserialize($alarm['alarm_params']),
                'title' => $this->_fromDriver($alarm['alarm_title']),
                'text' => $this->_fromDriver($alarm['alarm_text']),
                'snooze' => empty($alarm['alarm_snooze']) ? null : new Horde_Date($alarm['alarm_snooze']),
                'internal' => empty($alarm['alarm_internal']) ? null : @unserialize($alarm['alarm_internal']));
        }

        return $alarms;
    }

    /**
     * Adds an alarm hash to the backend.
     *
     * @param array $alarm  An alarm hash.
     */
    function _add($alarm)
    {
        $query = sprintf('INSERT INTO %s (alarm_id, alarm_uid, alarm_start, alarm_end, alarm_methods, alarm_params, alarm_title, alarm_text, alarm_snooze) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', $this->_params['table']);
        $values = array($alarm['id'],
                        isset($alarm['user']) ? $alarm['user'] : '',
                        $alarm['start']->sqlDateTime(),
                        empty($alarm['end']) ? null : $alarm['end']->sqlDateTime(),
                        serialize($alarm['methods']),
                        serialize($alarm['params']),
                        $this->_toDriver($alarm['title']),
                        empty($alarm['text']) ? null : $this->_toDriver($alarm['text']),
                        null);
        Horde::logMessage('SQL query by Horde_Alarm_sql::_add(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Updates an alarm hash in the backend.
     *
     * @param array $alarm  An alarm hash.
     */
    function _update($alarm)
    {
        $query = sprintf('UPDATE %s set alarm_start = ?, alarm_end = ?, alarm_methods = ?, alarm_params = ?, alarm_title = ?, alarm_text = ? WHERE alarm_id = ? AND %s',
                         $this->_params['table'],
                         isset($alarm['user']) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        $values = array($alarm['start']->sqlDateTime(),
                        empty($alarm['end']) ? null : $alarm['end']->sqlDateTime(),
                        serialize($alarm['methods']),
                        serialize($alarm['params']),
                        $this->_toDriver($alarm['title']),
                        empty($alarm['text'])
                              ? null
                              : $this->_toDriver($alarm['text']),
                        $alarm['id'],
                        isset($alarm['user']) ? $alarm['user'] : '');
        Horde::logMessage('SQL query by Horde_Alarm_sql::_update(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Updates internal alarm properties, i.e. properties not determined by
     * the application setting the alarm.
     *
     * @param string $id       The alarm's unique id.
     * @param string $user     The alarm's user
     * @param array $internal  A hash with the internal data.
     */
    function _internal($id, $user, $internal)
    {
        $query = sprintf('UPDATE %s set alarm_internal = ? WHERE alarm_id = ? AND %s',
                         $this->_params['table'],
                         !empty($user) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        $values = array(serialize($internal), $id, $user);
        Horde::logMessage('SQL query by Horde_Alarm_sql::_internal(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Returns whether an alarm with the given id exists already.
     *
     * @param string $id    The alarm's unique id.
     * @param string $user  The alarm's user
     *
     * @return boolean  True if the specified alarm exists.
     */
    function _exists($id, $user)
    {
        $query = sprintf('SELECT 1 FROM %s WHERE alarm_id = ? AND %s',
                         $this->_params['table'],
                         !empty($user) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        Horde::logMessage('SQL query by Horde_Alarm_sql::_exists(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->getOne($query, array($id, $user));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Delays (snoozes) an alarm for a certain period.
     *
     * @param string $id          The alarm's unique id.
     * @param string $user        The alarm's user
     * @param Horde_Date $snooze  The snooze time.
     */
    function _snooze($id, $user, $snooze)
    {
        $query = sprintf('UPDATE %s set alarm_snooze = ? WHERE alarm_id = ? AND %s',
                         $this->_params['table'],
                         !empty($user) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        $values = array($snooze->sqlDateTime(), $id, $user);
        Horde::logMessage('SQL query by Horde_Alarm_sql::_snooze(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Dismisses an alarm.
     *
     * @param string $id          The alarm's unique id.
     * @param string $user        The alarm's user
     */
    function _dismiss($id, $user)
    {
        $query = sprintf('UPDATE %s set alarm_dismissed = 1 WHERE alarm_id = ? AND %s',
                         $this->_params['table'],
                         !empty($user) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        $values = array($id, $user);
        Horde::logMessage('SQL query by Horde_Alarm_sql::_dismiss(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Returns whether an alarm is snoozed.
     *
     * @param string $id        The alarm's unique id.
     * @param string $user      The alarm's user
     * @param Horde_Date $time  The time when the alarm may be snoozed.
     *
     * @return boolean  True if the alarm is snoozed.
     */
    function _isSnoozed($id, $user, $time)
    {
        $query = sprintf('SELECT 1 FROM %s WHERE alarm_id = ? AND %s AND (alarm_dismissed = 1 OR (alarm_snooze IS NOT NULL AND alarm_snooze >= ?))',
                         $this->_params['table'],
                         !empty($user) ? 'alarm_uid = ?' : '(alarm_uid = ? OR alarm_uid IS NULL)');
        Horde::logMessage('SQL query by Horde_Alarm_sql::_isSnoozed(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->getOne($query, array($id, $user, $time->sqlDateTime()));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Deletes an alarm from the backend.
     *
     * @param string $id    The alarm's unique id.
     * @param string $user  The alarm's user. All users' alarms if null.
     */
    function _delete($id, $user = null)
    {
        $query = sprintf('DELETE FROM %s WHERE alarm_id = ?', $this->_params['table']);
        $values = array($id);
        if (!is_null($user)) {
            $query .= empty($user)
                ? ' AND (alarm_uid IS NULL OR alarm_uid = ?)'
                : ' AND alarm_uid = ?';
            $values[] = $user;
        }
        Horde::logMessage('SQL query by Horde_Alarm_sql::_delete(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Garbage collects old alarms in the backend.
     */
    function _gc()
    {
        $query = sprintf('DELETE FROM %s WHERE alarm_end IS NOT NULL AND alarm_end < ?', $this->_params['table']);
        Horde::logMessage('SQL query by Horde_Alarm_sql::_gc(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $end = new Horde_Date(time());
        $result = $this->_write_db->query($query, $end->sqlDateTime());
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__);
        }
        return $result;
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @return boolean  True on success, PEAR_Error on failure.
     */
    function initialize()
    {
        Horde::assertDriverConfig($this->_params, 'sql',
                                  array('phptype', 'charset'));

        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }
        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'horde_alarms';
        }

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                        array('persistent' => !empty($this->_params['persistent']),
                                              'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            Horde::logMessage($this->_write_db, __FILE__, __LINE__);
            return $this->_write_db;
        }
        $this->_initConn($this->_write_db);

        /* Check if we need to set up the read DB connection seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::logMessage($this->_db, __FILE__, __LINE__);
                return $this->_db;
            }
            $this->_initConn($this->_db);
        } else {
            /* Default to the same DB handle for the writer too. */
            $this->_db = &$this->_write_db;
        }

        return true;
    }

    /**
     */
    function _initConn(&$db)
    {
        // Set DB portability options.
        switch ($db->phptype) {
        case 'mssql':
            $db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;

        default:
            $db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }

        /* Handle any database specific initialization code to run. */
        switch ($db->dbsyntax) {
        case 'oci8':
            $query = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'";

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('SQL connection setup for Alarms, query = "%s"', $query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $db->query($query);
            break;

        case 'pgsql':
            $query = "SET datestyle TO 'iso'";

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('SQL connection setup for Alarms, query = "%s"', $query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $db->query($query);
            break;
        }
    }

}
