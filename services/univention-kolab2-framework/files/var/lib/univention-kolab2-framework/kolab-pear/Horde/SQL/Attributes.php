<?php
/**
 * This class provides attributes methods for any existing SQL class.
 *
 * $Horde: framework/SQL/SQL/Attributes.php,v 1.14 2004/04/07 14:43:12 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_SQL
 */
class Horde_SQL_Attributes {

    /**
     * The PEAR::DB object to run queries with.
     * @var object DB $_db
     */
    var $_db;

    /**
     * Parameters to use when generating queries:
     *   id_column       - The primary id column to use in joins.
     *   primary_table   - The main table name.
     *   attribute_table - The table that the attributes are stored in.
     * @var array $_params
     */
    var $_params = array();

    /**
     * The number of copies of the attributes table that we need to
     * join on in the current query.
     * @var integer $_table_count
     */
    var $_table_count = 1;

    /**
     * Constructor.
     *
     * @param object DB $dbh     A PEAR::DB object.
     * @param array     $params  The id column, table names, etc.
     */
    function Horde_SQL_Attributes($dbh, $params)
    {
        $this->_db = $dbh;
        $this->_params = $params;
    }

    /**
     * Returns all attributes for a given id or multiple ids.
     *
     * @param integer | array $id  The id to fetch or an array of ids.
     *
     * @return array  A hash of attributes, or a multi-level hash
     *                of ids => their attributes.
     */
    function getAttributes($id)
    {
        if (is_array($id)) {
            $query = sprintf('SELECT %1$s, attribute_name as name, attribute_key as "key", attribute_value as value FROM %2$s WHERE %1$s IN (%3$s)',
                             $this->_params['id_column'],
                             $this->_params['attribute_table'],
                             implode(', ', $id));

            Horde::logMessage('SQL Query by Horde_SQL_Attributes::getAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $rows = $this->_db->getAll($query, DB_FETCHMODE_ASSOC);
            if (is_a($rows, 'PEAR_Error')) {
                return $rows;
            }

            $id_column = $this->_params['id_column'];
            $data = array();
            foreach ($rows as $row) {
                if (empty($data[$row[$id_column]])) {
                    $data[$row[$id_column]] = array();
                }
                $data[$row[$id_column]][] = array('name'  => $row['name'],
                                               'key'   => $row['key'],
                                               'value' => $row['value']);
            }
            return $data;
        } else {
            $query = sprintf('SELECT %1$s, attribute_name as name, attribute_key as "key", attribute_value as value FROM %2$s WHERE %1$s = %3$s',
                             $this->_params['id_column'],
                             $this->_params['attribute_table'],
                             (int)$id);
            Horde::logMessage('SQL Query by Horde_SQL_Attributes::getAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return $this->_db->getAll($query, DB_FETCHMODE_ASSOC);
        }
    }

    /**
     * Return a set of ids based on a set of attribute criteria.
     *
     * @param array $criteria  The array of criteria. Example:
     *                         $criteria['OR'] = array(
     *                                      array('field' => 'name',
     *                                            'op'    => '=',
     *                                            'test'  => 'foo'),
     *                                      array('field' => 'name',
     *                                            'op'    => '=',
     *                                            'test'  => 'bar'));
     *                          This would return all ids for which the field
     *                          attribute_name is either 'foo' or 'bar'.
     */
    function getByAttributes($criteria)
    {
        if (!count($criteria)) {
            return array();
        }

        /* Build the query. */
        $this->_table_count = 1;
        $query = '';
        foreach ($criteria as $key => $vals) {
            if ($key == 'OR' || $key == 'AND') {
                if (!empty($query)) {
                    $query .= ' ' . $key . ' ';
                }
                $query .= '(' . $this->_buildAttributeQuery($key, $vals) . ')';
            }
        }

        /* Build the FROM/JOIN clauses. */
        $joins = array();
        $pairs = array();
        for ($i = 1; $i <= $this->_table_count; $i++) {
            $joins[] = sprintf('LEFT JOIN %1$s a%2$s ON a%2$s.%3$s = m.%3$s',
                               $this->_params['attribute_table'],
                               $i,
                               $this->_params['id_column']);

            $pairs[] = 'AND a1.attribute_name = a' . $i . '.attribute_name';
        }
        $joins = implode(' ', $joins);
        $pairs = implode(' ', $pairs);

        $query = sprintf('SELECT DISTINCT a1.%s FROM %s m %s WHERE %s %s',
                         $this->_params['id_column'],
                         $this->_params['primary_table'],
                         $joins,
                         $query,
                         $pairs);

        Horde::logMessage('SQL Query by Horde_SQL_Attributes::getByAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $this->_db->getCol($query);
    }

    /**
     * Given a new attribute set and an id, insert each into the
     * DB. If anything fails in here, rollback the transaction, return
     * the relevant error and bail out.
     *
     * @params int $id            The id of the record for which attributes
     *                            are being inserted.
     * @params array $attributes  An hash containing the attributes.
     */
    function insertAttributes($id, $attributes)
    {
        foreach ($attributes as $attr) {
            $query = sprintf('INSERT INTO %s (%s, attribute_name, attribute_key, attribute_value) VALUES (%s, %s, %s, %s)',
                             $this->_params['attribute_table'],
                             $this->_params['id_column'],
                             (int)$id,
                             $this->_db->quote($attr['name']),
                             $this->_db->quote($attr['key']),
                             $this->_db->quote($attr['value']));

            Horde::logMessage('SQL Query by Horde_SQL_Attributes::insertAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                $this->_db->rollback();
                $this->_db->autoCommit(true);
                return $result;
            }
        }

        /* Commit the transaction, and turn autocommit back on. */
        $result = $this->_db->commit();
        $this->_db->autoCommit(true);
    }

    /**
     * Given an id, delete all attributes for that id from the
     * attributes table.
     *
     * @params int $id  The id of the record for which attributes are being
     *                  deleted.
     */
    function deleteAttributes($id)
    {
        /* Delete attributes. */
        $query = sprintf('DELETE FROM %s WHERE %s = %s',
                         $this->_params['attribute_table'],
                         $this->_params['id_column'],
                         (int)$id);

        Horde::logMessage('SQL Query by Horde_SQL_Attributes::deleteAttributes(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Given an id, update all attributes for that id in the
     * attributes table with the new attributes.
     *
     * @params int $id            The id of the record for which attributes
     *                            are being deleted.
     * @params array $attributes  An hash containing the attributes.
     */
    function updateAttributes($id, $attributes)
    {
        /* Delete the old attributes. */
        $result = $this->deleteAttributes($id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Insert the new attribute set. */
        $result = $this->insertAttributes($id, $attributes);
        return $result;
    }

    /**
     * Build a piece of an attribute query.
     *
     * @param string $glue      The glue to join the criteria (OR/AND).
     * @param array  $criteria  The array of criteria.
     * @param bool $join        Should we join on a clean attributes table?
     *                          Defaults to false.
     *
     * @return string  An SQL fragment.
     */
    function _buildAttributeQuery($glue, $criteria, $join = false)
    {
        require_once 'Horde/SQL.php';

        /* Initialize the clause that we're building. */
        $clause = '';

        /* Get the table alias to use for this set of criteria. */
        if ($join) {
            $alias = $this->_getAlias(true);
        } else {
            $alias = $this->_getAlias();
        }

        foreach ($criteria as $key => $vals) {
            if (!empty($vals['OR']) || !empty($vals['AND'])) {
                if (!empty($clause)) {
                    $clause .= ' ' . $glue . ' ';
                }
                $clause .= '(' . $this->_buildAttributeQuery($glue, $vals) . ')';
            } elseif (!empty($vals['JOIN'])) {
                if (!empty($clause)) {
                    $clause .= ' ' . $glue . ' ';
                }
                $clause .= $this->_buildAttributeQuery($glue, $vals['JOIN'], true);
            } else {
                if (isset($vals['field'])) {
                    if (!empty($clause)) {
                        $clause .= ' ' . $glue . ' ';
                    }
                    $clause .= Horde_SQL::buildClause($this->_db, $alias . '.attribute_' . $vals['field'], $vals['op'], $vals['test']);
                } else {
                    foreach ($vals as $test) {
                        if (!empty($clause)) {
                            $clause .= ' ' . $key . ' ';
                        }
                        $clause .= Horde_SQL::buildClause($this->_db, $alias . '.attribute_' . $test['field'], $test['op'], $test['test']);
                    }
                }
            }
        }

        return $clause;
    }

    /**
     * Get an alias to an attributes table, incrementing it if
     * necessary.
     *
     * @param optional bool $increment  Increment the alias count? Defaults to
     *                                  false.
     */
    function _getAlias($increment = false)
    {
        static $seen  = array();

        if ($increment && !empty($seen[$this->_table_count])) {
            $this->_table_count++;
        }

        $seen[$this->_table_count] = true;
        return 'a' . $this->_table_count;
    }

    /**
     * Attempts to return a reference to a concrete SQL Attributes
     * instance based on parameters passed. It will only create a new
     * instance if no Attributes instance with the same parameters
     * currently exists.
     *
     * This should be used if multiple SQL attribute tables are
     * required.
     *
     * This method must be invoked as: $var =
     * &Horde_SQL_Attributes::singleton()
     *
     * @param object $dbh    An object pointing to a SQL database handle.
     *
     * @param array $params  Parameters for the attributes table, consisting
     *                       of the following keys:
     *                       'primary_table'   - the main SQL table
     *                       'attribute_table' - the second table containing
     *                                           the attributes to the main
     *                                           table.
     *                       'id_column'       - the name of the column with
     *                                           the ID or key field.
     */
    function &singleton($dbh, $params)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize($params);
        if (!isset($instances[$signature])) {
            $instances[$signature] = &new Horde_SQL_Attributes($dbh, $params);
        }

        return $instances[$signature];
    }

}
