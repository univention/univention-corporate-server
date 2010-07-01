<?php
/**
 * Turba directory driver implementation for PHP's PEAR database abstraction
 * layer.
 *
 * $Horde: turba/lib/Driver/sql.php,v 1.59.10.32 2009-10-07 16:16:38 mrubinsk Exp $
 *
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_Driver_sql extends Turba_Driver {

    /**
     * What can this backend do?
     *
     * @var array
     */
    var $_capabilities = array(
        'delete_all' => true,
        'delete_addressbook' => true
    );

    /**
     * Handle for the database connection.
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

    function _init()
    {
        include_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                        array('persistent' => !empty($this->_params['persistent']),
                                              'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            return $this->_write_db;
        }

        // Set DB portability options.
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;
        default:
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }

        if ($this->_params['phptype'] == 'oci8') {
            $this->_write_db->query('ALTER SESSION SET NLS_DATE_FORMAT = \'YYYY-MM-DD\'');
        }

        /* Check if we need to set up the read DB connection
         * seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                return $this->_db;
            }

            // Set DB portability options.
            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
                break;
            default:
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
            }
            if ($params['phptype'] == 'oci8') {
                $this->_db->query('ALTER SESSION SET NLS_DATE_FORMAT = \'YYYY-MM-DD\'');
            }
        } else {
            /* Default to the same DB handle for reads. */
            $this->_db =& $this->_write_db;
        }

        return true;
    }

    /**
     * Returns the number of contacts of the current user in this address book.
     *
     * @return integer  The number of contacts that the user owns.
     */
    function count()
    {
        static $count = array();

        $test = $this->getContactOwner();
        if (!isset($count[$test])) {
            /* Build up the full query. */
            $query = 'SELECT COUNT(*) FROM ' . $this->_params['table'] .
                     ' WHERE ' . $this->toDriver('__owner') . ' = ?';
            $values = array($test);

            /* Log the query at a DEBUG log level. */
            Horde::logMessage('SQL query by Turba_Driver_sql::count(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            /* Run query. */
            $count[$test] = $this->_db->getOne($query, $values);
        }

        return $count[$test];
    }

    /**
     * Searches the SQL database with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty array,
     * all records will be returned.
     *
     * @param array $criteria      Array containing the search criteria.
     * @param array $fields        List of fields to return.
     * @param array $appendWhere   An additional where clause to append.
     *                             Array should contain 'sql' and 'params'
     *                             params are used as bind parameters.
     *
     * @return array  Hash containing the search results.
     */
    function _search($criteria, $fields, $appendWhere = array())
    {
        /* Build the WHERE clause. */
        $where = '';
        $values = array();
        if (count($criteria) || !empty($this->_params['filter'])) {
            foreach ($criteria as $key => $vals) {
                if ($key == 'OR' || $key == 'AND') {
                    if (!empty($where)) {
                        $where .= ' ' . $key . ' ';
                    }
                    $binds = $this->_buildSearchQuery($key, $vals);
                    $where .= '(' . $binds[0] . ')';
                    $values += $binds[1];
                }
            }
            $where = ' WHERE ' . $where;
            if (count($criteria) && !empty($this->_params['filter'])) {
                $where .= ' AND ';
            }
            if (!empty($this->_params['filter'])) {
                $where .= $this->_params['filter'];
            }
            if (count($appendWhere)) {
                $where .= ' AND ' . $appendWhere['sql'];
                $values = array_merge($values, $appendWhere['params']);
            }
        } elseif (count($appendWhere)) {
            $where = ' WHERE ' . $appendWhere['sql'];
            $values = array_merge($values, $appendWhere['params']);
        }

        /* Build up the full query. */
        $query = 'SELECT ' . implode(', ', $fields) . ' FROM ' . $this->_params['table'] . $where;

        /* Log the query at a DEBUG log level. */
        Horde::logMessage('SQL query by Turba_Driver_sql::_search(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Run query. */
        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $results = array();
        $iMax = count($fields);
        while ($row = $result->fetchRow()) {
            if (is_a($row, 'PEAR_Error')) {
                Horde::logMessage($row, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            }

            $row = $this->_convertFromDriver($row);

            $entry = array();
            for ($i = 0; $i < $iMax; $i++) {
                $field = $fields[$i];
                $entry[$field] = $row[$i];
            }
            $results[] = $entry;
        }

        return $results;
    }

    /**
     * Reads the given data from the SQL database and returns the
     * results.
     *
     * @param string $key    The primary key field to use.
     * @param mixed $ids     The ids of the contacts to load.
     * @param string $owner  Only return contacts owned by this user.
     * @param array $fields  List of fields to return.
     *
     * @return array  Hash containing the search results.
     */
    function _read($key, $ids, $owner, $fields, $blob_fields = array())
    {
        $values = array();

        $in = '';
        if (is_array($ids)) {
            if (!count($ids)) {
                return array();
            }

            foreach ($ids as $id) {
                $in .= empty($in) ? '?' : ', ?';
                $values[] = $this->_convertToDriver($id);
            }
            $where = $key . ' IN (' . $in . ')';
        } else {
            $where = $key . ' = ?';
            $values[] = $this->_convertToDriver($ids);
        }
        if (isset($this->map['__owner'])) {
            $where .= ' AND ' . $this->map['__owner'] . ' = ?';
            $values[] = $this->_convertToDriver($owner);
        }
        if (!empty($this->_params['filter'])) {
            $where .= ' AND ' . $this->_params['filter'];
        }

        $query  = 'SELECT ' . implode(', ', $fields) . ' FROM '
            . $this->_params['table'] . ' WHERE ' . $where;

        /* Log the query at a DEBUG log level. */
        Horde::logMessage('SQL query by Turba_Driver_sql::_read(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->getAll($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $results = array();
        $iMax = count($fields);
        foreach ($result as $row) {
            $entry = array();
            for ($i = 0; $i < $iMax; $i++) {
                $field = $fields[$i];
                if (isset($blob_fields[$field])) {
                    switch ($this->_db->dbsyntax) {
                    case 'pgsql':
                    case 'mssql':
                        $entry[$field] = pack('H' . strlen($row[$i]), $row[$i]);
                        break;
                    default:
                        $entry[$field] = $row[$i];
                        break;
                    }
                } else {
                    $entry[$field] = $this->_convertFromDriver($row[$i]);
                }
            }
            $results[] = $entry;
        }

        return $results;
    }

    /**
     * Adds the specified object to the SQL database.
     */
    function _add($attributes, $blob_fields = array())
    {
        $fields = $values = array();
        foreach ($attributes as $field => $value) {
            $fields[] = $field;
            if (!empty($value) && isset($blob_fields[$field])) {
                switch ($this->_write_db->dbsyntax) {
                case 'mssql':
                case 'pgsql':
                    $values[] = bin2hex($value);
                    break;
                default:
                    $values[] = $value;
                }
            } else {
                $values[] = $this->_convertToDriver($value);
            }
        }
        $query  = 'INSERT INTO ' . $this->_params['table']
            . ' (' . implode(', ', $fields) . ')'
            . ' VALUES (' . str_repeat('?, ', count($values) - 1) . '?)';

        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    /**
     * @see turba/lib/Turba_Driver#_canAdd()
     */
    function _canAdd()
    {
        return true;
    }

    /**
     * Deletes the specified object from the SQL database.
     */
    function _delete($object_key, $object_id)
    {
        $query = 'DELETE FROM ' . $this->_params['table'] .
                 ' WHERE ' . $object_key . ' = ?';
        $values = array($object_id);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage('SQL query by Turba_Driver_sql::_delete(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    /**
     * Deletes all contacts from a specific address book.
     *
     * @return boolean  True if the operation worked.
     */
    function _deleteAll($sourceName = null)
    {
        if (!Auth::getAuth()) {
            return PEAR::raiseError('permission denied');
        }

        $query = 'DELETE FROM ' . $this->_params['table'] . ' WHERE owner_id = ?';

        if (empty($sourceName)) {
            $values = array(Auth::getAuth());
        } else {
            $values = array($sourceName);
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage('SQL query by Turba_Driver_sql::_deleteAll(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_write_db->query($query, $values);
    }

    /**
     * Saves the specified object in the SQL database.
     *
     * @return string  The object id, possibly updated.
     */
    function _save($object_key, $object_id, $attributes, $blob_fields = array())
    {
        $where = $object_key . ' = ?';
        unset($attributes[$object_key]);

        $fields = $values =  array();
        foreach ($attributes as $field => $value) {
            $fields[] = $field . ' = ?';
            if (!empty($value) && isset($blob_fields[$field])) {
                switch ($this->_write_db->dbsyntax) {
                case 'mssql':
                case 'pgsql':
                    $values[] = bin2hex($value);
                    break;
                default:
                    $values[] = $value;
                }
            } else {
                $values[] = $this->_convertToDriver($value);
            }
        }

        $values[] = $object_id;

        $query  = 'UPDATE ' . $this->_params['table'] . ' SET ' . implode(', ', $fields) . ' ';
        $query .= 'WHERE ' . $where;

        /* Log the query at a DEBUG log level. */
        Horde::logMessage('SQL query by Turba_Driver_sql::_save(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return $object_id;
    }

    /**
     * Creates an object key for a new object.
     *
     * @param array $attributes  The attributes (in driver keys) of the
     *                           object being added.
     *
     * @return string  A unique ID for the new object.
     */
    function _makeKey($attributes)
    {
        return md5(uniqid(mt_rand(), true));
    }

    /**
     * Builds a piece of a search query.
     *
     * @param string $glue      The glue to join the criteria (OR/AND).
     * @param array  $criteria  The array of criteria.
     *
     * @return array  An SQL fragment and a list of values suitable for binding
     *                as an array.
     */
    function _buildSearchQuery($glue, $criteria)
    {
        require_once 'Horde/SQL.php';

        $clause = '';
        $values = array();

        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR']) || !empty($vals['AND'])) {
                if (!empty($clause)) {
                    $clause .= ' ' . $glue . ' ';
                }
                $binds = $this->_buildSearchQuery(!empty($vals['OR']) ? 'OR' : 'AND', $vals);
                $clause .= '(' . $binds[0] . ')';
                $values = array_merge($values, $binds[1]);
            } else {
                if (isset($vals['field'])) {
                    if (!empty($clause)) {
                        $clause .= ' ' . $glue . ' ';
                    }
                    $rhs = $this->_convertToDriver($vals['test']);
                    $binds = Horde_SQL::buildClause($this->_db, $vals['field'], $vals['op'], $rhs, true, array('begin' => !empty($vals['begin'])));
                    if (is_array($binds)) {
                        $clause .= $binds[0];
                        $values = array_merge($values, $binds[1]);
                    } else {
                        $clause .= $binds;
                    }
                } else {
                    foreach ($vals as $test) {
                        if (!empty($test['OR']) || !empty($test['AND'])) {
                            if (!empty($clause)) {
                                $clause .= ' ' . $glue . ' ';
                            }
                            $binds = $this->_buildSearchQuery(!empty($vals['OR']) ? 'OR' : 'AND', $test);
                            $clause .= '(' . $binds[0] . ')';
                            $values = array_merge($values, $binds[1]);
                        } else {
                            if (!empty($clause)) {
                                $clause .= ' ' . $key . ' ';
                            }
                            $rhs = $this->_convertToDriver($test['test']);
                            if ($rhs == '' && $test['op'] == '=') {
                                $clause .= '(' . Horde_SQL::buildClause($this->_db, $test['field'], '=', $rhs) . ' OR ' . $test['field'] . ' IS NULL)';
                            } else {
                                $binds = Horde_SQL::buildClause($this->_db, $test['field'], $test['op'], $rhs, true, array('begin' => !empty($test['begin'])));
                                if (is_array($binds)) {
                                    $clause .= $binds[0];
                                    $values = array_merge($values, $binds[1]);
                                } else {
                                    $clause .= $binds;
                                }
                            }
                        }
                    }
                }
            }
        }

        return array($clause, $values);
    }

    /**
     * Converts a value from the driver's charset to the default charset.
     *
     * @param mixed $value  A value to convert.
     *
     * @return mixed        The converted value.
     */
    function _convertFromDriver($value)
    {
        return String::convertCharset($value, $this->_params['charset']);
    }

    /**
     * Converts a value from the default charset to the driver's charset.
     *
     * @param mixed $value  A value to convert.
     *
     * @return mixed        The converted value.
     */
    function _convertToDriver($value)
    {
        return String::convertCharset($value, NLS::getCharset(), $this->_params['charset']);
    }

    /**
     * Remove all entries owned by the specified user.
     *
     * @param string $user  The user's data to remove.
     *
     * @return mixed True | PEAR_Error
     */
    function removeUserData($user)
    {
        // Make sure we are being called by an admin.
        if (!Auth::isAdmin()) {
            return PEAR::raiseError(_("Permission denied"));
        }

        return $this->_deleteAll($user);
    }

    /**
     * Obtain Turba_List of items to get TimeObjects out of.
     *
     * @param Horde_Date $start  The starting date.
     * @param Horde_Date $end    The ending date.
     * @param string $field      The address book field containing the
     *                           timeObject information (birthday, anniversary)
     *
     * @return mixed  A Tubra_List of objects || PEAR_Error
     */
    function _getTimeObjectTurbaList($start, $end, $field)
    {
        $t_object = $this->toDriver($field);
        $criteria = $this->makesearch(
            array('__owner' => $this->getContactOwner()),
            'AND',
            array($this->toDriver('__owner') => true),
            false);

        // Limit to entries that actually contain a birthday and that are in the
        // date range we are looking for.
        $criteria['AND'][] = array('field' => $t_object,
                                   'op' => '<>',
                                   'test' => '');

        if ($start->year == $end->year) {
            $start = sprintf('%02d-%02d', $start->month, $start->mday);
            $end = sprintf('%02d-%02d', $end->month, $end->mday);
            $where = array('sql' => $t_object . ' IS NOT NULL AND SUBSTR('
                           . $t_object . ', 6, 5) BETWEEN ? AND ?',
                           'params' => array($start, $end));
        } else {
            $months = array();
            $diff = ($end->month + 12) - $start->month;
            $newDate = new Horde_Date(array('month' => $start->month,
                                            'mday' => $start->mday,
                                            'year' => $start->year));
            for ($i = 0; $i <= $diff; $i++) {
                $months[] = sprintf('%02d', $newDate->month);
                $newDate->month++;
                $newDate->correct();
            }
            $where = array('sql' => $t_object . ' IS NOT NULL AND SUBSTR('
                           . $t_object . ', 6, 2) IN ('
                           . str_repeat('?,', count($months) - 1) . '?)',
                           'params' => $months);
        }

        $fields_pre = array('__key', '__type', '__owner', 'name',
                            'birthday', 'category', 'anniversary');
        $fields = array();
        foreach ($fields_pre as $field) {
            $result = $this->toDriver($field);
            if (is_array($result)) {
                foreach ($result as $composite_field) {
                    $composite_result = $this->toDriver($composite_field);
                    if ($composite_result) {
                        $fields[] = $composite_result;
                    }
                }
            } elseif ($result) {
                $fields[] = $result;
            }
        }

        $res = $this->_search($criteria, $fields, $where);
        if (is_a($res, 'PEAR_Error')) {
            return $res;
        }
        return $this->_toTurbaObjects($res);
    }

}
