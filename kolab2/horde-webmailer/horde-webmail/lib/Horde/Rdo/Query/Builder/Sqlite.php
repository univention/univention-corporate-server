<?php
/**
 * SQLite query builder implementation
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Query_Builder_Sqlite extends Horde_Rdo_Query_Builder {

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
        return "SELECT name FROM sqlite_master WHERE type='table' " .
            "UNION ALL SELECT name FROM sqlite_temp_master " .
            "WHERE type='table' ORDER BY name";
    }

}
