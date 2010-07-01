<?php
/**
 * This is a utility class, every method is static.
 *
 * $Horde: framework/SQL/SQL.php,v 1.30.2.22 2009-09-25 07:55:38 selsky Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 2.2
 * @package Horde_SQL
 */
class Horde_SQL {

    /**
     * Returns a boolean expression using the specified operator. Uses
     * database-specific casting, if necessary.
     *
     * @param DB $dbh        The PEAR::DB database object.
     * @param string $lhs    The column or expression to test.
     * @param string $op     The operator.
     * @param string $rhs    The comparison value.
     * @param boolean $bind  If true, the method returns the query and a list
     *                       of values suitable for binding as an array.
     * @param array $params  Any additional parameters for the operator. @since
     *                       Horde 3.2
     *
     * @return mixed  The SQL test fragment, or an array containing the query
     *                and a list of values if $bind is true.
     */
    function buildClause(&$dbh, $lhs, $op, $rhs, $bind = false, $params = array())
    {
        switch ($op) {
        case '|':
        case '&':
            switch ($dbh->phptype) {
            case 'pgsql':
                // Only PgSQL 7.3+ understands SQL99 'SIMILAR TO'; use
                // ~ for greater backwards compatibility.
                $query = 'CASE WHEN CAST(%s AS VARCHAR) ~ \'^-?[0-9]+$\' THEN (CAST(%s AS INTEGER) %s %s) <> 0 ELSE FALSE END';
                if ($bind) {
                    return array(sprintf(Horde_SQL::escapePrepare($query),
                                         Horde_SQL::escapePrepare($lhs),
                                         Horde_SQL::escapePrepare($lhs),
                                         Horde_SQL::escapePrepare($op),
                                         '?'),
                                 array((int)$rhs));
                } else {
                    return sprintf($query, $lhs, $lhs, $op, (int)$rhs);
                }

            case 'oci8':
                // Oracle uses & for variables. We need to use the bitand
                // function that is available, but may be unsupported.
                $query = 'bitand(%s, %s) = %s';
                if ($bind) {
                    return array(sprintf(Horde_SQL::escapePrepare($query),
                                         Horde_SQL::escapePrepare($lhs), '?', '?'),
                                 array((int)$rhs, (int)$rhs));
                } else {
                    return sprintf($query, $lhs, (int)$rhs, (int)$rhs);
                }

            case 'mssql':
                // MSSQL must have a valid boolean expression
                $query = '(CASE WHEN ISNUMERIC(%s) = 1 THEN (%s & %s) ELSE %s END) = %s';
                if ($bind) {
                    return array(sprintf(Horde_SQL::escapePrepare($query),
                                         Horde_SQL::escapePrepare($lhs),
                                         Horde_SQL::escapePrepare($lhs), '?', '?', '?'),
                                 array((int)$rhs, (int)$rhs - 1, (int)$rhs));
                } else {
                    return sprintf($query, $lhs, $lhs, (int)$rhs, (int)$rhs - 1, (int)$rhs);
                }

            case 'odbc':
                // ODBC must have a valid boolean expression
                $query = '(%s & %s) = %s';
                if ($bind) {
                    return array(sprintf(Horde_SQL::escapePrepare($query),
                                         Horde_SQL::escapePrepare($lhs), '?', '?'),
                                 array((int)$rhs, (int)$rhs));
                } else {
                    return sprintf($query, $lhs, (int)$rhs, (int)$rhs);
                }

            default:
                if ($bind) {
                    return array($lhs . ' ' . Horde_SQL::escapePrepare($op) . ' ?',
                                 array((int)$rhs));
                } else {
                    return $lhs . ' ' . $op . ' ' . (int)$rhs;
                }
            }

        case '~':
            if ($dbh->phptype == 'mysql') {
                $op = 'REGEXP';
            }
            if ($bind) {
                return array($lhs . ' ' . $op . ' ?', array($rhs));
            } else {
                return $lhs . ' ' . $op . ' ' . $rhs;
            }

        case 'IN':
            if ($bind) {
                if (is_array($rhs)) {
                    return array($lhs . ' IN (?' . str_repeat(', ?', count($rhs) - 1) . ')', $rhs);
                } else {
                    // We need to bind each member of the IN clause
                    // separately to ensure proper quoting.
                    if (substr($rhs, 0, 1) == '(') {
                        $rhs = substr($rhs, 1);
                    }
                    if (substr($rhs, -1) == ')') {
                        $rhs = substr($rhs, 0, -1);
                    }

                    $ids = preg_split('/\s*,\s*/', $rhs);

                    return array($lhs . ' IN (?' . str_repeat(', ?', count($ids) - 1) . ')', $ids);
                }
            } else {
                if (is_array($rhs)) {
                    return $lhs . ' IN ' . implode(', ', $rhs);
                } else {
                    return $lhs . ' IN ' . $rhs;
                }
            }

        case 'LIKE':
            if ($dbh->phptype == 'pgsql') {
                $query = '%s ILIKE %s';
            } else {
                $query = 'LOWER(%s) LIKE LOWER(%s)';
            }
            if ($bind) {
                if (empty($params['begin'])) {
                    return array(sprintf($query,
                                         Horde_SQL::escapePrepare($lhs),
                                         '?'),
                                 array('%' . $rhs . '%'));
                } else {
                    return array(sprintf('(' . $query . ' OR ' . $query . ')',
                                         Horde_SQL::escapePrepare($lhs),
                                         '?',
                                         Horde_SQL::escapePrepare($lhs),
                                         '?'),
                                 array($rhs . '%', '% ' . $rhs . '%'));
                }
            } else {
                if (empty($params['begin'])) {
                    return sprintf($query,
                                   $lhs,
                                   $dbh->quote('%' . $rhs . '%'));
                } else {
                    return sprintf('(' . $query . ' OR ' . $query . ')',
                                   $lhs,
                                   $dbh->quote($rhs . '%'),
                                   $lhs,
                                   $dbh->quote('% ' . $rhs . '%'));
                }
            }

        default:
            if ($bind) {
                return array($lhs . ' ' . Horde_SQL::escapePrepare($op) . ' ?', array($rhs));
            } else {
                return $lhs . ' ' . $op . ' ' . $dbh->quote($rhs);
            }
        }
    }

