<?php
/**
 * This is a utility class, every method is static.
 *
 * $Horde: framework/SQL/SQL.php,v 1.27 2004/02/24 17:14:08 mdjukic Exp $
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
class Horde_SQL {

    /**
     * Return a boolean expression using the specified operator. Uses
     * database-specific casting, if necessary.
     *
     * @access public
     *
     * @param object $dbh  The PEAR::DB database object.
     * @param string $lhs  The column or expression to test.
     * @param string $op   The operator.
     * @param string $rhs  The comparison value.
     *
     * @returns string  The SQL test fragment.
     */
    function buildClause($dbh, $lhs, $op, $rhs)
    {
        switch ($op) {
        case '|':
        case '&':
            switch ($dbh->phptype) {
            case 'pgsql':
                // Only PgSQL 7.3+ understands SQL99 'SIMILAR TO'; use
                // ~ for greater backwards compatibility.
                return sprintf('CASE WHEN CAST(%s AS VARCHAR) ~ \'^-?[0-9]+$\' THEN (CAST(%s AS INTEGER) %s %d) <> 0 ELSE FALSE END', $lhs, $lhs, $op, (int)$rhs);

            case 'oci8':
                // Oracle uses & for variables. We need to use the
                // bitand function that is available, but may be
                // unsupported.
                return sprintf('bitand(%s,%d) = %d', $lhs, (int)$rhs, (int)$rhs);

            case 'odbc': 
                // ODBC must have a valid boolean expression 
                return sprintf('(%s & %d) = %d', $lhs, (int)$rhs, (int)$rhs); 

            default:
                return sprintf('%s %s %d', $lhs, $op, (int)$rhs);
            }

        case '~':
            if ($dbh->phptype == 'mysql') {
                $op = 'REGEXP';
            }
            return sprintf('%s %s %s', $lhs, $op, $rhs);

        case 'IN':
            return sprintf('%s IN %s', $lhs, $rhs);

        case 'LIKE':
            if ($dbh->phptype == 'pgsql') {
                $clause = '%s ILIKE %s';
            } else {
                $clause = '%s LIKE LOWER(%s)';
            }
            return sprintf($clause, $lhs, $dbh->quote('%' . $rhs . '%'));

        default:
            return sprintf('%s %s %s', $lhs, $op, $dbh->quote($rhs));
        }
    }

    function readBlob($dbh, $table, $field, $criteria)
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
            case 'pgsql':
                $result = pack('H' . strlen($result), $result);
                break;
            }
        }

        return $result;
    }

    function insertBlob($dbh, $table, $field, $data, $attributes)
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
        $stmt = $this->_db->prepare($query);
        return $this->_db->execute($stmt, $values);
    }

    function updateBlob($dbh, $table, $field, $data, $where, $alsoupdate)
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
                                  sprintf('SELECT %s FROM %s FOR UPDATE WHERE %s',
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
        $stmt = $dbh->prepare($query);
        return $dbh->execute($stmt, $values);
    }

}
