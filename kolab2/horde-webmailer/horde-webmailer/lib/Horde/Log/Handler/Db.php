<?php
/**
 * Horde Log package
 *
 * This package is based on Zend_Log from the Zend Framework
 * (http://framework.zend.com).  Both that package and this
 * one were written by Mike Naberezny and Chuck Hagenbuch.
 *
 * @category Horde
 * @package  Horde_Log
 * @subpackage Handlers
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */

/**
 * @category Horde
 * @package  Horde_Log
 * @subpackage Handlers
 * @author   Mike Naberezny <mike@maintainable.com>
 * @author   Chuck Hagenbuch <chuck@horde.org>
 * @license  http://opensource.org/licenses/bsd-license.php BSD
 */
class Horde_Log_Handler_Db extends Horde_Log_Handler_Base
{
    /**
     * Database adapter instance
     * @var Horde_Db_Adapter
     */
    private $_db;

    /**
     * Name of the log table in the database
     * @var string
     */
    private $_table;

    /**
     * Options to be set by setOption().  Sets the field names in the database table.
     *
     * @var array
     */
    protected $_options = array('fieldMessage'  => 'message',
                                'fieldLevel'    => 'level');

    /**
     * Class constructor
     *
     * @param Horde_Db_Adapter $db  Database adapter instance
     * @param string $table         Log table in database
     */
    public function __construct($db, $table)
    {
        $this->_db    = $db;
        $this->_table = $table;
    }

    /**
     * Write a message to the log.
     *
     * @param  array    $event    Log event
     * @return bool               Always True
     */
    public function write($event)
    {
        $fields = array(
            $this->_options['fieldMessage'] => $event['message'],
            $this->_options['fieldLevel']   => $event['level'],
        );

        $this->_db->insert($this->_table, $fields);
        return true;
    }

}
