<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * Database adapter abstract parent class for Rdo.
 *
 * @category Horde
 * @package Horde_Rdo
 */
abstract class Horde_Rdo_Adapter {

    /**
     */
    public static function factory($adapter, $options)
    {
        // Translate Horde-style configuration arrays into the format
        // we need.
        if ($adapter == 'pdo') {
            if ($options['phptype'] == 'mysqli') {
                $adapter = 'pdo_mysql';
            } else {
                $adapter = 'pdo_' . $options['phptype'];
            }
        }

        $adapter = str_replace(' ', '_' , ucwords(str_replace('_', ' ', basename($adapter))));
        $class = 'Horde_Rdo_Adapter_' . $adapter;
        if (!class_exists($class)) {
            throw new Horde_Rdo_Exception('Adapter class "' . $class . '" not found');
        }

        return new $class($options);
    }

    /**
     * DML query generator.
     *
     * @var Horde_Rdo_Query_Builder
     */
    public $dml = null;

    /**
     * Options for this Adapter.
     *
     * @var array $options
     */
    protected $_options = array();

    /**
     * Horde_Rdo_Adapter constructor. Sets options and sets up a
     * connection if necessary.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->_options = $options;
        $this->_connect();
    }

    /**
     * Get one of the options for this Adapter.
     *
     * @param string $option The option to get.
     */
    public function getOption($option)
    {
        return isset($this->_options[$option]) ? $this->_options[$option] : null;
    }

    /**
     * Set one of the options for this Adapter.
     *
     * @param string $option The option to set.
     * @param string $value The option's value.
     */
    public function setOption($option, $value)
    {
        $this->_options[$option] = $value;
    }

    /**
     * @param mixed $query
     * @param Horde_Rdo_Mapper $mapper
     */
    public function exists($query, $mapper = null)
    {
        $query = Horde_Rdo_Query::create($query, $mapper);
        $query->setFields(1)
              ->clearSort();
        list($sql, $bindParams) = $this->dml->getQuery($query);
        return $this->selectOne($sql, $bindParams);
    }

    /**
     * @param mixed $query
     * @param Horde_Rdo_Mapper $mapper
     */
    public function count($query, $mapper = null)
    {
        $query = Horde_Rdo_Query::create($query, $mapper);
        $query->setFields('COUNT(*)')
              ->clearSort();
        list($sql, $bindParams) = $this->dml->getCount($query);
        return $this->selectOne($sql, $bindParams);
    }

    /**
     * Use for SELECT and anything that returns rows.
     *
     * @param Horde_Rdo_Query $query A Query object.
     *
     * @return mixed Result set.
     */
    public function query($query)
    {
        list($sql, $bindParams) = $this->dml->getQuery($query);
        return $this->select($sql, $bindParams);
    }

    /**
     * Return a single value from a query. Useful for quickly getting
     * a value such as with a COUNT(*) query.
     *
     * @param Horde_Rdo_Query $query The Query object to fetch one value from.
     *
     * @return mixed The first value of the first row matched by $query.
     */
    public function queryOne($query)
    {
        list($sql, $bindParams) = $this->dml->getQuery($query);
        return $this->selectOne($sql, $bindParams);
    }

    /**
     * Return a single column from a query.
     *
     * @param Horde_Rdo_Query $query The Query object to fetch one column from.
     *
     * @return mixed The first column of all rows matched by $query.
     */
    public function queryCol($query)
    {
        list($sql, $bindParams) = $this->dml->getQuery($query);
        return $this->selectCol($sql, $bindParams);
    }

    /**
     * Get a description of the database table that $model is going to
     * reflect.
     *
     * @param Horde_Rdo_Model $model The Model object to load.
     */
    abstract public function loadModel($model);

