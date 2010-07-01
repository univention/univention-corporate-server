<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Mysqli_Cursor {

    /**
     * @var mysqli_stmt
     */
    protected $_statement;

    /**
     * @var mysqli_result
     */
    protected $_metadata;

    /**
     * @var array
     */
    protected $_columns = array();

    /**
     * @var array
     */
    protected $_values;

    /**
     * @param mysqli_stmt $statement
     */
    public function __construct(mysqli_stmt $statement)
    {
        $this->_statement = $statement;

        // Get result metadata
        $this->_metadata = $this->_statement->result_metadata();
        if ($this->_statement->errno) {
            throw new Horde_Rdo_Exception("Mysqli statement metadata error: " . $this->_stmt->error);
        }

        // Statements that have no result set do not return metadata
        if ($this->_metadata !== false) {
            // Get the column names that will result
            foreach ($this->_metadata->fetch_fields() as $column) {
                $this->_columns[] = $column->name;
            }

            // Results will be fetched with references to the $_values array.
            $this->_values = array_fill(0, count($this->_columns), null);

            // Between mysqli_stmt_bind_result() and
            // call_user_func_array() we have to build explicit
            // references to $_values.
            $refs = array();
            foreach ($this->_values as $i => &$f) {
                $refs[$i] = &$f;
            }

            // Bind the result variables
            call_user_func_array(array($this->_statement, 'bind_result'), $this->_values);
        }

        if (!$statement->execute()) {
            throw new Horde_Rdo_Exception('Unable to execute query: (' . $statement->errno . ') ' . $statement->error);
        }

        // @TODO Allow not doing this if queries aren't synchronous.
        if (!$statement->store_result()) {
            throw new Horde_Rdo_Exception('Unable to buffer query result: (' . $statement->errno . ') ' . $statement->error);
        }
    }

    /**
     */
    public function __destruct()
    {
        $this->_statement->reset();
        $this->_statement->free_result();
    }

    /**
     * @return array
     */
    public function fetch()
    {
        $result = $this->_statement->fetch();
        if (!$result) {
            $this->_statement->reset();
            $this->_statement->free_result();
            return false;
        }

        // Dereference the result values.
        $values = array();
        foreach ($this->_values as $value) {
            $values[] = $value;
        }

        return array_combine($this->_columns, $values);
    }

}
