<?php
/**
 * MySQL query builder implementation
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Query_Builder_Mysql extends Horde_Rdo_Query_Builder {

    /**
     * Escape an identifier, such as a table or column name, for safe
     * use in queries.
     *
     * @param string $identifier The identifier to escape.
     */
    public function quoteIdentifier($identifier)
    {
        return '`' . str_replace('`', '``', $identifier) . '`';
    }

    /**
     */
    public function getTables()
    {
        return 'SHOW TABLES';
    }

    /**
     */
    protected function _limit($query, &$sql, &$bindParams)
    {
        if ($query->limit) {
            $offset = !is_null($query->limitOffset) ? $query->limitOffset : 0;
            $sql .= ' LIMIT ' . $offset . ', ' . $query->limit;
        }
    }

}
