<?php
/**
 * The History:: class provides a method of tracking changes in Horde
 * objects, stored in a SQL table.
 *
 * $Horde: framework/History/History.php,v 1.28.2.23 2009-06-16 12:58:33 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_History
 */
class Horde_History {

    /**
     * Pointer to a DB instance to manage the history.
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
     * Attempts to return a reference to a concrete History instance.
     * It will only create a new instance if no History instance
     * currently exists.
     *
     * This method must be invoked as: $var = &History::singleton()
     *
     * @return Horde_History  The concrete History reference, or false on an
     *                        error.
     */
    function &singleton()
    {
        static $history;

        if (!isset($history)) {
            $history = new Horde_History();
        }

        return $history;
    }

    /**
     * Constructor.
     */
    function Horde_History()
    {
        global $conf;

        if (empty($conf['sql']['phptype']) ||
            $conf['sql']['phptype'] == 'none') {
            $this->_db = $this->_write_db =
                PEAR::raiseError(_("The History system is disabled."));
            return;
        }

        require_once 'DB.php';
        $this->_write_db = &DB::connect($conf['sql']);

        /* Set DB portability options. */
        if (is_a($this->_write_db, 'DB_common')) {
            switch ($this->_write_db->phptype) {
            case 'mssql':
                $this->_write_db->setOption('portability',
                                            DB_PORTABILITY_LOWERCASE |
                                            DB_PORTABILITY_ERRORS |
                                            DB_PORTABILITY_RTRIM);
                break;
            default:
                $this->_write_db->setOption('portability',
                                            DB_PORTABILITY_LOWERCASE |
                                            DB_PORTABILITY_ERRORS);
            }
        }

        /* Check if we need to set up the read DB connection
         * seperately. */
        if (!empty($conf['sql']['splitread'])) {
            $params = array_merge($conf['sql'], $conf['sql']['read']);
            $this->_db = &DB::connect($params);

            /* Set DB portability options. */
            if (is_a($this->_db, 'DB_common')) {
                switch ($this->_db->phptype) {
                case 'mssql':
                    $this->_db->setOption('portability',
                                          DB_PORTABILITY_LOWERCASE |
                                          DB_PORTABILITY_ERRORS |
                                          DB_PORTABILITY_RTRIM);
                    break;
                default:
                    $this->_db->setOption('portability',
                                          DB_PORTABILITY_LOWERCASE |
                                          DB_PORTABILITY_ERRORS);
                }
            }
        } else {
            /* Default to the same DB handle for reads. */
            $this->_db =& $this->_write_db;
        }
    }

    /**
     * Logs an event to an item's history log. The item must be uniquely
     * identified by $guid. Any other details about the event are passed in
     * $attributes. Standard suggested attributes are:
     *
     *   'who' => The id of the user that performed the action (will be added
     *            automatically if not present).
     *
     *   'ts' => Timestamp of the action (this will be added automatically if
     *           it is not present).
     *
     * @param string $guid            The unique identifier of the entry to
     *                                add to.
     * @param array $attributes       The hash of name => value entries that
     *                                describe this event.
     * @param boolean $replaceAction  If $attributes['action'] is already
     *                                present in the item's history log,
     *                                update that entry instead of creating a
     *                                new one.
     *
     * @return boolean|PEAR_Error  True on success, PEAR_Error on failure.
     */
    function log($guid, $attributes = array(), $replaceAction = false)
    {
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return $this->_write_db;
        }

        $history = &$this->getHistory($guid);
        if (!$history || is_a($history, 'PEAR_Error')) {
            return $history;
        }

        if (!isset($attributes['who'])) {
            $attributes['who'] = Auth::getAuth();
        }
        if (!isset($attributes['ts'])) {
            $attributes['ts'] = time();
        }

        /* If we want to replace an entry with the same action, try and find
         * one. Track whether or not we succeed in $done, so we know whether
         * or not to add the entry later. */
        $done = false;
        if ($replaceAction && !empty($attributes['action'])) {
            $count = count($history->data);
            for ($i = 0; $i < $count; $i++) {
                if (!empty($history->data[$i]['action']) &&
                    $history->data[$i]['action'] == $attributes['action']) {

                    $values = array($attributes['ts'],
                                    $attributes['who'],
                                    isset($attributes['desc']) ? $attributes['desc'] : null);
                    unset($attributes['ts']);
                    unset($attributes['who']);
                    unset($attributes['desc']);
                    unset($attributes['action']);
                    if ($attributes) {
                        $values[] = serialize($attributes);
                    } else {
                        $values[] = null;
                    }
                    $values[] = $history->data[$i]['id'];

                    $r = $this->_write_db->query('UPDATE horde_histories SET history_ts = ?,' .
                                                 ' history_who = ?,' .
                                                 ' history_desc = ?,' .
                                                 ' history_extra = ? WHERE history_id = ?', $values);
                    if (is_a($r, 'PEAR_Error')) {
                        Horde::logMessage($r, __FILE__, __LINE__, PEAR_LOG_ERR);
                        return $r;
                    }
                    $done = true;
                    break;
                }
            }
        }

