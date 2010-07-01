<?php
/**
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Db
 */

/** MDB2_Schema */
require_once 'MDB2/Schema.php';

/**
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 * @category Horde
 * @package  Horde_Db
 */
class Horde_SQL_Manager
{
    /**
     * Database manager for write operations
     * @var MDB2_Schema
     */
    var $_writer;

    /**
     * Database manager for read operations
     * @var MDB2_Schema
     */
    var $_reader;

    /**
     * Create a new schema manager.
     *
     * @param array $dsn  Overrides global Horde SQL config.
     */
    function getInstance($dsn = array())
    {
        // Merge local options with Horde database config.
        if (isset($GLOBALS['conf']['sql'])) {
            $dsn = array_merge($GLOBALS['conf']['sql'], $dsn);
        }
        unset($dsn['charset']);
        $options = array('seqcol_name' => 'id',
                         'portability' => MDB2_PORTABILITY_ALL & ~MDB2_PORTABILITY_FIX_CASE,
                         'force_defaults' => false);

        $writer = MDB2_Schema::factory($dsn, $options);
        if (is_a($writer, 'PEAR_Error')) {
            return $writer;
        }

        // Check if we need to set up the read DB connection seperately.
        $reader = null;
        if (!empty($dsn['splitread'])) {
            $read_dsn = array_merge($dsn, $dsn['read']);
            unset($read_dsn['charset']);

            $reader = MDB2_Schema::factory($read_dsn, $options);
            if (is_a($reader, 'PEAR_Error')) {
                return $reader;
            }
        }

        return new Horde_SQL_Manager($writer, $reader);
    }

    /**
     * Constructor
     *
     * @param MDB2_Schema $writer DB manager for the write database.
     * @param MDB2_Schema $reader DB manager for the read database (defaults to using $writer).
     */
    function Horde_SQL_Manager($writer, $reader = null)
    {
        $this->_writer = $writer;
        if ($reader !== null) {
            $this->_reader = $reader;
        } else {
            $this->_reader = $writer;
        }
    }

    /**
     * Dump XML schema info for $tables
     *
     * @param array $tables Tables to get XML for
     *
     * @return string XML schema
     */
    function dumpSchema($tables = array())
    {
        $defs = $this->getTableDefinitions($tables);
        if (is_a($defs, 'PEAR_Error')) {
            return $defs;
        }

        // Make the database name a variable
        $defs['name'] = '<variable>name</variable>';

        $args = array(
            'output_mode' => 'function',
            'output' => array(&$this, '_collectXml'),
        );
        $this->_xml = '';
        $this->_reader->dumpDatabase($defs, $args, MDB2_SCHEMA_DUMP_STRUCTURE);
        $xml = $this->_xml;
        $this->_xml = '';
        return $xml;
    }

    /**
     * Update the database using an XML schema file
     *
     * @param string $schema_file  The local filename of a .xml schema file.
     * @param boolean $debug       Whether to return the SQL statements instead
     *                             doing the upgrade.
     *
     * @return
     */
    function updateSchema($schema_file, $debug = false)
    {
        if (!file_exists($schema_file) || !is_readable($schema_file)) {
            return PEAR::raiseError('Unable to read ' . $schema_file);
        }

        $existing = $this->getTableDefinitions();
        if (is_a($existing, 'PEAR_Error')) {
            return $exiting;
        }

        if ($debug) {
            $this->_writer->db->setOption('debug', true);
            $this->_writer->db->setOption('debug_handler', 'MDB2_defaultDebugOutput');
        }

        $result = $this->_writer->updateDatabase(
            $schema_file,
            $existing,
            array('name' => $this->_writer->db->database_name,
                  'create' => false),
            $debug);

        return $debug ? $this->_writer->db->getDebugOutput() : $result;
    }

    /**
     * Scheme dumping callback for MDB2_Schema_Writer
     * @deprecated
     */
    function _collectXml($xml)
    {
        $this->_xml .= $xml;
    }

