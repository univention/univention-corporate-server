<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Horde_Rdo query building abstract base
 *
 * @category Horde
 * @package Horde_Rdo
 */
abstract class Horde_Rdo_Query_Builder {

    /**
     */
    public function getCount($query)
    {
        return $this->getQuery($query);
    }

    /**
     * Query generator.
     *
     * @param Horde_Rdo_Query $query The query object to turn into SQL.
     *
     * @return array A two-element array of the SQL query and an array
     * of bind parameters.
     */
    public function getQuery($query)
    {
        if ($query instanceof Horde_Rdo_Query_Literal) {
            return array((string)$query, array());
        }

        $bindParams = array();
        $sql = '';

        $this->_select($query, $sql, $bindParams);
        $this->_from($query, $sql, $bindParams);
        $this->_join($query, $sql, $bindParams);
        $this->_where($query, $sql, $bindParams);
        $this->_orderBy($query, $sql, $bindParams);
        $this->_limit($query, $sql, $bindParams);

        return array($sql, $bindParams);
    }

    /**
     * Escape an identifier, such as a table or column name, for safe
     * use in queries.
     *
     * @param string $identifier The identifier to escape.
     */
    abstract public function quoteIdentifier($identifier);

    /**
     * Return the database-specific version of a test.
     *
     * @param string $test The test to "localize"
     */
    public function getTest($test)
    {
        return $test;
    }

    /**
     */
    protected function _select($query, &$sql, &$bindParams)
    {
        $fields = array();
        foreach ($query->fields as $field) {
            $parts = explode('.@', $field, 2);
            if (count($parts) == 1) {
                $fields[] = $field;
            } else {
                $fields[] = str_replace('.@', '.', $field) . ' AS ' . $this->quoteIdentifier($parts[0] . '@' . $parts[1]);
            }
        }

        $sql = 'SELECT ' . implode(', ', $fields);
    }

    /**
     */
    protected function _from($query, &$sql, &$bindParams)
    {
        $sql .= ' FROM ' . $query->mapper->model->table;
    }

    /**
     */
    protected function _join($query, &$sql, &$bindParams)
    {
        foreach ($query->relationships as $relationship) {
            $relsql = array();
            foreach ($relationship['query'] as $key => $value) {
                if ($value instanceof Horde_Rdo_Query_Literal) {
                    $relsql[] = $key . ' = ' . (string)$value;
                } else {
                    $relsql[] = $key . ' = ?';
                    $bindParams[] = $value;
                }
            }

            $sql .= ' ' . $relationship['join_type'] . ' ' . $relationship['table'] . ' ON ' . implode(' AND ', $relsql);
        }
    }

    /**
     */
    protected function _where($query, &$sql, &$bindParams)
    {
        $clauses = array();
        foreach ($query->tests as $test) {
            if (strpos($test['field'], '@') !== false) {
                list($rel, $field) = explode('@', $test['field']);
                if (!isset($query->relationships[$rel])) {
                    continue;
                }
                $clause = $query->relationships[$rel]['table'] . '.' . $field . ' ' . $this->getTest($test['test']);
            } else {
                $clause = $query->mapper->model->table . '.' . $this->quoteIdentifier($test['field']) . ' ' . $this->getTest($test['test']);
            }

            if ($test['value'] instanceof Horde_Rdo_Query_Literal) {
                $clauses[] = $clause . ' ' . (string)$test['value'];
            } else {
                if ($test['test'] == 'IN' && is_array($test['value'])) {
                    $clauses[] = $clause . '(?' . str_repeat(',?', count($test['value']) - 1) . ')';
                    $bindParams = array_merge($bindParams, array_values($test['value']));
                } else {
                    $clauses[] = $clause . ' ?';
                    $bindParams[] = $test['value'];
                }
            }
        }

        if ($clauses) {
            $sql .= ' WHERE ' . implode(' ' . $query->conjunction . ' ', $clauses);
        }
    }

    /**
     */
    protected function _orderBy($query, &$sql, &$bindParams)
    {
        if ($query->sortby) {
            $sql .= ' ORDER BY';
            foreach ($query->sortby as $sort) {
                list($field, $direction) = $sort;
                if (strpos($field, '@') !== false) {
                    list($rel, $field) = explode('@', $field);
                    if (!isset($query->relationships[$rel])) {
                        continue;
                    }
                    $sql .= ' ' . $query->relationships[$rel]['table'] . '.' . $field . ' ' . $direction . ',';
                } else {
                    $sql .= ' ' . $field . ' ' . $direction . ',';
                }
            }

            $sql = substr($sql, 0, -1);
        }
    }

    /**
     */
    protected function _limit($query, &$sql, &$bindParams)
    {
        if ($query->limit) {
            $sql .= ' LIMIT ' . $query->limit;
            if (!is_null($query->limitOffset)) {
                $sql .= ' OFFSET ' . $query->limitOffset;
            }
        }
    }

}
