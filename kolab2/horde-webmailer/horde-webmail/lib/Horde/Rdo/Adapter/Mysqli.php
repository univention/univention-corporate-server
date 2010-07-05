<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/**
 * MySQL Improved Horde_Rdo adapter
 *
 * @category Horde
 * @package Horde_Rdo
 */
class Horde_Rdo_Adapter_Mysqli extends Horde_Rdo_Adapter {

    /**
     * Mysqli database connection object.
     *
     * @var mysqli
     */
    protected $_db = null;

    /**
     * Last generated insert_id.
     *
     * @var integer
     */
    protected $_lastInsertId;

    /**
     * Get the appropriate DML object and call the parent constructor.
     *
     * @param array $options Connection options.
     */
    public function __construct($options = array())
    {
        $this->dml = new Horde_Rdo_Query_Builder_Mysql();
        parent::__construct($options);
    }

    /**
     * Free any resources that are open.
     */
    public function __destruct()
    {
        if ($this->_db) {
            $this->_db = null;
        }
    }

    /**
     * Get a description of the database table that $model is going to
     * reflect.
     *
     * @param Horde_Rdo_Model $model The Model object to load.
     */
    public function loadModel($model)
    {
        $r = $this->_db->query('SHOW COLUMNS FROM ' . $this->dml->quoteIdentifier($model->table));
        while ($f = $r->fetch_assoc()) {
            $model->addField($f['Field'], array_change_key_case($f, CASE_LOWER));
            if ($f['Key'] == 'PRI') {
                $model->key = $f['Field'];
            }
        }

        return $model;
    }

    /**
     * Use for SELECT and anything that returns rows.
     *
     * @param string $sql A full SQL query to run.
     * @param array $bindParams Any parameters to bind to the query.
     *
     * @return PDOStatement Result set.
     */
    public function select($sql, $bindParams = array())
    {
        $statement = $this->_prepare($sql, $bindParams);
        return new Horde_Rdo_Adapter_Mysqli_Cursor($statement);
    }

    /**
     * Return a single value from a query. Useful for quickly getting
     * a value such as with a COUNT(*) query.
     *
     * @param string $sql The SQL to get one result from.
     *
     * @return mixed The first value of the first row matched by $sql.
     */
    public function selectOne($sql, $bindParams = array())
    {
        $statement = $this->_prepare($sql, $bindParams);
        if (!$statement->execute()) {
            throw new Horde_Rdo_Exception($statement->error, $statement->errno);
        }
        $statement->bind_result($value);
        $statement->fetch();
        $statement->close();

        return $value;
    }

    /**
     * Return a single column from a query.
     *
     * @param string $sql The SQL to get one column from.
     *
     * @return mixed The first column of all rows matched by $sql.
     */
    public function selectCol($sql, $bindParams = array())
    {
        $statement = $this->_prepare($sql, $bindParams);
        if (!$statement->execute()) {
            throw new Horde_Rdo_Exception($statement->error, $statement->errno);
        }
        $column = array();
        $statement->bind_result($value);
        while ($statement->fetch()) {
            $column[] = $value;
        }
        $statement->close();
        return $column;
    }

    /**
     * Use for INSERT, UPDATE, DELETE, and other queries that don't
     * return rows. Returns number of affected rows.
     *
     * @param string $sql The query to run.
     * @param array $bindParams Any parameters to bind to the query.
     *
     * @return integer The number of rows affected by $sql.
     */
    public function execute($sql, $bindParams = array())
    {
        $statement = $this->_prepare($sql, $bindParams);
        if (!$statement->execute()) {
            throw new Horde_Rdo_Exception($statement->error, $statement->errno);
        }
        $this->_lastInsertId = $statement->insert_id;
        return $statement->affected_rows;
    }

    /**
     */
    public function beginTransaction()
    {
        return $this->_db->autocommit(false);
    }

    /**
     */
    public function commit()
    {
        return $this->_db->commit();
    }

    /**
     */
    public function rollBack()
    {
        return $this->_db->rollback();
    }

    /**
     * Build a connection string and connect to the database server.
     */
    protected function _connect()
    {
        /* @TODO - any reason to use mysqli_init, mysqli_options,
         * mysqli_real_connect instead? */
        $this->_db = new mysqli($this->getOption('hostspec'),
                                $this->getOption('username'),
                                $this->getOption('password'),
                                $this->getOption('database'),
                                $this->getOption('port'),
                                $this->getOption('socket'));

        if (mysqli_connect_errno()) {
            throw new Horde_Rdo_Exception('Connect failed: (' . mysqli_connect_errno() . ') ' . mysqli_connect_error());
        }
    }

    /**
     * Prepare a statement for MySQLi - we have to detect data types
     * to call bind_param() correctly.
     *
     * @param string $stmt The statement object or raw SQL to run.
     * @param array $bindParams Any parameters to bind to the statement.
     *
     * @return mysqli_stmt A prepared statement with data bound, ready to run.
     */
    protected function _prepare($stmt, $bindParams = array())
    {
        if (!$stmt instanceof mysqli_stmt) {
            $stmt = $this->_db->prepare($stmt);
        }

        if ($stmt->param_count == 0) {
            return $stmt;
        }

        if ($stmt->param_count != count($bindParams)) {
            throw new Horde_Rdo_Exception('Expected ' . $stmt->param_count . ' parameters, got ' . count($bindParams));
        }

        // Build the type specifier string dynamically, and also do
        // some pretty spectacular workarounds for the fact that
        // bind_param() requires its arguments by reference, which
        // doesn't inherently happen with call_user_func_array().
        $i = 0;
        $types = '';
        $bindNames = array();
        foreach ($bindParams as $bindParam) {
            if (is_string($bindParam)) {
                $types .= 's';
            } elseif (is_int($bindParam)) {
                $types .= 'i';
            } elseif (is_resource($bindParam)) {
                $types .= 'b';
            } elseif (is_float($bindParam)) {
                $types .= 'd';
            } else {
                // @TODO Warning? Treat other data as strings (might
                // be an object with a __toString method).
                $types .= 's';
            }

            $bindName = 'bind' . $i++;
            $$bindName = $bindParam;
            $bindNames[] = &$$bindName;
        }

        $args = array_merge(array($types), $bindNames);
        call_user_func_array(array($stmt, 'bind_param'), $args);

        return $stmt;
    }

    /**
     * @param string $sequence The name of the sequence to get the
     * latest value in (ignored in this driver).
     *
     * @return integer The last auto-generated row id for $sequence
     */
    protected function _lastInsertId($sequence)
    {
        return $this->_lastInsertId;
    }

}