    /**
     * Create a backend object.
     *
     * @param Horde_Rdo_Mapper $mapper The Mapper creating the object.
     * @param array $fields Hash of field names/new values.
     *
     * @return integer The new object's primary key value, or throw an
     * exception if any errors occur.
     */
    public function create($mapper, $fields)
    {
        if (!$fields) {
            throw new Horde_Rdo_Exception('create() requires at least one field value.');
        }

        $sql = 'INSERT INTO ' . $this->dml->quoteIdentifier($mapper->model->table);
        $keys = array();
        $placeholders = array();
        $bindParams = array();
        foreach ($fields as $field => $value) {
            $keys[] = $this->dml->quoteIdentifier($field);
            $placeholders[] = '?';
            $bindParams[] = $value;
        }
        $sql .= ' (' . implode(', ', $keys) . ') VALUES (' . implode(', ', $placeholders) . ')';

        $this->execute($sql, $bindParams);
        return $this->_lastInsertId($mapper->model->table . '_' . $mapper->model->key . '_seq');
    }

    /**
     * Updates a backend object.
     *
     * @param Horde_Rdo_Mapper $mapper The Mapper requesting the update.
     * @param scalar $id The unique key of the object being updated.
     * @param array $fields Hash of field names/new values.
     *
     * @return integer Number of objects updated.
     */
    public function update($mapper, $id, $fields)
    {
        if (!$fields) {
            // Nothing to change.
            return true;
        }

        $sql = 'UPDATE ' . $this->dml->quoteIdentifier($mapper->model->table) . ' SET';
        $bindParams = array();
        foreach ($fields as $field => $value) {
            $sql .= ' ' . $this->dml->quoteIdentifier($field) . ' = ?,';
            $bindParams[] = $value;
        }
        $sql = substr($sql, 0, -1) . ' WHERE ' . $mapper->model->key . ' = ?';
        $bindParams[] = $id;

        return $this->execute($sql, $bindParams);
    }

    /**
     * Delete one or more objects from the database.
     *
     * @param Horde_Rdo_Mapper $mapper The Mapper requesting the deletion.
     * @param array|Horde_Rdo_Query $query Description of what to delete.
     *
     * @return integer Number of objects deleted.
     */
    public function delete($mapper, $query)
    {
        $query = Horde_Rdo_Query::create($query, $mapper);

        $clauses = array();
        $bindParams = array();
        foreach ($query->tests as $test) {
            $clauses[] = $this->dml->quoteIdentifier($test['field']) . ' ' . $test['test'] . ' ?';
            $bindParams[] = $test['value'];
        }
        if (!$clauses) {
            throw new Horde_Rdo_Exception('Refusing to delete the entire table.');
        }

        $sql = 'DELETE FROM ' . $this->dml->quoteIdentifier($mapper->model->table) .
               ' WHERE ' . implode(' ' . $query->conjunction . ' ', $clauses);

        return $this->execute($sql, $bindParams);
    }

    /**
     * Use for SELECT and anything that returns rows.
     *
     * @param string $sql A full SQL query to run.
     * @param array $bindParams Any parameters to bind to the query.
     *
     * @return PDOStatement Result set.
     */
    abstract public function select($sql, $bindParams = array());

    /**
     * Return a single value from a query. Useful for quickly getting
     * a value such as with a COUNT(*) query.
     *
     * @param string $sql The SQL to get one result from.
     *
     * @return mixed The first value of the first row matched by $sql.
     */
    abstract public function selectOne($sql, $bindParams = array());

    /**
     * Return a single column from a query.
     *
     * @param string $sql The SQL to get one column from.
     *
     * @return mixed The first column of all rows matched by $sql.
     */
    abstract public function selectCol($sql, $bindParams = array());

    /**
     * Use for INSERT, UPDATE, DELETE, and other queries that don't
     * return rows. Returns number of affected rows.
     *
     * @param string $sql The query to run.
     * @param array $bindParams Any parameters to bind to the query.
     *
     * @return integer The number of rows affected by $sql.
     */
    abstract public function execute($sql, $bindParams = array());

    /**
     */
    abstract public function beginTransaction();

    /**
     */
    abstract public function commit();

    /**
     */
    abstract public function rollBack();

}