    /**
     * Escapes all characters in a string that are placeholders for the
     * prepare/execute methods of the DB package.
     *
     * @param string $query  A string to escape.
     *
     * @return string  The correctly escaped string.
     */
    function escapePrepare($query)
    {
        return preg_replace('/[?!&]/', '\\\\$0', $query);
    }

    function readBlob(&$dbh, $table, $field, $criteria)
    {
        if (!count($criteria)) {
            return PEAR::raiseError('You must specify the fetch criteria');
        }

        $where = '';

        switch ($dbh->dbsyntax) {
        case 'oci8':
            foreach ($criteria as $key => $value) {
                if (!empty($where)) {
                    $where .= ' AND ';
                }
                if (empty($value)) {
                    $where .= $key . ' IS NULL';
                } else {
                    $where .= $key . ' = ' . $dbh->quote($value);
                }
            }

            $statement = OCIParse($dbh->connection,
                                  sprintf('SELECT %s FROM %s WHERE %s',
                                          $field, $table, $where));
            OCIExecute($statement);
            if (OCIFetchInto($statement, $lob)) {
                $result = $lob[0]->load();
            } else {
                $result = PEAR::raiseError('Unable to load SQL Data');
            }
            OCIFreeStatement($statement);
            break;

        default:
            foreach ($criteria as $key => $value) {
                if (!empty($where)) {
                    $where .= ' AND ';
                }
                $where .= $key . ' = ' . $dbh->quote($value);
            }
            $result = $dbh->getOne(sprintf('SELECT %s FROM %s WHERE %s',
                                           $field, $table, $where));

            switch ($dbh->dbsyntax) {
            case 'mssql':
            case 'pgsql':
                $result = pack('H' . strlen($result), $result);
                break;
            }
        }

        return $result;
    }

