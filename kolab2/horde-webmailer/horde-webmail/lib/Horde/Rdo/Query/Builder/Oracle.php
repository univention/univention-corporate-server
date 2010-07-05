<?php
/**
 * Oracle query builder implementation.
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Query_Builder_Oracle extends Horde_Rdo_Query_Builder {

    /**
     * Escape an identifier, such as a table or column name, for safe
     * use in queries.
     *
     * @param string $identifier The identifier to escape.
     */
    public function quoteIdentifier($identifier)
    {
        return '"' . str_replace('"', '""', $identifier) . '"';
    }

    /**
     */
    public function getTables()
    {
        return 'SELECT table_name FROM all_tables';
    }

    /**
     */
    protected function _limit($query, &$sql, &$bindParams)
    {
        if ($query->limit) {

            $sql = 'SELECT q2.* FROM (SELECT rownum r, q1.* FROM (' . $sql . ') q1) q2
                    WHERE r BETWEEN ' . $query->limitOffset . ' AND ' . ($query->limit + $query->limitOffset);
        }
    }

}