        /* If we're not replacing by action, or if we didn't find an entry to
         * replace, insert a new row. */
        if (!$done) {
            $history_id = $this->_write_db->nextId('horde_histories');
            if (is_a($history_id, 'PEAR_Error')) {
                Horde::logMessage($history_id, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $history_id;
            }
            $values = array($history_id,
                            $guid,
                            $attributes['ts'],
                            $attributes['who'],
                            isset($attributes['desc']) ? $attributes['desc'] : null,
                            isset($attributes['action']) ? $attributes['action'] : null);
            unset($attributes['ts']);
            unset($attributes['who']);
            unset($attributes['desc']);
            unset($attributes['action']);
            if ($attributes) {
                $values[] = serialize($attributes);
            } else {
                $values[] = null;
            }

            $r = $this->_write_db->query('INSERT INTO horde_histories (history_id, object_uid, history_ts, history_who, history_desc, history_action, history_extra)' .
                              ' VALUES (?, ?, ?, ?, ?, ?, ?)', $values);
            if (is_a($r, 'PEAR_Error')) {
                Horde::logMessage($r, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $r;
            }
        }

        return true;
    }

    /**
     * Returns a HistoryObject corresponding to the named history
     * entry, with the data retrieved appropriately. $autocreate has
     * no affect.
     *
     * @param string $guid         The name of the history entry to retrieve.
     * @param boolean $autocreate  Deprecated.
     */
    function &getHistory($guid, $autocreate = null)
    {
        if (is_a($this->_db, 'PEAR_Error')) {
            $false = false;
            return $false;
        }

        $rows = $this->_db->getAll('SELECT * FROM horde_histories WHERE object_uid = ?', array($guid), DB_FETCHMODE_ASSOC);
        $history = &new HistoryObject($guid, $rows);
        return $history;
    }

    /**
     * Finds history objects by timestamp, and optionally filter on other
     * fields as well.
     *
     * @param string $cmp     The comparison operator (<, >, <=, >=, or =) to
     *                        check the timestamps with.
     * @param integer $ts     The timestamp to compare against.
     * @param array $filters  An array of additional (ANDed) criteria.
     *                        Each array value should be an array with 3
     *                        entries:
     * <pre>
     *                         'op'    - the operator to compare this field
     *                                   with.
     *                         'field' - the history field being compared
     *                                   (i.e. 'action').
     *                         'value' - the value to check for (i.e. 'add').
     * </pre>
     * @param string $parent  The parent history to start searching at. If non-empty,
     *                        will be searched for with a LIKE '$parent:%' clause.
     *
     * @return array  An array of history object ids, or an empty array if
     *                none matched the criteria.
     */
    function getByTimestamp($cmp, $ts, $filters = array(), $parent = null)
    {
        if (is_a($this->_db, 'PEAR_Error')) {
            return false;
        }

        /* Build the timestamp test. */
        $where = array("history_ts $cmp $ts");

        /* Add additional filters, if there are any. */
        if ($filters) {
            foreach ($filters as $filter) {
                $where[] = 'history_' . $filter['field'] . ' ' . $filter['op'] . ' ' . $this->_db->quote($filter['value']);
            }
        }

        if ($parent) {
            $where[] = 'object_uid LIKE ' . $this->_db->quote($parent . ':%');
        }

        return $this->_db->getAssoc('SELECT DISTINCT object_uid, history_id FROM horde_histories WHERE ' . implode(' AND ', $where));
    }

    /**
     * Gets the timestamp of the most recent change to $guid.
     *
     * @param string $guid    The name of the history entry to retrieve.
     * @param string $action  An action: 'add', 'modify', 'delete', etc.
     *
     * @return integer  The timestamp, or 0 if no matching entry is found.
     */
    function getActionTimestamp($guid, $action)
    {
        /* This implementation still works, but we should be able to
         * get much faster now with a SELECT MAX(history_ts)
         * ... query. */
        $history = &$this->getHistory($guid);
        if (!$history || is_a($history, 'PEAR_Error')) {
            return 0;
        }

        $last = 0;
        if (is_array($history->data)) {
            foreach ($history->data as $entry) {
                if ($entry['action'] == $action && $entry['ts'] > $last) {
                    $last = $entry['ts'];
                }
            }
        }

        return (int)$last;
    }

    /**
     * Remove one or more history entries by name.
     *
     * @param array $names  The history entries to remove.
     */
    function removeByNames($names)
    {
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return false;
        }
        if (!count($names)) {
            return true;
        }

        $ids = array();
        foreach ($names as $name) {
            $ids[] = $this->_write_db->quote($name);
        }

        return $this->_write_db->query('DELETE FROM horde_histories WHERE object_uid IN (' . implode(',', $ids) . ')');
    }

}

/**
 * Class for presenting History information.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.1
 * @package Horde_History
 */
class HistoryObject {

    var $uid;
    var $data = array();

    function HistoryObject($uid, $data = array())
    {
        $this->uid = $uid;

        if (!$data || is_a($data, 'PEAR_Error')) {
            return;
        }

        foreach ($data as $row) {
            $history = array('action' => $row['history_action'],
                             'desc' => $row['history_desc'],
                             'who' => $row['history_who'],
                             'id' => $row['history_id'],
                             'ts' => $row['history_ts']);
            if ($row['history_extra']) {
                $extra = @unserialize($row['history_extra']);
                if ($extra) {
                    $history = array_merge($history, $extra);
                }
            }
            $this->data[] = $history;
        }
    }

    function getData()
    {
        return $this->data;
    }

}