    function insertBlob(&$dbh, $table, $field, $data, $attributes)
    {
        $fields = array();
        $values = array();

        switch ($dbh->dbsyntax) {
        case 'oci8':
            foreach ($attributes as $key => $value) {
                $fields[] = $key;
                $values[] = $dbh->quote($value);
            }

            $statement = OCIParse($dbh->connection,
                                  sprintf('INSERT INTO %s (%s, %s)' .
                                          ' VALUES (%s, EMPTY_BLOB()) RETURNING %s INTO :blob',
                                          $table,
                                          implode(', ', $fields),
                                          $field,
                                          implode(', ', $values),
                                          $field));

            $lob = OCINewDescriptor($dbh->connection);
            OCIBindByName($statement, ':blob', $lob, -1, SQLT_BLOB);
            OCIExecute($statement, OCI_DEFAULT);
            $lob->save($data);
            $result = OCICommit($dbh->connection);
            $lob->free();
            OCIFreeStatement($statement);
            return $result ? true : PEAR::raiseError('Unknown Error');

        default:
            foreach ($attributes as $key => $value) {
                $fields[] = $key;
                $values[] = $value;
            }

            $query = sprintf('INSERT INTO %s (%s, %s) VALUES (%s)',
                             $table,
                             implode(', ', $fields),
                             $field,
                             '?' . str_repeat(', ?', count($values)));
            break;
        }

        switch ($dbh->dbsyntax) {
        case 'mssql':
        case 'pgsql':
            $values[] = bin2hex($data);
            break;

        default:
            $values[] = $data;
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by Horde_SQL::insertBlob(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        return $this->_db->query($query, $values);
    }

    function updateBlob(&$dbh, $table, $field, $data, $where, $alsoupdate)
    {
        $fields = array();
        $values = array();

        switch ($dbh->dbsyntax) {
        case 'oci8':
            $wherestring = '';
            foreach ($where as $key => $value) {
                if (!empty($wherestring)) {
                    $wherestring .= ' AND ';
                }
                $wherestring .= $key . ' = ' . $dbh->quote($value);
            }

            $statement = OCIParse($dbh->connection,
                                  sprintf('SELECT %s FROM %s WHERE %s FOR UPDATE',
                                          $field,
                                          $table,
                                          $wherestring));

            OCIExecute($statement, OCI_DEFAULT);
            OCIFetchInto($statement, $lob);
            $lob[0]->save($data);
            $result = OCICommit($dbh->connection);
            $lob[0]->free();
            OCIFreeStatement($statement);
            return $result ? true : PEAR::raiseError('Unknown Error');

        default:
            $updatestring = '';
            $values = array();
            foreach ($alsoupdate as $key => $value) {
                $updatestring .= $key . ' = ?, ';
                $values[] = $value;
            }
            $updatestring .= $field . ' = ?';
            switch ($dbh->dbsyntax) {
            case 'mssql':
            case 'pgsql':
                $values[] = bin2hex($data);
                break;

            default:
                $values[] = $data;
            }

            $wherestring = '';
            foreach ($where as $key => $value) {
                if (!empty($wherestring)) {
                    $wherestring .= ' AND ';
                }
                $wherestring .= $key . ' = ?';
                $values[] = $value;
            }

            $query = sprintf('UPDATE %s SET %s WHERE %s',
                             $table,
                             $updatestring,
                             $wherestring);
            break;
        }

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('SQL Query by Horde_SQL::updateBlob(): query = "%s"', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        return $dbh->query($query, $values);
    }

    /**
     * Build an SQL SET clause.
     *
     * This function takes an array in the form column => value and returns
     * an SQL SET clause (without the SET keyword) with the values properly
     * quoted.  For example, the following:
     *
     *      array('foo' => 1,
     *            'bar' => 'hello')
     *
     * would result in the fragment:
     *
     *      foo = 1, bar = 'hello'
     *
     * @param DB $dbh        The PEAR::DB database object.
     * @param array $values  The array of column => value pairs.
     *
     * @return string  The SQL SET fragment.
     */
    function updateValues(&$dbh, $values)
    {
        $ret = array();
        foreach ($values as $key => $value) {
            $ret[] = $key . ' = ' . ($value === null ? 'NULL' : $dbh->quote($value));
        }
        return implode(', ', $ret);
    }

    /**
     * Build an SQL INSERT/VALUES clause.
     *
     * This function takes an array in the form column => value and returns
     * an SQL fragment specifying the column names and insert values, with
     * the values properly quoted.  For example, the following:
     *
     *      array('foo' => 1,
     *            'bar' => 'hello')
     *
     * would result in the fragment:
     *
     *      ( foo, bar ) VALUES ( 1, 'hello' )
     *
     * @param DB $dbh        The PEAR::DB database object.
     * @param array $values  The array of column => value pairs.
     *
     * @return string  The SQL fragment.
     */
    function insertValues(&$dbh, $values)
    {
        $columns = array();
        $vals = array();
        foreach ($values as $key => $value) {
            $columns[] = $key;
            $vals[] = $value === null ? 'NULL' : $dbh->quote($value);
        }
        return '( ' . implode(', ', $columns) . ' ) VALUES ( ' . implode(', ', $vals) . ' )';
    }

}
