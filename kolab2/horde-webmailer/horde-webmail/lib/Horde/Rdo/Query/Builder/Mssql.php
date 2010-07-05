<?php
/**
 * MS-SQL query builder implementation
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Query_Builder_Mssql extends Horde_Rdo_Query_Builder {

    /**
     * Escape an identifier, such as a table or column name, for safe
     * use in queries.
     *
     * @param string $identifier The identifier to escape.
     */
    public function quoteIdentifier($identifier)
    {
        return '[' . str_replace(']', ']]', $identifier) . ']';
    }

    /**
     */
    public function getTables()
    {
        return 'SELECT name FROM sysobjects WHERE type = \'U\' ORDER BY name';
    }

    /**
     */
    protected function _limit($query, &$sql, &$bindParams)
    {
        if ($query->limit) {
            $orderby = stristr($sql, 'ORDER BY');
            if ($orderby !== false) {
                $sort = (stripos($orderby, 'DESC') !== false) ? 'DESC' : 'ASC';
                $order = str_ireplace('ORDER BY', '', $orderby);
                $order = trim(preg_replace('/ASC|DESC/i', '', $order));
            }

            $sql = preg_replace('/^SELECT /i', 'SELECT TOP ' . ($query->limit + $query->limitOffset) . ' ', $sql);

            $sql = 'SELECT * FROM (SELECT TOP ' . $query->limit . ' * FROM (' . $sql . ') AS inner_tbl';
            if ($orderby !== false) {
                $sql .= ' ORDER BY ' . $order . ' ';
                $sql .= (stripos($sort, 'ASC') !== false) ? 'DESC' : 'ASC';
            }
            $sql .= ') AS outer_tbl';
            if ($orderby !== false) {
                $sql .= ' ORDER BY ' . $order . ' ' . $sort;
            }
        }
    }

}
