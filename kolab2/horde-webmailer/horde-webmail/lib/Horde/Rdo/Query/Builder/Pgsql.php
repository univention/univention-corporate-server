<?php
/**
 * PostgreSQL query builder implementation.
 *
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Query_Builder_Pgsql extends Horde_Rdo_Query_Builder {

    /**
     * Return the database-specific version of a test.
     *
     * @param string $test The test to "localize"
     */
    public function getTest($test)
    {
        if (strtolower($test) == 'like') {
            return 'ILIKE';
        }

        return $test;
    }

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
        return "SELECT c.relname AS table_name " .
            "FROM pg_class c, pg_user u " .
            "WHERE c.relowner = u.usesysid AND c.relkind = 'r' " .
            "AND NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = c.relname) " .
            "AND c.relname !~ '^(pg_|sql_)' " .
            "UNION " .
            "SELECT c.relname AS table_name " .
            "FROM pg_class c " .
            "WHERE c.relkind = 'r' " .
            "AND NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = c.relname) " .
            "AND NOT EXISTS (SELECT 1 FROM pg_user WHERE usesysid = c.relowner) " .
            "AND c.relname !~ '^pg_'";
    }

}