    /**
     * Wraps MDB2_Schema code to avoid overly strict validation and to
     * allow dumping a selective table list.
     *
     * @param array $tables Tables to get definitions for. If empty, all tables are dumped.
     */
    function getTableDefinitions($tables = array())
    {
        if (!count($tables)) {
            $tables = $this->_reader->db->manager->listTables();
            if (PEAR::isError($tables)) {
                return $tables;
            }
        }

        $database_definition = array(
            'name' => '',
            'create' => false,
            'overwrite' => false,
            'charset' => '',
            'description' => '',
            'comments' => '',
            'tables' => array(),
            'sequences' => array(),
        );

        foreach ($tables as $table_name) {
            $fields = $this->_reader->db->manager->listTableFields($table_name);
            if (PEAR::isError($fields)) {
                return $fields;
            }

            $database_definition['tables'][$table_name] = array(
                'was' => '',
                'description' => '',
                'comments' => '',
                'fields' => array(),
                'indexes' => array(),
                'constraints' => array(),
                'initialization' => array()
            );

            $table_definition =& $database_definition['tables'][$table_name];
            foreach ($fields as $field_name) {
                $definition = $this->_reader->db->reverse->getTableFieldDefinition($table_name, $field_name);
                if (PEAR::isError($definition)) {
                    return $definition;
                }

                if (!empty($definition[0]['autoincrement'])) {
                    $definition[0]['default'] = '0';
                }
                $table_definition['fields'][$field_name] = $definition[0];
                $field_choices = count($definition);
                if ($field_choices > 1) {
                    $warning = "There are $field_choices type choices in the table $table_name field $field_name (#1 is the default): ";
                    $field_choice_cnt = 1;
                    $table_definition['fields'][$field_name]['choices'] = array();
                    foreach ($definition as $field_choice) {
                        $table_definition['fields'][$field_name]['choices'][] = $field_choice;
                        $warning.= 'choice #'.($field_choice_cnt).': '.serialize($field_choice);
                        $field_choice_cnt++;
                    }
                    $this->_reader->warnings[] = $warning;
                }
            }

            $keys = array();
            $indexes = $this->_reader->db->manager->listTableIndexes($table_name);
            if (PEAR::isError($indexes)) {
                return $indexes;
            }

            if (is_array($indexes)) {
                foreach ($indexes as $index_name) {
                    $this->_reader->db->expectError(MDB2_ERROR_NOT_FOUND);
                    $definition = $this->_reader->db->reverse->getTableIndexDefinition($table_name, $index_name);
                    $this->_reader->db->popExpect();
                    if (PEAR::isError($definition)) {
                        if (PEAR::isError($definition, MDB2_ERROR_NOT_FOUND)) {
                            continue;
                        }
                        return $definition;
                    }

                    $keys[$index_name] = $definition;
                }
            }

            $constraints = $this->_reader->db->manager->listTableConstraints($table_name);
            if (PEAR::isError($constraints)) {
                return $constraints;
            }

            if (is_array($constraints)) {
                foreach ($constraints as $constraint_name) {
                    $this->_reader->db->expectError(MDB2_ERROR_NOT_FOUND);
                    $definition = $this->_reader->db->reverse->getTableConstraintDefinition($table_name, $constraint_name);
                    $this->_reader->db->popExpect();
                    if (PEAR::isError($definition)) {
                        if (PEAR::isError($definition, MDB2_ERROR_NOT_FOUND)) {
                            continue;
                        }
                        return $definition;
                    }

                    $keys[$constraint_name] = $definition;
                }
            }

            foreach ($keys as $key_name => $definition) {
                if (array_key_exists('foreign', $definition) && $definition['foreign']) {
                    foreach ($definition['fields'] as $field_name => $field) {
                        $definition['fields'][$field_name] = '';
                    }

                    foreach ($definition['references']['fields'] as $field_name => $field) {
                        $definition['references']['fields'][$field_name] = '';
                    }

                    $table_definition['constraints'][$key_name] = $definition;
                } else {
                    foreach ($definition['fields'] as $field_name => $field) {
                        $definition['fields'][$field_name] = $field;
                    }

                    $table_definition['indexes'][$key_name] = $definition;
                }
            }
        }

        return $database_definition;
    }

}
