<?php
/**
 * Turba directory driver implementation for PHP's PEAR database abstraction
 * layer.
 *
 * $Horde: turba/lib/Driver/sql.php,v 1.50 2004/04/07 14:43:52 chuck Exp $
 *
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_Driver_sql extends Turba_Driver {

    /** Handle for the current database connection. */
    var $_db = null;

    function init()
    {
        include_once 'DB.php';
        $this->_db = &DB::connect($this->_params,
                                  array('persistent' => !empty($this->_params['persistent'])));
        if (is_a($this->_db, 'PEAR_Error')) {
            return $this->_db;
        }

        $this->_db->setOption('optimize', 'portability');

        if ($this->_params['phptype'] == 'oci8') {
            $this->_db->query('ALTER SESSION SET NLS_DATE_FORMAT = \'YYYY-MM-DD\'');
        }
    }

    /**
     * Searches the SQL database with the given criteria and returns a
     * filtered list of results. If the criteria parameter is an empty
     * array, all records will be returned.
     *
     * @param $criteria      Array containing the search criteria.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function search($criteria, $fields)
    {
        /* Build the WHERE clause. */
        $where = '';
        if (count($criteria)) {
            foreach ($criteria as $key => $vals) {
                if ($key == 'OR' || $key == 'AND') {
                    if (!empty($where)) {
                        $where .= ' ' . $key . ' ';
                    }
                    $where .= '(' . $this->_buildSearchQuery($key, $vals) . ')';
                }
            }
            $where = ' WHERE ' . $where;
        }

        /* Build up the full query. */
        $query = 'SELECT ' . implode(', ', $fields) . ' FROM ' . $this->_params['table'] . $where;

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL search by %s: table = %s; query = "%s"',
                                  Auth::getAuth(), $this->_params['table'], $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Run query. */
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return array();
        }

        $results = array();
        $iMax = count($fields);
        while ($row = $result->fetchRow()) {
            if (is_a($row, 'PEAR_Error')) {
                Horde::logMessage($row, __FILE__, __LINE__, PEAR_LOG_ERR);
                return array();
            }

            $entry = array();
            for ($i = 0; $i < $iMax; $i++) {
                $field = $fields[$i];
                $entry[$field] = $this->_convertFromDriver($row[$i]);
            }
            $results[] = $entry;
        }

        return $results;
    }

    /**
     * Build a piece of a search query.
     *
     * @param string $glue      The glue to join the criteria (OR/AND).
     * @param array  $criteria  The array of criteria.
     *
     * @return string  An SQL fragment.
     */
    function _buildSearchQuery($glue, $criteria)
    {
        require_once 'Horde/SQL.php';

        $clause = '';
        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR']) || !empty($vals['AND'])) {
                if (!empty($clause)) {
                    $clause .= ' ' . $glue . ' ';
                }
                $clause .= '(' . $this->_buildSearchQuery($glue, $vals) . ')';
            } else {
                if (isset($vals['field'])) {
                    if (!empty($clause)) {
                        $clause .= ' ' . $glue . ' ';
                    }
                    $rhs = $this->_convertToDriver($vals['test']);
                    $clause .= Horde_SQL::buildClause($this->_db, $vals['field'], $vals['op'], $rhs);
                } else {
                    foreach ($vals as $test) {
                        if (!empty($test['OR']) || !empty($test['AND'])) {
                            if (!empty($clause)) {
                                $clause .= ' ' . $glue . ' ';
                            }
                            $clause .= '(' . $this->_buildSearchQuery($glue, $test) . ')';
                        } else {
                            if (!empty($clause)) {
                                $clause .= ' ' . $key . ' ';
                            }
                            $rhs = $this->_convertToDriver($test['test']);
                            $clause .= Horde_SQL::buildClause($this->_db, $test['field'], $test['op'], $rhs);
                        }
                    }
                }
            }
        }

        return $clause;
    }

    /**
     * Read the given data from the SQL database and returns the
     * result's fields.
     *
     * @param $criteria      Search criteria.
     * @param $id            Data identifier.
     * @param $fields        List of fields to return.
     *
     * @return               Hash containing the search results.
     */
    function read($criteria, $id, $fields)
    {
        $in = '';
        if (is_array($id)) {
            if (!count($id)) {
                return array();
            }

            foreach ($id as $key) {
                $in .= empty($in) ? $this->_db->quote($this->_convertToDriver($key)) 
                                    : ', ' . $this->_db->quote($this->_convertToDriver($key));
            }
            $where = $criteria . ' IN (' . $in . ')';
        } else {
            $where = $criteria . ' = ' . $this->_db->quote($this->_convertToDriver($id));
        }

        $query  = 'SELECT ' . implode(', ', $fields) . ' ';
        $query .= 'FROM ' . $this->_params['table'] . ' WHERE ' . $where;

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL read by %s: table = %s; query = "%s"',
                                  Auth::getAuth(), $this->_params['table'], $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->getAll($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        $results = array();
        $iMax = count($fields);
        if (!is_a($result, 'PEAR_Error')) {
            foreach ($result as $row) {
                $entry = array();
                for ($i=0; $i < $iMax; $i++) {
                    $field = $fields[$i];
                    $entry[$field] = $this->_convertFromDriver($row[$i]);
                }
                $results[] = $entry;
            }
        }

        return $results;
    }

    /**
     * Adds the specified object to the SQL database.
     */
    function addObject($attributes)
    {
        $fields = array();
        $values = array();
        foreach ($attributes as $field => $value) {
            $fields[] = $field;
            $values[] = $this->_db->quote($this->_convertToDriver($value));
        }

        $query  = 'INSERT INTO ' . $this->_params['table'] . ' (' . implode(', ', $fields) . ')';
        $query .= ' VALUES (' . implode(', ', $values) . ')';

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    /**
     * Deletes the specified object from the SQL database.
     */
    function removeObject($object_key, $object_id)
    {
        $where = $object_key . ' = ' . $this->_db->quote($object_id);
        $query = 'DELETE FROM ' . $this->_params['table'] . ' WHERE ' . $where;

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    /**
     * Saves the specified object in the SQL database.
     *
     * @return string  The object id, possibly updated.
     */
    function setObject($object_key, $object_id, $attributes)
    {
        $where = $object_key . ' = ' . $this->_db->quote($object_id);
        unset($attributes[$object_key]);

        $set = array();
        foreach ($attributes as $field => $value) {
            $set[] = $field . ' = ' . $this->_db->quote($this->_convertToDriver($value));
        }

        $query  = 'UPDATE ' . $this->_params['table'] . ' SET ' . implode(', ', $set) . ' ';
        $query .= 'WHERE ' . $where;

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL setObject by %s: table = %s; query = "%s"',
                                  Auth::getAuth(), $this->_params['table'], $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return is_a($result, 'PEAR_Error') ? $result : $object_id;
    }

    /**
     * Create an object key for a new object.
     *
     * @param array $attributes  The attributes (in driver keys) of the
     *                           object being added.
     *
     * @return string  A unique ID for the new object.
     */
    function makeKey($attributes)
    {
        return md5(uniqid(mt_rand(), true));
    }

    /**
     * Converts a value from the driver's charset to the default charset.
     *
     * @param mixed $value  A value to convert.
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
     * @return mixed        The converted value.
     */
    function _convertToDriver($value) 
    {
        return String::convertCharset($value, NLS::getCharset(), $this->_params['charset']);
    }

}
