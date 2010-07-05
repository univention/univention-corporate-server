<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Iterator for collections of Rdo objects.
 *
 * @TODO implement ArrayAccess as well?
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_List implements Iterator {

    /**
     * Rdo Mapper
     * @var Horde_Rdo_Mapper
     */
    protected $_mapper;

    /**
     * SQL query to run
     * @var string
     */
    protected $_sql;

    /**
     * Bind parameters
     * @var array
     */
    protected $_bindParams = array();

    /**
     * Result resource
     * @var Iterator
     */
    protected $_result;

    /**
     * Current object
     * @var Horde_Rdo_Base
     */
    protected $_current;

    /**
     * Current list offset.
     * @var integer
     */
    protected $_index;

    /**
     * Are we at the end of the list?
     * @var boolean
     */
    protected $_eof;

    /**
     * Constructor.
     *
     * @param mixed $query The query to run when results are
     * requested. Can be a Horde_Rdo_Query object, a literal SQL
     * query, or a tuple containing an SQL string and an array of bind
     * parameters to use.
     * @param Horde_Rdo_Mapper $mapper Mapper to create objects for this list from.
     */
    public function __construct($query, $mapper = null)
    {
        if ($query instanceof Horde_Rdo_Query) {
            // Make sure we have a Mapper object, which can be passed
            // implicitly by being set on the Query.
            if (!$mapper) {
                if (!$query->mapper) {
                    throw new Horde_Rdo_Exception('Mapper must be set on the Query object or explicitly passed.');
                }
                $mapper = $query->mapper;
            }

            // Convert the query into a SQL statement and an array of
            // bind parameters.
            list($this->_sql, $this->_bindParams) = $mapper->adapter->dml->getQuery($query);
        } elseif (is_string($query)) {
            // Straight SQL query, empty bind parameters array.
            $this->_sql = $query;
            $this->_bindParams = array();
        } else {
            // $query is already an array with SQL and bind parameters.
            list($this->_sql, $this->_bindParams) = $query;
        }

        // Keep a handle on the Mapper object for running the query.
        $this->_mapper = $mapper;
    }

    /**
     * Destructor - release any resources.
     */
    public function __destruct()
    {
        if ($this->_result) {
            unset($this->_result);
        }
    }

    /**
     * Implementation of the rewind() method for iterator.
     */
    public function rewind()
    {
        if ($this->_result) {
            unset($this->_result);
        }
        $this->_current = null;
        $this->_index = null;
        $this->_eof = true;
        $this->_result = $this->_mapper->adapter->select($this->_sql, $this->_bindParams);

        $this->next();
    }

    /**
     * Implementation of the current() method for iterator.
     *
     * @return mixed The current row, or null if no rows.
     */
    public function current()
    {
        if (is_null($this->_result)) {
            $this->rewind();
        }
        return $this->_current;
    }

    /**
     * Implementation of the key() method for iterator.
     *
     * @return mixed The current row number (starts at 0), or NULL if no rows
     */
    public function key()
    {
        if (is_null($this->_result)) {
            $this->rewind();
        }
        return $this->_index;
    }

    /**
     * Implementation of the next() method.
     *
     * @return Horde_Rdo_Base|null The next Rdo object in the set or
     * null if no more results.
     */
    public function next()
    {
        if (is_null($this->_result)) {
            $this->rewind();
        }

        if ($this->_result) {
            $row = $this->_result->fetch();
            if (!$row) {
                $this->_eof = true;
            } else {
                $this->_eof = false;

                if (is_null($this->_index)) {
                    $this->_index = 0;
                } else {
                    ++$this->_index;
                }

                $this->_current = $this->_mapper->map($row);
            }
        }

        return $this->_current;
    }

    /**
     * Implementation of the valid() method for iterator
     *
     * @return boolean Whether the iteration is valid
     */
    public function valid()
    {
        if (is_null($this->_result)) {
            $this->rewind();
        }
        return !$this->_eof;
    }

}
